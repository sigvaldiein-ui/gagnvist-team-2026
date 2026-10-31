# 5B-1 round 2 — YELLOW — measured gate failed; NO MERGE

Frozen executable commit: `58e8499ec3314a0f0465a945f4ef9603f8a9f790`. Report-only commit follows; executable source is unchanged.

Answers: **4/60**, 56 wrong, 0 execution errors (baseline 4/60; round 1: 2/60).
Single-table accepted-code top1: **16/40**. Exact canonical-anchor top1: **5/40**, a stricter/different measure. Both identities are retained; alternatives are not certified by code match.

## Gates

- accepted_first_table_at_least_16_of_40: PASS
- answers_at_least_4_of_60: PASS
- no_cell_drop_over_one_from_baseline: FAIL

## Language and level

| Language | Level | Baseline right | Round 2 right | Delta |
|---|---|---:|---:|---:|
| is | easy | 3 | 1 | -2 |
| is | medium | 0 | 0 | +0 |
| is | hard | 0 | 0 | +0 |
| en | easy | 1 | 3 | +2 |
| en | medium | 0 | 0 | +0 |
| en | hard | 0 | 0 | +0 |

## Fixed implementation

Only the approved round-2 changes: lexical1/dense1/lexical2/dense2 interleaving with full-folder deduplication, six-character normalized alphabetic prefixes in BM25 documents and queries, and subqueries disabled by default. Legacy RRF and decomposition remain solely for reproducible comparisons. No temporal/semantic reranking, category/math or multi-table changes. No weights adjusted after measurement.

## Ablations

Macro accepted-code part recall. Full grouped metrics, any/all and exact-anchor recall@1/5/10/100 are in measurement.json.

| Stage | @1 | @5 | @10 | @100 | Accepted first /40 | Exact anchor first /40 | CPU p50 / p95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| round1_rrf_subqueries | 0.2417 | 0.4667 | 0.6917 | 0.9250 | 10 | 1 | 80.665 / 112.633 |
| interleave_only | 0.4167 | 0.7167 | 0.8083 | 0.9417 | 18 | 7 | 54.132 / 99.771 |
| prefix_only | 0.3083 | 0.4917 | 0.7417 | 0.9667 | 13 | 1 | 92.274 / 98.375 |
| no_subqueries_only | 0.2583 | 0.4917 | 0.6917 | 0.9250 | 10 | 1 | 1.873 / 98.219 |
| interleave_prefix | 0.3833 | 0.7667 | 0.9000 | 0.9667 | 16 | 5 | 91.633 / 193.273 |
| round2_final | 0.3833 | 0.7917 | 0.8417 | 0.9583 | 16 | 5 | 3.388 / 96.411 |
| lexical_prefix | 0.3833 | 0.7917 | 0.8167 | 1.0000 | 16 | 5 | 0.797 / 1.227 |
| dense_top100 | 0.2333 | 0.3417 | 0.4333 | 0.8917 | 9 | 2 | 0.545 / 93.188 |

Live end-to-end latency p50 5.134 s / p95 8.411 s. Unsupported: 6 rows, 8 items.

## Reproducibility and review

395 tests pass (365 original + 30 retrieval). Ruff/format/mypy pass. The source tree, full Git blob manifest, baseline-to-round2 and round1-code-to-round2 diffs, logs, all480retrieval case traces and all60live answers are preserved in the review bundle on the existing Network Volume. Question/evaluator/index/data SHA256 and model revisions are in measurement.json. Historical reports are retained. Working-tree runtime data/local symlinks are not source changes.

The exact canonical-folder audit reuses the independent category/value validation from round1, without importing labels into retrieval. Single-table means one canonical table code across every required part: 20 easy +20medium questions. Hard20 have two canonical tables. The 16/40 approved gate uses all-parts accepted code for the first result; strict anchor scores are also shown so duplicate codes remain visible.

Reproduce using the isolated source and original data/index: `PYTHONPATH=src /workspace/gagnvist/.venv/bin/python tools/measure_5b1.py --repo /workspace/gagnvist-5b1 --baseline /workspace/gagnvist-phase4/evaluation-60.json --vectors /workspace/gagnvist-phase5b0-20261031T114552Z/results-checkpoints --out NEW_OUTPUT_DIRECTORY --answers`. Use a new output directory; never overwrite previous results. Then run the included independent audit with its output path set to the new run. Model revisions and settings must match.

Independent review by Kiddi and a later decision by Silli are still required. Passing measured gates is not approval to merge. Closed12and18sets were never accessed. No new GPU/storage; no stop/restart. Existing model services remain localhost only. Silli decides shutdown.
