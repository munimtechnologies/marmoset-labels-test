# marmoset-labels-test

An open test of the claim that common marmosets use individual "vocal labels" (names) in phee
calls (Oren et al. 2024, Science 385:996-1003, doi 10.1126/science.adp3757).

MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents; no human expert has reviewed this
work yet. Code Apache-2.0, text CC BY 4.0. The recordings, data and analysis are the authors'
work; their code and figure data are on Zenodo (record 12721811, CC BY 4.0).

## Status: closed, the test cannot be run from public data (2026-11-20)
See `DATA-NOTE.md`. The public record holds figure-level summaries and pooled pairwise
proximity ranks, but no per-call features, call identifiers, session, day or recording time.
A receiver null blocked by session and day therefore cannot be built. We stop here without a
result. This says nothing either way about whether marmoset vocal labels are real.

## The question we wanted to ask
The paper's random forest identifies the intended partner from a caller's phee calls. In a
pairwise design, partner identity can change together with session, day and the caller's
state. We planned to measure how much receiver signal survives a null that keeps session and
day structure fixed, as in our pre-registered test of the elephant "names" claim
(github.com/munimtechnologies/elephant-names-test).

## Files
* `describe_marmoset.py` + tests: lists the variables, shapes and label counts of the four
  figure-data files and copies the authors' MATLAB scripts. It computes no statistic about
  vocal labelling, and it was committed before it produced any output.
* `results/marmoset_describe.json`: its output (job `marmoset-labels-describe-v1`).
* `DATA-NOTE.md`: what the files contain and why the blocked test is impossible.

## Related work
Jaakkola 2025 (Learning & Behavior, doi 10.3758/s13420-024-00662-z) asks whether the calls are
names or receiver-specific accommodation; the authors replied in 2025 (doi
10.3758/s13420-025-00682-3). Neither reanalyses the data.
