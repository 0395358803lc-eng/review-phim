---
name: quality-delivery
description: Use when movie review pilots or final MP4s need independent decoding checks, semantic provenance auditing, version verification, and controlled delivery.
---

# N09 — Kiểm tra độc lập và bàn giao

## Khi sử dụng

Có thành phẩm đã render, cần xác minh **file thực** và đối chiếu nội dung theo lời bình trước khi bàn giao.

## Quy trình

1. Tính SHA-256 cho MP4, narration và mapping, `ffprobe` đầy đủ streams/duration/FPS/resolution; FFmpeg decode toàn bộ video và audio để phát hiện lỗi codec.
2. Kiểm mốc câu ↔ khung ↔ clip nguồn, không trùng project khác, không mất câu, tiếng không bị cắt, duration drift; lấy contact sheets **trực tiếp từ MP4** và xem lại các câu khó.
3. Phân biệt kỹ thuật (`technical_qc.json`) và nội dung (`semantic_qc.json`). Các nhãn `CONTEXT_ONLY`/`UNRESOLVED` và quan hệ chỉ ASR hỗ trợ phải hiển thị trong báo cáo, không ghi 100% khớp.
4. Kiểm artifact đầu ra và hash sau khi tạo, giữ original và các video đã duyệt không đổi; nếu lỗi tạo phiên bản sửa riêng.
5. Bàn giao link/đường dẫn **thực sự kiểm tra tồn tại** trên môi trường phù hợp, bảng timecode, bản quyết định cảnh và những hạn chế còn lại. Người dùng đưa ra quyết định cuối cùng.

## Đầu ra và gate

`delivery/final_review.mp4`, `delivery/delivery_manifest.json`, `qc/technical_qc.json`, `qc/semantic_qc.json`, tùy chọn `delivery/source_timeline.csv` và subtitles. `full_video_decoded`, `full_audio_decoded`, `provenance_rechecked`, `limitations_disclosed` chỉ PASS khi kết quả kiểm độc lập thật. Lỗi media hoặc contradiction chưa giải quyết → chưa nghiệm thu.
