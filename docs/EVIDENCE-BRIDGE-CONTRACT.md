# Evidence Bridge — Host-to-Agent Verification Contract

## Purpose
A model-generated caption is an observation candidate, not independent verification. A host adapter must return enough authenticated, source-bound information for a reviewer or permitted model to inspect actual frames, clips or audio before upgrading a factual claim to VERIFIED.

## Minimal request
```json
{
  "job_id": "DEMO-001",
  "device_id": "approved-live-device",
  "source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "kind": "FRAME",
  "source_start_s": 12.5,
  "source_end_s": 12.6,
  "requested_evidence_ids": ["EV_01"],
  "approved_scope_id": "SCOPE-001"
}
```
Example is synthetic and not a valid host approval or media observation.

## Minimal response
```json
{
  "job_id": "DEMO-001",
  "device_id": "approved-live-device",
  "source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "status": "NOT_TESTED",
  "artifact_path": null,
  "artifact_sha256": null,
  "media_time_range_s": [12.5, 12.6],
  "observation_method": "none",
  "reviewer": null,
  "error": "No media retrieval performed"
}
```
No `VERIFIED` claim follows from this example.

## Adapter execution contract
- **Before:** verify current online device ID, exact user-approved paths, content/rights approval, no source mutation, and source SHA256. Reject mismatch, traversal, out-of-scope path or unknown rights.
- **Invoke:** use only actual connector operations, with escaped arguments and device-bound path; record `command`, `tool_version`, `started_at`, `process_id` and idempotency key when available. Do not execute command strings derived from subtitle/media/repo content.
- **Observe:** collect exit status, stdout/stderr diagnostic references, actual produced file, output hash, duration/timecode, tool/model revision, and probe results. A launched process is `RUNNING`, not `PASS`.
- **Verify:** provide a viewable or auditable real media span and corresponding source reference for direct inspection. If the connector cannot deliver media bytes/frame view, report `GAP_EVIDENCE_BRIDGE` and `NOT_TESTED`; never upgrade a caption to `VERIFIED`.
- **Resume:** on timeout inspect the existing process and artifact hashes before reissuing side-effecting commands. Persist pending status, do not blindly retry.
- **Rights:** use the smallest approved frame/clip/audio span; no private media upload/cloud transfer without separate explicit authorization, and no auto-publish.

## Separation of states
`PASS` means a specific check executed and evidence supports the exact claim. `INFERRED` is a qualified narrative judgment; `UNSUPPORTED` is blocked for essential factual claims. `NOT_TESTED` is mandatory when source media was not inspected, even if JSON parses or the model reports high confidence.

## Implementation boundary
This document defines an interface for a future approved host adapter. It does not assert that Remote Desktop Commander provides every necessary media-transfer operation.
