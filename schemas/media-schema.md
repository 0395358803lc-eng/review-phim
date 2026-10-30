# media.json — Media Ingest Contract

## Envelope bắt buộc cho mọi artifact
schema_version: string (mặc định "1.0"); job_id: string; source_sha256: string (64 ký tự hex của tệp nguồn); generator: object {name:string,version:string, config_hash:string}; produced_at: ISO-8601 UTC string. Hash của artifact được lưu trong stage manifest; dữ liệu không chứa credentials.

## Fields
- media_path: string path inside approved root; source_path optionally outside but read-only
- duration_s: number > 0; width,height,fps: positive numeric; rotate_degrees: number
- video_streams/audio_streams: arrays of track objects with stream_index,codec,language?,sample_rate?,channels?
- decode_verified: boolean; rights_inventory_id: string|null; content_type: video/*; detected_by: executable and version

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
  "media_path": "work/DEMO-001/input/source.mp4",
  "duration_s": 5400,
  "width": 1920,
  "height": 1080,
  "fps": 24,
  "rotate_degrees": 0,
  "video_streams": [
    {
      "stream_index": 0,
      "codec": "h264"
    }
  ],
  "audio_streams": [
    {
      "stream_index": 1,
      "codec": "aac",
      "sample_rate": 48000,
      "channels": 2
    }
  ],
  "decode_verified": true,
  "rights_inventory_id": "RIGHTS-001"
}
~~~

## Validation checks
- Hash đúng định dạng, tính lại được từ source bytes thật; fixture hash toàn 0 không là bằng chứng
- duration_s>0,width>0,height>0,fps>0; streams nhất quán với ffprobe
- Không đánh dấu decode_verified=true nếu chỉ đọc header/metadata

Tham khảo ORCHESTRATION.md: schema invalid -> stage FAIL/NOT_TESTED, không được tự động coi là PASS.
