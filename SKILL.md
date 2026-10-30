---
name: ai-video-review-agent
description: Agent-Orchestrated Brain-Only workflow for evidence-grounded movie review, recaps, explainers and arbitrary-video commentary using authorized remote computer tools.
---

# AI Video Review — SKILL ENTRYPOINT

## Triggers
Khi người dùng yêu cầu review/tóm tắt/phân tích phim hoặc video, tạo video bình luận, xây dựng/cập nhật workflow sản xuất AI Video Review hoặc kiểm tra job đã thực hiện. Khi được gọi, đọc tài liệu liên quan thay vì cố giữ toàn bộ skill trong ngữ cảnh.

## Chọn năng lực
1. Khởi đầu ở [ORCHESTRATION.md](ORCHESTRATION.md); đặt trạng thái mới là NOT_STARTED.
2. Chọn [workflow](workflows/) theo đầu ra; không đồng nhất recap với review.
3. Kiểm tra máy qua remote tools thực có; nếu không có connector, trả báo cáo BLOCKED và hướng dẫn cần thiết, không giả lập output.
4. Trước thực thi đọc [ENVIRONMENT-POLICY.md](ENVIRONMENT-POLICY.md), [TOOL-REGISTRY.md](TOOL-REGISTRY.md) và [policies/gpu-selection.md](policies/gpu-selection.md).
5. Mỗi bước dùng một tệp hợp lệ: media, scene, evidence, narrative, script, edit, QC. Xem [schemas/](schemas/).
6. Các chuyên môn trong [agents/](agents/) là vai trò logic; không mặc định có agent nền, mạng riêng, tiến trình độc lập hoặc model ẩn.
7. Không tự nhận có khả năng nghe hoặc xem video nguồn khi connector chỉ trả đường dẫn. Cần frame/audio/transcript và quyền truy cập thực tế.

## Cổng quyết định
- G0: Chọn máy/thư mục, READ-ONLY inventory.
- G1: Thiết kế + danh sách tool/model và giấy phép được duyệt.
- G2: Ingest và phân đoạn xác minh metadata/timecodes.
- G3: ASR + visual evidence + narrative graph; claim quan trọng có chứng cứ.
- G4: Script lock và quyền sử dụng nguồn được xem xét.
- G5: Voice/timeline/render QC kỹ thuật.
- G6: Factual + editorial + rights QC, yêu cầu người duyệt nơi cần thiết.
- G7: Bàn giao file + báo cáo; KHÔNG tự publish.

## Phân loại trạng thái
NOT_STARTED, READ_ONLY, PROPOSED, APPROVED, RUNNING, PASS, PARTIAL, FAIL, BLOCKED, NOT_TESTED. Chỉ PASS nếu có artifact, test và log được đối chiếu. Khi thiếu evidence: dừng phần khẳng định ấy, yêu cầu thu thập thêm; không vượt gate.

## Hành động cấm nếu chưa duyệt
Cài model, xóa/chuyển dữ liệu, thay driver, ghi ngoài root đã chấp thuận, gọi API trả phí, upload phim lên cloud, xuất bản, tắt kiểm tra bản quyền, merge main. Quyền tải weights/công cụ, quyền đọc video và quyền publish là ba quyền riêng.

## Output tối thiểu mỗi lần
job_id, device_id, input file/hash, stage/status, artifacts/paths, tool+version, expected vs actual checks, unresolved risks, next gate. Xem [tests/quality-gates.md](tests/quality-gates.md).
