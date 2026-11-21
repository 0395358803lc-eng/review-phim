---
name: voice-production
description: Use when a user-approved movie review script needs real narration audio, sentence timing, pronunciation checking, or a voice profile approval.
---

# N06 — Giọng đọc và timeline câu

## Khi sử dụng

N05 đã duyệt; cần WAV có thể phát thực và mốc lời nói chính xác để chọn shot.

## Quy trình

- Kiểm người dùng chọn giọng nào; VieNeu/TTS khác tùy runtime. Giọng mẫu mới cần duyệt trước khi tạo full. Không tự clone giọng người khác khi chưa có quyền.
- Tổng hợp đúng nguyên văn `script/review_final.txt`; đo duration thật của audio từng câu bằng engine output/forced alignment có xác minh, tránh ước lượng theo số chữ.
- Ghi `sentence_id`, `text_sha256`, `voice_start_s`, `voice_end_s`, mốc nghỉ; chú ý nối tiếng Việt, tên nhân vật, dấu thanh và âm lượng.
- Kiểm toàn bộ WAV bằng công cụ: số channel, sample rate, duration, khoảng im, clipping/peak; nghe mẫu những đoạn có nguy cơ sai. TTS đã sinh file không có nghĩa đọc đúng.
- Nếu chỉnh lời/bản giọng, tạo version mới và làm lại các bước phụ thuộc.

## Đầu ra và gate

`voice/narration.wav`, `voice/sentence_audio_timeline.jsonl`, `voice/audio_qc.json`. `audio_render_verified`, `sentence_timing_verified` chỉ PASS khi file thật giải mã được và câu khớp. N07 sử dụng thời lượng WAV, không tự nén hoặc kéo giãn cảnh để ép công thức.
