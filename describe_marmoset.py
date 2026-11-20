# SPDX-License-Identifier: Apache-2.0
# describe_marmoset.py: a label-and-structure description of the public data of Oren et al.
# 2024, "Vocal labeling of others by nonhuman primates" (Science 385:996-1003; Zenodo record
# 12721811, CC BY 4.0). It lists every variable in Fig_1.mat .. Fig_4.mat (name, MATLAB class,
# shape, dtype), summarises numeric arrays (min, max, mean, NaN count) and counts the values of
# small label-like arrays (caller, callee, session, date, file names), and copies the authors'
# MATLAB scripts to the output so that they can be read in full. It computes no statistic about
# vocal labeling: it exists so that a later test can be designed, and pre-registered, knowing only
# the label structure (who called whom, in which session or on which day).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import hashlib
import json
import os
import shutil
import sys
import time
import urllib.request

import numpy as np

RECORD = "12721811"
URL = "https://zenodo.org/api/records/%s/files/%s/content"
MAT = {"Fig_1.mat": "67d0bb040028263598b0ea48f3ce6f72",
       "Fig_2.mat": "d9b20b599b2ca34b4c175762fe0e95b6",
       "Fig_3.mat": "a8003082efc09e16f8bfb32a6585e6c6",
       "Fig_4.mat": "8448257ca329dfde042a58db8b96da5c"}
CODE = {"calc_medoid.m": "aa09718f67eec683f756efc9c8a00c55",
        "calc_examplars.m": "e0ec3e3756670edd491667706acefa3a",
        "calc_immitation.m": "445e594bf2e5c86e210e4ad2fbd9034a",
        "spectrogramming.m": "0ba89491ad15f250bc727728fd3c37a3",
        "calc_acoustic_features.m": "070fae388b2f33033036f8b7d712145c",
        "RUS.m": "f3cf6267c48760714d70ad14eb2d11b0",
        "calc_proximity.m": "7b6e69e8276e8667f6e0c1915c91b6bb",
        "majorityVoting.m": "405937b6dbf461d703e377e54cda03c1",
        "calssify_all_monkey.m": "98d0fc22f5edd063a733c7740eade04c",
        "calc_roc.m": "bc5d9fc35a6bc15d86ce6a64e6fd58ef",
        "RF_Generic.m": "d416c756f8fd6d9ecce41738bf0bd7f0"}
MAX_UNIQUE = 80            # value counts are listed only for arrays with at most this many values
MAX_COUNT_ELEMS = 5000000  # and at most this many elements
MAX_LOAD_BYTES = 0.7e9     # variables estimated larger than this are listed but not loaded
MAX_DEPTH = 6
MAX_FIELDS = 60
MAX_CELL_SHOW = 3


# ---------------------------------------------------------------- generic description
def as_str(x):
    """A MATLAB char / one-element string-like value as a Python str, else None."""
    if isinstance(x, bytes):
        return x.decode("utf-8", "replace")
    if isinstance(x, str):
        return x
    if isinstance(x, np.ndarray) and x.dtype.kind in "US":
        if x.size == 0:
            return ""
        if x.size == 1:
            v = x.reshape(-1)[0]
            return v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v)
    if isinstance(x, np.str_):
        return str(x)
    return None


def counts_of(values):
    """Value counts (as a sorted list of [value, count]) if there are at most MAX_UNIQUE
    distinct values, else just the number of distinct values."""
    c = {}
    for v in values:
        c[v] = c.get(v, 0) + 1
    if len(c) > MAX_UNIQUE:
        return {"n_unique": len(c)}
    return {"n_unique": len(c),
            "counts": sorted([[k, n] for k, n in c.items()], key=lambda kv: str(kv[0]))}


def describe_numeric(a):
    out = {"type": "numeric", "dtype": str(a.dtype), "shape": list(a.shape)}
    if a.size == 0:
        return out
    if a.dtype.kind == "c":
        a = np.abs(a)
        out["complex"] = True
    x = a.astype(float, copy=False).reshape(-1)
    fin = np.isfinite(x)
    out["n_nan"] = int(np.sum(np.isnan(x)))
    out["n_inf"] = int(np.sum(np.isinf(x)))
    if fin.any():
        xf = x[fin]
        out.update(min=float(xf.min()), max=float(xf.max()), mean=float(xf.mean()))
        out["integer_valued"] = bool(np.all(xf == np.round(xf)))
    if a.size <= 20:
        out["values"] = [float(v) if np.isfinite(v) else str(v) for v in x]
    elif a.size <= MAX_COUNT_ELEMS:
        u = np.unique(x[fin]) if fin.any() else np.array([])
        if len(u) <= MAX_UNIQUE:
            vals = x[fin]
            out["value_counts"] = [[float(v), int(np.sum(vals == v))] for v in u]
        else:
            out["n_unique"] = int(len(u))
    return out


def describe(obj, depth=0):
    """A JSON-ready description of one value loaded by scipy.io.loadmat
    (squeeze_me=True, struct_as_record=False)."""
    from scipy.io.matlab import mat_struct
    try:
        from scipy.io.matlab import MatlabOpaque
    except ImportError:  # pragma: no cover
        MatlabOpaque = ()
    if depth > MAX_DEPTH:
        return {"type": "too_deep"}
    s = as_str(obj)
    if s is not None:
        return {"type": "str", "value": s[:200], "len": len(s)}
    if isinstance(obj, (bool, np.bool_)):
        return {"type": "bool", "value": bool(obj)}
    if isinstance(obj, (int, float, np.integer, np.floating)):
        return {"type": "scalar", "value": float(obj)}
    if isinstance(obj, mat_struct):
        names = list(getattr(obj, "_fieldnames", []))
        return {"type": "struct", "fields": names,
                "values": {k: describe(getattr(obj, k), depth + 1) for k in names[:MAX_FIELDS]}}
    if MatlabOpaque and isinstance(obj, MatlabOpaque):
        return {"type": "opaque", "repr": repr(obj)[:300]}
    if isinstance(obj, np.ndarray):
        if obj.dtype.names:
            names = list(obj.dtype.names)
            first = obj.reshape(-1)[0] if obj.size else None
            return {"type": "struct_array", "shape": list(obj.shape), "fields": names,
                    "first": ({k: describe(first[k], depth + 1) for k in names[:MAX_FIELDS]}
                              if first is not None else None)}
        if obj.dtype.kind in "US":
            flat = [as_str(v) if not isinstance(v, str) else v for v in obj.reshape(-1)]
            return dict({"type": "str_array", "shape": list(obj.shape)}, **counts_of(flat))
        if obj.dtype.kind == "O":
            flat = list(obj.reshape(-1))
            out = {"type": "cell", "shape": list(obj.shape)}
            strs = [as_str(v) for v in flat]
            if flat and all(s is not None for s in strs):
                out["all_str"] = True
                out.update(counts_of(strs))
                out["first"] = strs[:MAX_CELL_SHOW]
                return out
            nums = [v for v in flat if isinstance(v, (int, float, np.integer, np.floating))]
            if flat and len(nums) == len(flat):
                out["all_scalar"] = True
                out.update(describe_numeric(np.array(nums, dtype=float)))
                out["type"] = "cell"
                return out
            out["first"] = [describe(v, depth + 1) for v in flat[:MAX_CELL_SHOW]]
            kinds = {}
            for v in flat:
                k = type(v).__name__
                if isinstance(v, np.ndarray):
                    k += ":" + v.dtype.kind + ":" + "x".join(str(d) for d in v.shape)
                kinds[k] = kinds.get(k, 0) + 1
            out["element_kinds"] = sorted([[k, n] for k, n in kinds.items()])[:20]
            return out
        if obj.dtype.kind in "biufc":
            return describe_numeric(obj)
        return {"type": "ndarray_other", "dtype": str(obj.dtype), "shape": list(obj.shape)}
    return {"type": type(obj).__name__, "repr": repr(obj)[:300]}


# ---------------------------------------------------------------- MAT v5 and v7.3
def header(path):
    with open(path, "rb") as f:
        h = f.read(128)
    return h[:116].decode("latin-1", "replace").rstrip(" \x00")


def is_hdf5(path):
    with open(path, "rb") as f:
        f.seek(512)
        return f.read(8) == b"\x89HDF\r\n\x1a\n"


def est_bytes(shape, cls):
    n = 1
    for d in shape:
        n *= int(d)
    per = {"double": 8, "single": 4, "int64": 8, "uint64": 8, "int32": 4, "uint32": 4,
           "int16": 2, "uint16": 2, "int8": 1, "uint8": 1, "logical": 1, "char": 2}
    return n * per.get(cls, 64)


def describe_v5(path, log=print):
    import scipy.io
    out = {}
    for name, shape, cls in scipy.io.whosmat(path):
        e = {"class": cls, "shape": list(shape), "est_bytes": est_bytes(shape, cls)}
        if e["est_bytes"] > MAX_LOAD_BYTES:
            e["skipped"] = "too large to load"
        else:
            try:
                d = scipy.io.loadmat(path, variable_names=[name], squeeze_me=True,
                                     struct_as_record=False, chars_as_strings=True)
                e["value"] = describe(d.get(name))
            except Exception as ex:  # noqa: BLE001 - record and go on
                e["error"] = "%s: %s" % (type(ex).__name__, str(ex)[:300])
        log("  %s %s %s" % (name, cls, shape))
        out[name] = e
    return out


def describe_h5(path, log=print):
    import h5py
    out = {}

    def attrs(o):
        a = {}
        for k, v in o.attrs.items():
            if isinstance(v, bytes):
                v = v.decode("utf-8", "replace")
            elif isinstance(v, np.ndarray):
                v = v.tolist() if v.size <= 10 else "array%s" % (list(v.shape),)
            elif isinstance(v, np.generic):
                v = v.item()
            a[k] = v if isinstance(v, (str, int, float, list, bool)) else repr(v)[:100]
        return a

    def visit(name, o):
        if name.startswith("#refs#") or name.startswith("#subsystem#"):
            return
        e = {"kind": "group" if isinstance(o, h5py.Group) else "dataset", "attrs": attrs(o)}
        if isinstance(o, h5py.Dataset):
            e.update(shape=list(o.shape), dtype=str(o.dtype))
            cls = e["attrs"].get("MATLAB_class")
            try:
                if cls == "char" and o.size <= 10000:
                    e["value"] = "".join(chr(int(c)) for c in np.array(o).reshape(-1, order="F"))[:200]
                elif o.dtype.kind in "biufc" and o.size * o.dtype.itemsize <= MAX_LOAD_BYTES:
                    e["value"] = describe_numeric(np.array(o))
                elif o.dtype.kind == "O" and o.size:
                    refs = np.array(o).reshape(-1)
                    shown = []
                    for r in refs[:MAX_CELL_SHOW]:
                        t = o.file[r]
                        tc = t.attrs.get("MATLAB_class")
                        tc = tc.decode() if isinstance(tc, bytes) else tc
                        item = {"class": tc, "shape": list(t.shape)}
                        if tc == "char" and t.size <= 1000:
                            item["value"] = "".join(chr(int(c)) for c in np.array(t).reshape(-1, order="F"))
                        shown.append(item)
                    e["first"] = shown
                    if o.size <= 200000:
                        vals = []
                        for r in refs:
                            t = o.file[r]
                            tc = t.attrs.get("MATLAB_class")
                            tc = tc.decode() if isinstance(tc, bytes) else tc
                            if tc == "char" and t.size <= 1000:
                                vals.append("".join(chr(int(c)) for c in np.array(t).reshape(-1, order="F")))
                            else:
                                vals = None
                                break
                        if vals is not None:
                            e["all_str"] = True
                            e.update(counts_of(vals))
            except Exception as ex:  # noqa: BLE001
                e["error"] = "%s: %s" % (type(ex).__name__, str(ex)[:300])
        log("  %s %s" % (name, e.get("shape", "")))
        out[name] = e

    with h5py.File(path, "r") as f:
        f.visititems(visit)
    return out


# ---------------------------------------------------------------- main
def fetch(url, timeout=600):
    req = urllib.request.Request(url, headers={"User-Agent": "marmoset-describe/1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def get(data_dir, name, md5):
    path = os.path.join(data_dir, name)
    for attempt in range(2):
        if attempt or not os.path.exists(path):
            blob = fetch(URL % (RECORD, name))
            with open(path + ".part", "wb") as f:
                f.write(blob)
            os.replace(path + ".part", path)
        if md5_file(path) == md5:
            return path, True
    return path, False


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="/data/marmoset")
    ap.add_argument("--out-dir", default="/out")
    a = ap.parse_args(argv)
    os.makedirs(a.data_dir, exist_ok=True)
    os.makedirs(os.path.join(a.out_dir, "m"), exist_ok=True)
    import scipy
    out = {"record": RECORD, "python": sys.version.split()[0], "numpy": np.__version__,
           "scipy": scipy.__version__,
           "utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "code": {},
           "files": {}}
    for name, md5 in sorted(CODE.items()):
        try:
            path, ok = get(a.data_dir, name, md5)
            shutil.copy(path, os.path.join(a.out_dir, "m", name))
            out["code"][name] = {"md5_ok": ok}
        except Exception as ex:  # noqa: BLE001
            out["code"][name] = {"error": "%s: %s" % (type(ex).__name__, str(ex)[:200])}
    for name, md5 in sorted(MAT.items()):
        e = {}
        try:
            path, ok = get(a.data_dir, name, md5)
            e.update(md5_ok=ok, bytes=os.path.getsize(path), header=header(path),
                     hdf5=is_hdf5(path))
            print(name, e["header"], flush=True)
            e["variables"] = (describe_h5(path) if e["hdf5"] else describe_v5(path))
        except Exception as ex:  # noqa: BLE001
            e["error"] = "%s: %s" % (type(ex).__name__, str(ex)[:300])
        out["files"][name] = e
        with open(os.path.join(a.out_dir, "marmoset_describe.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=str)
    out["utc_end"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(a.out_dir, "marmoset_describe.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=str)
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "variables"}
                      for k, v in out["files"].items()}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
