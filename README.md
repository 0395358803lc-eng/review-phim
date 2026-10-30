# AI Video Review — Agent-Orchestrated Brain-Only

Bộ tài liệu điều phối ChatGPT để phân tích video/phim dựa trên bằng chứng, viết kịch bản, chọn cảnh, tổng hợp lời đọc, dựng và kiểm tra video bằng công cụ/model chạy trên máy người dùng.

**Trạng thái:** V1 documentation baseline / NOT YET RUNTIME-VALIDATED. Có tài liệu và quy trình, chưa có bằng chứng model cục bộ đã được cài, video mẫu đã render hay chất lượng đầu cuối được nghiệm thu.

## Bắt đầu
1. Cấp quyền kết nối Remote Desktop Commander; đọc [SKILL.md](SKILL.md) và [ORCHESTRATION.md](ORCHESTRATION.md).
2. Chọn máy, thư mục làm việc và vị trí lưu tools/models/cache/output. Khảo sát READ-ONLY trước mọi cài đặt.
3. Đọc [ENVIRONMENT-POLICY.md](ENVIRONMENT-POLICY.md), [TOOL-REGISTRY.md](TOOL-REGISTRY.md) để lập bảng có/thiếu và phương án tăng tốc GPU thực sự tương thích.
4. Chọn workflow: [movie-review](workflows/movie-review.md), [movie-recap](workflows/movie-recap.md), [ending-explained](workflows/ending-explained.md), [generic-video-review](workflows/generic-video-review.md), [youtube-longform](workflows/youtube-longform.md), [shorts-tiktok](workflows/shorts-tiktok.md).
5. Chỉ thao tác khi đã duyệt phạm vi; vận hành theo gates và các schema trong [schemas/](schemas/).
6. Đối chiếu [tests/acceptance-tests.md](tests/acceptance-tests.md) trước khi gọi dự án hoàn tất.

## Tài liệu nền
Tài liệu nghiên cứu do người dùng cung cấp: **deep-research-report.md** (391 dòng; không được sao chép vào kho công khai). Đọc riêng file đính kèm khi có quyền truy cập. [Traceability](docs/RESEARCH-TRACEABILITY.md) ghi rõ yêu cầu trích xuất từ báo cáo và những bổ sung thiết kế.

## Nguyên tắc không thỏa hiệp
- Brain-only: các file skill là chỉ dẫn, không tự thực thi; FFmpeg/Remotion/ASR/VLM vận hành qua công cụ được cấp quyền trên máy.
- Evidence-first: câu kể sự kiện phải có source hash/timecode và evidence ID; thiếu bằng chứng không được biến thành sự thật.
- Local-first: không tải phim riêng tư lên cloud và không dùng API trả phí nếu chưa có phê duyệt riêng.
- Không tự cài công cụ, tải weights, ghi đè/xóa, đăng video, sửa production hoặc tự phê duyệt bản quyền.
- Phân biệt việc **đã tạo tài liệu** với **đã xác minh thực thi** và **đã nghiệm thu chất lượng**.

## Trách nhiệm
Người sử dụng cung cấp nguồn video có quyền xử lý, chọn máy và nơi lưu, phê duyệt bước cài đặt và các quyết định pháp lý/biên tập rủi ro. ChatGPT lập kế hoạch, yêu cầu bằng chứng, thao tác qua connector nếu thực sự được cấp quyền, đọc artifact, kiểm tra và báo cáo trung thực.

Xem [docs/IMPLEMENTATION-ROADMAP.md](docs/IMPLEMENTATION-ROADMAP.md) để triển khai tiếp theo.
