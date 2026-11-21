# Quy tắc bất biến (Film Review Agent 2.0)

1. **Phim nguồn bất biến:** đọc nguồn gốc trực tiếp bằng đường dẫn và SHA-256; không sửa hoặc xóa, không dùng review/clip/transcript/caches phim khác làm chứng cứ.
2. **Nguồn chứng cứ tách biệt:** thị giác, ASR, bản dịch và bình luận là những loại chứng cứ khác nhau. Caption mô hình và CLIP là **ứng viên**, không phải xác nhận sự kiện.
3. **Chính xác hơn đẹp:** xác nhận nhân vật, hành động, vật, địa điểm và quan hệ bằng cảnh thật; nếu không đủ chứng cứ, đánh dấu giới hạn.
4. **Nhịp kể theo audio thực:** phân đoạn theo câu và ý, không ấn định độ dài clip, FPS, crop, zoom, intro, watermark, nhạc theo preset.
5. **Không suy diễn:** không gán người nói, danh tính, động cơ, quan hệ, quá khứ, dự báo hoặc nguyên nhân chỉ vì khung hình trông phù hợp.
6. **Gate người dùng:** duyệt kịch bản, giọng mẫu nếu mới, pilot; không tự tạo nhãn phê duyệt. Hành động upload, thay quyền môi trường, cài tool, xóa dữ liệu cần quyền đúng phạm vi.
7. **Truy vết và QC:** mọi shot phải có hash phim nguồn và timecode; mọi kết luận phải có lý do; QC kỹ thuật không đồng nghĩa QC nội dung.
8. **Không công việc nền hứa hẹn:** một lượt Agent thực hiện được đến đâu thì ghi kết quả thực tới đó; tiếp tục bằng checkpoint thật ở lượt sau.
9. **Bản quyền:** xác nhận quyền sử dụng phim/âm thanh và cân nhắc chính sách phát hành; không coi lời bình có tính chuyển đổi là sự cho phép tự động.
10. **Revision cô lập:** output mới dùng phiên bản mới, đối chiếu SHA-256 trước/sau, không ghi đè bản duyệt.

## Nhãn bằng chứng

| Nhãn | Ý nghĩa | Được phép kết luận |
|---|---|---|
| `VISUAL_DIRECT` | Bằng chứng hình ảnh trực tiếp về chi tiết nhìn thấy | Hành động/đồ vật/trạng thái nhìn thấy, không tự xác nhận tên/động cơ |
| `DIALOGUE_SUPPORTED` | Lời thoại thời gian nguồn xác nhận một phát ngôn | Có phát ngôn đó; người nói chỉ khi được xác thực riêng |
| `CONTEXT_ONLY` | Hình ảnh minh họa phù hợp bối cảnh | Chỉ là minh họa, không khẳng định toàn bộ mệnh đề |
| `UNRESOLVED` | Chưa đủ dữ liệu | Chưa được dựng như sự thật đã xác minh |
| `CONTRADICTED` | Mâu thuẫn với chứng cứ đã kiểm tra | Chặn phát hành câu/shot đó, trả về sửa lời bình hoặc chọn cảnh khác |

Không có nhãn `100%_MATCHED`.
