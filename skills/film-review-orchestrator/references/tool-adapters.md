# Khả năng công cụ và adapter (không khóa vendor)

**Tự phát hiện trong môi trường được phép**: `ffprobe`/`ffmpeg`, PySceneDetect, CLIP/OpenCLIP, ASR Whisper hoặc model có hỗ trợ ngôn ngữ, Qwen3-VL hoặc vision tương đương, TTS VieNeu hoặc engine người dùng chọn, encoder GPU/CPU. Phải kiểm version, định dạng vào/ra và quota/bộ nhớ trước khi chạy.

1. Đọc `templates/adapter-config.example.json` làm mẫu và tạo bản riêng trong từng job; **không** lấy đường dẫn mẫu làm lệnh chạy được.
2. Thử một đoạn có nguồn thật, kiểm thời gian, độ phân giải, mã tiếng Việt và VRAM. Khi GPU lỗi, báo nguyên nhân; chỉ dùng phương án khác phù hợp với quyền đã cấp.
3. CLIP chỉ tìm ứng viên; Qwen/VLM chỉ đưa mô tả cần kiểm chứng; Whisper chỉ sinh ASR kèm độ chắc chắn; FFmpeg chỉ dựng theo quyết định chứng cứ đã chốt.
4. Ngoại tuyến là mặc định khi xử lý phim có bản quyền; mọi dịch vụ cloud/upload phải được người dùng cho phép riêng, kèm điều kiện bảo mật.
5. Nếu tác vụ cần truy cập máy từ xa, dùng công cụ điều khiển đã kết nối và được phép; skill không tự có quyền truy cập phần cứng hay ổ đĩa.
6. Có thể thay từng backend (Whisper ↔ ASR khác; Qwen3-VL ↔ VLM khác) nếu đáp ứng cùng hợp đồng chứng cứ; lưu model ID + version, config và độ tin cậy.

Các ví dụ không đi kèm weights, codec bên thứ ba, API keys, file phim hoặc nguồn cá nhân.
