# Phase 3 — Existing local models acceptance (2026-11-22)

**Verdict:** Real local AI inference and short synthetic scene-review render PASS. Full real-film production and unattended agent production workflow NOT YET CERTIFIED.

**Machine:** DESKTOP-2GP3E41; RTX 4060 8188 MiB; existing CUDA 12.8 runtime.  
**Legacy data source:** User-authorized Windows workspace, accessed read-only. The absolute path is retained only in the local QA checkpoint.  
**Isolated work folder:** A separate Windows QA workspace outside the legacy project (all new outputs; absolute path retained locally).  
**Safety:** No installs, model downloads, legacy film data modifications, new public movie/media uploads, or main merge.

## Local models identified and genuinely exercised

| Component | Legacy model path relative to legacy root | Actual technical result |
| --- | --- | --- |
| Whisper | models/asr/faster-whisper-large-v3-turbo | CUDA inference and accurate Vietnamese transcript |
| CLIP | models/embeddings/clip-vit-base-patch32 | Real 512-dim image/text embeddings, top-1 retrieval |
| Qwen3-VL | models/vision/qwen3-vl-2b-instruct | Real image inference on RTX 4060 |
| VieNeu | models/tts/vieneu-v3-turbo plus models/tts/moss-audio-tokenizer-nano | Real 48 kHz synthesized WAV on CUDA |

Each worker used its preinstalled environment, local model files and offline-mode environment variables. The preset Trúc Ly voice was used for technical synthetic QC only, NOT approved as production voice.

## Independent inference evidence

- **VieNeu** generated the synthetic phrase "Xin chào, đây là kiểm thử âm thanh." as WAV 2.000 s / 192044 bytes / SHA256 8e39ea1d762283d54a13525738fb2e4e53464c671bbba90d0bbf0c3a6c2a9fd9. A second WAV of a visual-review test sentence was **2.960 s**, **284204 bytes**, SHA256 15aa0a246018df01e79b72da3ba805d8eb4075737de11f5e3c9e3ffae8bb9514.
- **Whisper** initially loaded its model but failed CUDA because cublas64_12.dll was not on the process PATH. A subsequent test used that DLL from already installed VieNeu PyTorch torch/lib in the PROCESS-LOCAL PATH only. GPU ASR then passed twice with exit 0, recognizing both synthesized utterances accurately; language vi.
- **Qwen3-VL 2B** saw a synthetic drawing and wrote exactly: "A red square and a blue circle." GPU peak PyTorch allocated memory: **4,284,524,032 bytes**. Process exit 0.
- **CLIP ViT-B/32** computed 512-dimensional image and text vectors; self-retrieval cosine approximately 1.0. Using Qwen's ACTUAL answer as the CLIP query, the correct image ranked **#1** against green/blue distractors (source score 0.3436; nearest distractor 0.2846). A green-square control query ranked the green image #1. Scores are NOT probabilities.

## Cross-model evidence bridge

The new portable QA helper at qa/local_model_bridge.py binds:
1. Qwen report SHA to the CLIP source-caption query; rejects swapped/altered reports.
2. VieNeu WAV SHA to BOTH TTS and ASR result manifests; rejects mismatched audio.
3. Normalized ASR transcript to actual narrated review text (minimum similarity 0.72); observed **1.0000**.
4. An explicit synthetic story-memory event, deterministic Vietnamese visual-review sentence and a source-timebounded sentence/shot map with actual evidence IDs (visual_direct for synthetic shape), validated by the independent evidence_qc checker.
5. A real FFmpeg MP4 video with the same synthetic image and the synthesized narration; separately verified by FFprobe and full FFmpeg -xerror decode, both exit 0.

**Resulting output MP4:** 2.960 seconds, MPEG-4 video / AAC audio, 56184 bytes, SHA256 e4cd84479638c98d644f58acc2d24f90596987187c4499bab38bceedec54fb3f.

Local output folder: qc/linked_real_models_v1/ beneath the NEW isolated QA directory, with review_final.mp4, review_final.txt, story_memory.json, sentence_shot_map.json, acceptance.json. These media and transcripts are deliberately NOT uploaded into the public repository.

## What did NOT become production-ready

- This verified a technical synthetic color-and-shapes sequence. It does **not** show that CLIP/Qwen identify real film characters/actions correctly, or that a 2-hour movie can be processed end-to-end.
- The synthetic review was built deterministically from evidence. This does **not** certify autonomous creative screenplay review or LLM grounding over real plot events.
- The bridge is a QA tool; it is not a fully host-approved Engine21 provider worker running production stages automatically. The model weights and VENV are installed, but production workers, OS isolation and actual approval signer still require integration.
- Legacy analysis, review, timeline, shots and out directories each have **zero data files**; assets and beats are also empty. Only one small ~0.06 MiB temporary NVENC test MP4 was found. There was **no original full film and no real transcript/story memory** in the authorized old folder.
- Test-only voice preset is not approval for real film narration. No human-approved production pilot or real film source was used.

## Regression/security testing

- New tests prove valid binding, reject swapped Qwen/CLIP provenance, incorrect TTS/ASR voice hash and unrelated ASR text.
- All local runtime outputs remain in the isolated QA directory, not in the legacy workspace or GitHub.
- Run complete unit suite and clean source release validation before claiming readiness or merging.

**Review gate:** Keep changes on feature/phase3-existing-local-model-qa with a DRAFT PR against feature/phase3-ai-adapters. No merge to main until real-film/source approval, secure signed approval channel and production provider workers are independently verified.

## Fresh final verification

- The full repository suite discovered **49** tests; **48 executed PASS, 1 Windows symlink privilege test skipped**, exit 0.
- Independent evidence_qc sentence-shot map check: PASS (exit 0); FFprobe: MPEG-4 video and AAC audio, duration **2.960000 seconds**, 56184 bytes; FFmpeg full -xerror decode: exit 0.
- Clean source export containing **65 source files**: release validator PASS (no bundled media/weights/user data), git diff --check exit 0.
- Legacy model acceptance was conducted separately from the synthetic Engine 2.1 N00–N09 adapter acceptance. It does not change any signed approval gate or certify real-film semantics.


## 6. Additional Engine 2.1 real-worker integration acceptance

This goes beyond independent provider smoke tests. New QA-only host workers run the existing local model installations **through the Engine 2.1 controlled stage runner** on a newly generated 2.96-second synthetic source. No full-length real movie was used.

### First attempt: reproduced and fixed Windows offline-cache bug

The first real-worker Engine run reached DONE for N00 through N05 (real Whisper at N02, real Qwen3-VL at N03), then N06 failed. The TTS stderr showed WinError 206 because Engine21's subprocess environment allowlist had stripped HF_HOME, so the model cache resolved under a too-long relative "~/.cache" path inside an attempt directory.

A new red/green regression test now verifies a restricted helper in engine21/runner.py:
- Passes only explicitly permitted offline model environment values including HF_HOME, HF_HUB_OFFLINE, TRANSFORMERS_OFFLINE and TORCH_HOME.
- Rejects unrelated environment variables/secrets.
- Does not modify system PATH or global environment configuration.

The first FAILED job remains untouched under the isolated QA root for audit. A completely fresh job was used after the fix.

### Second attempt: genuine N00–N09 Engine run

**Outcome:** Engine21 real-local-model synthetic acceptance **PASS, 13 of 13 CLI checks as expected** (init, ten N00–N09 stages and two intentionally rejected approval-free calls), with **10 of 10 actual stages DONE** in independently read-back Engine state.

| Stage | Actual worker | Observed runtime |
| --- | --- | --- |
| N00 | FFmpeg probe and decode | 0.32s |
| N01 | FFmpeg scene timestamp index | 0.28s |
| N02 | Faster-Whisper large-v3-turbo on CUDA | 3.65s |
| N03 | Qwen3-VL 2B on CUDA | 9.77s |
| N04 | Deterministic evidence-linked story memory, NOT LLM understanding | 0.43s |
| N05 | Deterministic visual facts review, NOT freeform creative writing | 0.32s |
| N06 | VieNeu v3 Turbo on CUDA, test-only preset | 7.97s |
| N07 | CLIP ViT-B/32 on CUDA using actual Qwen caption | 5.18s |
| N08 | Host-signed TEST-only pilot hash, guarded delivery | 0.48s |
| N09 | FFmpeg final verification/manifest | 0.43s |

The Engine N06 and N08 checks **without any approval receipts** both failed closed with exit 2; test-only HMAC receipts allowed QA stage completion, but **are NOT user approvals**.

Production provider configuration inputs pin SHA256 of executables, QA worker script and relevant local model weight files, with each stage checked separately; source is SHA-locked by Engine21.

Independent verification:
- Engine state: **10/10 DONE** before any user-media-related operations (there are none).
- N07 evidence map checker: exit **0**, source ranges and visual claim evidence linked.
- Final MP4: **2.916667s**, **55,808 bytes**, MPEG-4 video + AAC audio.
- Independent FFprobe and full FFmpeg -xerror decode: **exit 0**.
- Final SHA256: **d68601c197f6b93879b4943950933dffb345b79e2325901b09b65675bd23184e**.

Local detailed result: runs/real-engine-06880b29c6/report.json inside the new isolated QA root; generated media and test-only keys remain there and are **NOT uploaded to GitHub**.

### Remaining acceptance boundaries

- N04 and N05 are rule-based assembly from the two actual model evidence streams, not autonomous film-plot creative review.
- The host HMAC signer is QA-only; production signing must run under a trusted separate identity/OS permission boundary.
- Workers and runtime are not a hardened OS sandbox. Filenames, external model versions, artifact SHA and configured provider scripts are checked, but real film data and unknown-length workloads require additional isolation/capacity testing.
- Real movie footage and original transcripts were absent from the authorized legacy workspace. Full-movie content correctness, actor/plot continuity and professional edit review are NOT verified.
- The specific old voice preset still requires project-specific authorization before actual production.

**Final technical verdict:** Four real local models + actual Engine21 N00–N09 subprocess orchestration **PASS on synthetic QA**, production full-film certification **NOT AVAILABLE** from the supplied legacy data alone.
