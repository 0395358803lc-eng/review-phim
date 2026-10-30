# qc.json — Validation and Handoff

## Envelope bắt buộc cho mọi artifact
schema_version: string (mặc định "1.0"); job_id: string; source_sha256: string (64 ký tự hex của tệp nguồn); generator: object {name:string,version:string, config_hash:string}; produced_at: ISO-8601 UTC string. Hash của artifact được lưu trong stage manifest; dữ liệu không chứa credentials.

## Fields
- checks: {check_id,category(FACTUAL|EDITORIAL|TECHNICAL|RIGHTS|ENVIRONMENT),status(PASS|PARTIAL|FAIL|NOT_TESTED|BLOCKED),evidence_paths[],measured_value?,threshold?,reviewer?,reason}
- blocking_issues: string[]; overall_status never PASS if blocking check failed/untested
- human_approvals: approvals per gate; no implicit copyright approval
- render_artifact: path + sha256 only when file exists and has been probed

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
  "checks": [
    {
      "check_id": "QC_FACT_001",
      "category": "FACTUAL",
      "status": "NOT_TESTED",
      "evidence_paths": [],
      "reason": "synthetic example only"
    }
  ],
  "blocking_issues": [
    "real source video not provided"
  ],
  "overall_status": "NOT_TESTED",
  "human_approvals": [],
  "render_artifact": null
}
~~~

## Validation checks
- Every PASS needs observable evidence and outcome; absent run -> NOT_TESTED
- Overall PASS blocked by critical claims unsupported or unresolved rights
- Technical PASS does not imply editorial/legal PASS

Tham khảo ORCHESTRATION.md: schema invalid -> stage FAIL/NOT_TESTED, không được tự động coi là PASS.
