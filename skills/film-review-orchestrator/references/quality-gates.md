# Kiểm tra tính đúng và nghiệm thu

## Thứ tự kiểm

1. **Source trust:** đường dẫn và SHA256 phim gốc, stream timebase đúng; không có source thuộc project khác.
2. **Data coverage:** trường hợp đoạn tối, chồng lời, ASR bất thường đều được báo cáo; không buộc caption không chắc thành sự thật.
3. **Script trace:** mọi câu và mọi mệnh đề sự kiện quan trọng có bằng chứng riêng (`VISUAL_DIRECT`, `DIALOGUE_SUPPORTED`) hoặc ghi giải thích vì sao vẫn `CONTEXT_ONLY`.
4. **Narration:** đối chiếu 100% câu, phụ âm/tên riêng, timecode thực, cắt WAV, âm lượng/clipping.
5. **Scene match:** kiểm `sentence-shot-map.schema.json` + `scripts/evidence_qc.py`, sau đó lấy mẫu hoặc kiểm riêng các đoạn trọng yếu trong source thật và MP4; không tin điểm AI một mình.
6. **Technical:** `ffprobe` stream; giải mã đầy đủ video và audio về null, độ dài lệch không vượt ngưỡng dung sai đã lập từ source timebase; không khẳng định PASS nếu thiếu output/ffmpeg.
7. **Release:** video, báo cáo, hash, phiên bản, hạn chế còn tồn tại; quyết định nhận xét cuối do người dùng.

## Tình huống bắt buộc dừng

- Claim có `CONTRADICTED` nhưng chưa sửa.
- Shot dùng source timecode ngoài phim hoặc sai film hash.
- Mốc voice chưa xác nhận hoặc file narration thiếu.
- Không thể giải mã MP4 cuối hoặc âm thanh lỗi.
- Chưa có quyền sử dụng, phát hành, cloud upload, cài driver/model hay xóa data cần thiết.

## Mục đích hai loại QC

- **Kiểm máy** xác minh file hợp lệ, không chứng minh ý nghĩa câu phù hợp.
- **Kiểm biên tập** xác minh mối liên hệ chứng cứ; cảm xúc, suy luận và bình luận được biểu đạt trung thực nhưng không tự nhận đã có khung hình chứng minh.
