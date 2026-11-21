# Quy trình Film Review Agent 2.0, từ một bộ phim mới

## Luồng chính

```text
N00 Nhận phim + SHA-256 + ffprobe + giải mã mẫu
  ├─ N01 Phân cảnh + ảnh nguồn + chỉ mục CLIP (tùy chọn)
  └─ N02 Audio + ASR nguyên ngữ + dịch + điểm không chắc
       \                    /
        N03 Vision (sau N01)
         \                  /
          N04 Bộ nhớ phim + claim ledger
           ↓
          N05 Viết lời bình → USER DUYỆT SCRIPT
           ↓
          N06 WAV + timeline từng câu → duyệt giọng mới nếu cần
           ↓
          N07 Truy hồi CLIP/ASR → kiểm VLM/frame → chọn cảnh có chứng cứ
           ↓
          N08 Pilot thật → USER DUYỆT PILOT → dựng từng chương + MP4
           ↓
          N09 QC video + audio + mapping → USER XEM VÀ NGHIỆM THU
```

Tầng N01–N02 có thể chạy song song khi môi trường đủ năng lực. Chỉ một workspace cho một phim, chỉ dùng phim gốc được xác minh; không mặc định lịch vận hành chạy ngầm. Thời lượng lời đọc thực quyết định timeline; câu review quyết định ứng viên hình ảnh.

## Bằng chứng tối thiểu khi chọn shot

`sentence_id`, câu review chính xác, atomic claims có nhãn, timecode WAV, mốc source phim gốc, IDs frame/ASR, qualifier và sha256 phim gốc. Không có hình khớp một ý có nghĩa là **chưa đủ chứng cứ**, không có nghĩa hệ thống phải chọn bừa một clip.

## Chế độ hợp tác với người dùng

Agent mặc định xử lý kỹ thuật trong phạm vi đã cấp quyền, ghi kết quả hữu hình và trình bày rủi ro. Phê duyệt nội dung không đồng nghĩa cấp quyền cài package, upload phim, xóa file hoặc xuất bản lên nền tảng công khai. Khi bị giới hạn khả năng, Agent báo rõ công đoạn nào còn BLOCKED và đường dẫn artifact thực thay vì khẳng định hoàn tất.
