# Film Review Agent 2.1 — Runtime + 11 Agent Skills

**Mã nguồn chạy được, không kèm dữ liệu phim/test.** Repository này chứa 11 Agent Skills hướng dẫn, Execution Engine 2.1, bộ xử lý FFmpeg, các thư viện chứng cứ/CLIP/Qwen/Anh–Việt, và công cụ kiểm tra cảnh cho AI Agent. Không tự động tải model hay đem theo dữ liệu của phim cũ.

## Tích hợp vào AI Agent (Windows / Linux / macOS)

```bash
python scripts/install_agent_runtime.py doctor
python scripts/install_agent_runtime.py install --project "/path/to/YOUR_NEW_AGENT_PROJECT"
```

Trên Windows, dùng đường dẫn Windows trong `--project`. Lệnh tạo:
- `.agents/skills/` — 11 skill được AI Agent khám phá.
- `.agents/film-review-runtime/` — Engine và module Python có thể thực thi.

Cài đặt **không sửa đè** skills hay dữ liệu đã có. Để tích hợp đầy đủ, đọc [AGENT_RUNTIME.md](AGENT_RUNTIME.md).

## Đã thực thi / đã kiểm chứng

- 11 skills và jobctl Python; Engine21 kiểm tra hash, tiến độ, phục hồi, evidence và cổng phê duyệt.
- N00/N01: FFprobe, FFmpeg, lập chỉ mục video — chạy trực tiếp trên source mới khi có FFmpeg.
- N02/N03/N06/N07: Whisper, Qwen3-VL, VieNeu, CLIP đã được thử với model có sẵn trên máy Windows; tuy nhiên **worker AI production tổng quát chưa được đóng gói**. AI Agent phải chỉ định adapter và model cục bộ.
- N04/N05: lưu sự kiện và viết bản nháp có mã chứng cứ; chưa bảo đảm diễn biến phim đúng nếu chưa duyệt.
- Phase5: xác minh SHA câu Anh/bản dịch Việt, CLIP→Qwen, storyboard nhiều câu.
- Phase6: đối chiếu audio và điểm cắt cảnh, hồ sơ nghe/xem lại **chưa ký**.

**Không tuyên bố:** AI có thể tự chạy trọn vẹn N00–N09 trên bất cứ phim thật nào chỉ bằng một lệnh. Dựng phim có giọng thật vẫn cần adapter sản xuất và phê duyệt script/voice/pilot từ con người.

## Gói mã sạch (không mang test data)

```bash
python scripts/package_release.py --output "/path/to/film-review-runtime-2.1-source-only.zip"
```

Lệnh đóng gói theo danh sách cho phép, chỉ chứa source runtime và installer; **không có** `tests/`, QA outputs, phim, video, giọng, transcript, cache, checkpoint AI, khóa bí mật hay trọng số mô hình. Các tệp test cũ đang có sẵn trong lịch sử repository không được đưa vào gói tích hợp và không được dùng làm nguồn cho phim mới.

## Từ phim mới đến Engine

1. AI Agent đọc skill `film-review-orchestrator` và `references/runtime-integration.md`.
2. Tạo job mới: `python skills/film-review-orchestrator/scripts/jobctl.py init --source NEW_MOVIE.mp4 --workspace-root NEW_WORKSPACES --title "Movie"`.
3. Chủ máy cấu hình `engine21` với adapter cục bộ và phép duyệt thật **ở ngoài job phim**. Không tự tạo chữ ký hoặc dùng demo QA.
4. Chạy từng stage và đối chiếu hash/timecode, dừng khi thiếu model hay lời duyệt.

Thư mục nguồn và job của mọi phim cũ không được truy nhập hoặc ghi đè trong quy trình cài đặt này.

[Hướng dẫn cài](INSTALL.md) · [Runtime chi tiết](AGENT_RUNTIME.md) · [Quy trình](WORKFLOW.md) · [An toàn](SECURITY.md).
