# state.json — Resumable Jobs

## Envelope bắt buộc cho mọi artifact
schema_version: string (mặc định "1.0"); job_id: string; source_sha256: string (64 ký tự hex của tệp nguồn); generator: object {name:string,version:string, config_hash:string}; produced_at: ISO-8601 UTC string. Hash của artifact được lưu trong stage manifest; dữ liệu không chứa credentials.

## Fields
- stage: current stage; stages[] record {name,status,tool_version,input_hash,config_hash,artifact_paths,artifact_hashes,started_at,finished_at,verified_by}
- host_device_id and approved_root required before any host action
- pending_call_id and process_id optional for async connector operations, to check before retry
- rights_approval and install_approval separate fields

## Example synthetic (KHÔNG phải kết quả phân tích video thật)
~~~json
{
  "schema_version": "1.0",
  "job_id": "DEMO-001",
  "source_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "generator": {
    "name": "synthetic-fixture",
    "version": "0",
    "config_hash": "demo"
  },
  "produced_at": "2026-10-30T00:00:00Z",
  "stage": "DISCOVER",
  "host_device_id": null,
  "approved_root": null,
  "stages": [
    {
      "name": "INGEST",
      "status": "NOT_STARTED",
      "tool_version": null,
      "input_hash": null,
      "config_hash": null,
      "artifact_paths": [],
      "artifact_hashes": [],
      "started_at": null,
      "finished_at": null,
      "verified_by": null
    }
  ],
  "pending_call_id": null,
  "process_id": null,
  "rights_approval": false,
  "install_approval": false
}
~~~

## Validation checks
- PASS stage must include hashes/verifier; running stage with pending call must be polled before retry
- Changes to source hash/config/model version invalidate dependent stages
- Device and root never silently inherited from unrelated job

Tham khảo ORCHESTRATION.md: schema invalid -> stage FAIL/NOT_TESTED, không được tự động coi là PASS.
