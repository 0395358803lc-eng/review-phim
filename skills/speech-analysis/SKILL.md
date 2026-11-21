---
name: speech-analysis
description: Use when a film needs original-language transcript, Vietnamese translation, subtitle alignment or uncertainty tracking from the film audio.
---

# N02 — Âm thanh, ASR và bản dịch có timecode

## Khi sử dụng

Phim có lời thoại hoặc âm thanh cần giải mã để hiểu câu chuyện; N00 nguồn đã xác nhận.

## Quy trình

1. Trích audio từ phim gốc bằng FFmpeg, xác thực duration và sample rate. Không tái dùng lời thoại của phim khác.
2. Sử dụng Whisper/ASR thích hợp tiếng nói thực tế. Tách `segment_id`, thời gian `[start_s,end_s]`, lời nguyên ngữ, độ tin cậy; đánh dấu đoạn lẫn nhạc, tiếng nền, âm lượng thấp.
3. Nếu cần, dùng forced alignment hoặc kiểm nghe trực tiếp các điểm trọng yếu. ASR kéo dài bất thường, tên riêng và lời nghe không rõ phải có nhãn; **không thay bằng một câu phỏng đoán tự tin**.
4. Dịch tiếng Việt riêng theo từng segment, không đánh tráo lời nguyên ngữ; bảo toàn ID và thời gian; phân biệt bản dịch diễn giải và từ ngữ trực tiếp.
5. Không gán speaker ID/danh tính chỉ vì câu thoại gần một khuôn mặt trên hình; muốn xác nhận speaker phải có evidence riêng.

## Đầu ra và gate

`speech/transcript_original.jsonl`, `speech/transcript_vi.jsonl`, `speech/uncertainties.jsonl` và báo cáo QC. `asr_timestamp_in_range`, `unclear_speech_disclosed` có chứng cứ; hỗ trợ `story-memory` và `semantic-matching`. Nếu phim không có thoại, tạo báo cáo sự thật `NO_SPEECH_CONFIRMED` sau khi kiểm tra, không sáng tạo transcript.
