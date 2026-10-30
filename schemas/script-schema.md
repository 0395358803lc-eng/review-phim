# script.json — Narration + Claim Ledger

## Envelope bắt buộc cho mọi artifact
schema_version: string (mặc định "1.0"); job_id: string; source_sha256: string (64 ký tự hex của tệp nguồn); generator: object {name:string,version:string, config_hash:string}; produced_at: ISO-8601 UTC string. Hash của artifact được lưu trong stage manifest; dữ liệu không chứa credentials.

## Fields
- editorial_brief: {genre,format,language,spoiler_policy,target_duration_s,aspect_ratio}
- sentences: {sentence_id,text,function,claim_type(FACT|OPINION|INTERPRETATION),evidence_ids[],state,visual_intent,story_time_range?,target_duration_s}[]
- approval: {script_locked:boolean,approved_by?,timestamp?}; locked only after checks

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
  "editorial_brief": {
    "genre": "science-fiction",
    "format": "review",
    "language": "vi",
    "spoiler_policy": "spoilers",
    "target_duration_s": 90,
    "aspect_ratio": "9:16"
  },
  "sentences": [
    {
      "sentence_id": "S001",
      "text": "Bộ phim sử dụng chiếc radio làm biểu tượng cho sự hối tiếc.",
      "function": "INTERPRETATION",
      "claim_type": "INTERPRETATION",
      "evidence_ids": [
        "EV_042"
      ],
      "state": "INFERRED",
      "visual_intent": "radio close-up",
      "target_duration_s": 5
    }
  ],
  "approval": {
    "script_locked": false
  }
}
~~~

## Validation checks
- Every FACT must have direct verified evidence; INFERRED claim clearly qualified in text
- All evidence IDs and character/time references resolve; no unsupported critical FACT
- Voice timing is estimate until actual TTS, do not lock video duration from text length

Tham khảo ORCHESTRATION.md: schema invalid -> stage FAIL/NOT_TESTED, không được tự động coi là PASS.
