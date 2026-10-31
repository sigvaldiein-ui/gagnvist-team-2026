# Full review bundle

[Drive review ZIP](https://drive.google.com/file/d/1iFPX70-o6ZQjHQLdggPuUyolUOodbDY3/view?usp=drivesdk)

SHA256: `8b5aedee66e97e0e69f91ba90286cbebf6b6b91d7695243d104f3cff9908c572`

Contains tested-source.tar, full Git tree/blob SHAs, diffs from baseline and round1 executable commit, all 480 retrieval traces, all60answers with raw candidates, canonical-folder audit, 395-test logs/JUnit, Ruff/format/mypy logs, source hashes and JSON/HTML reports. Internal sha256-manifest.json hashes each evidence file. No environment credentials or SSH keys included.

Tested source commit: `58e8499ec3314a0f0465a945f4ef9603f8a9f790`. The report commit adds only reports/5b1-round2. Existing Network Volume retains `/workspace/gagnvist-5b1-round2-results`; previous run is untouched. Closed12and18questions not accessed.

YELLOW / NO MERGE: accepted-code first-table16/40 and final answers4/60 pass their individual targets, but IS easy3/10→1/10 fails the maximum one-answer regression gate. Exact canonical anchor first-table is5/40; accepted alternatives are a different measure and are not silently treated as exact folder matches.
