# 5B-1: metadata hybrid retrieval

Related: Issue #4. Base: `a09746847e884190aa51ea9f91fab8c4c90c2088`.

The configured pipeline retrieves up to 100 candidates and still reads **one**
table: candidate 1. It does not ask Qwen to choose among 100 tables. Retrieval
decomposition does not implement multi-table answers or calculated facts.

## Fixed configuration and score

`[retrieval]` in `gagnvist.toml` declares all settings. Defaults are selected before
the development-set comparison, not fitted to expected answers:

| Setting | Default |
|---|---:|
| mode | hybrid |
| candidate_limit | 100 |
| dense_weight / lexical_weight | 1 / 1 |
| rrf_k | 60 |
| bm25_k1 / bm25_b | 1.2 / 0.75 |
| decompose | true |
| max_subqueries | 3 |
| subquery_weight | 0.5 |

Each channel supplies its own top-100. For candidate `d`, the final score is
`sum(query_weight * channel_weight / (rrf_k + channel_rank))`. The full question
has weight 1. Subqueries share a total weight of 0.5. Full folder path breaks
fusion ties, and merging deduplicates by folder, never by table code. The final
union is capped at 100. Raw dense/BM25 scores, ranks, queries and each contribution
remain in `Match.signals`. Dense-only with decomposition disabled preserves the
original cosine score and ordering for exact ablation.

BM25 uses the shipped card's title and dimension labels, plus folder tokens.
It is built separately per language and has no new dependencies. Tokens are NFC,
casefolded Unicode alphanumeric terms; underscores and path separators split.
A closed-class grammatical stop list contains no subject-specific synonyms or
table IDs. Query term duplicates are ignored and processing order is sorted.
BM25 uses `log(1 + (N-df+0.5)/(df+0.5))` IDF and standard length normalization.
No-hit lexical queries produce no fabricated zero-score matches.

General decomposition splits conjunction clauses on `and`, `og` and semicolons.
It always retains the full question, drops duplicate/numeric-only fragments,
and caps fragments at three. It does not infer omitted context, named metrics,
dates or operands. This deliberately simple retrieval aid may introduce noise;
the decomposition ablation reports its effect separately.

`Pipeline.from_settings` enables the declared configuration. The direct Python
`Pipeline(...)` constructor keeps its legacy dense behavior unless given
`retrieval_config=RetrievalConfig(...)`, preserving existing API callers.

## Explicitly outside this change

No semantic/period penalties, scope rules, category-selection changes,
deterministic answer arithmetic, `extra_tables`, modified embeddings, rebuilt
shipped vectors, scorer changes or question-specific mappings. Period bounds
in measurement traces are descriptive lexical code bounds, not a ranking rule
or proof of actual temporal coverage.

## Measurement and leakage boundary

`tools/measure_5b1.py` records dense top-5, dense top-100, lexical, hybrid and
hybrid+subqueries, all at fixed settings. Full questions replay the independently
verified Gate-0 vectors; previously unseen subqueries call BGE-M3 once and cache.
Reported CPU retrieval time subtracts uncached API time; initialization and
embedding timings are separate. End-to-end answer times include real live model
calls. These are different measurements and must not be conflated.

Recall uses the unchanged scorer's accepted table codes for **each part**, with
any-part/all-parts and macro/micro part recall reported explicitly. Every result
retains full folders and source paths. Duplicate table codes make code-level
recall optimistic in some cases; accepted-folder identities are reported as
ambiguous, not promoted to semantic ground truth.

The 60 published questions are an open development set. The sealed 12-question
set is not read, downloaded, or executed during this implementation. Its known
SHA-256 is `6f318981e809bcc2fd182d4866b79dc017dbd402ee8757ba5886e3405c2ce493`.
A separate owner approval is required to open it after the code is frozen.

The original 4/60 report and Gate-0 evidence remain immutable. Regression of more
than one correct answer in any language/level cell is reported as a failed gate,
not hidden by the total. Passing tests is not independent reviewer approval.

## Review and operations

Run the original tests plus `tests/test_hybrid.py`, `ruff check src tests`,
`ruff format --check src tests`, and `mypy`. See the PR report for measured results.
Do not merge without Silli. Runtime APIs remain bound to localhost, and the
already-running A40 is kept running per Silli; this tool never stops a Pod.
