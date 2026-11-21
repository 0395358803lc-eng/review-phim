# Changelog

## 2.0.0 — 2026-11-21

- Tạo độc lập 11 Agent Skills theo workflow N00–N09 (1 orchestrator, 10 chuyên môn).
- Hợp đồng schema JSON, template adapter công cụ và mẫu chứng cứ tổng hợp.
- Python standard-library job state / source integrity / evidence mapping validators.
- Không có metadata hoặc runtime bị ràng buộc vào plugin cũ, không mang theo dữ liệu phim của người dùng.
- Không áp dụng hiệu ứng, intro, watermark, nhạc hay tỷ lệ cắt cảnh mặc định.

## 2.1.0 development branch — Phase 1 Execution Engine

- Add standalone engine21 Task Runner, recovery/state, signed approval and stage-evidence gates.
- Add tests for source/config tampering, interrupted and stale tasks, media decoding, bounded timeout/retry and missing approvals.
- Preserve 11 existing Agent Skills and v2.0 jobctl APIs unchanged; **no automatic migration or changes to main**.
- No production model integrations in this phase.
