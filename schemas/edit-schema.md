# edit.json — Evidence-Grounded EDL

## Envelope bắt buộc cho mọi artifact
schema_version: string (mặc định "1.0"); job_id: string; source_sha256: string (64 ký tự hex của tệp nguồn); generator: object {name:string,version:string, config_hash:string}; produced_at: ISO-8601 UTC string. Hash của artifact được lưu trong stage manifest; dữ liệu không chứa credentials.

## Fields
- timeline: items {timeline_id, start_s,end_s,sentence_id,source_sha256,source_start_s,source_end_s,scene_id,evidence_ids,verified_visual_match,rights_status,crop?,audio_refs[]}
- audio_tracks: narration/music/sfx refs and ducking settings; captions ref; output_spec width,height,fps
- clip_selection: candidate scores + verification reason; never treat score as final proof
- render_status and output_hash are filled only by actual run

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
  "timeline": [
    {
      "timeline_id": "EDL_001",
      "start_s": 0,
      "end_s": 5,
      "sentence_id": "S001",
      "source_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
      "source_start_s": 3130,
      "source_end_s": 3135,
      "scene_id": "SC_042",
      "evidence_ids": [
        "EV_042"
      ],
      "verified_visual_match": false,
      "rights_status": "REQUIRES_REVIEW",
      "audio_refs": [
        "VO_001"
      ],
      "crop": null
    }
  ],
  "audio_tracks": [
    {
      "kind": "narration",
      "ref": "VO_001"
    }
  ],
  "captions_ref": "output/DEMO-001/subtitles.srt",
  "output_spec": {
    "width": 1080,
    "height": 1920,
    "fps": 30
  },
  "render_status": "NOT_TESTED"
}
~~~

## Validation checks
- End > start for timeline/source; media bounds respected; no unexpected overlaps/gaps
- verified_visual_match true only after source segment verified; rights_status must be cleared before release
- Output frame rate and aspect match approved profile; scene/claim references resolve

Tham khảo ORCHESTRATION.md: schema invalid -> stage FAIL/NOT_TESTED, không được tự động coi là PASS.
