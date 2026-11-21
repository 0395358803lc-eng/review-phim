# Phase 5 — Real Fatman sampling and synthetic Engine21 QA

**2026-11-22 · Verdict:** TECHNICAL PASS / REAL-FILM SEMANTIC ACCEPTANCE PARTIAL. Public information here is numerical metadata only; no movie frames, audio, subtitles, full dialogue or translations are uploaded.

## Real Fatman source (strictly read-only)

A user-approved original Fatman (2020) source runs 5,823.552 seconds. Phase5 read the original film and the three previously approved 30-second excerpts at 00:09, 00:37, and 01:16 (total 90 seconds = 1.55%). All outputs are in isolated host QA storage, not in the GitHub repository. Original SHA-256 was checked before and after.

### English → Vietnamese source fidelity
- Previous actual offline Whisper CUDA produced 17 English time-stamped ASR rows.
- Existing offline Qwen3-VL produced 17 **tentative** Vietnamese translation candidates from those source rows. Original English text and source SHA were retained; zero translations approved.
- Two ASR rows need human audio listening. At least one specific mistranslation (mail “letters” interpreted as alphabet characters) was identified; the machine translation cannot be treated as correct without review.

### Visual facts and temporal observations
- Nine original movie frames from prior QA, plus **two short sequences of four consecutive source frames spaced one second apart** examined through Qwen3-VL. The sequence captions are hypotheses, not continuous action or plot certification.
- CLIP’s earlier self-caption retrieval recovered the original source frame top1 in 8/9 cases. One source frame was ranked second; exact-claim Qwen visual YES on the correct frame allowed an evidence-bound tentative selection without swapping its original claim ID.
- Qwen independently checked the exact original Stage4 claim text hash and frame SHA for three movie source claims: **3/3 YES**. Two unsupported visible-event statements (visible handwritten Santa letter, a rifle visibly firing) were answered **NO** and blocked. These verdicts are model QA, not human truth labels.
- Three source-anchored Vietnamese storyboard sentences preserved the original Stage4 claim IDs and source timestamps. No voice timeline was invented. Status: **NOT READY TO RENDER**, human script/voice/pilot approval missing.

## Engine21 real-worker check (synthetic input ONLY)
- The modified N07 truly loads CLIP then Qwen3-VL from existing CUDA installations; Qwen YES on exact N05 evidence, N03 frame SHA agreement.
- N00–N09 **10/10 DONE**, **13/13 CLI outcomes expected**, including two missing-approval attempts correctly blocked.
- Final synthetic MP4 audio/video decoded: **2.916667 sec, 55,059 bytes**, SHA256 126a6d5af4908a5027f409d11e6b575c0d98e114e90f785a6f29d992938ed0f1.
- Three approval-request manifests remain unsigned. QA HMAC signer is test-only; no genuine human film/voice approval.
- Host execution pins source modules plus both local CLIP and Qwen3-VL model weight checksums.

## Quality gates and remaining work
- **121 unittest tests discovered, 120 passed, one skipped** for Windows symlink privilege (exit 0); fresh git diff --check exit 0.
- Real-film production N00–N09 **NOT** run: current N02 assumes synthetic Vietnamese ASR, N03 samples only one still and downstream QA audio/matching handles a single sentence.
- Real-film story accuracy, full 97-minute scene retrieval, independent human labels, voice ownership, full multi-sentence audio segmentation, and approved 90–120s recap pilot still require separate work.
- No installation, deleted old film data, raw movie uploads or main merge.
