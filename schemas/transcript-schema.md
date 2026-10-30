# transcript.jsonl — ASR Speech Contract

## Envelope bắt buộc cho mọi artifact
schema_version: string (mặc định "1.0"); job_id: string; source_sha256: string (64 ký tự hex của tệp nguồn); generator: object {name:string,version:string, config_hash:string}; produced_at: ISO-8601 UTC string. Hash của artifact được lưu trong stage manifest; dữ liệu không chứa credentials.

## Fields
- segment_id unique; start_s,end_s numeric video-clock seconds
- text: verbatim speech string; language: BCP-47 or identified language
- speaker_cluster: string|null (SPEAKER_00 not character identity)
- asr_confidence: number 0..1|null, measured/estimated label
- words: array of {text,start_s,end_s,confidence?,alignment_status?}
- source_refs: array of audio segment IDs; overlap_flag: boolean

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
  "segment_id": "ASR_042",
  "start_s": 3130.4,
  "end_s": 3133.6,
  "text": "Đừng mở cánh cửa đó.",
  "language": "vi",
  "speaker_cluster": "SPEAKER_00",
  "asr_confidence": null,
  "overlap_flag": false,
  "words": [
    {
      "text": "Đừng",
      "start_s": 3130.4,
      "end_s": 3130.75
    },
    {
      "text": "mở",
      "start_s": 3130.8,
      "end_s": 3131
    }
  ],
  "source_refs": [
    "audio:3130.4-3133.6"
  ]
}
~~~

## Validation checks
- All segments fit in media duration; start_s < end_s; one track's ordered words cannot cross bounds
- Word timestamps must be measured on final audio, not guessed from character count
- Transcription uncertainty and diarization overlap explicitly marked; ASR not treated as source of absolute fact

Tham khảo ORCHESTRATION.md: schema invalid -> stage FAIL/NOT_TESTED, không được tự động coi là PASS.
