# Phase 3 — AI Adapter Integration (2026-11-22)

## Goal
Implement all eight user-approved scopes on a new development branch without installs, use solely synthetic test media, and never claim uninstalled AI models have run.

## Approved constraints
- Work in new isolated Windows QA workspace; do not open/copy/modify old film footage or products.
- Use installed system binaries and model runtimes only. Do not install packages or download model weights.
- Keep all 11 Agent Skills byte-for-byte unchanged; Engine 2.1 approval gates remain authoritative.
- GitHub changes only in feature/phase3-ai-adapters with Draft PR; main never merged.
- Never manufacture real human approval; synthetic HMAC fixture receipts strictly confined to QA.

## Decision and tradeoff
Implement **production-gated stage adapters plus deterministic synthetic fixtures** rather than simulated inference disguised as actual AI. All real AI operations require configured, approved, installed local provider executables/checkpoints. Missing providers fail closed and are reported as blocked. FFmpeg/ffprobe video analysis and render may operate on a permitted real source later, but this phase runs synthetic only.

## Architecture
- `adapters/inventory.py`: read-only detection GPU, executables, Python packages and model provider capabilities; no installation.
- `adapters/framework.py`: validates Engine environment, stage-specific required outputs, input hashes, provider config, logs/limits; emits SHA-linked evidence and never writes outside Engine output_dir.
- `adapters/media.py`: FFmpeg probe/decode/scenes/frame sampling and media construction; no old assets.
- `adapters/providers.py`: local worker contracts for Whisper, CLIP, Qwen3-VL, VieNeu and narrative generation; require approved host paths and checksums, report unavailable rather than assume model presence.
- `adapters/stage_adapter.py`: single trusted dispatch entry for N00–N09; explicit `--mode synthetic` vs `--mode production`, deterministic synthetic payloads, evidence QC.
- `qa/phase3_synthetic_acceptance.py`: synthetic movie/WAV, HMAC test-only supervisor, real `engine21` CLI for all stages; end-to-end QC and failure cases.

## Stage evidence contract
Output files are always produced within unique `.engine21/attempts/Nxx/####/`. The engine validates expected filenames, hashes, source provenance, valid JSON/JSONL, audio/video full decode, sentence-shot map; adapter also pins trusted provider workers and writes provider provenance/mode to `evidence.json` limitations. Engine manages dependencies, approval at N06 and N08, retry and state.

## Security and failure behavior
- Provider executable/worker and model checkpoint must exist locally and match configured SHA. No implicit model downloads.
- Reject out-of-job access, unknown command placeholders, nonzero exit and timeout. No arbitrary remote API calls in synthetic.
- If provider cannot supply actual content, production stage errors. Synthetic `PASS` never implies semantic correctness or human approval.
- File paths and stage strings are validated before work. Source digest checked pre/post.

## Acceptance criteria
1. Environment capability report clearly distinguishes available, missing and unverified components.
2. TDD unit tests fail before implementation, then pass for each new component; original suite remains green.
3. Synthetic MP4/WAV test drives all N00–N09 using `engine21` and mock human approval only within synthetic QA; video decodes.
4. Negative tests: wrong input SHA/approval, production missing providers, missing outputs/invalid media, invalid provider signatures.
5. Draft PR and QA report published, main untouched, 11 skills unchanged.
