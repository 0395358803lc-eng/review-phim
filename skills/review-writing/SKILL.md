---
name: review-writing
description: Use when a source-grounded story memory must become a new Vietnamese movie recap or narration script without mixing factual claims and speculation.
---

# N05 — Viết lời review từ bộ nhớ phim

## Khi sử dụng

Bộ nhớ N04 đã có evidence cho các tình tiết cốt lõi; cần kịch bản review mới, hấp dẫn nhưng đúng nguồn.

## Quy trình

1. Đọc event ledger và những unresolved quan trọng. Xác định phong cách/độ dài user yêu cầu; không dùng lời review và cách chia nội dung của một phim khác làm template dựng.
2. Viết lời kể tự nhiên theo diễn biến, có hook, mở nút, kết nối và kết thúc. Đối chiếu mỗi câu chứa nhân vật, hành động, quan hệ, vật chứng, lời nói, nguyên nhân.
3. Tách từng câu thành `atomic_claims` với ID ổn định; bản review TXT chỉ chứa lời đọc, chứng cứ/ghi chú giữ trong `script/evidence_ledger.jsonl`.
4. Chi tiết chỉ do suy luận phải viết thận trọng hoặc sửa/loại; nếu `CONTRADICTED`, không chuyển N06. Ghi các câu trừu tượng cho N07, nhưng không làm mất ý bình luận.
5. Đưa người dùng duyệt nội dung; chỉ ghi gate `script` khi nhận được đồng ý thực.

## Đầu ra và gate

`script/review_final.txt`, `script/sentence_claims.jsonl`, `script/evidence_ledger.jsonl`, evidence N05. `review_text_verified`, `atomic_claims_reconciled`; user duyệt trước khi thu giọng full. Sửa kịch bản tạo revision có nguồn mới, không ghi đè bản đã duyệt.
