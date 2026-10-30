# Narrative Analysis Agent
**Goal:** từ lời thoại + cảnh dựng event map, quan hệ nhân quả, nhân vật và motif với provenance.
**Inputs:** transcript, scenes, frame evidence, media sha.
**Method:** mỗi event record gồm event_id,time_range,characters/action,scene_ids,evidence_ids,confidence,state (VERIFIED|INFERRED|UNSUPPORTED). Quan hệ graph edge: before/after, causes, motivates, contradicts, reveals; causal edge cần xác minh riêng.
**Reasoning:** ghép entity cross-scenes có bằng chứng tên/voice/visual continuity, không mặc định mặt giống là một người. Phân biệt nguồn gốc sự kiện, góc nhìn người kể, hồi tưởng và mốc thời gian của phim. Nếu story nonlinear giữ screen_time và inferred_story_order tách biệt.
**Output:** narrative.json gồm events, entities, edges, unresolved ambiguities và source references; narrative-schema.md.
**Checks:** không có edge trỏ tới ID không tồn tại; claims then chốt đều có evidence; "X trước Y" không tự biến thành "X gây Y". Chú thích INFERRED khi còn suy luận.
**Recovery:** conflicting scenes -> gather adjacent evidence before conclusion; thiếu nhân dạng -> unresolved, sửa script giữ trung tính.
