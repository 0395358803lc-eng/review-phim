# Phase6 Real-film Review Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and red-green TDD task by task.

**Goal:** A durable, offline human review queue for authentic Fatman dialogue, translations and source scene selections without signing or generating production media.
**Architecture:** Untrusted ASR and Qwen translation are source-hash checked; FFmpeg cuts are candidate timestamps only; original N05 claim IDs/scene matches survive; local offline media previews and HTML form show issues, not approvals.
**Tech Stack:** Existing Python3.13 standard library, FFmpeg/FFprobe, repo Stage4/5 contracts, unittest (no installs).
**Spec:** docs/superpowers/specs/2026-11-22-phase6-real-film-review-queue.md

## Global constraints
- Source film/old Phase4/Phase5 workspaces read-only, 11 Agent Skills unmodified, no installs, no Git main merge.
- Film/movie audio/transcripts/weights and local absolute host paths NEVER in GitHub.
- All output decisions start PENDING; no trusted external signer is invoked; no real TTS/pilot.

## Review focus
- Tampered English word or source SHA must stop review pack, not be silently carried.
- Mistranslated polysemy such as mail letters vs alphabetic letters must be flagged for human review.
- Out-of-window scene cut timecodes must not attach to unrelated sampled excerpt.
- A model YES or copied frame evidence never auto-signs script/voice/pilot.
- No arbitrary visual story/causality sentence inherits VISUAL_DIRECT from unrelated screenshot.

### Task 1: Build English-VI listening queue
**Files:** stage6/dialogue_review.py; tests/test_stage6_dialogue_review.py
**Interface:** build_dialogue_review_queue(translation_pack, original_asr_rows, source_sha256, movie_duration_s, source_windows).
- [ ] RED: exact provenance, mismatched hash/text, dropped/duplicate row, weak confidence, false friend, preview bounded by original source window, statuses pending.
- [ ] Implement validated candidate evidence and risk rows; GREEN.

### Task 2: Source-window shot proposals from real cuts
**Files:** stage6/scene_proposals.py; tests/test_stage6_scene_proposals.py
**Interface:** build_scene_proposals(source_sha256, movie_duration_s, windows, cuts_by_window).
- [ ] RED: three source windows, timecode offsets, duplicates/out-of-bounds/nonfinite cuts, no scenes falsely verified.
- [ ] GREEN with at least one segment per original 30s window.

### Task 3: Unsigned multi-claim human review pack
**Files:** stage6/review_packet.py; tests/test_stage6_review_packet.py
**Interface:** build_review_packet(source_sha256, storyboard, catalog, proposed_scenes, dialogue_queue).
- [ ] RED: retains exact S/C/V IDs and window/time, no approvals, refuses unsupported/altered evidence or unbounded scene.
- [ ] GREEN, all requests PENDING, real rendering blocked.

### Task 4: Actual Fatman audio, source video workbench
**Files:** qa/phase6_workbench.py (generic source-only runner, published), stage6/offline_html.py, tests/test_stage6_html.py, docs/qa/phase6-fatman-2026-11-22.md, PHASE6.md.
- [ ] Read authorized manifest/source SHA, no changes.
- [ ] Existing FFmpeg: 17 ASR sound previews; detect cutpoints in three 30-second old clips; record original film timecode + SHA.
- [ ] Generate local HTML with audio & source movie playback controls, unsigned JSON decisions.
- [ ] Independently verify source unchanged, content anchored, local media decodes.

### Task 5: Full regression, Draft PR
- [ ] Run complete suite and source-only release validator.
- [ ] Confirm no film/audio/translation/model weights in staged source.
- [ ] Publish Phase6 branch and Draft PR targeting Phase5, never main.
- [ ] Verify 11 Agent Skills unchanged, zero old files deleted.
- [ ] Save checkpoint awaiting genuine human review.

## Exit
Move from unverified model output to inspectable reviewer workbench; not certified recap production.
