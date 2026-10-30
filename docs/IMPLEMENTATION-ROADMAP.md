# Lộ trình — Scope hiện tại chỉ là bộ tài liệu

## Pha tài liệu (đang bàn giao trên nhánh GitHub)
| Hạng mục | Deliverable | Nghiệm thu ở mức tài liệu |
|---|---|---|
| D0 | Design, phạm vi, traceability | Có lý do và giới hạn |
| D1 | SKILL.md, kiến trúc và điều phối | Entrypoint và gate nhất quán |
| D2 | Agent roles và workflows | Input/output, decisions, recovery |
| D3 | Schemas và artifact contracts | Example syntax, linkage rules |
| D4 | Policies, QA, future-use guide | Không tự cấp quyền máy/đăng tải |
| D5 | DOC-QA và GitHub PR | Rõ kết quả đã kiểm và chưa kiểm |

**Phạm vi yêu cầu hiện tại dừng ở D5.** Không yêu cầu máy, ổ đĩa, model, trình cài đặt hay video thử nghiệm. GitHub repo chỉ chứa bộ não Markdown có thể được đọc bởi ChatGPT/Agent trong nhiệm vụ tương lai.

## Lộ trình thực thi tương lai — chỉ tài liệu hướng dẫn, KHÔNG đang chạy
| Đợt | Nội dung dự kiến | Cần quyết định riêng |
|---|---|---|
| 0 | Chọn thiết bị/project root | Quyền kết nối |
| 1 | READ-ONLY inventory | Quyền đọc và path |
| 2 | Model/tool/license matrix | Quyết định cấu hình |
| 3 | Cài tool/weights | Phê duyệt tải và ghi |
| 4 | Ingest/ASR/Vision | Nguồn video có quyền |
| 5 | Evidence, narrative, script | Kiểm tra nội dung |
| 6 | Clip retrieval + TTS + EDL | Rights và chất lượng |
| 7 | FFmpeg/Remotion render | Profile đầu ra |
| 8 | QC factual/editorial/technical/rights | Phê duyệt thành phẩm |
| 9 | End-to-end benchmark + handoff | Kết quả đo thật |

**Hardware-First bắt buộc:** Đợt 0 xác thực thiết bị; Đợt 1 kiểm kê READ_ONLY **phần cứng + toàn bộ tool/model đang có**; Đợt 2 mới lập compatibility matrix và danh sách cần bổ sung; Đợt 3 chỉ cài sau G1 và kiểm chứng runtime. Xem [HARDWARE-FIRST-SELECTION.md](HARDWARE-FIRST-SELECTION.md).

Không lẫn trạng thái của Pha tài liệu với Đợt máy thực. Tests ở tests/ là specification, không được coi là đã chạy. Muốn triển khai sau này bắt đầu từ [HOST-INTEGRATION.md](HOST-INTEGRATION.md) khi người dùng tạo nhiệm vụ mới.

## Không tự động được phép
Cài driver, thay đổi ổ đĩa, sử dụng API trả phí, upload nguồn, công bố video, xác định pháp lý fair use hoặc merge main.
