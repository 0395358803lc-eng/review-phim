---
name: video-editing
description: Use when an approved narration-to-source shot map must be assembled into pilot clips, timestamped chapters, revisions or a final movie review timeline.
---

# N08 — Dựng pilot và video chính

## Khi sử dụng

N07 đã có bảng ghép cảnh nguồn với timecode và hạn chế rõ ràng; cần dựng hình thật.

## Quy trình

- Tạo timeline từ `sentence_shot_map.json` và `narration.wav`. Chỉ dùng clip gốc chỉ rõ source hash và phạm vi timecode; FFmpeg/NVENC khi tương thích hoặc codec phù hợp đã được phép.
- Chọn một pilot đại diện khoảng 60–120 giây (hoặc độ dài user chỉ định) bao gồm lời bình cụ thể, hình ảnh tốt và một vài câu khó. Không tái dùng video review cũ làm footage.
- Render pilot thật, giải mã clip và nghe kiểm giọng/cảnh. Đưa user xem; **không** tự gán `pilot` approval.
- Sau duyệt, dựng từng chương, tái sử dụng EDL mới đã được kiểm và lồng audio nhất quán. Không tự thêm zoom/crop/FPS mặc định, intro, logo, nhạc hay thumbnail nếu user không yêu cầu.
- Với cảnh sai, tạo `edit/revisions/vNN/` mới, giữ version trước và thông tin shot nguồn; chỉ tái dựng phần phụ thuộc bị ảnh hưởng.

## Đầu ra và gate

`edit/pilot.mp4`, `edit/timeline.json`, `edit/chapters/*.mp4`, `edit/render_manifest.json`; `pilot_reviewed`, `chapter_media_decoded`, `narration_alignment_checked`. Nếu FFmpeg chỉ trả mã 0 nhưng clip mất tiếng, không được PASS. Sau N08 gửi sang N09 kiểm độc lập.
