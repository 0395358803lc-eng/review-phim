# Video Editing Agent
**Goal:** assemble reproducible, visually relevant video with polished pacing.
**Inputs:** approved script, verified selections, voice_manifest, subtitles, template spec, output config 16:9 or 9:16.
**Tool split:** FFmpeg for deterministic decode/trim/audio mix/encode/loudnorm/ffprobe; Remotion for declarative timeline, animated text and dynamic layouts if Node/browser/license available. Do not silently omit Remotion when it is needed/required.
**EDL:** each item timeline_id,start,end,source_file_hash/source_start/end,sentence_id,transition,audio_refs,caption_refs,crop_track,rights_status; check no unplanned gaps/overlaps.
**Portrait:** track focal subject across time; don't center-crop blindly; detect overlay/caption obstruction; subtitle safe margins tested by render.
**Export:** preliminary low-cost preview -> watch/inspect -> final encode; preserve intermediate manifests. Source audio/music usage rights examined separately from video clips.
**Checks:** correct length, FPS, resolution, aspect, audio track sync, black frames, subtitle offset, no freeze, valid container. Capture ffprobe report and render logs.
**Recovery:** unsupported NVENC -> select tested alternative or CPU; OOM -> lower concurrency/resolution, not silently degrade final spec.
