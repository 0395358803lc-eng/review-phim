# Phase 4 Grounded Review and Approval Requests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and test-driven-development to implement each task.

**Goal:** Build a verifiable multi-event movie review drafting core and host-only human approval request preparation.
**Architecture:** Immutable source-bound event catalogs, extractive claim-cited drafts, quarantined proposed non-grounded claims, Engine21's existing trusted signer and evidence gate unchanged.
**Tech Stack:** Python 3.13 standard library, existing Engine21 + evidence_qc; Windows FFmpeg only for QA preview.
**Spec:** docs/superpowers/specs/2026-11-22-phase4-grounded-review.md

## Global Constraints
- No new packages/install; no film source copied, altered or arbitrarily selected.
- No SSH/key/signature/approval creation by agent; output is UNSIGNED request only.
- Preserve all 11 skills, no main merge; use Draft PR.
- TDD red first for each new module, run full regression before publishing.

## Review Focus
- Duplicate/forged source evidence IDs: fail closed, never double count.
- Out-of-range/no-overlap utterances: preserve standalone events, no false visual linkage.
- Conflicting model captions: mark as unresolved rather than choose one silently.
- Freeform LLM assertions without literal source support: quarantine, never publish as approved truth.
- Voice/pilot approval subjects: derive actual SHA and Engine21 exact subject semantics; unsigned request cannot act as an approval.

### Task 01 — Story evidence index
**Files:** Create stage4/evidence.py, tests/test_stage4_evidence.py.
**Interface:** build_timeline(asr_rows,visual_rows,source_sha256,source_duration_s) -> dict with catalog and ordered events.
- [ ] Write tests for merged, unpaired, duplicate, invalid timestamp, hash, conflict.
- [ ] Verify RED (module not implemented).
- [ ] Implement normalized catalog and interval overlap events with provenance.
- [ ] Verify GREEN, then full suite.

### Task 02 — Grounded narrative drafting
**Files:** Create stage4/review.py, tests/test_stage4_review.py.
**Interface:** build_draft(timeline, proposals=None, max_sentences=None) -> review draft, claims, evidence ledger, quarantine.
- [ ] Test multiple sources, literal support validation and unresolved proposal.
- [ ] Verify RED.
- [ ] Implement evidence-first extractive sentences and no hallucination fallback.
- [ ] Verify GREEN and existing evidence_qc compatibility.

### Task 03 — Approval request pack
**Files:** Create stage4/approval_requests.py, tests/test_stage4_approval.py.
**Interface:** make_request(job,gate) -> unsigned manifest; write_request -> file under specified isolated QC output.
- [ ] RED tests for script SHA from N05 evidence, voice/pilot hashes, tamper and no signature.
- [ ] Implement exact gate subject resolution with no key use.
- [ ] GREEN and stale subject verification.

### Task 04 — Engine N04/N05 integration and technical QA
**Files:** qa/legacy_offline_worker.py, tests/test_stage4_worker.py, docs/qa/phase4-grounded-authoring.md.
- [ ] RED tests for N04/N05 structured trace and supported review without synthetic scene hardcode.
- [ ] Integrate opt-in adapter with existing N04/N05 required files.
- [ ] GREEN, full 11-skills release validation and optional synthetic Engine run.
- [ ] Publish Draft PR targeting feature/phase3-existing-local-model-qa only; no main merge.

## Exit gate
- [ ] All test runs captured by actual exit code.
- [ ] No unsupported movie claims, model deployment or real approval signed.
- [ ] Next real-film source and genuine user approval require explicit separate scope.
