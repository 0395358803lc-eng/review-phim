---
name: visual-analysis
description: Use when model-generated captions or raw film frames need grounded verification of characters, actions, objects, locations or temporal movement.
---

# N03 — Quan sát hình ảnh và chuyển động

## Khi sử dụng

Cần hiểu ai/cái gì xuất hiện trong **chuỗi khung hình của phim gốc**, sau N01.

## Quy trình

- Từ `shot_id` và frame gốc chọn cửa sổ thời gian vừa đủ để nhận biết hành động; tăng mật độ ở vùng chuyển động nhanh và chi tiết then chốt.
- Dùng Qwen3-VL/VLM có khả năng đọc chuỗi frame nếu được phép, hoặc kiểm thị giác trực tiếp. Ghi sự kiện nhìn thấy (đến, cầm, chạy, ngã, trao vật), vật thể, bối cảnh và điều chưa rõ.
- Lưu nguyên `model_id`, version, prompt, IDs frame, nguồn quan sát, câu cảnh báo; giữ **observed** khác **inferred**. Tên nhân vật nếu chưa có bằng chứng nhận diện phải dùng nhãn mô tả ngoại hình trung tính.
- Khi lời thoại trái với ảnh, tạo `vision/uncertain.jsonl` và yêu cầu đối chiếu, không để AI tự chọn lời nào đúng.
- Quan sát một frame tĩnh không chứng minh hành động có thời lượng; phải kiểm frame trước/sau hoặc clip gốc.

## Đầu ra và gate

`vision/visual_observations.jsonl` kèm `source_film_sha256`, mốc và frame IDs, `vision/uncertain.jsonl`. `original_frames_checked`, `uncertain_visual_claims_labeled` chỉ đánh true sau khi đã xem bằng chứng thật. Dữ liệu N03 phục vụ N04, không tự trở thành lời review.
