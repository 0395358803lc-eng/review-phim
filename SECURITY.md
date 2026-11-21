# Bảo mật, bản quyền, bảo toàn dữ liệu

1. **Không di chuyển phim ngoài hệ thống** khi chưa được cấp quyền rõ; tránh gửi tệp có bản quyền hoặc lời thoại nhạy cảm lên dịch vụ bên ngoài.
2. **Không ghi đè phim gốc**, không xóa artifact đã được chấp nhận hoặc thư mục máy khác. `jobctl` tạo workspace mới, ghi trạng thái trong workspace mới.
3. **Phạm vi xác nhận:** người dùng cho phép tạo video không đồng nghĩa cho phép cài model, thay driver, xóa nhiều thư mục, phát hành lên YouTube hoặc mua dịch vụ.
4. **Hash nguồn:** nếu phim thay đổi, dừng quy trình; không tái sử dụng scene index/ASR/shot map của nguồn khác.
5. **Tính xác thực media:** ảnh ví dụ tổng hợp trong gói là dữ liệu giả định, không được trình bày là bằng chứng phim. Chỉ dùng frame/clip trích trực tiếp từ file source đã kiểm.
6. **Bằng chứng quyền:** ghi lại phê duyệt thật; các lệnh `approve` không thể thay chữ ký hoặc xác nhận danh tính người dùng.
7. **Tối thiểu quyền:** tool adapter chỉ chạy với quyền cần thiết; bí mật và token không nằm trong SKILL.md, template hoặc release zip.
8. **Truyền dữ liệu:** không tự bật remote/cloud model khi local không đủ VRAM. Báo cho người dùng lựa chọn fallback.
9. **Giới hạn pháp lý:** sự tồn tại của phim gốc không đồng nghĩa có quyền tái sử dụng hoặc phát hành công khai; cần tuân thủ quyền và quy định áp dụng.
