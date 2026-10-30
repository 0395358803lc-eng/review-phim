# Phạm vi bàn giao v1.0 — Chỉ tài liệu skill

## Người dùng yêu cầu
Xây dựng và duy trì **bộ tài liệu** để một AI Agent/ChatGPT sau này có thể đọc rồi điều phối mô hình và công cụ cục bộ xử lý video. Mục tiêu hiện tại là kho tham chiếu đầy đủ, có thể đọc, cập nhật, tái sử dụng. **Không vận hành hoặc sửa chữa máy tính trong yêu cầu này.**

## Phạm vi CÓ
- Entrypoint SKILL.md có điều kiện kích hoạt và file tham chiếu.
- Kiến trúc Brain-Only, local-first, evidence-grounded; phân ranh lý luận / remote actions / local execution.
- 9 mô tả vai trò agent và 6 workflow cho loại nội dung/khung hình.
- Ma trận nghiên cứu model và tool, tiêu chí chọn theo phần cứng khi triển khai.
- Data contracts media, transcript, scenes, evidence, causal narrative, script, EDL, QC, state.
- SOP gồm gates, recovery, privacy, source rights và handoff.
- Checklist nghiệm thu tài liệu và **định nghĩa** test runtime cho giai đoạn sau.
- Hướng dẫn nạp bộ skill vào agent hỗ trợ, không cam kết khả năng tích hợp tự động.

## Phạm vi KHÔNG
- Không connect Remote Desktop Commander cho đợt bàn giao tài liệu.
- Không chọn máy, chọn ổ, kiểm kê phần mềm trên máy, chạy lệnh host, tải/cài model, tải phim, thử render.
- Không viết ứng dụng dựng phim hay adapter chạy nền; nếu tương lai cần runtime thêm, phải thiết kế riêng và được phê duyệt.
- Không tuyên bố chất lượng phim, tốc độ xử lý GPU, độ chính xác ASR/VLM, tính hợp pháp của footage hoặc thành công trên TikTok/YouTube khi chưa kiểm chứng.
- Không tự merge vào main hoặc publish tài liệu nghiên cứu gốc ngoài ý muốn.

## Tiêu chí nghiệm thu tài liệu (khác nghiệm thu sản phẩm video)
DOC-PASS khi: các file tham chiếu tồn tại; entrypoint trỏ đúng; agent roles/workflows có input/output/gate/recovery; schema examples parse JSON; thuật ngữ thống nhất; test scenarios có cả tình huống lỗi; source report được đối chiếu; không chứa dữ liệu nhạy cảm; danh mục phần chưa kiểm chứng minh bạch.
DOC-PASS không có nghĩa là RUNTIME-PASS. Không thử máy hoặc video là phù hợp với phạm vi người dùng hiện tại, không phải một sự thất bại của bộ tài liệu.

## Thứ tự bàn giao
1. Nhánh GitHub chứa bộ Markdown.
2. Tài liệu hướng dẫn và biên bản DOC-QA.
3. Pull Request để người dùng xem, không tự merge.
4. Tương lai chỉ khi người dùng giao nhiệm vụ mới thực hiện cài đặt/kiểm thử trên máy.
