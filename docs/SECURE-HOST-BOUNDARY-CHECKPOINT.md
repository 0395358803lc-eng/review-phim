# Secure host boundary checkpoint — 2026-10-31

**Branch:** `feat/balanced-cpu-gpu-runtime-20261031` (PR #4 Draft). **State:** prototype, uninstalled, no actual host/media tests.

## Why this checkpoint exists

The prior mockable Windows adapter only checked command-vector SHA-256 in a returned receipt. A checksum is **not an authentication mechanism**: an untrusted sender could fabricate both the response and its hash. The earlier GPU release method relied on an injected process-status callback, and the source-hash bind had no handle-based verification contract.

## Additions

1. **`g0_attestation.py` — G0 HMAC scope contract.** Host-held 256-bit-or-longer key produces a domain-separated HMAC-SHA256 over device, scope ID, permitted G0-only operations, authorization reference and normalized UTC validity. Maximum grant validity 15 minutes. Tampering, wrong device, overbroad operations, malformed grant and expiry fail closed. **No real signing issuer or key-management service is provided.** The host/connector must retain keys outside plugin prompts, repository, tool outputs and logs.
2. **`source_binding.py` — approved-source digest contract.** A separate `SOURCE_HASH` grant containing `PROCESS_APPROVED` reference, target device/job, exact Windows local path, file size and full expected SHA-256 is checked *before* calling the host's handle opener. The opener must return one verified canonical path, file identity and binary stream from the same OS handle; hashing proceeds on that stream only. The result carries digest/size/identity, never film bytes. An injected verifier is not itself a real grant issuer. Video contents were NOT read in this checkpoint.
3. **`process_attestation.py` — signed exit receipt contract.** Domain-separated HMAC-SHA256 receipt binds device, job, PID, process creation timestamp, state and observation time. A signed `EXITED` observation no more than ten seconds old, matching the stored GPU lease, is required to release via `release_with_attestation`. A signed assertion is not proof of OS truth unless issued *after* a real trusted Windows handle check. The trusted host should bind `windows_process_inspector.py` to receipt issuance, not accept arbitrary caller-provided status.

## Test scope and red-green proof

The new tests use exclusively mocked connector responses, in-memory synthetic source bytes and isolated SQLite databases. They exercise tampering, wrong key/device, time boundaries, expired grants, wrong media path, source hash or size mismatches, reused PID, falsified `EXITED` status and stale observations.

## Important unresolved release gates

- **Authentic issuer and connector integration missing.** The signing classes expose `sign` as code-only contracts; only a trusted host service holding protected keys and validating explicit user consent can issue real tokens. The `approved=True` lower-level G0 entrypoint still exists; **do not expose it to untrusted callers**.
- **Authentic source handle missing.** A production Windows adapter must open and pin the actual file handle, verify canonical volume/file identity, detect concurrent mutation, and enforce source scope while it is used. A path name and injected callback alone cannot prevent race conditions.
- **Authentic process lifecycle missing.** An authenticated host process monitor must bind kernel handle/creation time to its signed exit receipt. A missing old process handle remains `UNKNOWN` and requires separately authorized reconciliation; do not silently free GPU leases.
- The `SafeRunner` is a prototype: media scope signatures, original source digest enforcement at execution, durable PID launch, exact command identity, real byte-output limits and cancellation are not wired end-to-end.
- No GPU/CUDA/NVENC benchmark, FFmpeg installation, ASR, VLM, TTS, movie inspection, voiceover, render, media transfer, publication or merge occurred. `main` remains unchanged.

**Next checkpoint:** isolated Windows integration tests for a trusted connector/issuer adapter and handle-bound source verification, then synthetic FFmpeg adapter tests. Any host install/write needs G1; any original film probe/hash/processing needs separately scoped `PROCESS_APPROVED` and any output requires its own approval.
