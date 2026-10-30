# evidence.jsonl — Grounded Claims

## Envelope bắt buộc cho mọi artifact
schema_version: string (mặc định "1.0"); job_id: string; source_sha256: string (64 ký tự hex của tệp nguồn); generator: object {name:string,version:string, config_hash:string}; produced_at: ISO-8601 UTC string. Hash của artifact được lưu trong stage manifest; dữ liệu không chứa credentials.

## Fields
- evidence_id unique; kind = TRANSCRIPT|FRAME|CLIP|AUDIO_EVENT|EXTERNAL_REFERENCE
- media_source_sha256: hash of source or URL citation for independently verified external reference
- start_s,end_s numeric where applicable; references IDs/paths and tool metadata
- observation: what was observed (not speculative cause); state = VERIFIED|INFERRED|UNSUPPORTED
- reviewed_by / reviewed_at optional; reason: why evidence supports or does not support claim

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
  "evidence": [
    {
      "evidence_id": "EV_042",
      "kind": "FRAME",
      "media_source_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
      "start_s": 3130,
      "end_s": 3131,
      "reference": "KF_42_01",
      "observation": "person holding portable radio",
      "state": "INFERRED",
      "reason": "one frame cannot establish destruction",
      "reviewed_by": null
    }
  ]
}
~~~

## Validation checks
- All evidence IDs resolve to real frames/transcript/audio and within source duration
- Confidence distinct from state; 'VERIFIED' requires direct evidence of assertion, not model confidence alone
- Do not include user-private media in public GitHub artifacts

Tham khảo ORCHESTRATION.md: schema invalid -> stage FAIL/NOT_TESTED, không được tự động coi là PASS.
