---
name: film-intake
description: Use when a new film source is supplied or source integrity, media streams, permissions, hardware and job isolation must be checked before analysis.
---

# N00 — Tiếp nhận phim gốc

## Khi sử dụng

Phim mới được cung cấp, thay đổi nguồn/phần cứng, hoặc đang khôi phục job có nguy cơ trộn dữ liệu phim. Đây là giai đoạn kiểm kê **không chỉnh sửa nguồn**.

## Đầu vào và thao tác

- Xác nhận thiết bị, đường dẫn phim được phép truy cập, mục đích sử dụng, quyền tạo review và profile mong muốn (ngôn ngữ, thời lượng, tỉ lệ hình, các thành phần tùy chọn).
- Chạy `film-review-orchestrator/scripts/jobctl.py init` từ vị trí cài đặt thực tế, không tự suy đoán đường dẫn. Lấy hash SHA256 trên **phim thật**, kích thước và mốc thời gian nguồn. Nếu project ID đã tồn tại, không ghi đè.
- Dùng `ffprobe` để phân tích codec, stream, duration, FPS/timebase, rotation, audio/subtitles; dùng FFmpeg giải mã mẫu đầu/giữa/cuối để chứng minh nguồn phát được. `ffprobe` thành công chưa đủ khẳng định giải mã toàn bộ.
- Kiểm công nghệ có sẵn qua lệnh/version và VRAM/RAM, nêu tool chưa cài mà không tự cài. Không chuyển phim lên API bên ngoài nếu không được chấp thuận.

## Đầu ra

`ingest/source_manifest.json`, `ingest/hardware_capabilities.json`, `job_state.json`, `evidence/n00.json` có hash và giới hạn; xem mẫu trong skill điều phối.

## Điều kiện đạt

`source_file_verified`, `media_probe_verified`, `decode_verified` đều có bằng chứng thực tế. Nếu sai nguồn/hỏng file/mất quyền: `BLOCKED` và yêu cầu đầu vào hoặc quyền hợp lệ. Chuyển tiếp `scene-indexing` và `speech-analysis` sau N00 được xác thực.
