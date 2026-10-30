# Audio Understanding Agent
**Goal:** transcript theo thời gian, phân nhóm speaker, sound event clues. Speaker cluster không đồng nghĩa danh tính nhân vật.
**Inputs:** media.json/audio track + source_sha256.
**Tools:** faster-whisper hoặc Whisper, WhisperX (forced alignment), pyannote (conditional/terms); FFmpeg extract; chọn device theo gpu-selection.
**Procedure:** trích audio bản làm việc; VAD; ASR theo chunks có overlap quản lý; normalize timestamps về thời gian video; align word-to-audio khi model hỗ trợ ngôn ngữ; speaker segmentation; gom overlaps và flag uncertainty; giữ text nguyên văn bên cạnh bản dịch.
**Artifacts:** transcript.jsonl với segment_id,start,end,text,language,asr_confidence,speaker_cluster,word timings,source_ref; audio-events.jsonl; diagnostics (speech coverage, gaps, unresolved names).
**Checks:** all times bounded, monotonic per track, transcription coverage trên speech regions, words nằm trong segments, speaker IDs stable qua chunk boundary. Không lấy low ASR confidence làm nội dung đúng.
**Recovery:** tái chạy đoạn confidence thấp bằng model lớn hơn; cảnh nhạc/đám đông -> mark uncertain; overlapping speech -> cần human review; không tự quy speaker thành nhân vật chỉ từ giọng.
