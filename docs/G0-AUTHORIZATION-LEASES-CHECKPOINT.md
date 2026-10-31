# G0 authorization and durable GPU scheduling — development checkpoint

**Date:** 2026-10-31. **Branch:** feat/balanced-cpu-gpu-runtime-20261031. **Status:** UNDEPLOYED / SYNTHETIC-TESTED ONLY.

## Implemented code

- `g0_security.py`: immutable scope envelope (device ID, scope ID, authorization reference, allowed G0 operation, UTC validity window). A separately injected verifier must return literal `True` before invoking the connector's device-bound runner. Denial, mismatch, expiry and verification errors fail closed.
- `telemetry_receipt.py`: bound `G0_TELEMETRY` grant; monotonic start/end measurement; UTC timestamp assigned **after** observation; >5s sample, clock rollback, expiry and malformed data block scheduling.
- `gpu_lease_store.py`: SQLite transactions (`BEGIN IMMEDIATE`), per-device leases, conservative cumulative GPU/CPU budget, single heavy GPU job, duplicate reservation prevention, durable post-restart state. Reservations do **not** automatically expire; releasing an allocated PID requires a positive external end-of-process check. No PID => release blocked.
- Tests: `test_g0_security_gate.py`, `test_telemetry_receipt.py`, `test_gpu_lease_store.py`. They use synthetic host responses, not a real user's video or GPU.

## Binding limits: not production-ready

1. The permission verifier and runner are injected mocks: **no connector-issued signed G0 grant implementation exists**. A dishonest verifier callback could approve anything. Only a trusted host/connector can issue an attestation. Older `collect_g0(... approved=True)` remains a compatibility entry point and **must never be used directly by an external request**; it requires integration hardening.
2. The sampling code depends on authentic clocks passed by a trusted host adapter. The CPU and GPU command reads are sequential, not atomic, and the environment may change immediately after measurement.
3. The persistent lease store is not yet integrated into an authorized process launcher, and PID-only reconciliation must be strengthened against PID reuse and races using verified process creation identity. No automatic timeout recovery exists.
4. GPU memory reservation is a conservative prediction, not measured physical allocation. A second application outside the plugin can still consume VRAM. **GPU runtime / CUDA / NVENC is NOT tested.**
5. Missing before live operation: source SHA-256-bound permissions; handle-bound Windows source-path checks; exact executable identity/CLI validators; durable job/PID verification; G1; `PROCESS_APPROVED`; model/runtime installation and host integration.
6. Do not run `G0ReadGrant` tests as permission to inspect the selected film or create output files. The host and film remain untouched.

## Release gates

Required before moving beyond this checkpoint: connect G0 verifier to a real authenticated connector; add host-backed trusted timestamps; test cross-process concurrency on Windows; reconcile PID with start identity; separately authorize any G1 installation, process, transfer and write operation; run independent security review. Keep PR #4 Draft and `main` untouched.
