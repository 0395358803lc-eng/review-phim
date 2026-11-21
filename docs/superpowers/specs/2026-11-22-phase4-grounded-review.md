# Phase 4 — Evidence-grounded authoring and human approval request design (2026-11-22)

## Goal
Advance from Phase3's hardcoded geometric shape sentence to a reusable, claim-traceable, multi-event story and review draft builder. Maintain Engine21's existing host-signed script/voice/pilot approval gates. Run synthetic QA only.

## Critical boundaries
- No real-film input selected/authorized for this phase. Old film/model workspaces are strictly read-only.
- Never infer a character identity, ownership, intent or causality from visual appearance alone. Exact visual or dialogue quotes are evidence; model-written narrative is a proposal, NOT a verified claim.
- Emit requested `review_final.txt` only as a **draft pending host script approval**; the name satisfies Engine21's contract but is not itself evidence of human sign-off.
- Unsigned approval requests are informational only; do not build a signer, issue receipts or bypass Engine21 approvals. Host remains responsible for signature.
- No installs, no model downloads, no user media bundled, no changes to 11 skills, GitHub feature branch/Draft PR only.

## Design
- `stage4/evidence.py`: ingest N02 ASR and N03 visual JSONL with immutable source SHA and finite source-bound time ranges. Reject duplicate/unknown IDs and invalid spans; preserve separate speech-only events. Merge utterances with visual intervals only on evidence-backed time overlap; mark conflicting observations unresolved. Produce ordered events + catalog.
- `stage4/review.py`: generate an extractive Vietnamese presentation draft from documented source visual text and/or verbatim dialogue, with every atomic claim linked to real, time-scoped visual/ASR evidence. All draft sentences carry source SHA, per-sentence IDs, claim IDs, verdicts and a `human_review_required` marker. Support >1 events without inventing plot. A proposed freeform/LLM sentence is only accepted if it exactly reproduces a grounded source quotation; otherwise quarantine as UNRESOLVED (cannot go into approved script automatically).
- `stage4/approval_requests.py`: read Engine21 job state; produce **unsigned** request manifest(s) bound to real current script evidence digest, actual voice WAV or pilot MP4 SHA, source movie SHA and exact job ID. Do not include keys or signatures. Recompute digests at time of request. Human approval happens OUTSIDE the agent.
- `qa/legacy_offline_worker.py`: optionally route N04/N05 through new engine for genuine source evidence for single-scene synthetic acceptance, while preserving phase3 contracts. Do not claim full length/writer model.
- `tests/test_stage4_*.py`: TDD coverage for positive multi-event joins, wrong source SHA, duplicate IDs, bad time range, contradictory visuals, unsupported LLM claims, exact ASR quote, unsigned approval subject binding, missing artifacts.
- `docs/qa/phase4-grounded-authoring.md`: evidence of full regression, source audit and actual Engine21 small-media QA where possible.

## Acceptance
1. Multiple evidence-bound events yield multiple sentences and a traceable ledger; no imaginary actors, intents or events.
2. Unmatched ASR events preserved; overlapping contradictory visual observations flagged for manual review.
3. Wrong SHA, forged evidence IDs and unsupported candidate prose rejected or quarantined.
4. A user-facing approval request is unsigned, subject hashes anchored to current Engine21 job artifacts; cannot be confused for actual approval.
5. Existing Engine21 approval gates remain unchanged and two privileged N06/N08 calls still fail without approved receipts.
6. Full existing unit regression + clean release validator PASS; all original 11 skills preserved.
7. Do not imply factual story/movie truth from JSON structure alone or synthetic QA.
