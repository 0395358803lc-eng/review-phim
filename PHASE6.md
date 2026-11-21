# Phase 6 — Real Film Human Review Workbench (Draft)

**Outcome:** A private, offline and source-locked review queue for authentic film dialogue and film scene boundaries. Phase6 prepares a person to decide whether a Vietnamese review sentence actually matches its clip. It does NOT certify the source transcript/translation, sign any approval, produce a production voice or render a real-film recap.

## Architecture

- stage6/dialogue_review.py: cross-checks every original English Whisper segment against Stage5 ASR and Vietnamese candidate data by source movie SHA, original English text SHA, ID and timecode. No altered English, dropped or duplicate IDs, forged model approval or ASR outside authorized excerpt. Adds priorities for low-confidence audio and translation polysemy errors (e.g., postal letters vs alphabetic letters).
- stage6/scene_proposals.py: takes real FFmpeg relative cutpoint times from each source 30-second clip and transforms them into full-movie timecode intervals. All candidates are pending human video inspection, never established plot events.
- stage6/review_packet.py: binds *original* Stage4 N05 sentence/claim/frame evidence IDs from Stage5 to observed video shot candidates. If a frame window overlaps a detected cut, it marks PENDING_HUMAN_CUT_BOUNDARY_REVIEW with BOTH candidate scenes instead of guessing. Invalid/unseen action claims and faked approval flags are rejected.
- stage6/offline_html.py: escapes model text, provides local-only audio and source video controls, plus in-browser export of unsigned notes. User feedback notes are not human-signed Engine21 approvals.
- qa/phase6_workbench.py: reusable CLI that SHA-pins the existing movie and Phase4/Phase5 QA sources, uses preinstalled FFmpeg and FFprobe to generate private original-audio listening excerpts, discovers scene cutpoints, renders JSON and offline HTML. Requires an empty output directory and does not overwrite prior user work.

## How to run safely

Run only on a machine with the original authorized movie, prior QA and FFmpeg:
python -B -X utf8 qa/phase6_workbench.py --repo PATH_TO_CHECKOUT --source PATH_TO_MOVIE --source-sha256 PINNED_MOVIE_SHA --prior-qa PATH_TO_PHASE4_QA --phase5-qa PATH_TO_PHASE5_QA --out NEW_EMPTY_PRIVATE_DIRECTORY

The output directory must be **outside Git**. Do not commit generated audio previews, transcripts, human review notes, screen frames, sample clips or literal character dialogue. Python and FFmpeg are reused from the existing approved Windows installation, no installations or downloads.

## Real user-authorized Fatman sampling result

- Three previously authorized disjoint 30-second excerpts (90s out of 5823.552s = 1.55% of film).
- 17 real English ASR entries and 17 private original movie audio preview WAVs, 16kHz mono and independently decoded.
- 22 FFmpeg automatic cutpoints across F01/F02/F03 (6/9/7), converted to 25 tentative scene intervals.
- Three original Stage5 review candidates retain N05 source claim IDs C0001, C0015 and C0022.
- Two original still-frame intervals overlap actual cutpoints, so no single scene was accepted by the agent: F01 ~00:09:04.917 and F02 ~00:37:25.000. F03 had one containing candidate scene.
- Two ASR entries explicitly prioritized for listening, one incorrect EN→VI postal-letters translation flagged; **zero** translations/script/voice/pilot approved.
- The final offline reviewer page is saved only on the Windows PC as fatman_offline_review_UNAPPROVED_v2.html. The page shows both ambiguous candidate scenes, original text/draft translation, playable 17 original-audio crops and 3 original movie excerpts.
- Independent local verification checked 17 WAV SHA+decode/sample rates, 3 clips, source film SHA and false-approval gates.

## Remaining limitations

- Automated cuts ≠ editorial scene boundaries, motion recognition or correct story narrative.
- 90s/97min sampling ≠ complete movie understanding; no blind scene retrieval quality benchmark.
- Phase6 creates human-review *materials*, but no person has yet listened to/approved the original 17 dialogues, corrected the Vietnamese translation or certified the 3 source shots.
- No approved review script, TTS voice, 90–120s pilot or production N00–N09 real-film end-to-end run.
- Genuine script/voice/pilot approval must originate from a trusted user/host mechanism; not this local HTML page or model output.

**Safety:** Existing film and previous QA data read-only; 11 original Agent Skills unchanged; Draft PR only, never merge main. No movie, audio, screenshots, transcripts, model weights or user paths published.
