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

## Phase 3 — local adapter integration (development preview)

See [PHASE3.md](PHASE3.md) and [Windows synthetic QA](docs/qa/phase3-windows-2026-11-22.md). The new stage3 adapter provides real FFmpeg intake, scene indexing and MP4 rendering plus strict optional AI-provider contracts. System Python on the QA machine does not contain Whisper, CLIP or Qwen3-VL models; VieNeu TTS is only detected in a separate environment, not used for real synthesis. **Synthetic QA PASS never equals real-film or real-model acceptance.** No original Agent Skills are modified.

## Phase 4 — evidence-grounded narration and unsigned approvals (Draft)

See [PHASE4.md](PHASE4.md) and the [Windows acceptance report](docs/qa/phase4-grounded-review-2026-11-22.md). This adds a portable multi-event, source-SHA-bound extractive draft engine, a model-proposal quarantine, exact claim-to-shot provenance checks, and unsigned external-approval request preparation. Synthetic Engine21 QA with existing local AI models passes; **full-film autonomous story writing and genuine human approval are not certified.**

## Phase 5 — Source-locked bilingual evidence and CLIP → Qwen verification (Draft)

See [PHASE5.md](PHASE5.md) and [sanitized Fatman QA](docs/qa/phase5-fatman-2026-11-22.md). Source-bound EN→VI candidates, Qwen verification of exact N05 visual claims after CLIP and multi-sentence storyboard planning are tested. Real-film narrator/pilot remain unapproved; no movie/media/model weights are packaged.

## Phase 6 — Offline real-film dialogue and scene human review queue (Draft)

See [PHASE6.md](PHASE6.md) and [sanitized Fatman QA](docs/qa/phase6-fatman-2026-11-22.md). The source-locked 17-dialogue private audio review, FFmpeg candidate scene cuts, boundary-aware three-claim storyboard checks and unsigned offline HTML human worksheet have been tested. No real film/script/voice/pilot has been approved, and no movie/audio/transcripts/model weights are packaged.
