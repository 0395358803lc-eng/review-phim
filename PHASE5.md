# Phase 5 — Bilingual film evidence, CLIP → Qwen gate and multi-sentence storyboard

**Status:** code and synthetic Engine21 integration pass, real Fatman scene samples technically reviewed; real-film production **NOT approved**. Based on Phase4 Draft PR #8.

## Added modules

- stage5/translation.py: keeps immutable English ASR evidence (movie SHA, original text SHA, ID and source timecode), plus machine-created Vietnamese translation **candidates**. Duplicates, source mismatch, tampering, and model claims of human approval fail closed or quarantine.
- stage5/visual_gate.py: CLIP only retrieves source-frame candidates. A separate Qwen result for the exact claim text hash and exact source-frame SHA must be YES before output can be marked **TENTATIVE_VISUAL_CANDIDATE**. NO, UNCERTAIN, lack of evidence, mismatched sources and recognized single-frame motion claims remain unresolved.
- stage5/qwen_provider.py: existing offline Qwen3-VL model, CUDA only. Ambiguous freeform model output is parsed as UNCERTAIN, never YES.
- stage5/storyboard.py: handles multiple review sentences, preserves original N05 sentence and claim IDs and source timecodes. Without genuine human script/voice/pilot approvals, it is never marked ready to render. Original source-frame intervals do not prove continuous film actions.
- stage5/temporal.py: preserves ordered frames and Qwen temporal hypotheses. It does not certify motives, causal events, violence, or actor identity.
- qa/legacy_offline_worker.py: Engine N07 **now actually calls Qwen after CLIP**, validates the exact N05 claim against the same N03 movie-frame hash and refuses a NO/UNCERTAIN result; no CLIP top-1-only acceptance.
- qa/acceptance_engine_real_models.py: pins **both** CLIP and Qwen local model weights and all loaded Stage4/Stage5 Python source hashes.

## Workflow & limits

1. Verify source media and ASR hash/timecodes, then generate optional VI suggestions without overwriting original English or claiming a verified translation.
2. Build source-evidence event timeline, record atomic claims and generate tentative review sentences.
3. CLIP candidates → Qwen exact-claim visual check → fail closed on NO/UNCERTAIN or wrong frame; keep original claim/evidence IDs.
4. Prepare a multi-sentence storyboard, but do not infer voice timing or full scene coverage.
5. Only an external trusted human gate can approve real voice, script and pilot; no model verdict or test-only HMAC receipt substitutes for it.

**Synthetic** Engine21 N00–N09 with real local Whisper, Qwen, VieNeu and CLIP: 10/10 DONE, 13/13 expected results, Qwen YES in N07. **Real film** QA used three 30-second excerpts of Fatman and produced 17 unapproved VI translations, three tentative source scene anchors, two blocked unsupported claims and a three-sentence unapproved storyboard. See [sanitized QA](docs/qa/phase5-fatman-2026-11-22.md).

Still missing: independently reviewed English ASR and faithful VN translation, continuous film-length temporal action indexing, true review-sentence → scene benchmark, autonomous cinematic story writing, fully timed multi-sentence real-film TTS and human-approved pilot. No movie/media, transcripts, cache, weights or signing keys are in this repository. 11 original Agent Skills and main are unchanged.
