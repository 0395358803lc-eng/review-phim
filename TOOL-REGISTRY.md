# Tool / Model Registry — Decision Matrix

Đây là danh sách nghiên cứu và tiêu chí chọn, KHÔNG phải danh sách đã cài hay benchmark trên máy.

| Năng lực | Candidate | Ưu tiên | Kiểm tra bắt buộc |
|---|---|---|---|
| Probe/convert/render | FFmpeg + ffprobe | Required | binary, codecs, loudnorm, GPU encoder thực tế |
| Shot segmentation | PySceneDetect | Required for long film | phiên bản, timecode coverage |
| Transcription | faster-whisper | Required when speech exists | ngôn ngữ, VAD, timestamps, GPU backend |
| Word alignment | WhisperX | Optional/high value | model tiếng tương ứng, lỗi từ khó |
| Diarization | pyannote.audio | Conditional | terms HF, overlapping speakers |
| Small vision reasoning | MiniCPM-V or suitable local VLM | Conditional | license, load on actual VRAM, batch frames |
| Visual grounding | Qwen2.5-VL or verified replacement | Conditional | true action/time verification |
| Semantic retrieval | SigLIP | Required for semantic film retrieval | embedding reproducibility; false matches |
| Object tracking/reframe | SAM 2 | Optional | GPU/VRAM; track fragmentation |
| Video embedding | InternVideo family | Experimental | license, measured value over baseline |
| Crossmodal embedding | ImageBind | Experimental | licensing/benefit |
| TTS | Piper or verified local alternative | Required for AI narration | target language/voice license/quality |
| Advanced speech | Coqui family | Conditional | code vs weight license, packaging |
| Motion templates | Remotion | Required when templates needed | Node/browser, license and font checks |
| GPU acceleration | CUDA/ROCm/Metal/DirectML/CPU | Backend not product | detect supported actual path |

## Quy tắc lựa chọn
1. Xem máy có gì, không cài lại khi hoạt động đúng.
2. Chọn **nhỏ và chuyên biệt trước**, tăng model size ở những đoạn mơ hồ sau khi có test so sánh.
3. Chỉ đánh dấu GPU PASS sau khi benchmark thực chạy với device/backend xác thực; không lấy tên GPU làm bằng chứng.
4. License code, model weights, giọng và nguồn phim khác nhau; rà từng hạng mục trước tải/dùng thương mại.
5. Nếu chưa có giao diện CLI/API local gọi được từ connector, ghi GAP_ADAPTER và đề xuất triển khai riêng. Không biến tài liệu Markdown thành mã máy chủ mà không xin duyệt.

## Báo cáo công cụ
Ghi: component, installed(Y/N), version, binary/module path, license and terms, model size, CPU/GPU, VRAM/RAM measured, test input, elapsed, success/fail, source command/log. Thất bại CUDA có thể dùng CPU fallback nếu chất lượng và thời gian cho phép, ghi tradeoff.

## Các bước xác minh trước cập nhật
Kiểm tra tài liệu/phiên bản và giấy phép upstream mới nhất tại thời điểm thực thi. Dữ liệu trong báo cáo gốc là điểm xuất phát, không phải lời bảo đảm tương thích hiện hành.
