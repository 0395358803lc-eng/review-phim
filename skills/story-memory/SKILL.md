---
name: story-memory
description: Use when visual observations and timecoded dialogue must be reconciled into character, event, timeline and causal evidence for one film.
---

# N04 — Bộ nhớ phim dựa trên chứng cứ

## Khi sử dụng

Sau N02+N03, cần nối các sự kiện và nhân vật của **đúng một phim**, không kể lại theo suy đoán từ caption.

## Quy trình

1. Nối `shot_id`, frame IDs, ASR segment IDs theo timecode và phim hash; ghi provenance cấp mệnh đề.
2. Lập thực thể nhân vật và alias, chỉ kết luận danh tính khi có lời thoại hoặc xác minh hình đáng tin. Quan hệ gia đình, nghề nghiệp, tổ chức cần nguồn cụ thể.
3. Sắp xếp story timeline theo diễn biến phim và phân biệt hồi tưởng/cảnh mở đầu/flashforward với thời gian thực trong truyện.
4. Tạo claim ledger cho các sự kiện lớn: ai, làm gì, với ai, vật gì, ở đâu, căn cứ nào, chưa biết gì. Các suy luận nguyên nhân phải có chuỗi bằng chứng thay vì một caption.
5. Mâu thuẫn ảnh–thoại, tên không rõ hoặc hậu quả chưa xuất hiện → ghi `UNKNOWN`, `UNRESOLVED` hoặc `CONTRADICTED`, kèm ID nguồn.

## Đầu ra và gate

`story/story_timeline.json`, `story/characters.json`, `story/event_claims.jsonl`, `story/unresolved.jsonl`. Gate `key_story_claims_traceable` và `conflicts_logged`. Bộ nhớ là file trong workspace, không phải bộ nhớ vĩnh viễn ChatGPT.
