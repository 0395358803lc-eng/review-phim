# Cài Film Review Agent 2.1 — Source-only

Python 3.10+ là yêu cầu tối thiểu. Cài đặt **mã nguồn** không tải FFmpeg,
model AI, driver, media hay bất kỳ dữ liệu phim cũ nào.

1. Clone repository, mở terminal trong thư mục repo.
2. Kiểm tra: `python scripts/install_agent_runtime.py doctor`.
3. Tạo riêng một project Agent (chủ máy chọn thư mục), rồi chạy
   `python scripts/install_agent_runtime.py install --project "C:\YourAgentProject"`.
4. Tại `C:\YourAgentProject\.agents\film-review-runtime`, chạy
   `python -m engine21 --help` và `python -m stage4.cli --help` để kiểm tra.
5. Agent đọc skill `film-review-orchestrator` và [AGENT_RUNTIME.md](AGENT_RUNTIME.md).
6. Tạo job cho một phim **mới và đã được chủ máy cấp quyền**. Không dùng lại
   movie source, ASR, video, voice, QA results hoặc approval của job khác.

Lệnh `install` **từ chối ghi đè** thư mục runtime/skill đã có.
Source ZIP tối giản: `python scripts/package_release.py --output PATH_TO_NEW_ZIP`.

`doctor` chỉ xác nhận thư viện nguồn và có/không có FFmpeg hiện hành;
nó không tự xác nhận model Whisper/Qwen/CLIP/VieNeu đã cài hoặc sẵn sàng
dựng full review. Cấu hình adapter và duyệt kịch bản/giọng/pilot là việc
riêng theo quyền của host. Xem thêm [AGENT_RUNTIME.md](AGENT_RUNTIME.md).
