# Phase 3 Windows technical acceptance — 2026-11-22

Machine: DESKTOP-2GP3E41. New isolated root: D:\Phim\__FRA_PHASE3_20261122. Branch: feature/phase3-ai-adapters, base e795391f07d8798ac9a1cfb35053c5c687fcc1ad (Engine 2.1). No old film data, no installs/downloads, no main merge.

## Inventory
- GPU NVIDIA RTX 4060, 8188 MiB VRAM, driver 617.42. Python 3.13.15, FFmpeg/FFprobe 9.0.2, Git 2.55.
- System Python lacks Whisper, faster-whisper, open_clip, torch, transformers, qwen_vl_utils and scenedetect.
- Separate existing VieNeu Python 3.11.18 venv has vieneu, torch and transformers. No local model checkpoint or authorized voice profile was validated. No VieNeu inference was run.
- Detailed passive machine inventory exists at the isolated root inventory.json (not published).

## Deliverables by approved work package
| ID | Evidence | Verdict |
| --- | --- | --- |
| 01 Inventory | GPU/Python/AI modules checked read-only | PASS |
| 02 Framework | Wrong source/attempt, unpinned provider, changed runtime SHA tests | PASS |
| 03 Scene indexing | Real FFmpeg probe, full decode and complete scene timeline for synthetic MP4 | PASS synthetic |
| 04 Whisper | N02 JSONL and production provider fail-closed | Interface ready; model inference BLOCKED |
| 05 Qwen3-VL and CLIP | N03 observations, N07 sentence-shot map and missing model denial | Fixture PASS; actual inference BLOCKED |
| 06 Story/review | N04 event/source keys and N05 synthetic review/claim ledger | Fixture PASS; actual creative work BLOCKED |
| 07 VieNeu/matching | Generated WAV decoded, real time offsets and bounded source ranges | Fixture PASS; real VieNeu BLOCKED |
| 08 Rendering/E2E | FFmpeg pilot/final MP4 audio/video decode, Engine N00-N09, source tamper invalidation | PASS synthetic only |

## Security regression
- TDD reproduced and fixed N08 production accepting unreviewed automatic first-source pilot.
- TDD reproduced and fixed provider config without pinned worker file.
- TDD reproduced and fixed production editor substituting an output pilot different from approved preview.
- Stage3 runtime digest includes every stage3 Python source, not only entry script; mismatched digest stops execution.
- No real signer secret was used; all fixture receipts confined to synthetic QA runs.

## Scope
All tests use a generated 1.4-second color/sample-tone movie and synthetic story/review/voice fixtures; these are NOT actual AI inference, narrative verification, or proof of creative video quality. Missing AI model workers remain explicitly blocked. Production AI setup, full-film verification and genuine human approvals require separate authorization.

## Next safe gates
1. Approve offline model/runtime installation or specific preexisting model executable/checkpoint paths and licenses for Whisper, CLIP, Qwen3-VL; test GPU fit first.
2. Approve VieNeu local model and authorized voice profile, run only synthetic text smoke tests first.
3. Later authorize a specific real-film sample, only after provider integration and security review. Never auto-merge main.

## Observed final synthetic verification
- Entire repository: python -B -X utf8 -m unittest discover -s tests -v → **45 tests discovered, OK (skipped=1), exit 0**. This is 44 executed passing tests and one Windows symlink privilege skip.
- Stage 3 isolated end-to-end: **18/18 Engine CLI checks passed**, N00–N09 DONE on synthetic sample prior to intentional tampering; test-only missing/forged approvals blocked.
- Final synthetic N09: **0.833333 seconds**, **8,681 bytes**, SHA256 `93ccef7e0c3c4d50b34c3d2f4c068370dc83e666857dd7b0d8bf9b1338dd53e3`; both video/audio streams passed FFmpeg full decode.
- The QA run intentionally invalidates its synthetic source and an artifact *after* validating the final MP4; this is a recovery/tamper test and does not touch any real film.
- Full machine-only result: `D:\Phim\__FRA_PHASE3_20261122\runs\stage3-0c2d36da0\acceptance.json`.
