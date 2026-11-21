---
name: semantic-matching
description: Use when Vietnamese narration sentences need source-film shots that actually match character actions, dialogue, objects and story context, including ambiguous or unobservable claims.
---

# N07 — Truy hồi và kiểm duyệt cảnh theo từng ý

## Khi sử dụng

Đã có N04 và N06; cần quyết định chọn cảnh trong **phim gốc** cho mỗi câu/ý lời bình.

## Quy trình

1. Đối với mỗi `sentence_id`, chia câu thành mệnh đề kiểm chứng được: nhân vật, hành động, đồ vật, địa điểm, thời điểm, quan hệ và suy luận. Giữ thời lượng WAV thật.
2. Truy hồi `top-K` ứng viên từ CLIP/OpenCLIP nếu có, full-text ASR và event graph. Không lấy kết quả score làm verdict; các ứng viên không có bằng chứng được gắn `UNRESOLVED`.
3. Rerank bằng Qwen3-VL/chuỗi frame thật, xem clip gốc ở mỗi đoạn tiềm năng, đối chiếu người–hành động–thời điểm. Không được dùng cảnh quay đối phương để minh họa hành động của nhân vật chính chỉ vì cùng có súng.
4. Chọn 1–n shot một câu nếu cần, phân bổ theo nhịp câu; bảo toàn continuity, hạn chế reuse vô lý. Với suy nghĩ, động cơ, quan hệ không thể thấy trực tiếp, dùng nhãn `CONTEXT_ONLY` và mô tả giới hạn.
5. Bắt buộc ghi `source_movie_sha256`, `source_start_s/end_s`, `voice_start_s/end_s`, frame/ASR evidence IDs, `verdict`, `qualifier`; không có scene tốt hơn thì ghi unresolved queue và chuyển người dùng duyệt phương án thay thế, không giả clip.
6. Chạy công cụ kiểm cấu trúc: `python <orchestrator-skill>/scripts/evidence_qc.py --map <job>/match/sentence_shot_map.json`; sau đó **kiểm mắt** các ứng viên thật. Validator chỉ kiểm cấu trúc và mốc, không đảm bảo nghĩa đúng.

## Đầu ra và gate

`match/candidate_scenes.jsonl`, `match/sentence_shot_map.json`, `match/evidence_and_limits.jsonl`, `match/unresolved_shot_queue.jsonl`. `all_sentences_have_decision`, `source_clips_traceable`, `unresolved_disclosed`; `CONTRADICTED` chặn render như cảnh chứng thực. Người duyệt phân biệt footage trực tiếp và hình minh họa.
