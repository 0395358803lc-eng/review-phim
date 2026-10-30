# Hướng dẫn sử dụng bộ skill trong tương lai

## Mục đích
Đây là hướng dẫn nạp tài liệu vào AI Agent, không phải yêu cầu thao tác máy ngay lúc đọc file. Có thể dùng một phiên ChatGPT có khả năng đọc repo/tài liệu và công cụ máy từ xa (nếu được cấp quyền sau này).

## Quy tắc không được bỏ qua
Chỉ khi đã xác minh máy thật và kiểm kê READ_ONLY **phần cứng cùng phần mềm/model** mới được lập danh sách công nghệ phù hợp để cài đặt. Khi mới đọc repo, chỉ được nói về catalog chung. Trình tự và trạng thái nằm trong [Hardware-First](HARDWARE-FIRST-SELECTION.md).

## Cách nạp
1. Trỏ AI Agent đến đường dẫn kho nhánh được phê duyệt; yêu cầu đọc toàn bộ [SKILL.md](../SKILL.md).
2. Agent chỉ đọc thêm file theo ngữ cảnh: [ORCHESTRATION.md](../ORCHESTRATION.md), workflow cụ thể, agent chuyên môn, schema và policies. Tránh tải tất cả tệp vào một prompt cùng lúc.
3. Xác định yêu cầu là **chỉ tài liệu** hay **thực thi video**. Nếu chỉ tài liệu: sửa/đánh giá Markdown, không yêu cầu kết nối máy.
4. Nếu về sau xử lý video: yêu cầu nguồn có quyền xử lý, chọn thiết bị và phạm vi ghi; xem [docs/HOST-INTEGRATION.md](HOST-INTEGRATION.md). Hệ thống không tự có công cụ hoặc quyền chỉ vì có skill.
5. Ở mỗi stage, tạo artifact phù hợp và đọc kết quả thật. Lưu state; nếu thiếu quyền hoặc không có media inspection, trả BLOCKED/NOT_TESTED rõ ràng.
6. Kiểm tra nguồn, bản quyền và QC trước bàn giao; đăng video chỉ theo yêu cầu riêng.

## Ví dụ lệnh cho người sử dụng (tương lai)
> "Đọc SKILL.md của repo review-phim, chọn workflow movie-review, lập brief và các bước dựa trên video tôi cấp quyền. Trước khi thực thi hãy báo khả năng kết nối và quyền được cấp."

> "Chỉ kiểm tra chất lượng thiết kế skill; không kết nối máy, không chạy video. Đối chiếu các schema, agent và workflow để chỉ ra chỗ thiếu."

## Bản chất Brain-Only
- Tài liệu nói **khi nào, vì sao, dùng gì, nhận gì, xác minh thế nào**.
- Không coi prompt là thay thế của executable, model weights, tokenizer, codec hay GPU runtime.
- Không trộn code triển khai hay model binary vào repo tài liệu trừ khi người dùng thay đổi yêu cầu và có phê duyệt.
- Không khẳng định ChatGPT đã trực tiếp nghe/xem video chỉ từ metadata; nếu cần, pipeline phải đưa evidence frames/audio qua kênh khả dụng được cấp quyền.

## Sai lầm thường gặp
- "Đã đọc SKILL.md" không có nghĩa đã triển khai tool.
- "Semantic score 0.9" không chứng minh nhân vật thực sự làm hành động đang kể.
- "Video MP4 render OK" không chứng minh chất lượng nhận định hay bản quyền.
- "Agent đã đưa command" không chứng minh lệnh đã được chạy thành công.
