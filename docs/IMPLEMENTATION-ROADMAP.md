# Triển khai theo Đợt (GitHub → máy thực)

Mọi đợt có: deliverable, thử nghiệm cụ thể, log và PASS/PARTIAL/FAIL/NOT_TESTED.

| Đợt | Scope | Gate nghiệm thu |
|---|---|---|
| 0 | Kết nối + chọn máy/thư mục | device_id hiện thời, approved root |
| 1 | Kiểm kê READ-ONLY | inventory có versions/backend/VRAM/disk |
| 2 | Thiết kế/đánh giá | người dùng duyệt design, risks & rights |
| 3 | Ma trận công cụ/model | danh sách install, license, size, GPU plan được duyệt |
| 4 | Brain-only docs + schemas | link tồn tại, kiểm tra mẫu, review chéo |
| 5 | Host evidence engine integration | sample shot/ASR/visual/source hash/causal refs |
| 6 | Script writer/reviewer | claim-evidence 1:1, no unsupported facts |
| 7 | Clip retrieval, TTS, EDL, Remotion/FFmpeg | end-to-end sample render source permitted |
| 8 | QA đa lớp | factual/editorial/technical/rights signoffs |
| 9 | Remote connector orchestration | resume/retry/permissions verified |
| 10 | Real video tests, docs, ZIP handoff | artifact hash + real test logs + owner approval |

## Trạng thái hiện tại
GitHub-only documentation implementation: Đợt 2–4 **drafted**, validation pending. Đợt 0: máy được liệt kê qua connector; chưa được xác nhận target directory/device dành riêng cho job. Đợt 1,3,5–10: NOT_TESTED/NOT_STARTED trên máy. Không xem repo docs như bằng chứng đã xử lý video.

## Đầu ra từng đợt
- G0 inventory.md (device, OS, hardware, versions).
- G1 architecture+install manifest có xác nhận.
- G2 media.json, shot/scenes jsonl, keyframes manifests.
- G3 transcript, evidence, graph, claims validation.
- G4 script.json + edit.json with rights rationale.
- G5 final video, ffprobe report, technical qc.
- G6 final qc report + human approved where necessary.

## Thứ tự ưu tiên MVP
A: ffprobe/FFmpeg/PySceneDetect/transcript+keyframes.
B: evidence store/scene metadata/narrative graph.
C: claim-supported script + matched scene retrieval.
D: voice/subtitles/EDL/render; QC.
E: VLM/SAM2/InternVideo add-ons chỉ theo số liệu so sánh.

## Không được tự động hoá mặc định
Quyền riêng tư, thanh toán/API, cài driver, việc đăng tải, quyết định fair-use, merge main. Mỗi mục này có gate riêng.
