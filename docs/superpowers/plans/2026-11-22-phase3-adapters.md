# Phase 3 — AI Adapter Integration Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:executing-plans and test-driven-development task-by-task.

**Goal:** Deliver the approved eight scoped integrations with real FFmpeg execution and fail-closed local AI provider contracts; validate with synthetic media only.

**Architecture:** Strict adapter outputs in Engine21 attempt directories, immutable source provenance, fixture mode explicitly identified; provider-specific jobs execute only installed/host-approved binaries.

**Tech Stack:** Python 3.13 standard library, FFmpeg 9.0.2, existing NVIDIA GPU inventory. Optional external AI model runtimes only if preinstalled.

**Spec:** docs/superpowers/specs/2026-11-22-phase3-adapters-design.md

## Global Constraints
- No installs, no downloads, no old film data, no GitHub main merge.
- 11 Agent Skills and Engine 2.1 must remain untouched.
- TDD with recorded red/green for each deliverable.
- Synthetic outputs never masquerade as model inference or human approval.

## Review Focus
- Unknown/missing providers must fail closed rather than generate content.
- Corrupted or retargeted source and artifact paths must be rejected.
- Timing in generated JSONL and video must remain inside source duration.
- Power loss or process failure must not mark a stage DONE.
- HMAC signing test-only must remain outside production adapter.

### Task 01 — Environment inventory
- [ ] Inventory GPU and installed runtimes, record unavailable dependencies.
- [ ] Verify output read-only, no downloads or installs.

### Task 02 — Adapter Framework
- [ ] Write failing contract tests: validated context and artifact SHA handling.
- [ ] Implement framework, run tests, capture green output.

### Task 03 — Video input, scene segmentation
- [ ] Test synthetic source probe/decode/scene spans.
- [ ] Implement media adapter and N00/N01, verify with FFmpeg.

### Task 04 — ASR and translation
- [ ] Add fail-closed production worker contract test and synthetic transcript tests.
- [ ] Implement N02 provider routing with verified provenance.

### Task 05 — CLIP and Qwen3-VL
- [ ] Test production provider unavailability and synthetic vision artifacts.
- [ ] Implement N03/N07 worker interfaces and provenance contract.

### Task 06 — Story memory and review
- [ ] Test N04/N05 valid traceable synthetic artifacts and hard production gate.
- [ ] Implement event timeline and review evidence.

### Task 07 — VieNeu TTS and semantic matching
- [ ] Test N06 real WAV decode with synthetic audio and N07 sentence-map validation.
- [ ] Implement timing and matching with explicit unresolved claims.

### Task 08 — FFmpeg video editing & end-to-end
- [ ] Test actual pilot/final MP4 render with voice, failure gates.
- [ ] Full N00–N09 synthetic CLI run, FFprobe/FFmpeg QC, report.
- [ ] Run all tests and release checker in clean export; review and publish Draft PR, no main merge.
