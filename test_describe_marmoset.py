# SPDX-License-Identifier: Apache-2.0
# Tests for describe_marmoset.py (run as the first step of job marmoset-describe-v1).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import os
import tempfile
import unittest

import numpy as np
import scipy.io

import describe_marmoset as dm


class TestDescribe(unittest.TestCase):
    def test_as_str(self):
        self.assertEqual(dm.as_str("ab"), "ab")
        self.assertEqual(dm.as_str(b"ab"), "ab")
        self.assertEqual(dm.as_str(np.array(["xy"])), "xy")
        self.assertEqual(dm.as_str(np.array([], dtype="<U1")), "")
        self.assertIsNone(dm.as_str(np.array([1.0])))
        self.assertIsNone(dm.as_str(3.0))

    def test_counts(self):
        self.assertEqual(dm.counts_of(["b", "a", "b"]),
                         {"n_unique": 2, "counts": [["a", 1], ["b", 2]]})
        self.assertEqual(dm.counts_of(range(dm.MAX_UNIQUE + 1)),
                         {"n_unique": dm.MAX_UNIQUE + 1})

    def test_numeric(self):
        d = dm.describe_numeric(np.array([[1.0, 2.0], [2.0, np.nan]]))
        self.assertEqual(d["shape"], [2, 2])
        self.assertEqual(d["n_nan"], 1)
        self.assertEqual((d["min"], d["max"]), (1.0, 2.0))
        self.assertAlmostEqual(d["mean"], 5.0 / 3.0)
        self.assertTrue(d["integer_valued"])
        self.assertEqual(d["values"], [1.0, 2.0, 2.0, "nan"])
        d = dm.describe_numeric(np.arange(30) % 3)
        self.assertEqual(d["value_counts"], [[0.0, 10], [1.0, 10], [2.0, 10]])
        d = dm.describe_numeric(np.arange(200) / 7.0)
        self.assertEqual(d["n_unique"], 200)
        self.assertFalse(d["integer_valued"])

    def test_v5_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "t.mat")
            cell = np.empty((4,), dtype=object)
            cell[:] = ["Ana", "Bob", "Ana", "Cy"]
            scipy.io.savemat(p, {"callee": cell, "x": np.ones((3, 5)),
                                 "s": {"date": "2023-01-02", "n": 3.0}})
            self.assertFalse(dm.is_hdf5(p))
            self.assertTrue(dm.header(p).startswith("MATLAB 5.0 MAT-file"))
            v = dm.describe_v5(p, log=lambda m: None)
            self.assertEqual(sorted(v), ["callee", "s", "x"])
            c = v["callee"]["value"]
            self.assertEqual(c["type"], "cell")
            self.assertTrue(c["all_str"])
            self.assertEqual(c["counts"], [["Ana", 2], ["Bob", 1], ["Cy", 1]])
            x = v["x"]["value"]
            self.assertEqual(x["shape"], [3, 5])
            self.assertEqual(x["mean"], 1.0)
            s = v["s"]["value"]
            self.assertEqual(s["type"], "struct")
            self.assertEqual(sorted(s["fields"]), ["date", "n"])
            self.assertEqual(s["values"]["date"]["value"], "2023-01-02")
            self.assertEqual(s["values"]["n"], {"type": "scalar", "value": 3.0})

    def test_h5(self):
        try:
            import h5py
        except ImportError:
            self.skipTest("h5py not installed")
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "t73.mat")
            with h5py.File(p, "w", userblock_size=512) as f:
                d = f.create_dataset("x", data=np.arange(6.0).reshape(2, 3))
                d.attrs["MATLAB_class"] = np.bytes_(b"double")
                c = f.create_dataset("name", data=np.array([[97], [98], [99]], dtype=np.uint16))
                c.attrs["MATLAB_class"] = np.bytes_(b"char")
            self.assertTrue(dm.is_hdf5(p))
            v = dm.describe_h5(p, log=lambda m: None)
            self.assertEqual(sorted(v), ["name", "x"])
            self.assertEqual(v["name"]["value"], "abc")
            self.assertEqual(v["x"]["value"]["shape"], [2, 3])
            self.assertEqual(v["x"]["value"]["max"], 5.0)
            self.assertEqual(v["x"]["attrs"]["MATLAB_class"], "double")


if __name__ == "__main__":
    unittest.main()
