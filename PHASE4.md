# Phase 4 — Grounded Review Drafting and Approval Requests

**Status: technical QA demonstrated on synthetic video.** This is a source-cited extractive review builder and host approval request protocol, **not** an autonomous feature-film storyteller or a service that can approve actions.

## Modules
- `stage4/evidence.py` — compile time-bounded visual observations and source-dialogue rows into multi-event timelines. The exact original SHA must match for every evidence item; duplicate IDs, invalid time ranges and missing observations fail closed. Multiple conflicting captions for the same time are marked `unresolved`.
- `stage4/review.py` — build multi-sentence, source-quoted narration draft with each atomic claim referencing a real observation or ASR ID. Candidate LLM sentences that add unsupported facts, claim nonexistent identities or cite nonexistent evidence are **quarantined** and excluded from review. Output is always **unapproved**.
- `stage4/matching.py` — validate N05 claims against N07 selected source shots and *actual* N06 sentence-level voice timestamps. No remapping claim IDs or swapping visual/dialogue evidence.
- `stage4/approval_requests.py` — prepare **UNSIGNED** requests for human review of `script`, `voice`, `pilot`, using Engine21's exact SHA subjects. Never contains keys, receipts or signature and cannot authorize Engine.
- `stage4/media.py` — repeat the source image **for synthetic QA only** to avoid cutting off TTS narration when the source clip is shorter; decode final audio/video independently. Never treat repetition as a film-edit technique.
- `stage4/cli.py` — portable, standard-library CLI for Agent Skills. No model API, installation or model download in this module.
- `qa/legacy_offline_worker.py` — N04/N05 now consume real job evidence and N07 uses actual N05 claim IDs instead of the prior hardcoded synthetic claim. Existing QA N05 emits **one sentence** to fit the currently limited N06/N07; multi-sentence drafts can be generated separately with the portable Stage4 library.
- `qa/acceptance_engine_real_models.py` — test-only Engine21 full-run harness; pins worker and ALL directly imported Stage4 source modules plus semantic validator by SHA. Existing local Whisper, Qwen3-VL, CLIP and VieNeu still used read-only.

## CLI examples

Create a new, human-review-pending draft from verified model data:

~~~bash
python -B -m stage4.cli draft --visual visual_observations.jsonl --asr transcript_vi.jsonl --source-sha256 <64-hex-source-hash> --source-duration 120 --output-dir ./new-draft-output
~~~

Optional author/model suggestions can be passed as `--proposals candidates.json`. A candidate may be automatically included only when it reproduces a literal source quote and cites the same source-bound ID; everything else is written to `quarantined_proposals.jsonl` for human review.

Prepare unsigned requests for external host approval, from a real Engine21 job:

~~~bash
python -B -m stage4.cli approval-request --job <Engine21-job-folder> --gate script
python -B -m stage4.cli approval-request --job <Engine21-job-folder> --gate voice
python -B -m stage4.cli approval-request --job <Engine21-job-folder> --gate pilot
~~~

These commands create files under `<job>/approvals/requests/`. The signer must be external to the AI agent with its own authentication, review UI and secret; the agent MUST NOT produce actual HMAC receipts. Engine21 already rejects unsigned requests as approvals.

**Important:** Stage N05's historic filename `review_final.txt` is an Engine artifact, **not a human-approved final review**. Existing N06 requires a separate actual script approval receipt.

## Acceptance and limitations

See [Phase4 Windows technical report](docs/qa/phase4-grounded-review-2026-11-22.md). The new E2E exercise uses a locally generated geometric shape video, preinstalled local model weights, a test-only signer and a synthetic voice preset. It does not verify actual movie characters, causality, story correctness, full-length clip retrieval or genuine human sign-off.

**Protected:** 11 original `SKILL.md` discovery files, old film data, model weights, main branch. One bug fix changes the existing semantic evidence *utility script* so it can validate more than one sentence; this does not alter the 11 skill descriptions. Work remains on a development branch and Draft PR.
