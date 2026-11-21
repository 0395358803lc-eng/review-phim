# Film Review Agent — Phase 3 adapters

**Status: AI provider integration still BLOCKED without local models.** This module implements a tested adapter framework and real FFmpeg processing on generated synthetic media. It is not a completed real-film review pipeline.

## Eight approved packages

| ID | Implemented | Runtime outcome |
| --- | --- | --- |
| 01 | Passive GPU/Python/package inventory | PASS on DESKTOP-2GP3E41 |
| 02 | StageContext source/attempt validation, SHA runtime package and provider pinning | PASS |
| 03 | FFmpeg probe/full decode, scene cut detection, indexed timestamps | PASS with synthetic video |
| 04 | N02 Whisper/translation provider contract, synthetic transcript | Production Whisper worker/checkpoint missing |
| 05 | N03 Qwen3-VL and N07 CLIP/Qwen provider contracts | Production model workers/checkpoints missing |
| 06 | N04 story evidence graph, N05 script/atomic claim fixtures | Production narrative/LLM worker missing |
| 07 | N06 actual decodable WAV fixture; N07 source-constrained sentence-shot map | VieNeu environment present, real TTS and semantic inference not tested |
| 08 | N08/N09 real FFmpeg MP4/AAC render, QC and Engine 2.1 E2E | Synthetic accepted; production video worker not configured |

## Security / contract

The new adapter is stage3_adapter.py. It accepts --mode synthetic or --mode production, and always requires --runtime-sha256 with actual runtime_digest() of all its Python sources. The entire runtime is pinned, not just the launcher. Production N02-N09 require --provider-config outside the job, with absolute installed executable, SHA256, at least one pinned local worker/model file, bounded timeout, and a provider_verification.json reporting model_id, source SHA, stage and validated checks. Missing provider or missing data fails closed, NEVER synthetic fallback.

Engine21 still owns stage preconditions, locks, source hashes, signed human approval receipts at N06/N08 and FFmpeg independent validation. In production N08, generated pilot.mp4 must have the exact digest of the pilot approved by the host, otherwise reject.

NO untrusted model weights are downloaded and no new software is installed. An adapter is not an OS sandbox: the host must enforce filesystem/network restrictions and keep approval signing secrets outside the AI agent.

## Local commands

From repository root:

    python -B -m stage3.inventory
    python -B -c "from stage3.framework import runtime_digest;print(runtime_digest())"
    python -B -m unittest discover -s tests -v

Synthetic runner argv to configure in the trusted Engine21 adapter configuration (requires the actual installed absolute Python and source paths):

    -B ABSOLUTE_REPO\stage3_adapter.py --mode synthetic --runtime-sha256 THE_ACTUAL_DIGEST

The production example config in examples/phase3-providers.example.json intentionally enables no workers. Never use synthetic mode to make a real-film deliverable. Acceptance script:

    python -B qa\phase3_synthetic_acceptance.py --qa-root D:\Phim\__FRA_PHASE3_20261122

## Remaining constraints

System Python 3.13.15 lacks faster-whisper, Whisper, OpenCLIP, Transformers, PyTorch, qwen_vl_utils and PySceneDetect. A separate already installed VieNeu TTS Python 3.11.18 venv has vieneu, torch and transformers, but no user-approved local voice model checkpoint/profile or production worker has been configured. NVIDIA RTX 4060 has 8188 MiB VRAM; model fit must be tested separately.

Synthetic approval receipts are test-only, not human consent. Synthetic transcript and review are labeled as fixtures; no actual film story/actor/action matching was performed. Production connectors remain pending separately scoped installation/configuration approvals.

## Existing local model acceptance (2026-11-22)

Real local Whisper, CLIP, Qwen3-VL and VieNeu models were smoke-tested on isolated synthetic content using preinstalled legacy weights and environments; a short cross-modal evidence-linked review render was independently checked. See [dated local-model acceptance report](docs/qa/local-models-2026-11-22.md) and [the QA evidence bridge](qa/local_model_bridge.py). This is not production-model orchestration or an approved real-film review; no old model weights, generated media or transcripts are bundled.
