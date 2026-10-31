# 5B-3: grounded answers on frozen 5B-2 retrieval

Authority: Silli's GREEN on PR #5, comment 6547533166, and direct Codex approval.
Work stays on feature/5b1-hybrid-retrieval-20261031. No main merge or deployment.

The search tree, configuration, evaluator, 60 open questions, vector index and PX
parser are byte-for-byte unchanged from dfb0550. No closed tests are read or run.

## Three changes

1. Category selection also returns per-dimension scope. A total guard corrects only
an explicitly `unspecified` dimension with one unique total. Time and measure
dimensions and category wording in the question veto correction. Missing/uncertain
scope and missing/ambiguous totals abstain; notes retain this decision. Existing
proposal validation/default behavior remains. Semantic scope still depends on the
model; the guard cannot certify every paraphrase or detect every selection error.

2. A second JSON call proposes only operations and fetched cell IDs. Python rejects
extra fields (including numeric operands), nonexistent or duplicate IDs, wrong roles,
period-mode disagreement, missing/non-finite values, incompatible/ambiguous units,
unverified period order and zero denominators. References retain full folder,
category codes, labels, original value, marker, unit and period_mode. The existing
PX header parser supplies units; its grammar is unchanged. Arithmetic is Decimal
with precision 28 and displayed with at most ten decimals. Operations: published
value, difference, percent change, subgroup share and ratio. No automatic unit
conversion, arbitrary sums, extra tables or new temporal parsing is introduced.
Order is explicit in operand_roles; chronological change additionally verifies
new > old and matching granularity using the frozen category-period reader.
For non-temporal comparisons, left/right remains a semantic model choice visible
in the rendered operand descriptions and trace, not a proven interpretation.

3. Deterministic bilingual templates render validated values and operand facts.
No model-authored number or prose enters the final answer. Rejected/empty plans
produce a visible warning and display fetched cells, never their unverified result.
The unchanged unsupported-number function runs both against original sources and
against original sources plus explicitly validated calculated values. Both lists
are saved; calculation records expose each added value and its references.
This supports provenance, not proof that the chosen table/cells answer the question.

## Measurement

Run the previous 428 tests plus new synthetic guard/provenance/arithmetic tests,
Ruff, format and mypy. Freeze executable commit before running all 60 open questions
once. No post-measurement tuning. Preserve original 4/60 and 5B-2 7/60 results.

Report all cases, original scoring, warnings, unsupported lists, references, plans,
validated/rejected calculations, timings, 3x2 cells and checksums. Compare candidate
order with 5B-2 as well as byte identity of frozen search/configuration.

Gates: >=14/60, IS-easy >=3/10, no 3x2 cell drops more than one from original 4/60,
and no unsupported numbers in officially correct answers. A warning-bearing answer
may still score correct under the unchanged evaluator; report that limitation.

A40 stays running at Silli's instruction. Kiddi independently reviews. Only Silli
may authorize a later merge. Performance gates are targets, not promised outcomes.
