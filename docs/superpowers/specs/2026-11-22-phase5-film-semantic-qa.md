# Phase 5 — Source-locked bilingual evidence, verified visual retrieval and multi-sentence storyboard

**Date:** 2026-11-22. **Base:** Draft PR #8. Original 11 Agent Skills unchanged. User-approved Fatman (2020) film QA: 3 pre-existing distinct 30s samples of the 97-minute movie.

## Architecture
1. stage5/translation.py: English→Vietnamese candidate packs with original ASR ID, original English text SHA, original film SHA and timestamps. Candidate translations must NEVER be marked verified without human approval. Invalid, duplicate or shifted records fail closed.
2. stage5/visual_gate.py: CLIP proposes candidates, a separate Qwen visual YES/NO/UNCERTAIN per claim and candidate is required. Only YES may produce a TENTATIVE source-bound visual candidate; NO or uncertainty blocks. Qwen YES is not human visual truth. CLIP rank can be overruled when Qwen rejects top1 and positively verifies rank2, preserving original frame and claim IDs.
3. stage5/storyboard.py: map multiple original N05 sentences with original claims to selected source shots, all within original movie timecodes. If no user-approved voice, the result remains a plan and carries no fabricated audio timeline/production authorization. No swapping IDs.
4. stage5/temporal.py: sequence of ordered frame observations can be compared for visible differences, but model claims about firing, stealing, death or causality remain unverified. Frames cannot stand in for an independently inspected full video clip.
5. QA-only Fatman scripts read prior authorized film evidence in read-only mode and produce locally isolated reports. Model evidence must carry original movie SHA.

## Acceptance tests
- Wrong original source/English text SHA, duplicate ids, out-of-range timestamps and empty or forged translations fail closed or quarantine.
- CLIP shortlist is not ground truth: Qwen NO/UNCERTAIN blocks VISUAL_DIRECT; mismatched SHA or missing frame is denied, including unsupported action assertions.
- Storyboard for more than one claim preserves exact IDs and original timecodes, blocks missing claims/unsupported shots.
- Real local Fatman QA verifies previous 17 ASR, 9 Qwen captions, one misrank, three visual controls; real short multi-image temporal inference when practical.
- No production TTS, pilot, signed approval, user media/model publication. Main and 11 Agent Skills unchanged. Draft PR only.

## Remaining limitations
Existing Phase4 N02 is synthetic-Vietnamese-ASR only; N03 sees a still and QA N05/N06/N07 currently processes one sentence end-to-end. Phase5 bilingual candidate and storyboard components do not imply fully automated true movie narration or continuous scene-accurate video production.
