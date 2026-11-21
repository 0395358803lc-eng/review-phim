# Phase6 sanitized QA — Real Fatman (2020), 2026-11-22

**Verdict:** TECHNICAL PASS — LOCAL USER REVIEW WORKBENCH READY; FILM SEMANTICS STILL PENDING. Numerical metrics only, no copyrighted film media or original dialogue in Git.

## Verified input scope
- Original user-authorized movie: 5,823.552 seconds.
- Old Phase4 and Phase5 QA data are unchanged, read-only. Three distinct source windows at 00:09:00–00:09:30, 00:37:00–00:37:30 and 01:16:00–01:16:30. 90 seconds = 1.55% total source.
- Source SHA256 verified prior to and after every local workbench run.

## Evidence and reviewer materials
- 17 raw English Whisper ASR evidence rows cross-bound to source SHA, English text hashes and original timestamps.
- 17 private local WAV original-audio excerpts, FFprobe confirmed 16kHz mono and nonzero audio; aggregate 1,956,526 bytes; SHA256 of each local preview checked.
- 2 low-ASR confidence rows prioritized for listening, 1 translation false friend flagged; no translation auto-corrected or human-approved.
- FFmpeg scene score threshold 0.27 found 6 / 9 / 7 cutpoint candidates across the three film clips: **22 cuts, 25 shot intervals**. These are candidate edit boundaries, NOT ground-truth film semantic scenes.
- Three original Phase5 source-bound Vietnamese review sentence candidates preserve claim IDs C0001, C0015, C0022, with links to original Qwen frame/source times.
- **Two frame windows straddle real detected cuts**: F01 cut at source time 544.917s, F02 cut at 2245.000s. Both were set to PENDING_HUMAN_CUT_BOUNDARY_REVIEW with *two possible scenes*, not silently assigned a single shot. The third is still PENDING_HUMAN_VIDEO_REVIEW.
- A private self-contained HTML worksheet offers playable 3 original source excerpts, 17 audio excerpts, raw English and Vietnamese draft per segment and notes export; notes are unsigned and cannot unlock Engine approvals.

## Result and limits
- Host-side real media process: exit 0; independent readback: exit 0, original movie SHA unchanged.
- Technical source matching and scene-candidate provenance validated. **No visual claims or dialogue transcripts independently human-verified**; full film semantics, actual character actions, causal story order and source-to-Vietnamese truth remain unapproved.
- No real voice approval, 90–120s narrated pilot, main merge, package installs, modified older footage/outputs, or uploads of film, transcripts, frames, voice or model weights.

## Next separate permission
A human should listen to original dialogue WAVs, correct the English/VI data where needed, view BOTH video sides of 2 cut-boundary claims and approve/revise the three source-bound Vietnamese claims. Only after external trusted script/voice approval can N06–N09 real-film pilot work be considered. No test-only signatures can substitute.
