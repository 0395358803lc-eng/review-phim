# Film Review Agent Skills 2.0.0

**11 Agent Skills độc lập (1 điều phối + 10 chuyên môn), không phải plugin ChatGPT.** Bộ này biến bộ phim nguyên bản thành một dự án review có thể truy vết bằng chứng, ghép cảnh theo từng ý và kiểm duyệt sản phẩm thật. Tất cả được viết mới; không đóng gói data phim, timeline hay state machine của plugin cũ.

## Có gì trong gói?

- `skills/film-review-orchestrator/SKILL.md` — chọn giai đoạn N00–N09, xác định phụ thuộc, ghi tiến độ, phục hồi công việc, khóa nguồn.
- `skills/film-intake` — kiểm nguồn; `scene-indexing` — chia cảnh; `speech-analysis` — ASR và dịch; `visual-analysis` — xem chuyển động.
- `skills/story-memory` — mạch chuyện có chứng cứ; `review-writing` — lời bình; `voice-production` — TTS/timestamp; `semantic-matching` — tìm/kiểm shot.
- `skills/video-editing` — dựng; `quality-delivery` — QC độc lập và bàn giao.
- Bên trong skill điều phối có `references/`, `schemas/`, `templates/` và `scripts/jobctl.py`, `scripts/evidence_qc.py` dùng **Python standard library**, không cần cài package AI để quản lý job.
- `tests/` và `scripts/validate_release.py` chỉ dùng khi kiểm gói nguồn; có thể không cài cùng skills vào môi trường agent.

## Cài nhanh — sao chép thư mục skills

Xem [INSTALL.md](INSTALL.md) cho Windows và Linux/macOS. Ví dụ cài phạm vi một project trên Linux/macOS:

```bash
mkdir -p .agents/skills
cp -R skills/* .agents/skills/
```

Ví dụ trên Windows PowerShell, thực hiện **từ thư mục đã giải nén ZIP**:

```powershell
New-Item -ItemType Directory -Force -Path .agents\skills | Out-Null
Copy-Item -Path .\skills\* -Destination .\.agents\skills\ -Recurse -Force
```

Các agent nhận diện `.agents/skills/` hoặc `~/.agents/skills/` có thể khám phá từng skill theo phần mô tả trong YAML frontmatter. Nếu nền tảng dùng thư mục khác, theo hướng dẫn của nền tảng đó. Bộ này chưa thiết lập công cụ thực thi giúp agent truy cập máy của bạn; phải cấu hình adapter và quyền truy cập riêng.

## Lệnh cốt lõi (từ thư mục gói)

```bash
python skills/film-review-orchestrator/scripts/jobctl.py init \
  --source "/authorized/path/original_movie.mp4" \
  --workspace-root "/authorized/workspaces" \
  --title "Tên phim"
python skills/film-review-orchestrator/scripts/jobctl.py status --job "/authorized/workspaces/film-..."
python skills/film-review-orchestrator/scripts/jobctl.py verify-source --job "/authorized/workspaces/film-..."
python skills/film-review-orchestrator/scripts/evidence_qc.py \
  --map "/authorized/workspaces/film-.../match/sentence_shot_map.json"
```

Trên Windows, thay đường dẫn nguồn/workspace bằng đường dẫn Windows của thiết bị **được cấp quyền**. `init` tạo project, hash phim, thử `ffprobe`; **không chạy ASR, vision, TTS, render video**. Media cần adapter và thực thi tương ứng; không nhầm tạo job với hoàn tất phân tích.

## Điểm phê duyệt không được tự bỏ qua

Người dùng duyệt review trước toàn bộ lời đọc; duyệt giọng mẫu mới nếu có; duyệt pilot trước khi dựng full; xem/duyệt thành phẩm cuối. `jobctl.py` chỉ ghi nguồn tham chiếu phê duyệt thật, **không chứng minh nguồn tham chiếu là chính người dùng**. Agent phải nhận phê duyệt qua kênh hiện hành và không tự tạo.

## Quy trình và hợp đồng

[Xem quy trình N00–N09](WORKFLOW.md) · [Cài đặt](INSTALL.md) · [Bảo mật](SECURITY.md) · [Bộ bài kiểm thử và giới hạn](TESTING.md). Các quy tắc chứng cứ có tại `skills/film-review-orchestrator/references/global-rules.md`.

## Chưa được đóng gói và chưa được làm

- Không mang model weights, phim, audio thật, cache/embedding/transcript, API keys, logo, thumbnail hoặc video của người dùng.
- Không thay thế hay gỡ hai plugin `review-phim` cũ; không đụng tới dữ liệu Windows của các dự án trước.
- Không giả định mọi agent đều có FFmpeg, PySceneDetect, CLIP, Whisper, Qwen3-VL hoặc VieNeu.
- Không tự gán “100% khớp hình”, không coi điểm embedding hoặc caption AI là chứng cứ tuyệt đối.

**Yêu cầu runtime:** Python 3.10+ cho script hỗ trợ; `ffprobe`/`ffmpeg` và AI model là phụ thuộc ngoài chỉ khi muốn thực thi các công đoạn. Các schema dùng JSON Schema 2020-12. Chưa có giấy phép tái phân phối công khai được chỉ định; trước khi public, chủ sở hữu cần chọn LICENSE thích hợp.

## Execution Engine 2.1 — isolated development preview

An optional, **not yet production-complete** execution core is available in
[`engine21/`](engine21/) and documented in [ENGINE21.md](ENGINE21.md). It introduces
bounded subprocess adapters, signed-approval verification, fresh source/artifact
checks and crash recovery without changing any of the existing 11 Agent Skills.
Real AI model adapters and full-movie acceptance testing are future work.
