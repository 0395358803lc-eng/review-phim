# Orchestration Runbook

## Nhận yêu cầu
Capture: job_id, device_id (from live connector), source_path + source_sha256, goal (review/recap/explain/generic), language, duration target, audience, 16:9/9:16, spoiler policy, voice requirements, copyright evidence, output root. Các tham số không có dùng default đề xuất, gắn PROPOSED để người dùng biết.

## Stage machine
DISCOVER -> G0 READ_ONLY -> PROPOSE G1 -> APPROVED -> INGEST -> SHOTS -> ASR_VISUAL -> EVIDENCE -> NARRATIVE -> SCRIPT -> RETRIEVAL -> VO_EDL -> RENDER -> QC -> HANDOFF.
Chuyển stage chỉ khi artifact có thể đọc, schema hợp lệ và gate acceptance PASS. Unverified/failed không tự động tăng stage.

## Stage template
**Input:** path + hash + upstream manifest.
**Invoke:** dùng connector tool thực sự có quyền, command được tham số hóa/escaped đúng shell trên thiết bị đã chọn. Capture tool version/config.
**Observe:** đọc return code, logs và output; tránh chỉ dựa vào thông báo "started".
**Validate:** schema, duration bounds, coverage, causal evidence; kiểm tra bằng mắt/nghe khi có công cụ hỗ trợ.
**Persist:** artifact + manifest + checkpoints.
**Recover:** retry có giới hạn với lý do; chuyển BLOCKED nếu không đủ chứng cứ/quyền.

## Sample reasoning loop
1. Script sentence S012: "Nhân vật phá hủy bộ phát sóng".
2. Retrieve scene candidates bằng transcript + entity/time + semantic ranking.
3. Không chấp nhận cảnh chỉ có nhân vật đứng cạnh bộ phát; phải thấy hành động hoặc bằng chứng trực tiếp.
4. Nếu không tìm thấy, sửa thành câu có chứng cứ hoặc dùng B-roll phi minh họa rõ nhãn; không tạo claim sai.
5. Ghi selection score, verification status và rationale vào EDL.

## Quality gates and state
- Mọi claim sự kiện thiết yếu có evidence verified hoặc marked inferred with clear language.
- Không có UNSUPPORTED factual claims trong script lock.
- Không phát hành nếu media corrupted, transcript/subtitle lệch nghiêm trọng, rights unresolved, hoặc chưa có human signoff nơi quy định.
- Render có media probe, shot/aspect/timestamp qc; PASS cho kỹ thuật không đồng nghĩa PASS cho sáng tạo.
- Những bài kiểm thử không chạy được ghi NOT_TESTED và lý do.

## Resume
Mỗi job có state.json và stages.json: stage, status, run_id, input_hash, config_hash, output_hashes, producer, verified_by, timestamp. Resume chỉ nếu inputs unchanged; không chạy lại tác vụ side-effecting đang pending. Tên file/id mang tính gợi ý, chưa có runtime đọc/ghi tự động.

## Completion response
Job + target; completed stages with real evidence; files & checksums; missing steps; failures/recovery; quality verdict; rights risks; machine load/elapsed measured; explicit next approval. Khi thực thi không có máy kết nối báo BLOCKED, không tự dựng báo cáo giả.
