# marmoset-labels-test

An open test, in progress, of the claim that common marmosets address each other with
individual "vocal labels" (names) in their phee calls:
Oren, Shapira, Lifshitz, Vinepinsky, Cohen, Fried, Hadad and Omer 2024, *Vocal labeling of
others by nonhuman primates*, Science 385:996-1003 (doi 10.1126/science.adp3757). The authors
published code and figure data on Zenodo (record 12721811, CC BY 4.0). All credit for the
recordings, the data and the original analysis goes to them.

MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents; no human expert has reviewed this
work yet. Code Apache-2.0, text CC BY 4.0.

## The question

The paper shows that a random forest can tell, from a caller's phee calls, which partner the
call was addressed to. In a pairwise recording design the partner can change together with the
recording session, the day and the caller's state. We want to know how much of the receiver
signal survives a null that keeps session and day structure fixed, or, if receivers never vary
within a session, how much better calls to different partners are separated than calls to the
same partner recorded in different sessions. This is the same kind of test we pre-registered for
the elephant "names" of Pardo et al. 2024
([elephant-names-test](https://github.com/munimtechnologies/elephant-names-test)).

## Status

* `describe_marmoset.py` (tests: `test_describe_marmoset.py`), job
  `marmoset-labels-describe-v1`: lists the variables, shapes and label counts in the four
  figure-data files and copies the authors' MATLAB scripts so that they can be read in full. It
  computes no statistic about vocal labeling. It was committed before the job produced output.
* Next: a pre-registration (design, nulls, calibration, decision rules and Brier-scored
  predictions) written from the label structure alone, before any acoustic statistic is
  computed.

Related prior work we know of: Jaakkola 2025 (Learning & Behavior, doi
10.3758/s13420-024-00662-z) questions whether the calls are names rather than receiver-specific
accommodation; the authors replied in 2025 (doi 10.3758/s13420-025-00682-3). Neither reanalyses
the data.
