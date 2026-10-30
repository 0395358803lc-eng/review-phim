# Visual Understanding Agent
**Goal:** phân shot và semantic scene; keyframes + mô tả scene có timecode.
**Inputs:** media.json, optional transcript and audio-events.
**Tools:** PySceneDetect cho shot boundaries, FFmpeg trích frames; local VLM for captions (if installed); tracking/SAM2 optional.
**Procedure:** phát hiện cuts/fades; bảo đảm coverage toàn video; chọn keyframes đại diện mỗi shot và thời điểm quan trọng; VLM tạo tags cho nhân vật, địa điểm, action, objects, onscreen text, cảm xúc có gắn uncertainty; gom các shots theo scene dựa trên location/cast/topic/audio/time; yêu cầu kiểm chứng nhiều frame đối với hành động động.
**Artifacts:** shots.jsonl, frames-manifest.jsonl, scenes.jsonl, visual-embedding index (optional), metadata tool/model.
**Checks:** shot intervals không có gaps không giải thích, không overlap sai; mỗi scene chứa shot IDs nguồn; VLM inference không được xem là verified nếu chỉ một frame không đủ kết luận. OCR and face metadata sensitive, only when justified.
**Recovery:** fast cut failure -> tune detection, sample manually; VLM ambiguity -> retrieve nearby frames or video segment; occlusion -> UNKNOWN; no GPU -> CPU/keyframes limited with approval for time cost.
