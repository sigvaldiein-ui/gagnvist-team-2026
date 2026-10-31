# 5B-2 independent review bundle

[Drive ZIP](https://drive.google.com/file/d/1I465ArEfhR4G_c4h8iO0JdRgPMrxaPdy/view?usp=drivesdk)

SHA256: `085865b713ca2f36808bfa92f338788f7830c166b072b067a4b21a108b7b899b`

Frozen tested code: `dfb0550af71c65b2b50b38440a20ceaf846a57c0`.

The later report-only commit adds reports/5b2, not executable changes. Full source archive, Git/blob manifest, baseline/round2 diffs, 180 retrieval traces, 60 live answers, canonical-folder audit, synthetic contract tests, 428-test JUnit/logs and SHA256 manifest are included. source-byte-identity.json distinguishes working CRLF bytes from Git LF blobs and verifies equality after newline normalization; raw working hashes and committed blob hashes are both supplied. No keys or environment credential files included.

Preserved on existing Network Volume `/workspace/gagnvist-phase5b2-results`; all earlier runs retained. Main, question/evaluator files, original vectors/data and closed12/18sets untouched.

**YELLOW / NO MERGE:** 7/60 correct answers passes >=6, but first accepted table22/40 misses28, IS-easy first5/10 misses7, and IS-easy answers3/10→1/10 fails the maximum one-answer regression gate. Exact canonical first9/40 is separate from accepted alternatives. Warm rerank p95 98.268ms misses5ms target; first-pass p95 427.178ms. Production date ties remain inactive without authoritative equivalence records.

Kiddi reviews actual code/diff and results. No 5B-2b/5B-3 or merge follows automatically. Silli decides separately.
