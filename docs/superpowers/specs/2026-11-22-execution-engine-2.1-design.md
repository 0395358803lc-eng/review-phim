# Execution Engine 2.1 — Design specification

## Intent
Make the existing eleven Agent Skills executable through a local host-controlled engine, while preserving all existing skills, user media, and the main branch. Phase 1 is an execution core with synthetic and real-media QC tests, not full AI model integrations.

## Approaches evaluated
1. **Extend the old jobctl:** smallest diff but legacy `approve --reference` can be authored by an agent, and stage DONE stores claims, not runtime proof.
2. **Standalone core + controlled tool adapters (selected):** keeps `skills/**/SKILL.md` byte-for-byte and old jobctl intact; adds a fail-closed state machine and separates trusted adapter configuration and approvals. Costs a second state store, documented explicitly.
3. **Large workflow engine/Celery/Temporal:** mature scheduler but excessive dependencies, services and privileges for phase 1.

## Scope and interfaces
- Python 3.10+ standard library for runtime. Optional ffmpeg/ffprobe for media stage verification (missing commands block, never silently skip).
- `engine21` package: state/recovery, HMAC approval verifier, stage runner, CLI. `jobctl` 2.0 remains the intake utility, not an authoritative engine-state writer.
- Job source path/hash from `job_state.json`; stages N00..N09 and dependency DAG from the established 2.0 skill pack. Stage outputs written to unique `engine21/attempts/Nxx/####` locations and never overwrite previous attempts.
- Adapter config outside job is explicitly chosen by operator, pinned by SHA-256 in state. Allowed adapters use explicit executable path and argv list, never shell. Config changes require new engine state/revision. The tool is *not* a security sandbox; scripts from untrusted sources must not be authorized.
- Each stage writes `evidence.json` with PASS, original source hash, mandatory check names, artifacts with SHA-256. Engine independently rehashes all files; N00, N06, N08, N09 require real media decode, N07 additionally validates sentence-shot map. Semantic assertions require human evidence review; Boolean flags alone never certify semantic correctness.
- Gate before N06: signed `script` and `voice` approval bound to N05 evidence digest and voice sample hash; before full N08: signed `pilot` approval bound to a real pilot MP4 hash. HMAC key is provided by an external trusted host; no production signing tool exists inside the agent package. If trust boundary cannot be enforced, don't enable execution needing approvals.
- State uses atomic JSON and OS file locking; interrupted RUNNING jobs reconciled as INTERRUPTED. A stage can be reattempted only when its adapter declares `retry_safe` or with fresh operator authorization. DONE stage artifacts revalidated every run; corrupted stage and descendants become STALE; no implicit destructive repair.
- The 2.0 skill descriptions and 9 baseline tests must remain unchanged and passing. No source/media files packaged. No writes to main. The user will review the development branch before merge.

## Non-goals
No actual Whisper/Qwen/CLIP/VieNeu integrations, unattended full film production, enterprise security boundary against a malicious OS-level agent, new data migrations, auto-signing approval, CI deployment to main, changing the existing 11 SKILL.md files, or automatic delete of V1/V2 state.

## Acceptance
- Runner executes allowlisted synthetic adapter, persists stage evidence, preserves artifact hashes, and blocks out-of-order stages.
- Recovery handles interrupted, failed, stale, changed config/source, invalid HMAC signatures, revoked/expired approvals, attempts/timeouts.
- Real FFmpeg smoke media proves independent decode checks; fake claims without genuine media fail.
- 9 legacy tests + new tests pass. Branch remote is verified; main unchanged. Provide PR for human review, not merge.
