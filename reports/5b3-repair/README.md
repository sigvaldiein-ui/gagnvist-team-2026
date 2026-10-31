# 5B-3 repair — YELLOW — MEASURED GATE(S) FAILED — NO MERGE

Full frozen run: **9/60 right, 51 wrong, 0 execution errors**.
Executable commit: `a99385390ff2f52a3cb38522fc450bfacb6b6e3b`; tree `9666c2b49c1549e4bf1d5f3efdcd91a2dc5ab625`.
One repair code commit. No executable changes after measurement. Original 4/60, 5B-2 7/60 and the incomplete first 5B-3 attempt are preserved.

## Gates

| Gate | Result |
|---|---|
| at_least_14 | FAIL |
| is_easy_at_least_3 | FAIL |
| no_cell_drops_more_than_one | FAIL |
| correct_answers_have_no_unsupported | PASS |

## Six-cell comparison

| Language | Level | Original | 5B-2 | Repaired 5B-3 | Delta from original |
|---|---|---:|---:|---:|---:|
| is | easy | 3 | 1 | 1 | -2 |
| is | medium | 0 | 0 | 1 | +1 |
| is | hard | 0 | 0 | 0 | +0 |
| en | easy | 1 | 5 | 5 | +4 |
| en | medium | 0 | 1 | 2 | +2 |
| en | hard | 0 | 0 | 0 | +0 |

## Exactly the reviewed repair

1. Malformed/invalid/none planner output falls back to the unchanged 5B-2 factual writer. Notes, cell_references, period_mode and unsupported checks remain. A malformed factual-writer payload falls back to raw facts; service failures propagate.
2. Planner schema is an object with an enumerated operation and nonempty zero-based integer operands. Python validates the shape and indices independently. No invented operand values. Existing unit/period checks remain; zero and near-zero denominators are rejected.
3. Thirty additional tests cover malformed replies through the real client and pipeline, missing/invalid operands, division guards, and HTTP/connect/timeout propagation. All 490 tests pass; Ruff/format/mypy pass.
4. Measurement distinguishes content failures from service failures. It records failed and successful calls and stops only on a model-service failure. No question is retried.

## Runtime evidence

Fallback rows: 53/60. Verified nontrivial calculations: 7. Rejected calculations: 2. Unsupported rows/items: 5/7.
Answer latency p50/p95: 9.222/12.440 seconds. Full candidate order matched 5B-2 for 60/60 cases.
Provenance audit reread 86 selected cells from PX files and recomputed 7 verified outputs. It confirms values/arithmetic, not semantic correctness.
Two synthetic API tests returned [] even with object schemas. This demonstrates that the served path did not enforce the supplied root shape in those calls; the exact backend/configuration cause is not established. The original 5B-3 production schema already required an object. No service configuration or model weights were changed.

## Limits and review

Passing recovery tests does not guarantee equal or better answer accuracy. Category choices, factual-writer wording and retrieval errors remain. This is one run on the 60 open development questions, not a closed-set or generalization result. No new search/category/evaluator/model tuning occurred in this repair. No sums, conversions or extra-table support were introduced.
The reviewer bundle includes the exact repair diff, source archive, failed/successful model trace, all 60 outcomes, references, timing/GPU samples, test logs, SHA manifests and the server-schema diagnostic. Kiddi reviews the diff and measurements together. Main merge still requires separate approval.
The existing A40 and both localhost services remain running at Silli's instruction. No new hardware/storage or lifecycle mutation.


## Evidence delivery

The complete case-by-case JSON and HTML, raw model outputs and logs are in the locally delivered review ZIP described in [EVIDENCE.md](EVIDENCE.md). GitHub receives this aggregate summary only. Automatic approval review rejected publishing the detailed payload; no detailed results or traces were uploaded here.
