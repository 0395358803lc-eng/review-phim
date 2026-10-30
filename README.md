# AI Video Review — Agent-Orchestrated Brain-Only

**BỘ TÀI LIỆU SKILL, KHÔNG PHẢI ỨNG DỤNG THỰC THI.**

Bộ kỹ năng bằng Markdown hướng dẫn ChatGPT điều phối công cụ và model trên máy được kết nối trong tương lai để phân tích video/phim, tạo kịch bản có bằng chứng, chọn cảnh, dựng video và kiểm soát chất lượng. Phạm vi bàn giao **hiện tại chỉ là tài liệu trong GitHub**. Không yêu cầu chọn máy, cài thư viện, tải model, xử lý phim hoặc cung cấp đường dẫn video lúc này.

**Trạng thái phát hành:** documentation v1.0 (chờ đánh giá sử dụng thực tế). Nội dung đã được soạn; **chưa kiểm thử agent thực hiện theo tài liệu** và chưa có kết quả render video thực tế.

## Hardware-First: quy tắc bắt buộc trước khi đề xuất cài đặt
Khi xử lý video trên máy thực, ChatGPT phải **kết nối đúng máy → kiểm kê READ_ONLY CPU/RAM/GPU/VRAM/driver/OS/ổ cứng và phần mềm/model đã cài → đánh giá tương thích theo nhu cầu → đề xuất danh sách công cụ còn thiếu → xin duyệt → mới cài và chạy thử**. TOOL-REGISTRY.md chỉ là catalog, không phải gói cài mặc định. Không có inventory thì không được cá nhân hóa danh sách cài đặt. Xem [Hardware-First Selection](docs/HARDWARE-FIRST-SELECTION.md).

## Bắt đầu đọc
1. [SKILL.md](SKILL.md) — entrypoint agent, điều kiện kích hoạt, quy tắc và dẫn đến tài liệu chuyên sâu.
2. [docs/DOCUMENTATION-SCOPE.md](docs/DOCUMENTATION-SCOPE.md) — định nghĩa phạm vi bộ tài liệu và những gì chưa được làm.
3. [docs/USAGE-GUIDE.md](docs/USAGE-GUIDE.md) — nạp skill vào môi trường agent trong tương lai và quy trình sử dụng.
4. [ORCHESTRATION.md](ORCHESTRATION.md) — state machine, quality gates, recovery.
5. [docs/AGENT-INSTRUCTIONS.md](docs/AGENT-INSTRUCTIONS.md) — playbook/prompt dùng lại cho từng pha khi agent được cấp quyền.
6. [docs/ARTIFACT-CONTRACTS.md](docs/ARTIFACT-CONTRACTS.md) — nối dữ liệu giữa các khâu và danh sách output.
7. [docs/DOCUMENTATION-VALIDATION.md](docs/DOCUMENTATION-VALIDATION.md) — kịch bản tự kiểm tra tài liệu, chưa thay thế kiểm thử thực tế.

## Cấu trúc bộ não
- [ARCHITECTURE.md](ARCHITECTURE.md) — các lớp điều phối / remote actions / local tools / dữ liệu bằng chứng.
- [TOOL-REGISTRY.md](TOOL-REGISTRY.md) — danh mục công cụ và nguyên tắc chọn, **không khẳng định đã cài**.
- [ENVIRONMENT-POLICY.md](ENVIRONMENT-POLICY.md) — phạm vi và quyền vận hành, khi được người dùng cho phép trong tương lai.
- [agents/](agents/) — 9 vai trò chuyên môn (ingest, audio, visual, narrative, script, clip retrieval, voice, editing, QC).
- [workflows/](workflows/) — movie-review, recap, ending-explained, generic-video-review, YouTube 16:9, Shorts/TikTok 9:16.
- [schemas/](schemas/) — hợp đồng dữ liệu, các mẫu JSON **giả lập**.
- [policies/](policies/) — evidence validation, bản quyền, GPU, lỗi và remote security.
- [tests/](tests/) — các tình huống cần chạy khi có môi trường thực, **không phải kết quả đã PASS**.
- [docs/IMPLEMENTATION-ROADMAP.md](docs/IMPLEMENTATION-ROADMAP.md) — lộ trình tài liệu và hướng dẫn triển khai tương lai.

## Nguyên tắc cốt lõi
**Evidence-first:** lời kể dựa trên timestamp, scene IDs, transcript và video frames; không bịa hành động. **Local-first:** ưu tiên tool/model cục bộ khi thực thi về sau, không tự upload media. **Brain-only:** Markdown là hướng dẫn, không có tiến trình hay model tự chạy. **Quality-gated:** kết quả chỉ PASS khi có kiểm chứng, quyền sử dụng và phê duyệt phù hợp. **No publish:** xuất bản là quyền riêng.

## Nguồn
Thiết kế dựa trên báo cáo người dùng cung cấp `deep-research-report.md` (391 dòng); không đăng bản báo cáo gốc lên kho public. Đối chiếu theo [docs/RESEARCH-TRACEABILITY.md](docs/RESEARCH-TRACEABILITY.md). Các cách triển khai bổ sung được phân biệt với nội dung báo cáo.
