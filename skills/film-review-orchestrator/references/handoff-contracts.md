# Hợp đồng bàn giao N00–N09

Tất cả đầu ra là **per-film**, đường dẫn tương đối bên trong workspace. Phim gốc nằm ngoài, chỉ mang metadata và hash.

| Stage | Input bắt buộc | Output tối thiểu | Gate hoàn tất |
|---|---|---|---|
| N00 | Nguồn được phép, mục tiêu đầu ra | `ingest/source_manifest.json`, `job_state.json` | ffprobe, kiểm giải mã nguồn và SHA |
| N01 | N00 PASS | `scenes/scenes.jsonl`, `scenes/frames.jsonl` | phủ nguồn, thời gian không âm, ảnh trích đúng mốc |
| N02 | N00 PASS | `speech/transcript_original.jsonl`, `speech/transcript_vi.jsonl`, `speech/uncertainties.jsonl` | mỗi ASR nằm trong nguồn, chỗ nghe mơ hồ có nhãn |
| N03 | N01 PASS | `vision/visual_observations.jsonl`, `vision/uncertain.jsonl` | các hành động chính phải kiểm lại bằng hình thực |
| N04 | N02+N03 PASS | `story/story_timeline.json`, `story/event_claims.jsonl`, `story/unresolved.jsonl` | những claim chính có evidence hoặc UNKNOWN |
| N05 | N04 PASS | `script/review_final.txt`, `script/sentence_claims.jsonl`, `script/evidence_ledger.jsonl` | review đầy đủ, user duyệt nội dung (`script`) |
| N06 | N05 PASS | `voice/narration.wav`, `voice/sentence_audio_timeline.jsonl`, `voice/audio_qc.json` | voice đã duyệt nếu mẫu mới, WAV thật, câu khớp |
| N07 | N04+N06 PASS | `match/candidate_scenes.jsonl`, `match/sentence_shot_map.json`, `match/evidence_and_limits.jsonl` | không mâu thuẫn và có phương án cho từng câu |
| N08 | N07 PASS | `edit/pilot.mp4`, `edit/timeline.json`, `edit/chapters/*.mp4` | user duyệt pilot, decode tất cả clip được tạo |
| N09 | N08 PASS | `delivery/final_review.mp4`, `qc/technical_qc.json`, `qc/semantic_qc.json`, `delivery/delivery_manifest.json` | full media decode, mapping audit, user xem bản cuối |

N01 và N02 được chạy song song khi dữ liệu và tài nguyên độc lập; N03 sau N01; N04 sau N02+N03. Ở N08, không được coi `pilot.mp4` duyệt là mặc nhiên chấp nhận video cuối.

## Định dạng stage-evidence

Theo `../schemas/stage-evidence.schema.json`; chứa `stage`, `outcome`, `source_sha256`, `reviewed_at_utc`, `checks`, `artifacts` (path+SHA256), `limitations`. Kiểm bằng `python scripts/jobctl.py complete-stage --job ... --stage Nxx --evidence ...`. Script kiểm các cờ và file/hash, nhưng **không thể thay con người xác nhận rằng AI hiểu đúng nội dung**.

## Trách nhiệm các công đoạn

- Một nhiệm vụ mà môi trường thiếu model/driver/binary sẽ `BLOCKED`, không tạo dữ liệu mô phỏng giả thành thật.
- Source artifact phải ở vị trí đã xác thực; sai nguồn, hết quyền hoặc hash thay đổi thì dừng.
- Khi user thay lời bình/giọng/shot, tạo revision và chạy lại các bước phụ thuộc; không chỉnh sửa stage `DONE` tại chỗ.
