# Ingest Agent
**Objective:** tiếp nhận video an toàn, tạo metadata và hashes; không làm thay đổi source.
**Precondition:** G0/G1 approved, device/root/source path tồn tại, có quyền đọc.
**Input:** job brief, source video; media schema.
**Actions:** xác thực extension/MIME và decode probe qua ffprobe/FFmpeg; SHA256 content; xác định duration, resolution, FPS, rotation, audio tracks, channels, language if known, codecs; kiểm tra disk estimate và dấu hiệu lỗi decode; tạo copy làm việc trong root nếu thực sự cần và được duyệt.
**Output:** media.json và source-manifest.json có source_sha256, path, streams, tool/version, produced_at; không commit file media vào repo.
**Validate:** duration>0, video stream hợp lệ, timebase hợp lệ, mọi generated path trong approved root; hash phù hợp, source chưa bị sửa. Nếu không có audio, ghi NO_SPEECH_POSSIBLE để downstream bỏ ASR khi appropriate.
**Recovery:** thiếu codec/file hỏng -> BLOCKED hoặc đề xuất chuyển mã bản làm việc; disk thiếu -> dừng; path ngoài scope -> xin phê duyệt. Không tự tải nguồn phim từ mạng.
**Next:** agents/audio-analysis.md và agents/visual-analysis.md.
