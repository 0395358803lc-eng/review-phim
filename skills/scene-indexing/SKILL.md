---
name: scene-indexing
description: Use when an original feature-length film needs a trustworthy timeline of shots, source frames, scene boundaries, and reusable visual-search candidates.
---

# N01 — Lập chỉ mục toàn bộ cảnh phim

## Khi sử dụng

Cần trích cảnh nguồn, tạo chỉ mục thời gian và tìm kiếm hình ảnh trong toàn bộ phim sau N00.

## Quy trình

1. Đọc source hash, duration và timebase từ job. Lựa chọn PySceneDetect hoặc giải pháp phân đoạn có thể kiểm chứng; đối chiếu lại điểm cắt bằng frame **lấy trực tiếp từ phim**.
2. Ghi mọi shot theo `shot_id`, `source_start_s`, `source_end_s`, `source_film_sha256`, source stream/timebase. Coverage phải bao phủ toàn phim, phân biệt quảng cáo/credit nhưng không tự bỏ phần chưa đọc.
3. Trích frame đại diện và frame tại đoạn có chuyển động cao, cận cảnh hành động/đồ vật. Ghi `frame_id`, `shot_id`, `source_time_s`, `image_sha256` và đường dẫn ảnh trong job.
4. Nếu được cấu hình, tạo embeddings CLIP/OpenCLIP để truy hồi **ứng viên**; tuyệt đối không dùng similarity score để khẳng định nhân vật, quan hệ hay hành động.
5. Kiểm các đoạn tối, lẫn scene, cắt sai, cảnh quá dài và drift thời gian. Duyệt lại điểm cắt có ảnh hưởng cốt truyện.

## Đầu ra và gate

`scenes/scenes.jsonl`, `scenes/frames.jsonl`, `scenes/shot_index.jsonl`, tùy chọn `scenes/visual_index/`; bảng checksum. `all_source_time_covered=true` và `source_scene_timestamp_verified=true` chỉ khi có kết quả kiểm thật. Mất frame hoặc nguồn lỗi thì giữ N01 chưa hoàn tất, không bỏ gap để hợp thức hóa.
