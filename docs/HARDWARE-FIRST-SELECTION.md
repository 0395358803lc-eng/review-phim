# Hardware-First Tool and Model Selection — Normative Runbook

## Nguyên tắc
Khi dùng AI Video Review trên máy thật, **không đề xuất danh sách cài đặt trước khi kiểm kê cấu hình phần cứng và phần mềm/model có sẵn**. TOOL-REGISTRY.md chỉ là catalog candidate, không có benchmark hay xác nhận tương thích. Quy tắc này không cấp quyền tải/cài/xử lý media.

## Decision gates
1. **CONNECT:** xác minh online device_id từ connector hiện tại và phạm vi được phép đọc; không kế thừa máy từ phiên cũ.
2. **G0-A HARDWARE READ_ONLY:** thu thập OS/architecture, CPU, RAM, GPU vendor/model/VRAM, driver, runtime/backend candidate (CUDA/ROCm/Metal/MPS/DirectML/CPU), ổ đĩa/free capacity, source commands/log/timestamp. Backend chỉ được coi verified sau smoke test được cho phép.
3. **G0-B INSTALLED READ_ONLY:** liệt kê tool/model đã có (FFmpeg, ffprobe, Python, Node/npm, PySceneDetect, ASR, VLM, SigLIP, TTS, Remotion...), version, local path, model weights/revision và điều khoản sử dụng có thể đối chiếu. Có file hoặc version chỉ chứng minh presence, không tự động PASS.
4. **G0-C WORKLOAD:** lấy brief (review/recap/explained/generic, ngôn ngữ, speech/no speech, duration, aspect, chất lượng, quyền footage, local-only), chỉ kiểm tra metadata và nội dung nguồn khi được phép.
5. **ASSESS:** từ inventory thật và brief, so sánh tương thích OS/CPU/RAM/VRAM/backend/disk, dependency versions, language, commercial license và tài nguyên. Chọn **bộ tối thiểu đủ năng lực**; tái dùng công cụ đã cài hoạt động tốt. Với mỗi candidate phải ghi một trạng thái:
   - **INSTALLED_USABLE** — hiện có và đã được kiểm chứng đủ để dùng, không cài trùng.
   - **INSTALL_PROPOSED** — còn thiếu, phù hợp sơ bộ theo evidence, thiết yếu cho workload nhưng chưa cấp quyền cài.
   - **CONDITIONAL** — cần thêm kiểm thử, quyền hoặc điều kiện (bao gồm installed chưa thử).
   - **INCOMPATIBLE** — evidence cho thấy không chạy/không đáp ứng yêu cầu; không cài.
   - **UNKNOWN** — thiếu thông số trọng yếu, không được tự nâng thành đề xuất.
6. **REPORT:** xuất [TOOL-COMPATIBILITY-REPORT.md](templates/TOOL-COMPATIBILITY-REPORT.md) theo host, tách clearly: đã có/dùng lại; thiếu và nên cài; chưa xác định; loại; kèm lý do/alternatives. Đánh giá video probe, shot/scene, ASR nếu có lời thoại, vision/retrieval, TTS nếu cần, editing, QC. Không buộc cài tất cả các model nghiên cứu.
7. **G1 PROPOSAL:** chỉ sau REPORT mới nêu chính xác từng bản package/model cần cài: version/revision pinned, official source, license code/weights/voice, size/download estimates, disk cap, network endpoints, install paths/cache/tmp, test plan, backend CPU/GPU/fallback, rollback và quyền yêu cầu. Cần **phê duyệt riêng** cho cài/ghi. Không tự cài chỉ vì người dùng yêu cầu "dùng skill".
8. **INSTALL + TEST:** chỉ cài các mục INSTALL_PROPOSED được phê duyệt, trong root được duyệt. Kiểm thử thực model inference, GPU backend và **encoder GPU riêng**, đo lỗi, RAM/VRAM/time/output. Model hoặc backend fail -> quay lại ASSESS; không tự cài thay thế ngoài scope.
9. **PROCESS:** sau PROCESS_APPROVED và công cụ đã kiểm chứng, mới dùng pipeline evidence -> script -> retrieval -> voice -> edit -> QC; không tự upload/publish.

## Failure/edge cases
- **Không có host/connector hoặc chưa được quyền đọc:** BLOCKED; chỉ nói catalog chung, không có host install list.
- **Không rõ GPU/VRAM/driver/disk cần thiết cho lựa chọn:** UNKNOWN; bổ sung số liệu trước khi chọn.
- **Chỉ có CPU / GPU không hỗ trợ:** chọn CPU-compatible model/cấu hình nhỏ hơn có chất lượng chấp nhận được, hoặc BLOCKED; không giả CUDA/ROCm/NVENC.
- **NVIDIA/AMD/Apple:** tên GPU không đủ chứng minh backend; render encoder và AI inference phải thử độc lập.
- **Disk thiếu / license không rõ / môi trường không khớp:** loại hoặc đặt CONDITIONAL; không được cài.
- **Đã có tool nhưng chưa xác minh runtime:** CONDITIONAL, ưu tiên kiểm thử sau cấp quyền; không tự reinstall.
- **Nguồn không có audio:** có thể bỏ ASR/diarization theo brief; không cài thừa.
- **Không có CLI/API adapter hoặc connector không chuyển được khung hình:** GAP_ADAPTER/GAP_EVIDENCE_BRIDGE, không giả đã thực thi/quan sát.

## Evidence contract
Inventory: host ID, thời gian, từng thông số và chứng cứ lệnh, phần mềm/model đã có, unknowns. Recommendation: mỗi capability và candidate, compatibility reason, installed status, fallback, license, GPU/CPU constraints, storage/download estimate, G1 approval state. Cache/weights/temp/output phải nằm trong root được duyệt; không thay driver, đẩy media lên cloud hay xuất bản nếu chưa có quyền. Tests [D10–D14](DOCUMENTATION-VALIDATION.md) và [AT13–AT16](../tests/acceptance-tests.md) mới là **test specifications**, chưa được gọi PASS.
