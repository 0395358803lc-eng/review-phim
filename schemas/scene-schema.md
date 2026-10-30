# shots.jsonl, scenes.jsonl — Visual Segmentation

## Envelope bắt buộc cho mọi artifact
schema_version: string (mặc định "1.0"); job_id: string; source_sha256: string (64 ký tự hex của tệp nguồn); generator: object {name:string,version:string, config_hash:string}; produced_at: ISO-8601 UTC string. Hash của artifact được lưu trong stage manifest; dữ liệu không chứa credentials.

## Fields
- shot_id, scene_id: stable unique strings
- start_s,end_s in video-clock seconds; shots list per scene
- keyframes: array of {frame_id,time_s,path,sha256}
- characters: entity IDs plus identification_status; setting/action/objects as observations
- source_refs: shot IDs, transcript IDs; visual_tags: string[]; confidence 0..1|null

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
  "scene_id": "SC_042",
  "start_s": 3124.2,
  "end_s": 3198.8,
  "shot_ids": [
    "SH_161",
    "SH_162"
  ],
  "setting": "underground station",
  "characters": [
    {
      "entity_id": "CHAR_01",
      "identification_status": "INFERRED"
    }
  ],
  "actions": [
    "two people talk near radio"
  ],
  "keyframes": [
    {
      "frame_id": "KF_42_01",
      "time_s": 3130,
      "path": "work/DEMO-001/artifacts/kf_42.jpg",
      "sha256": "1111111111111111111111111111111111111111111111111111111111111111"
    }
  ],
  "visual_tags": [
    "radio",
    "platform"
  ],
  "confidence": null,
  "source_refs": [
    "ASR_042"
  ]
}
~~~

## Validation checks
- Shot set covers film or explicit known gaps; scene boundaries need not equal every camera cut
- Every keyframe inside referenced shot and scene and corresponds to actual source time
- Face/speaker identity is never auto-VERIFIED by similarity alone

Tham khảo ORCHESTRATION.md: schema invalid -> stage FAIL/NOT_TESTED, không được tự động coi là PASS.
