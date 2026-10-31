# 5B-1 — YELLOW / NO MERGE

The fixed hybrid retrieval experiment regressed from 4/60 to 2/60 correct answers (58 wrong, 0 errors). Icelandic easy fell 3/10 → 0/10, exceeding the allowed one-answer drop. English easy rose 1/10 → 2/10; all four medium/hard cells remain 0/10. Do not merge or deploy this branch.

Tested code: `41c2079ff108d21894fdc50d4c359830475a0ba2`. Subsequent report-only commit does not change executable code. Baseline main: `a09746847e884190aa51ea9f91fab8c4c90c2088`.

## Implementation

BM25 over card text and folder + dense top100; fixed equal-weight RRF (k=60), stable full-folder identity and raw provenance. Bounded conjunction fragments are retrieval only. No domain-specific synonyms, temporal reranking, category selection, deterministic arithmetic or extra_tables implementation. No tuning against the 60 answers.

## Oracle before implementation

Dense top100 finds at least one accepted part for 58/60 and all parts for 49/60. Of 100 required parts, 41 rank 1–10, 47 rank 11–100 and 12 outside 100. Local CPU p50 5.801 ms / p95 7.751 ms; embedding excluded.

## Retrieval ablations

Macro part recall; any/all counts use the unchanged accepted table-code alternatives.

| Stage | @1 | @5 | @10 | @100 | Any / all @100 | CPU p50 / p95 ms |
|---|---:|---:|---:|---:|---:|---:|
| dense_top5 | 0.2333 | 0.3417 | 0.3417 | 0.3417 | 26 / 15 | 0.176 / 0.307 |
| dense_top100 | 0.2333 | 0.3417 | 0.4333 | 0.8917 | 58 / 49 | 6.582 / 96.119 |
| lexical | 0.4167 | 0.6833 | 0.7333 | 0.9333 | 57 / 55 | 0.804 / 1.183 |
| hybrid | 0.2583 | 0.4917 | 0.6917 | 0.9250 | 58 / 53 | 2.467 / 95.087 |
| hybrid_subqueries | 0.2417 | 0.4667 | 0.6917 | 0.9250 | 58 / 53 | 10.902 / 99.457 |

Lexical alone has stronger top1 recall than the approved fixed fusion. Broader candidate coverage did not yield better answers. The current pipeline still answers from its first selected table. A revised ranking design needs review before further code changes; these measurements do not justify changing weights or enabling lexical-only by default.

## Validation and evidence

388 tests passed (365 original + 23 new), zero failures. Ruff, format and mypy pass. Questions and evaluator unchanged; exact hashes and all 60 answer texts/verdicts/sources are in measurement.json. Full 300 retrieval traces retain raw scores, full folders, metadata and signal contributions in the review bundle. Separate canonical-folder audit validates all 100 anchor-part cells; it does not certify every alternative folder.

End-to-end answers p50 5.186 s / p95 8.114 s. Five rows contain six unsupported items. These are single-run results, not statistically established improvements. Full question retrieval embeddings are replayed Gate0 vectors; fragment embeddings were live and cached. Index construction and embedding timing are separate in retrieval-summary.json.

Original source, evaluation, data and previous evidence preserved. Main unchanged; closed 12 questions not accessed. No new GPU/storage, stop or restart. GPU snapshot: 32,519 / 46,068 MiB; existing services remain localhost only. Silli decides shutdown.

## Review request for Kiddi and Gummi

Verify unchanged evaluator/questions and frozen source SHA, reproduce oracle and ablations, inspect the Icelandic easy regression and canonical-folder ambiguity, then return a revised design decision. This draft is evidence for review, not a merge recommendation.
