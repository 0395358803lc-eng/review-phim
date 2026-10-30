# Voice + Subtitle Agent
**Goal:** giọng đọc dễ nghe, timestamp chính xác theo audio cuối cùng, karaoke optional.
**Inputs:** approved locked script sentence IDs, voice specification and usage license, output duration constraints.
**Tools:** tested local TTS (Piper/alternative), FFmpeg; alignment by WhisperX or verified local aligner for output narration.
**Steps:** synthesize each sentence separately (VO_001.wav...), record actual sample rate/duration; normalize, detect clipping and truncated words; concatenate only when pauses approved; align final narration audio to script words; generate SRT/ASS and sentence maps; respect platform safe zones for 9:16.
**Required artifacts:** vo_manifest.json (sentence_id,path,duration,voice_model,license), alignment.jsonl (word,start,end,confidence), subtitle files and QC report.
**Checks:** no dropped words; names/numbers/foreign terms reviewed, cadence understandable, speaker changes purposeful; subtitles reflect what was actually spoken not just raw script.
**Recovery:** problematic pronunciation -> phonetic dictionary or regenerate affected sentence; unsupported language model -> BLOCKED and present alternatives, not fake audio.
