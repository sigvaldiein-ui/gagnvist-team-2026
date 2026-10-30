# Gagnaþon 2026 — Kimi implementation handoff

**Date:** 2026-10-30
**Repository:** https://github.com/sigvaldiein-ui/gagnvist-team-2026 (PRIVATE)
**Official upstream:** https://github.com/SyedMuhammadAzhar/gagnvist-starter (READ-ONLY upstream)
**Owner and final approver:** Sigvaldi Einarsson
**Gatekeeper:** Claude (independent GREEN/RED)
**Status:** ChatGPT repository push permission VERIFIED; Kimi access and LUMI runtime NOT YET VERIFIED.

## Role split
- **Kimi:** Lead implementation agent; small focused patches, local tests, evidence and precise commit references.
- **ChatGPT / Codex:** Frontend, integration and independent regression review.
- **Gemini / Antigravity:** Architecture, table retrieval and reranking experiments.
- **DeepSeek:** PX-API/Python back-end support when needed.
- **Claude:** Independent reviewer, no self-approval.
- **Sigvaldi:** Product owner; grants access and approves merge/release.

## What we know, and what we don't
Kimi reviewed upstream main at `f2ad3bede71b387857a2731bd57e78c6eb6f476d` and observed `jureca` branch at `d9b63ef901e100e086501669b47b7a820f518268`. These are **Kimi-reported observations**; re-check current upstream state before implementation. Upstream is not writable by our account (403 push).

Current `questions/examples.jsonl` was independently verified: **60** cases, **20 easy / 20 medium / 20 hard**, **30 Icelandic / 30 English**. An older presentation described 52; use current repository tests. No complete 60-case baseline has been run: LUMI and team-key/runtime are pending. No model score is claimed.

## Approved v0.2 principles (from earlier Claude GREEN)
The *complete approved JSON /ask schema is not yet present in this repository*: obtain the exact approved document before introducing a contract change. Preserve:
1. Fixed machine-readable clarification codes (not invented by an LLM).
2. Complete numeric provenance in `cell_references`.
3. Status/suppressed/missing values must not be coerced to zero.
4. Synthetic examples must be marked; never present placeholder codes as live data.
5. Explicit `period_mode`, not unannounced LLM period selection.
6. Send the model only metadata needed to answer the question.
7. Apply T1-T3 numeric gates from the first run, and measure T4 in the demo.

## First assignment — period-aware retrieval (proposed, not approved as a measured win)
1. Inspect the current source, index/card structure, README and test set. Record an exact version and branch.
2. Propose and implement **deterministic period-aware reranking of the top 10 retrieved tables**, but only when the requested period can be identified explicitly from the question or contract. Do not invent implicit periods; return clarification where ambiguous.
3. Preserve other ranking signals and avoid arbitrary boosts that distort clearly matching tables.
4. Write small local unit tests covering a clearly dated query, an ambiguous query and missing/out-of-range periods.
5. When LUMI/team access is confirmed, run `gagnvist evaluate` against all 60 cases, compare before/after by difficulty and language, report table accuracy, numerical correctness, citation correctness, latency and failure examples. Do not invent scores.
6. Work on a **Kimi-owned feature branch** in this private team repo; no direct commits to `main` and no force pushes or merges without Sigvaldi approval and Claude GREEN.

## Security
- Never commit or disclose `.env`, private SSH keys, passphrases, LUMI team keys, personal access tokens, service credentials or data archives requiring separate authorization.
- Never upload the unrelated USA elections map ZIP into this repository.
- The official source tables are Statistics Iceland data; ensure citation/licence attribution in outputs.
- Do not imply Kimi has write access because ChatGPT has it. Kimi must authenticate independently.

## Required result
Report: **READ OK / WRITE OK / LUMI VERIFIED or BLOCKED**; version/branch; exact files changed; commit SHA; test commands; evidence; regression risks; and a review package for Claude. Stop and ask for one explicit authorization action if authentication blocks work.
