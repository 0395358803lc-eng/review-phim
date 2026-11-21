# Hướng dẫn cài đặt độc lập

## 1. Giải nén và kiểm tra

Giải nén ZIP vào thư mục bạn kiểm soát, giữ nguyên tên thư mục các skill. Chạy:

```bash
python -m unittest discover -s tests -v
python scripts/validate_release.py .
```

Bộ phát hành kiểm thử bằng Python 3.13; runtime hỗ trợ Python 3.10+ (các kiểm thử YAML/JSON schema có thể cần PyYAML và jsonschema, không bắt buộc khi chạy skill/jobctl).

## 2. Cài tại project

- **Linux/macOS** (từ thư mục giải nén): `mkdir -p <project>/.agents/skills && cp -R skills/* <project>/.agents/skills/`.
- **Windows PowerShell** (từ thư mục giải nén):

```powershell
New-Item -ItemType Directory -Path "C:\du-an\.agents\skills" -Force
# Đổi đường dẫn C:\du-an cho phù hợp.
Copy-Item .\skills\* -Destination "C:\du-an\.agents\skills\" -Recurse
```

- **Cài cá nhân:** chép các thư mục skill vào `~/.agents/skills/` nếu agent nhận diện nơi đó. Một số môi trường có thư mục riêng; tra tài liệu của chính agent.
- Chỉ cần cài thư mục `skills/*`; các script hỗ trợ vận hành nằm **bên trong** `film-review-orchestrator`, nên vẫn có thể dùng sau khi copy.

## 3. Kết nối công cụ

Tạo một bản config từ `skills/film-review-orchestrator/templates/adapter-config.example.json` **ở ngoài thư mục skills**, trong workspace từng phim. Bổ sung công cụ và quyền thực tế. Không chỉnh ví dụ thành chứa secrets.

- N00/N01/N08/N09 cần FFprobe/FFmpeg có thể truy cập hoặc adapter tương đương.
- N01 và N07 có thể sử dụng PySceneDetect + CLIP, nhưng nếu không có phải làm truy hồi khác và ghi rõ độ phủ.
- N02 dùng ASR có hỗ trợ ngôn ngữ phim (Whisper là ví dụ).
- N03/N07 dùng VLM để đề xuất/kiểm tra, có đánh giá frame gốc thực tế (Qwen3-VL là ví dụ).
- N06 cần TTS được phép, bản WAV và kiểm âm.

Không tự cài công cụ, cập nhật driver, đổi PATH hoặc gửi phim lên cloud chỉ vì file cấu hình nêu một backend.

## 4. Vận hành và tiếp tục

Với phim gốc hợp lệ và quyền đúng phạm vi, chạy `python path/to/jobctl.py init --source ... --workspace-root ... --title ...`. Giữ lại `job_state.json` từ lần trước; khi quay lại, dùng `status` và `verify-source` để xác định những gì **thật sự** đã làm xong.

Trường hợp bị ngắt ở giữa một stage, không tự đánh dấu DONE; chạy tiếp công đoạn còn thiếu, đối chiếu file và hash. Khi thay review/voice/clip, xuất bản revision mới thay vì ghi đè version đã duyệt.

## 5. Gỡ bỏ

Gỡ thư mục skills được cài nếu muốn ngừng sử dụng. Workspace và phim gốc nằm **ngoài** skills, không được tự xóa; chỉ xóa workspace theo lệnh có phạm vi rõ ràng và sau khi sao lưu nếu cần.
