# Upstream baseline: integrity record

Date: 2026-10-30 (UTC)
Repository: `sigvaldiein-ui/gagnvist-team-2026`
Review branch: `upstream/baseline-f2ad3be`
Base branch: `main`
Last verified pre-documentation commit: `494061a6b1426ed22a137fc554502589c72c9100`

## Scope and verification method

This is a Git-object and repository-tree integrity record, **not** a claim that the
application has passed runtime tests or that its data values are substantively correct.
The GitHub tree was fetched recursively (not truncated), and the two known expected
blob SHAs were compared directly with GitHub's reported values.

| File | Expected Git blob SHA | Observed Git blob SHA | Result |
| --- | --- | --- | --- |
| `docs/setup-windows.md` | `4c4f38e52a502a2ab95826cf7252a2503608200c` | `4c4f38e52a502a2ab95826cf7252a2503608200c` | MATCH |
| `src/gagnvist/lumi/jobs.py` | `75890854239fced0f8c657c5b40383835361209d` | `75890854239fced0f8c657c5b40383835361209d` | MATCH |

Additional tracked files in the verified tree:

| File | Observed Git blob SHA |
| --- | --- |
| `tests/test_lumi_connection.py` | `c23303e2e272e7111fba4b385921c78fb0b136a4` |
| `tests/fixtures/data/catalogue.csv` | `7bfb1b398b7a6ec155359d57cff85b81a55f8748` |
| `tests/fixtures/data/SHA256SUMS.txt` | `624f69bf88d3bbf2c435acb5262bf53faf43f61a` |

The following 12 `metadata.json` fixture blobs were present in the fetched
tree. Previous work reported **eight** metadata fixtures already verified; this
record lists all 12 current blobs, **without** claiming all 12 were previously
independently compared with their intended source bytes.

| Fixture (under `tests/fixtures/data/`) | Observed Git blob SHA |
| --- | --- |
| `Business_Sectors/en/ferdathjonusta/gisting/4_eldraefni/SAM91452/metadata.json` | `f329001191e73b2f14b002de12a07d6a2bbb44c0` |
| `Business_Sectors/is/ferdathjonusta/Gisting/4_eldraefni/SAM91452/metadata.json` | `5622b958bd1158d896d2e2dca3b6e30dfd0a17dd` |
| `Economy/en/visitolur/2_byggingarvisitala/byggingarvisitala/VIS13401/metadata.json` | `5143c6c7983718c5a830aa67ea9f23497a87cffe` |
| `Economy/is/visitolur/2_byggingarvisitala/byggingarvisitala/VIS13401/metadata.json` | `71a8060ad9e29b1504940dcc10b008dcb8b7b2da` |
| `Population/en/kosningar/althingi/althkjosendur/KOS02105/metadata.json` | `c499f9f3c5f754bc50e5e731d265dec0da66c6a6` |
| `Population/en/kosningar/forsetakosningar/KOS07112/metadata.json` | `7ecf6ea067a9a66afdc96e8e3b76183da4edaae1` |
| `Population/is/kosningar/althingi/althkjosendur/KOS02105/metadata.json` | `6a46f52436df211a1db276ca7099925807044840` |
| `Population/is/kosningar/forsetakosningar/KOS07112/metadata.json` | `12ecc0081f0e7e168b45099072edb9b59452f5a3` |
| `Society/en/felagsmal/jafnrettismal/2_kkahrifastodur/HEI02601/metadata.json` | `d2a22019a140bccfdf8cf70657c391620a547c5e` |
| `Society/en/felagsmal/jafnrettismal/3_kk75/HEI11505/metadata.json` | `f0b64babff11618876a1342bcb722325c75db759` |
| `Society/is/felagsmal/jafnrettismal/2_kkahrifastodur/HEI02601/metadata.json` | `c8ea9aab5b46e657afcc10f15e8bffb0051b009a` |
| `Society/is/felagsmal/jafnrettismal/3_kk75/HEI11505/metadata.json` | `caa2682342df6952cfd8512e26ced7de0c1bea66` |

## Incident and remediation

During baseline preparation an assistant reported becoming stuck in a tool-call
loop: six redundant commits to `docs/setup-windows.md` (`c0873df`,
`3faeb56`, `ba049ba`, `c81b888`, `b4947fa`,
`a41efe1`) and seven accidental probe commits (`180cc61`,
`b0d02a4`, `9befa4c`, `3c405f8`, `a860e03`,
`5849a5d`, `3a2acfe`).

The branch head was verified to equal
`3a2acfe0b90c86cb68df17e2644c18bd53ca1707` before cleanup.
The accidental `docs/.probe-delete-me` file (blob
`c1b0730e0133447badcfd47fd144e254807b06e1`) was
removed with a normal commit:
`494061a6b1426ed22a137fc554502589c72c9100`.
A subsequent recursive tree read showed that the file was absent. The
`setup-windows.md` and `jobs.py` blob SHAs remained unchanged.

No branch deletion, force-push, or history rewriting was used.
The redundant commits remain in history for traceability; they need not be
preserved as individual commits if a squash merge is later separately approved.

## Review checklist

- [x] Expected `setup-windows.md` Git blob SHA matches
- [x] Expected `jobs.py` Git blob SHA matches
- [x] Accidental probe file absent after cleanup
- [x] Recursive Git tree fetched, not truncated
- [x] Catalogue, LUMI connection test and 12 fixture metadata files present
- [ ] Independently validate the fixture source bytes, as needed
- [ ] Run Python test suite and Windows/LUMI setup acceptance checks
- [ ] Claude/human review of code and data integrity
- [ ] Merge authorization (not granted)

**Review-only**: nothing in this document authorizes merging into `main`.


## Full upstream comparison — final sweep (post-cleanup)

Compared the **complete, non-truncated recursive Git trees** of this review branch
at `7fccf344ece3cf6577044b0ea92c004eaf1d9db8` and the official upstream at `f2ad3bede71b387857a2731bd57e78c6eb6f476d`.
This was a Git-object integrity comparison; **no runtime or data-value tests were performed**.

| Measure | Verified result |
| --- | --- |
| Upstream tracked files | 122 |
| Files in this review branch | 99 |
| Files from upstream present in branch | 98 |
| Present upstream files with identical Git blob SHA | 98 |
| Present upstream files with differing SHA | 0 |
| Missing upstream files | 24 |
| Additional review-branch files | 1 (`UPSTREAM_BASELINE.md`, this audit) |
| Accidental `docs/.probe-delete-me` in final tree | Absent |
| Git tree truncated | No (both) |

**Scope qualification / review blocker:** this is **not** a byte-identical or
reproducibly runnable full copy of upstream: 24 upstream blobs have not
been imported. These are the four large card files, six split data archives, two vector-index
files and twelve `data.px` test fixtures. Their absence must be resolved through
an approved data-mount/download method, or imported where permitted, before
claiming full upstream parity or running end-to-end test baselines.

**Cards and table metadata (4)**

| Missing path in this branch | Upstream blob SHA |
| --- | --- |
| `cards/cards-en.jsonl` | `6b964898c1cf8b54f778a165535d5af9b97cce8b` |
| `cards/cards-is.jsonl` | `4783a7f7f6c58aedb5508f87856b73867b73631e` |
| `cards/cards.csv` | `7bede07420978313ff411a0f819c43d4184d3b89` |
| `cards/pairs.csv` | `c871dc02772c7179287d339512f76be174a10b0d` |

**Dataset archive (6)**

| Missing path in this branch | Upstream blob SHA |
| --- | --- |
| `data-release/gagnvist-pxweb-data-2026-10-18.zip.part01` | `fade33c87c4f235380ff5908f13a617eda878a79` |
| `data-release/gagnvist-pxweb-data-2026-10-18.zip.part02` | `1814bf909c0d4be4f1e017319c51a2de6d0d7cb5` |
| `data-release/gagnvist-pxweb-data-2026-10-18.zip.part03` | `36b4389fba70f750b05526e482449e738674133f` |
| `data-release/gagnvist-pxweb-data-2026-10-18.zip.part04` | `ec39629649d1c8552edd5401f1caac3b03113350` |
| `data-release/gagnvist-pxweb-data-2026-10-18.zip.part05` | `5faff678ca11d317fa2159f4cfbb9ba97242dfe4` |
| `data-release/gagnvist-pxweb-data-2026-10-18.zip.part06` | `612b1262ccc434926fb6e04003f807d65b52d067` |

**Vector index (2)**

| Missing path in this branch | Upstream blob SHA |
| --- | --- |
| `index/cards.jsonl` | `9ff8d84da9b0137354bef78803d479b31e2f38bb` |
| `index/vectors.npy` | `14fb2eef1468fcbd3be238691cad0c6d010b89b9` |

**PX test fixtures (12)**

| Missing path in this branch | Upstream blob SHA |
| --- | --- |
| `tests/fixtures/data/Business_Sectors/en/ferdathjonusta/gisting/4_eldraefni/SAM91452/data.px` | `c0fd67e9dd7754c9e4d3dc3d42c806feea6d5ac9` |
| `tests/fixtures/data/Business_Sectors/is/ferdathjonusta/Gisting/4_eldraefni/SAM91452/data.px` | `e7ba51f9c7b12143611820c402c324b43a6233e1` |
| `tests/fixtures/data/Economy/en/visitolur/2_byggingarvisitala/byggingarvisitala/VIS13401/data.px` | `b010ac8a470edc2c86963770bc0fa3a91a01acb4` |
| `tests/fixtures/data/Economy/is/visitolur/2_byggingarvisitala/byggingarvisitala/VIS13401/data.px` | `28485964b238e8fc652cb25e33a4157a1f860d3c` |
| `tests/fixtures/data/Population/en/kosningar/althingi/althkjosendur/KOS02105/data.px` | `266b3e8ed0923d150c9213de443d0ab8167bc29b` |
| `tests/fixtures/data/Population/en/kosningar/forsetakosningar/KOS07112/data.px` | `7c27bc552e738fa53358226782a57779cd29301e` |
| `tests/fixtures/data/Population/is/kosningar/althingi/althkjosendur/KOS02105/data.px` | `5d90b084d1f47d315396152da3d379fcd4403430` |
| `tests/fixtures/data/Population/is/kosningar/forsetakosningar/KOS07112/data.px` | `85c86cf5ae29deda574ee45e79059422f886364e` |
| `tests/fixtures/data/Society/en/felagsmal/jafnrettismal/2_kkahrifastodur/HEI02601/data.px` | `8b3fa46b76edfd9aa3f8e362442b16809bec0ef9` |
| `tests/fixtures/data/Society/en/felagsmal/jafnrettismal/3_kk75/HEI11505/data.px` | `6e9f4581b6a27ff3b84089241d91d693f38a7ac2` |
| `tests/fixtures/data/Society/is/felagsmal/jafnrettismal/2_kkahrifastodur/HEI02601/data.px` | `d11b2bc51cb08156e4cb3700a53174b61521e661` |
| `tests/fixtures/data/Society/is/felagsmal/jafnrettismal/3_kk75/HEI11505/data.px` | `82ce81c7add70d3b7ce09160e55ae1d198f7c7a5` |

### Post-cleanup change isolation

Compared three non-truncated Git trees in sequence:

1. Before cleanup: `3a2acfe0b90c86cb68df17e2644c18bd53ca1707`.
2. After cleanup: `494061a6b1426ed22a137fc554502589c72c9100`
   — **only** `docs/.probe-delete-me` (blob
   `c1b0730e0133447badcfd47fd144e254807b06e1`) was removed.
3. After documentation: `7fccf344ece3cf6577044b0ea92c004eaf1d9db8`
   — **only** `UPSTREAM_BASELINE.md` was added. No other blob changed
   across these two commits.

The expected `docs/setup-windows.md` and `src/gagnvist/lumi/jobs.py`
SHAs are intact. Every other present upstream-tracked file matches its
upstream blob SHA at the pinned original commit. No unapproved source,
test, or data file modifications are detected in the final reviewed tree.

**Status: ready for independent Claude review of the *partial* baseline and
cleanup; NOT ready for merge or end-to-end claim.** No force-push, reset,
branch recreation, or merge was performed.
