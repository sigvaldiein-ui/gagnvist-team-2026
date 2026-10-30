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
