---
name: film-review-orchestrator
description: Use when an AI agent receives a new movie to review, resumes a paused film project, coordinates N00-N09 tasks, or manages approvals and source-safe delivery.
---

# Film Review Agent 2.0 — điều phối dự án phim

## Mục tiêu

Điều phối một job **từ phim nguyên bản đến video review có bằng chứng**, không sử dụng timeline/công thức từ dự án trước. Đây là skill hướng dẫn, **không tự cấp quyền file, GPU, internet hoặc máy từ xa**.

## Runtime 2.1 — cần đọc trước khi tích hợp

Đọc [hướng dẫn runtime nguồn sạch](references/runtime-integration.md) và `AGENT_RUNTIME.md` ở thư mục gốc repository. Phân biệt rõ 11 skill hướng dẫn với adapter AI thực thi: dùng `scripts/install_agent_runtime.py` để kiểm tra/cài mã nguồn, không sao chép media hay dữ liệu test cũ. Runtime có thể vận hành từng stage với provider được chủ máy cấu hình; không tự coi chạy QA tổng hợp là đã sẵn sàng dựng phim thật.

## Bắt đầu một phim mới

1. Xác định phim nguồn được người dùng cấp phép, thiết bị/thư mục làm việc và mục đích sử dụng. Không tự cài ứng dụng hay tải nguồn vào cloud.
2. Tạo project mới bằng `python scripts/jobctl.py init --source "<path>" --workspace-root "<authorized_dir>" --title "<film>"` khi đang ở thư mục skill này; lệnh chỉ kiểm kê, hash và thử ffprobe. Đọc `job_state.json` và `ingest/source_manifest.json`.
3. Đọc [quy tắc chứng cứ](references/global-rules.md), [hợp đồng bàn giao](references/handoff-contracts.md), [adapter công cụ](references/tool-adapters.md), [điều kiện QC](references/quality-gates.md). Chỉ gọi skill chuyên môn khi điều kiện trước đã thật sự được xác minh.
4. Thứ tự phụ thuộc: N00 → {N01, N02}; N01 → N03; {N02, N03} → N04 → N05 → N06; {N04, N06} → N07 → N08 → N09. N01/N02 có thể chạy song song nếu không tranh chấp tài nguyên.
5. Trước khi đổi stage `DONE`, tạo file evidence JSON trong job chứa `checks`, danh sách **artifact tồn tại và SHA256**, giới hạn và mốc thời gian; chạy `python scripts/jobctl.py complete-stage --job "<job_dir>" --stage N00 --evidence "evidence/n00.json"` (thay N00 bằng stage cần xác nhận).
6. Nếu muốn tiếp tục job, chạy `python scripts/jobctl.py status --job "<job_dir>"` và `verify-source`; bỏ qua bước `DONE` **chỉ khi đầu ra và hash còn khớp**, khác thì dừng hoặc tạo revision mới. Không dựa vào việc Agent “nhớ đã làm”.

## Quyền phê duyệt

- N05: người dùng duyệt lời review (`script`) trước giọng đọc đầy đủ.
- N06: người dùng duyệt giọng mới khi chưa có profile được duyệt.
- N08: người dùng duyệt **pilot** trước khi dựng đầy đủ.
- N09: người dùng quyết định chấp nhận video cuối hoặc yêu cầu bản revision.

Khi thực sự nhận được phản hồi, ghi mã tham chiếu hội thoại/thư duyệt thật bằng `python scripts/jobctl.py approve --job "<job_dir>" --gate script --reference "<actual_user_approval_ref>"`. Công cụ ghi trạng thái không kiểm tra được danh tính người duyệt: Agent tuyệt đối không được tự bịa mã approval hoặc gắn trạng thái duyệt khi người dùng chưa duyệt.

## Khôi phục và giới hạn

Nếu nguồn sai hash, tệp không có hoặc quyền truy cập thiếu → `BLOCKED`, nêu rõ nguyên nhân, không giả lập kết quả. Nếu sửa review, giọng đọc hoặc shot thì tạo phiên bản `revision_XX` riêng, tính lại các stage bị ảnh hưởng; giữ nguyên bản đã duyệt. **Không tự tuyên bố khớp 100%.**

## Danh mục skill con

`film-intake` (N00), `scene-indexing` (N01), `speech-analysis` (N02), `visual-analysis` (N03), `story-memory` (N04), `review-writing` (N05), `voice-production` (N06), `semantic-matching` (N07), `video-editing` (N08), `quality-delivery` (N09).
