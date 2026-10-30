# Research traceability

**Source:** user-supplied deep-research-report.md, 391 lines, current conversation. File not committed to public repo to avoid unintentionally publishing user material.

| Source paragraphs / lines | Requirement | Implemented guidance |
|---|---|---|
| 3–27 | Distinguish criticism, recap, analysis and feedback loop | workflows/*, tests/quality-gates |
| 29–85 | Hooks/storytelling/visualizable script | agents/scriptwriting.md, schemas/script-schema.md |
| 87–178 | Evidence layer, shots/scenes, ASR, speaker/character, causal graph | agents/ingest, audio-analysis, visual-analysis, narrative-analysis; schemas/evidence/narrative |
| 180–239 | Script-first selection, voice/word timing, FFmpeg/Remotion | agents/scene-retrieval, voice-subtitles, editing |
| 241–270 | Local-first model/tool choices, measured VRAM | TOOL-REGISTRY, gpu-selection, ENVIRONMENT-POLICY |
| 272–353 | Agent stage gates, artifact schemas, recovery, provenance | ORCHESTRATION, schemas, policies/failure-recovery |
| 355–391 | Four QC layers, copyright, YouTube retention, human review | agents/quality-control, copyright-review, tests |

## Những bổ sung thiết kế (không phải khẳng định trong báo cáo)
- Nhánh GitHub riêng và PR thay vì merge trực tiếp; environment approvals.
- Checkpoint hashing/idempotency và atomic commit artifact.
- Quy tắc bảo mật remote execution, secrets, path scope.
- Cấu trúc Markdown brain-only và công việc ngoài kho trên máy đích.
- Test IDs/acceptance metrics là tiêu chí kỹ thuật đề xuất cần kiểm chứng.

## Điểm cần kiểm chứng khi có máy/video thật
Hiệu suất GPU, model weights/licenses khả dụng, mapping speaker-character, temporal retrieval correctness, giọng TTS tiếng Việt, exact captions alignment, rights status, retention thực tế. Không đánh dấu verified chỉ từ mô tả tài liệu.
