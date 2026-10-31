# CPU/GPU Balanced Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans, with TDD and verification. This file is a task map; full version with acceptance conditions was delivered to the user as 2026-10-31-review-phim-cpu-gpu-integration-plan.md.

**Goal:** Add local-first runtime adapters and hardware arbitration for the approved Balanced profile without touching live video or the Windows host.

**Architecture:** Skill orchestrates; local runtime executes only separately approved, host-bound operations; ChatGPT receives evidence text and supplies explicit review receipts.

**Tech Stack:** Python 3.13 (isolated future venv); candidate FFmpeg 9.0.2, PySceneDetect 0.7.2, faster-whisper 1.2.1, CTranslate2 4.8.4, Silero VAD 6.2.3, ONNX Runtime CPU, Ollama/Qwen3-VL 4B Q4. No runtime or models are installed by this plan.

**Spec:** docs/superpowers/specs/2026-10-31-cpu-gpu-balanced-runtime-design.md

## Global constraints
- Keep main unchanged; use separate feature branch.
- No machine install, model download, film probing, output writes, media transfer or publication without separately scoped approval.
- Preserve source hashes, model digests, timecodes, modality distinctions, and five-niche stage order.
- TECHNICAL_PASS and AI_REVIEW_PASS are not factual film verification.
- Windows reparse paths, PID uncertainty and quota uncertainty fail closed.

## Tasks
- [ ] 1. Reconcile installed skill against repo main; write contract tests (five niches, G0 before G1, half-open intervals, no invented VERIFIED); implement pure contracts; run unit suite.
- [ ] 2. Add scope engine and shell-free runner; test expired/wrong-device/traversal/junction/quota/unapproved media and duplicate timeout; require genuine Windows path canonicalizer before use.
- [ ] 3. Add G0 read-only collector, version/licensing registry and G1 proposal generator; test installed != tested and GPU name != GPU PASS.
- [ ] 4. Add lease-based GPU/CPU scheduler and persistent recovery; test one heavy GPU job, VRAM cap, CPU reserve, OOM downgrade and PID reconciliation.
- [ ] 5. Build FFmpeg/PySceneDetect adapters; mock-only tests first; synthetic Windows tests need G1 scope.
- [ ] 6. Build VAD/ASR/VLM adapters with digest-based provenance; no film processing until PROCESS_APPROVED.
- [ ] 7. Build fusion, receipt validation and review dispatcher; no text-only VERIFIED claim.
- [ ] 8. Build optional search, voice catalog, EDL, rendering with separate approvals.
- [ ] 9. Implement synthetic benchmarks, CI (Windows), packaging and independent review. Leave main unchanged until explicit merge authorization.

## Known uncompleted constraints (current checkpoint)
Foundational source modules are pure-code prototypes. Missing: actual Windows canonical path resolver, durable process journal, executable-specific argument grammar, cumulative quotas, live G0 collector, resource telemetry, adapters and measured GPU/CPU tests. Do NOT deploy on the device.

## Test command for current prototype
From repository root: PYTHONPATH=runtime python -m unittest discover -s runtime/tests -v (POSIX) or PowerShell set PYTHONPATH to runtime then run python -m unittest discover -s runtime/tests -v. Tests use synthetic paths and mock launchers only; no movie decoding.
