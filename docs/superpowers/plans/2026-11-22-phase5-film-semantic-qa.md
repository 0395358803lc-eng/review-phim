# Film Review Agent Phase5 Semantic QA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement task-by-task; use red-green TDD for every change.

**Goal:** Improve source-bound EN→VI translation, Qwen verification after CLIP, multi-sentence video planning and temporal observations, on user-authorized Fatman scenes without production TTS.
**Architecture:** Immutable upstream source/model evidence, source SHA/timecode, external human gates, Qwen fail-closed semantic verification, protected original claim IDs.
**Tech Stack:** Python 3.13/unittest, existing FFmpeg, Whisper, Qwen3-VL and CLIP.
**Spec:** docs/superpowers/specs/2026-11-22-phase5-film-semantic-qa.md

## Global Constraints
- Film and all previous jobs strictly read only; no new installs/downloads.
- Never forge real voice/script/pilot approval; no main merge; 11 SKILL.md unchanged.
- Only source and sanitized numerical QA reports to Draft PR; no raw movie media, transcribed dialogue or model weights.

## Review Focus
- Wrong source SHA/English ASR hash: error, never silently accept
- Translation proposed by AI: not human-approved truth
- False visual/direct motion claim: fail closed even with CLIP score
- Incorrect or missing shot/claim ID: no plan/render
- Genuine missing voice timing: keep storyboard unrenderable

### Task 01 — English/Vietnamese evidence
Files: stage5/translation.py, tests/test_stage5_translation.py.
Interface: build_translation_pack(asr_rows, source_sha256, source_duration_s, proposals=None).
- [ ] Write tests for valid candidate, duplicate ids, out-of-range, text source SHA mismatch, uncertainty marking, unapproved result.
- [ ] Run RED and confirm expected missing feature.
- [ ] Implement minimal fail-closed validated pack; tests GREEN.

### Task 02 — CLIP/Qwen visual gate
Files: stage5/visual_gate.py, tests/test_stage5_visual_gate.py.
Interface: select_visual_shot(source_sha256, claim, clip_candidates, qwen_verdicts, source_duration_s).
- [ ] RED for YES top1, top1 NO/top2 YES, all NO, missing Qwen decision, SHA mismatch, action unsupported, one claim ID.
- [ ] GREEN with source-matched trace; only tentative, never human-approved.

### Task 03 — Multi-sentence storyboard
Files: stage5/storyboard.py, tests/test_stage5_storyboard.py.
Interface: build_storyboard(source_sha256, source_duration_s, sentences, catalog, selections, voice_timeline=None).
- [ ] RED for multiple original claim IDs, absent voice, forged references, incomplete shot coverage, time bound.
- [ ] GREEN source-timeline plan; no inferred voice or fabricated frames.

### Task 04 — Temporal observations, real Fatman regression
Files: stage5/temporal.py, tests/test_stage5_temporal.py, qa/phase5_fatman_existing_evidence.py, docs/qa/phase5-fatman-2026-11-22.md.
- [ ] RED for missing/order/time/source evidence and single frame falsely implying dynamic action.
- [ ] GREEN ordered pack with model-unverified motion.
- [ ] Read existing Fatman data, run local independent tests; optionally run Qwen multiple frames without approvals/installs.

### Task 05 — QA-worker integration, release
Files: qa/legacy_offline_worker.py, tests/test_stage5_worker_gate.py, PHASE5.md.
- [ ] Wire Qwen visual gate after CLIP for synthetic QA while preserving model/TTS approval.
- [ ] Re-run synthetic Engine N00-N09 if feasible and full unit suite.
- [ ] Validate source-only clean package; publish new Draft PR based on Phase4 dev, not main.
- [ ] Verify 11 SKILL.md unchanged, protected original film SHA and checkpoint state.

## Exit
No claim of film-plot accuracy or production-quality real narrated review without separately granted human voice/script/pilot approvals.
