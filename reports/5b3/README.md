# 5B-3 — STOPPED / INCOMPLETE / NO MERGE

**460 tests pass, but the live 60-question measurement stopped on its fifth case.**
3 right, 1 wrong, 1 execution error; 55 NOT_RUN. No 60-question accuracy or improvement claim.

Frozen executable: `94346a68309b7bf0b84b9c761bab02cbb27c839f`; tree `202bad310065e5617ff0a082c6a56f3d6b24b9b7`.
All application/evaluation source remained frozen after measurement began. Historical 4/60 and 7/60 are preserved.

## Failure

`births-2024-en`: `ModelError: the model did not answer with JSON: '[]'`.
Category selection returned an object. The answer-plan call returned an empty array, not an object with outputs. ModelClient rejected it before the new gate could render a visible structured rejection; the harness then stopped. GPU/services remained healthy. The server-side reason for violating the supplied schema is not established. No retry or post-result tuning was performed.

## Six cells (incomplete, not a full comparison)

| Language | Level | Original 4/60 | 5B-2 7/60 | Right observed | Wrong | Error | NOT_RUN |
|---|---|---:|---:|---:|---:|---:|---:|
| is | easy | 3 | 1 | 1 | 1 | 0 | 8 |
| is | medium | 0 | 0 | 0 | 0 | 0 | 10 |
| is | hard | 0 | 0 | 0 | 0 | 0 | 10 |
| en | easy | 1 | 5 | 2 | 0 | 1 | 7 |
| en | medium | 0 | 1 | 0 | 0 | 0 | 10 |
| en | hard | 0 | 0 | 0 | 0 | 0 | 10 |

## Validation and limitations

460/460 tests (428 previous + 32 new); Ruff, format and mypy PASS. The integration coverage missed malformed live planner JSON: new tests directly exercise the gate, while the old stand-in does not implement this failure path.
Four returned cell values and labels were reread from the original PX files and all four verified outputs independently recomputed. No completed answer had unsupported numbers. No nontrivial calculation completed before the stop.
The 14/60, IS-easy 3/10 and regression gates are NOT EVALUABLE. The unsupported gate holds only for the three observed correct answers. These are not passed release gates.
Full 60-case status table, partial timing values, raw plan/category trace, cell references, logs, source archive, Git tree and byte-identity manifest are included. NOT_RUN fields are null. No closed tests were accessed.

## Proposed next change — for review, not implemented

See NEXT_CHANGE_PROPOSAL.md: typed handling of malformed structured replies at the planner boundary, explicit rejection/provenance, failure-path trace, and API-level regression tests. Freeze a new reviewed commit before a fresh full measurement; preserve this attempt.

## Operations

Existing A40 remains RUNNING at 0.59 USD/hour, 32,621 / 46,068 MiB used (70.8%). Qwen and BGE-M3 remain localhost-only. Network volume: 27G used, 67G available at the recorded check. No infrastructure lifecycle changes. Silli decides when to stop it.

## All 60 statuses

| ID | Language | Level | Result | Seconds |
|---|---|---|---|---:|
| population-iceland-2026-en | en | easy | right | 8.448 |
| population-iceland-2026-is | is | easy | right | 8.260 |
| population-reykjavik-en | en | easy | right | 7.680 |
| population-reykjavik-is | is | easy | WRONG | 6.356 |
| births-2024-en | en | easy | error | 6.197 |
| births-2024-is | is | easy | NOT_RUN | — |
| cpi-2026-09-en | en | easy | NOT_RUN | — |
| cpi-2026-09-is | is | easy | NOT_RUN | — |
| wage-index-2026-08-en | en | easy | NOT_RUN | — |
| wage-index-2026-08-is | is | easy | NOT_RUN | — |
| unemployment-2026q2-en | en | easy | NOT_RUN | — |
| unemployment-2026q2-is | is | easy | NOT_RUN | — |
| gdp-2025-en | en | easy | NOT_RUN | — |
| gdp-2025-is | is | easy | NOT_RUN | — |
| overnight-stays-2025-en | en | easy | NOT_RUN | — |
| overnight-stays-2025-is | is | easy | NOT_RUN | — |
| immigrants-2026-en | en | easy | NOT_RUN | — |
| immigrants-2026-is | is | easy | NOT_RUN | — |
| vigdis-1980-en | en | easy | NOT_RUN | — |
| vigdis-1980-is | is | easy | NOT_RUN | — |
| reykjavik-growth-2026-en | en | medium | NOT_RUN | — |
| reykjavik-growth-2026-is | is | medium | NOT_RUN | — |
| reykjavik-share-2026-en | en | medium | NOT_RUN | — |
| reykjavik-share-2026-is | is | medium | NOT_RUN | — |
| reykjavik-kopavogur-2026-en | en | medium | NOT_RUN | — |
| reykjavik-kopavogur-2026-is | is | medium | NOT_RUN | — |
| men-minus-women-2026-en | en | medium | NOT_RUN | — |
| men-minus-women-2026-is | is | medium | NOT_RUN | — |
| cpi-points-2026-en | en | medium | NOT_RUN | — |
| cpi-points-2026-is | is | medium | NOT_RUN | — |
| overnight-stays-change-2025-en | en | medium | NOT_RUN | — |
| overnight-stays-change-2025-is | is | medium | NOT_RUN | — |
| women-share-2026-en | en | medium | NOT_RUN | — |
| women-share-2026-is | is | medium | NOT_RUN | — |
| wage-index-points-2026-08-en | en | medium | NOT_RUN | — |
| wage-index-points-2026-08-is | is | medium | NOT_RUN | — |
| immigrants-growth-2026-en | en | medium | NOT_RUN | — |
| immigrants-growth-2026-is | is | medium | NOT_RUN | — |
| foreign-stays-share-2025-en | en | medium | NOT_RUN | — |
| foreign-stays-share-2025-is | is | medium | NOT_RUN | — |
| population-and-cpi-2026-en | en | hard | NOT_RUN | — |
| population-and-cpi-2026-is | is | hard | NOT_RUN | — |
| wages-and-prices-2026-08-en | en | hard | NOT_RUN | — |
| wages-and-prices-2026-08-is | is | hard | NOT_RUN | — |
| stays-and-population-2025-en | en | hard | NOT_RUN | — |
| stays-and-population-2025-is | is | hard | NOT_RUN | — |
| gdp-and-births-2025-en | en | hard | NOT_RUN | — |
| gdp-and-births-2025-is | is | hard | NOT_RUN | — |
| stays-per-inhabitant-2025-en | en | hard | NOT_RUN | — |
| stays-per-inhabitant-2025-is | is | hard | NOT_RUN | — |
| births-per-1000-2025-en | en | hard | NOT_RUN | — |
| births-per-1000-2025-is | is | hard | NOT_RUN | — |
| wages-and-unemployment-2026-en | en | hard | NOT_RUN | — |
| wages-and-unemployment-2026-is | is | hard | NOT_RUN | — |
| gdp-and-stays-2025-en | en | hard | NOT_RUN | — |
| gdp-and-stays-2025-is | is | hard | NOT_RUN | — |
| births-and-immigrants-2026-en | en | hard | NOT_RUN | — |
| births-and-immigrants-2026-is | is | hard | NOT_RUN | — |
| cpi-and-unemployment-2026-en | en | hard | NOT_RUN | — |
| cpi-and-unemployment-2026-is | is | hard | NOT_RUN | — |
