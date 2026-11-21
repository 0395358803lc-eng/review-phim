# Kết quả kiểm tra bản phát hành 2.0.0

**Đã kiểm tra khi tạo gói (21/11/2026)**

- Có đúng 11 thư mục Agent Skills, mỗi skill có `SKILL.md`, `name`, `description` và trigger đúng quy ước.
- Các path Markdown nội bộ, JSON schemas và template synthetic xác thực hợp lệ; không chứa video, audio, model weights, source dữ liệu phim người dùng.
- Công cụ stdlib `jobctl.py` và `evidence_qc.py` có thể chạy trên Python 3.13 trong môi trường thử.
- Unit tests: 9/9 PASS (discovery, cấu trúc, ngăn lỗi ngoài workspace, hash nguồn, phụ thuộc stage, không tự bỏ approval gate, source timeline, evidence linkage).
- `evidence_qc.py` trên ví dụ synthetic: PASS; nó không thay thế đánh giá cảm nhận và nội dung thật.
- ZIP được giải nén/kiểm SHA-256 từng file và thử chạy test lại từ thư mục giải nén trong bước đóng gói.

**Chưa kiểm tra:** Agent hành vi thực trên ChatGPT/Codex/Claude/Gemini; thực hiện ASR, Qwen3-VL, CLIP hoặc VieNeu trên máy đích; dựng/quy chiếu video phim thật; quyền phát hành nguồn phim. Những phần này cần kiểm thử tích hợp riêng, kết nối công cụ và quyền thực tế.

**Không cập nhật plugin REVIEW PHIM cũ, không xóa dữ liệu Windows, không cài model/driver/tool.**
