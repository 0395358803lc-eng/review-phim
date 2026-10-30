# Kiến trúc tham chiếu

## Các lớp độc lập
A. ChatGPT / orchestrator: lập kế hoạch, lựa chọn workflow, gọi tool được cấp quyền, đánh giá evidence, xác nhận stage và giải thích lỗi.
B. Remote action bridge: Remote Desktop Commander (khi kết nối) cung cấp filesystem/process/output; mọi lệnh thực thi theo quyền và thiết bị được xác minh. Không được suy ra quyền nghe/xem phim từ đường dẫn.
C. Local execution: FFmpeg/PySceneDetect/faster-whisper/WhisperX/pyannote/VLM/SigLIP/TTS/Remotion khi thật sự có trên máy; backend GPU tùy driver và phần cứng.
D. Artifact store: job folder gồm metadata, keyframes, transcripts, scenes, evidence, narrative graph, script, voice, EDL, outputs, logs, qc.
E. Human review: phê duyệt cài đặt, script lock, đoạn trích có rủi ro và xuất bản.

## Dòng xử lý
Input video -> decode/probe -> shots -> semantic scenes -> ASR/diarization + vision -> time-aligned evidence -> narrative graph -> claim/evidence script -> clip retrieval/verification -> voice/time align -> EDL -> render -> technical/factual/editorial/rights QC -> handoff.
Quy tắc: lý giải từ chứng cứ, không chạy thẳng từ VLM summary sang sản xuất.

## Storage tách biệt
- Source media: input/ (readonly; không chỉnh tệp gốc).
- Ephemeral: work/<job_id>/tmp, work/<job_id>/cache; chỉ cleanup khi có quyền.
- Model weights: tools/models; installers riêng, không đưa trong git.
- Checkpoints: work/<job_id>/artifacts và manifests bất biến theo từng bước.
- Release outputs: output/<job_id>/final; không tự upload.

## Contracts
Mọi artifact là JSON/JSONL hoặc media liên kết bằng đường dẫn; có schema_version, job_id, source_sha256, generator (name/version/config), produced_at, lineage. Timeline timebase giây thập phân, khoảng [start,end); end > start; timestamps không âm và không vượt duration. Mỗi claim Factual có evidence_ids, không có phải UNSUPPORTED.

## Độ tin cậy & tái chạy
Các stage có idempotency key (input hash + config/version), ghi vào thư mục staging rồi atomic rename khi thành công; không ghi đè artifact đã duyệt. Resume từ stage PASS có cùng hash/config; chạy lại khi thay đổi đầu vào hay model. Nếu connector timeout phải kiểm tra tiến trình hiện tại trước khi chạy lại nhằm tránh render/cài đặt hai lần.

## Phân ranh mô hình
Shot != semantic scene; speaker cluster != character; confidence score != bằng chứng; semantic similarity != cảnh chứa đúng hành động; diễn biến sau != quan hệ nhân quả. Các giả định này là bài toán xác minh, không phải năng lực mặc định của một thư viện.

## Các vị trí sử dụng engine
FFmpeg: probe/decoding/audio/encode/normalization/crop có điều kiện.
Remotion: motion graphics, captions, timeline/templates (license và môi trường Chrome kiểm tra trước).
ASR: transcript với timestamps và quality inspection.
VLM: captions và xác minh candidate theo batches nhỏ, khi model thực có.
Không có runtime tự động được tạo bởi Markdown: muốn chạy đầy đủ cần đã cài các CLI/adapter/command trên host hoặc phê duyệt phát triển lớp runtime tách riêng.
