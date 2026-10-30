# Design: AI Video Review Agent-Orchestrated Brain-Only

## Why
Review/recap tự động dễ chọn sai cảnh, bịa tình tiết, thuyết minh lệch nhịp và vi phạm bản quyền. Hệ thống cần chia observation/reasoning/writing/render để lần vết.

## Goals
Skill Markdown điều phối remote tool và local model, hoạt động trên các host được cấp quyền; hỗ trợ review, recap, ending-explained, generic-video, YouTube long và 9:16; evidence linkage và đo chất lượng. Không lẫn weights, binary, private films vào git.

## Non-goals
Không tự xây SaaS hoặc công cụ video fullstack, không tự publish, không tuyên bố fair-use guaranteed, không tự chuyển file riêng tư qua cloud, không đảm bảo có thể nghe/xem video bằng ChatGPT nếu connector không hỗ trợ.

## Options considered
1. Standalone Python application: dễ kiểm thử E2E nhưng trái Brain-Only và phụ thuộc runtime riêng.
2. All-in-one LLM video summarization: nhanh triển khai nhưng thiếu scene-level grounding/accuracy.
3. **Selected proposal:** Markdown-orchestrated evidence-first pipeline, local specialized tools, JSON contracts, stage gates. Tối ưu cập nhật độc lập; rủi ro là connector latency và adapter local interface chưa có.

## Key interface decisions
Mọi claim/events/timecodes link media SHA256; mỗi stage artifact phải schema-validated; device & root explicit; runtime tasks execute by authorized connection. Models selected against real hardware and licenses; upgrade only after measurements. Script-first clip retrieval with frame verification. Remotion optional for motion styles, FFmpeg for deterministic media.

## Residual risks
Speaker != character, nonlinear narrative, implicit actions, TTS prosody, vision hallucination, source rights, GPU driver compatibility, local TTS Vietnamese models, storage exhaustion. Use fail closed for unsupported critical claims and rights.

## Acceptance
Docs pass link/schema review; installed host tools verified separately; end-to-end gate only after a rights-cleared sample produces video plus QC + human approval. Design implemented as initial draft in separate GitHub feature branch pending user acceptance.
