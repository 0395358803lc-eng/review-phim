# CPU/GPU Balanced Runtime — approved technical design

**Approved in conversation:** 2026-10-31. **Permission boundary:** repository feature-branch code/doc updates only. Not approval for installations, machine writes, model downloads, movie inspection or release.

## Goal
Integrate a host-local evidence-gated runtime with review-phim, optimized for Intel i7-14700F (20 cores/28 threads), NVIDIA RTX 4060 (8188 MiB VRAM), 31.79 GiB RAM, Windows 11, without weakening skill-level human approval.

## Architecture
ChatGPT is the decision-maker; device-specific runtime adapters execute approved local work. Separate responsibility into immutable contracts; scoped authorization; safe process runner; read-only inventory / capability assessment; CPU/GPU resource scheduler; FFmpeg/ASR/VLM/TTS adapters; source-bound evidence fusion; assistant review gate; and output QC. An installed skill alone does not install or execute these adapters.

## Mandatory user flow and truth gates
CONNECT_DEVICE -> SELECT_SOURCE_FOLDER -> SELECT_SOURCE_VIDEO -> SELECT_REVIEW_NICHE (exactly one of review, recap, review-recap, film-explained, character-theme) -> G0 -> optional G1 -> PROCESS_APPROVED -> G2-G7 evidence-reviewed work. Original source is immutable; no default cloud media upload. Text-only model claims remain MODEL_OUTPUT_UNVERIFIED or LOCAL_CROSSCHECKED; direct-film VERIFIED is separate and requires authorized media review.

## Resource profile (proposal, NOT benchmark)
GPU budget = max(0, min(floor(total_VRAM_MiB * .75), free_VRAM_MiB - 1024)). One heavy ASR/VLM/TTS job at a time; reserve GPU memory. CPU scheduler starts at 12 aggregate compute workers with at least four logical processors free. OOM: reduce batch/context once, then try a 4B->2B VLM with new provenance, otherwise BLOCKED. Never claim CUDA or encoder usability until measured.

## Threats and restrictions
- Canonical Windows paths must resolve junctions/reparse points on host and remain below an authorized root. No path resolver = block.
- Scope binds job, device, operation, original source, time window, expiry, cumulative quota, hashes and approved output root. Missing scope blocks.
- Shell execution must be disabled; executable and argument grammar validated per adapter. Connector timeout requires PID reconciliation before retry.
- No resource benchmark or synthetic test proves film-content correctness. No voice selected before catalog verification and user confirmation.
- G1, PROCESS_APPROVED, EVIDENCE_WRITE, MEDIA_TRANSFER, VOICEOVER, OUTPUT_WRITE and PUBLISH are separate grants.

## Deliverable strategy
First implement mock-testable foundational contracts, scope, runner and scheduler, then verified Windows inventory, adapters and evidence gates. Runtime prototype must not claim deployment or Windows device validation. Every change is test-first and is independently reviewable; maintain the main branch untouched until separately approved.
