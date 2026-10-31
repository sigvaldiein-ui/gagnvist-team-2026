# 5B-2 — YELLOW — measured target(s) failed; NO MERGE

Frozen tested executable commit: `dfb0550af71c65b2b50b38440a20ceaf846a57c0`. Later report-only commit does not change source.

Answers **7/60** (53 wrong, 0 errors); both baseline and previous round were4/60.
Single-table accepted-code first result **22/40**; stricter/different exact canonical anchor **9/40**. IS-easy accepted first table **5/10**.

## Targets recorded before measurement

- is_easy_first_table_at_least_7_of_10: FAIL
- accepted_first_table_at_least_28_of_40: FAIL
- answers_at_least_6_of_60: PASS
- no_cell_drop_over_one_from_baseline: FAIL

## Six-cell regression versus approved baseline

| Language | Level | Baseline | 5B-2 | Delta |
|---|---|---:|---:|---:|
| is | easy | 3 | 1 | -2 |
| is | medium | 0 | 0 | +0 |
| is | hard | 0 | 0 | +0 |
| en | easy | 1 | 5 | +4 |
| en | medium | 0 | 1 | +1 |
| en | hard | 0 | 0 | +0 |

## Binding contract

Only verified time conflicts go last; MATCH and UNKNOWN share a bucket. Score is a distinct content-word count over title/dimension/category labels, with missing fields adding zero. No fixed bonuses/penalties or canonical rank. Whole equal-count groups retain source order unless every member is MATCH with complete categories. Eligible groups may use unmatched dimensions; dates require externally certified equivalence. Production has no such certification map and does not guess one. Prefixes apply to Icelandic only. Top10membership and unchanged tail order were checked for all60queries. No new model calls or answer/category/arithmetic changes.

## Retrieval ablations

Macro accepted-code part recall. Any/all, full-folder anchor ranks and all language/level metrics are in measurement.json; all raw candidates/evidence are in the full review bundle.

| Stage | @1 | @5 | @10 | @100 | First accepted /40 | Exact anchor /40 |
|---|---:|---:|---:|---:|---:|---:|
| round2_prefix_both | 0.3833 | 0.7917 | 0.8417 | 0.9583 | 16 | 5 |
| is_prefix_only | 0.4833 | 0.8250 | 0.8583 | 0.9583 | 21 | 7 |
| phase5b2_final | 0.4667 | 0.8083 | 0.8583 | 0.9583 | 22 | 9 |

## Timing and validation

428 tests pass:365original+30prior retrieval+33new conformance tests. Ruff/format/mypy pass. End-to-end live answers p50/p95: 6.262/8.303s. Unsupported rows/items:8/10.
CPU rerank first-pass p50/p95:219.243/427.178ms; cached second-call p50/p95:10.324/98.268ms. The <5ms p95 target is not met for the warm benchmark. No latency is inferred from the absence of model calls.
Top10temporal states:{'UNKNOWN': 390, 'VERIFIED_MATCH': 152, 'VERIFIED_CONFLICT': 58}.

Elapsed times measure CPU-only reranking including SQLite/cache costs and scheduling, not process CPU time.

## Evidence and limits

Review bundle includes frozen source archive, full Git/blob manifest, diffs from baseline and previous executable commit,180retrieval traces with rerank evidence, all60live answers, canonical-folder audit, logs/JUnit and file hashes. Questions/evaluator/index/data SHA are retained. Historical outputs remain untouched. Both structured answer fields and selected metadata reasoning are in all60cases in measurement.json.

Calendar parsing is conservative and cannot establish every natural-language date/frequency. Unsupported or incomplete coverage is UNKNOWN. Exact canonical anchors are not the sole valid sources. The referenced external KIDDI classification/original word-pair file was not located in connected search; no replacement semantic classification was invented. Existing independent anchor audit was reused; ten synthetic open word pairs are unit cases only. No date-based ranking was activated without authoritative equivalence records.

Passing tests or targets is not independent approval. Kiddi reviews the actual code/diff and results; Silli alone decides later merge. No tuning after results, no 5B-2b/5B-3 or closed12/18access. Existing A40/model services stay running under Silli; no stop/restart/newhardware.
