# 5B-2 — frozen four-stage metadata contract

Authorized by Silli in Codex, 2026-10-31. Supersedes incompatible earlier
score proposals. [Binding design and review history](https://docs.google.com/document/d/1wh6ld1OgrPkPb4pZVI2li4Gd1iBQbMJW5etRsqwkIXg/edit).
No main merge, 5B-2b, 5B-3, model-based selection or closed-test access.

The configured pipeline first uses existing lexical/dense interleaving with
subqueries disabled. Six-character alphabetic prefixes now apply only to
Icelandic, in both lexical retrieval and metadata matching. English uses full
words. `prefix_language="all"` remains solely to reproduce the old ablation.

Only the first ten candidates are reordered. Their membership, full folders,
raw scores and retrieval signals are retained. The tail is unchanged. Answering
still reads candidate 1 with the existing category/number/answer modules.

1. **Bucket:** VERIFIED_CONFLICT goes after non-conflict. MATCH and UNKNOWN have
   identical priority in this bucket step. No hard removal and no numeric penalty.
2. **Count:** descending number of distinct normalized alphabetic content tokens
   of the question found anywhere in title, dimension labels or category labels.
   Uses the existing grammatical stoplist; no domain synonyms or answer mappings.
   An absent field adds zero. Repetition, year digits, source rank, time match,
   canonical folder and update date add no word-count points.
3. **Whole equal-count group within one bucket:** unless **every** candidate is
   MATCH with nonempty dimension codes/labels and all category codes/labels, keep
   the whole group's source order. Otherwise fewer unmatched dimensions may lead.
   A dimension is matched by overlap in its label/category labels, or by a verified
   explicit period for a time dimension. This never selects category values.
   Dates apply only within contiguous, externally certified equivalent peers
   with equal unmatched-dimension counts and all valid dates. A title/table code
   never establishes equivalence. Without accessible certification records,
   production has no equivalence mapping and date sorting remains inactive.
4. **No canonical rank, fixed bonuses or fixed score penalties.**

`RerankSignal` stores original rank, temporal state, word count/matched terms,
unmatched dimensions, category completeness, requested and available periods.
`Match.score` remains the pre-rerank score, not an aggregate of metadata rules.

## Period evidence and conservative fallback

Read actual `is_time` dimension codes and labels from the existing read-only
SQLite index. Never use MIN/MAX as evidence of interior coverage. Supported
explicit calendars: YYYY, YYYYMmm, YYYYQn/ YYYYÁn, month names with year, numeric
quarter labels and bounded year ranges. Calendar vocabulary is bilingual and
general, not a subject lexicon. Relative dates and unsupported formats are UNKNOWN.

MATCH requires every explicit requested period to be found in a time dimension.
CONFLICT requires fully parsed values of the same granularity and an absent
requested period in every time dimension. Unparseable/missing values, mixed
granularity, no requested period or no time dimension produce UNKNOWN rather
than an assumed conflict. Cross-frequency aggregation is not inferred. Conflicting
code/label periods remain unknown. This is intentionally incomplete calendar
understanding; unsupported natural phrases must not cause false exclusion.

Metadata is loaded only for the top ten, cached by full folder. New GPU/LLM calls
are zero. Cold SQLite/tokenization and cached CPU latency are measured separately
from live answer latency. p95 <5ms is a target, never assumed.

## Frozen measurement plan

Run the unchanged 365 original tests, existing 30 retrieval tests and new synthetic
contract tests, including ten open word pairs and UNKNOWN/CONFLICT group
counterexamples. The pairs document prefix collisions and false negatives; they
are unit cases, not a new development corpus. No existing adjudication table is
rebuilt or inferred from a canonical-folder list.

Compare old both-language prefixes, Icelandic-only prefixes without rerank, and
the four-stage final rerank. All 60 original open questions: code-level part
recall@1/5/10/100, any/all, language/level groups, first-table accepted code out of
40 and exact canonical anchors **separately**, latency and all live answer texts.
Reuse the independent prior anchor audit; alternative exact folders are not
silently certified. Preserve original questions, evaluator, data/index, prior runs.

Review targets recorded before measurement: accepted first table >=28/40;
IS-easy first table >=7/10; live correct answers >=6/60; no six-cell drop greater
than one against the approved 4/60 baseline. Failure is YELLOW/NO MERGE, not an
automatic 5B-2b authorization. Kiddi reviews, Silli decides separately.

Commands: `PYTHONPATH=src python -m pytest`; `ruff check src tests`;
`ruff format --check src tests`; `mypy`; `PYTHONPATH=src python tools/measure_5b2.py
--repo REPO --baseline BASELINE_JSON --vectors GATE0_QUERY_VECTORS --out NEW_DIR
--answers`. Freeze code before live measurement, never overwrite old output.
