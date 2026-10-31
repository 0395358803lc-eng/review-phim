# Windows G0 command boundary + process identity — code checkpoint

**Date:** 2026-10-31. **Status:** UNDEPLOYED, NOT PRODUCTION-READY. Applies only to feature branch `feat/balanced-cpu-gpu-runtime-20261031`.

## New code

1. `runtime/review_phim_runtime/g0_windows_adapter.py` — an injected transport wrapper permitting exactly four fixed, non-media command vectors from `g0_collector` and `telemetry`. Requires the response to bind the same device, SHA-256 digest of exact argv, integer return code, and bounded text output. It never invokes a shell, and cannot accept caller-supplied media paths. **Transport itself must be authenticated and trusted; the wrapper does not sign or verify cryptographic attestations.**
2. `runtime/review_phim_runtime/gpu_lease_store.py` — persist both PID and Windows process creation timestamp (`process_started_ns`). The legacy `bind_pid` is disabled. A `ProcessStatus` proof with matching device, PID, start timestamp and `EXITED` from a trusted checker is required before release. Existing PID-only reservations remain blocked and need manual separately approved reconciliation; no automatic reclaim.
3. `runtime/review_phim_runtime/windows_process_inspector.py` — read-only Win32 process query through a single `OpenProcess` kernel handle, `GetProcessTimes` and `WaitForSingleObject`. A missing/reused PID or inaccessible handle returns UNKNOWN rather than EXITED. It does not create, kill or modify processes.
4. `runtime/tests/test_g0_windows_adapter.py`, `test_process_identity.py`, `test_windows_process_inspector.py` — synthetic test cases for exact allowlists, receipt spoofing, oversized output, PID reuse, persistence, and one synthetic Python subprocess on Windows CI.

## Critical gates still missing

- There is **no real connector transport implementation** or cryptographic grant issuer. Device ID, SHA-256 command digest and a typed `ProcessStatus` are NOT authentication by themselves; an untrusted caller could fabricate all three. Runtime must receive these exclusively from a connector/OS-trusted boundary.
- Independent authorization must be enforced by a real host/connector against time, device, job, permissions, scope ID and all side effects. Existing `approved=True` compatibility calls in lower-level code cannot be exposed to untrusted callers.
- Win32 `OpenProcess` returns UNKNOWN when an old process object has disappeared, even if it truly exited: the lease remains reserved. This is intentionally conservative. Future host process orchestration should retain a durable process HANDLE or equivalent independently verified lifecycle record to enable safe eventual reconciliation.
- SQLite does not automatically reclaim leases. No cross-process live resource manager, actual RTX 4060 benchmark, model runtime, or disk quotas have been proven.
- No source-file handle binding, source SHA-256 scope enforcement, real FFprobe/ASR/VLM adapter or media access is authorized.

**Approval boundaries:** PR may be reviewed in Draft; **do not merge, install, download models, process films, transfer media or publish** based on this document. G1/PROCESS_APPROVED and other gates remain separate.
