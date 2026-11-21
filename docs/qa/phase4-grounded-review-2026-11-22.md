# Phase 4 — Evidence-grounded review & approval pack Windows QA

**Date:** 2026-11-22, Asia/Bangkok. **Host:** DESKTOP-2GP3E41, RTX 4060.  
**Scope:** feature/phase4-grounded-review-approval based on Phase3 PR #7; synthetic shapes and Vietnamese test voice. Old film/model directories only read, no installs/downloads, no main merge.

## What was implemented

1. N02 and N03 JSONL evidence source compiler with exact source SHA and time bounds; separate unpaired ASR events, flag conflicting visual observations.
2. Multi-event extractive review builder; every sentence has its own event, atomic claim and true source ID. Unsupported proposed plot/character/USB content is quarantined, never silently inserted.
3. Cross-stage N05 to N07 mapping binds the ORIGINAL claim and evidence ID to a selected time-bounded shot and actual sentence audio timestamps; independently validates multi-sentence evidence. A legacy utility variable-shadowing defect that crashed on the second sentence was reproduced and fixed.
4. Human-facing request writer for script/voice/pilot with actual Engine21 approval subject SHA, but with NO signing key, signature or authorization.
5. Synthetic QA-only looping-video renderer preserves 100% of narration where source imagery is shorter.
6. SHA pinning of Stage4 source modules, the QA worker and the semantic validation utility for trust-bound provider execution.

## Real GPU integration evidence (the input media is synthetic)

A fresh Engine21 N00–N09 run using already-installed local Whisper large-v3-turbo, Qwen3-VL-2B, VieNeu v3 Turbo and CLIP ViT-B/32 reported:
- **10/10 stages DONE; 13/13 CLI outcomes as expected**, including N06 and N08 attempts without approvals correctly denied.
- Stage N04: real ASR/vision input joined as source evidence; N05: one extractive QA sentence, **NOT full-film narration**.
- N05 and N07 exact sentence ID, original claim ID and evidence ID all matched by actual file read-back.
- TTS WAV **2.56 seconds**. Final MP4 **2.583333 seconds**, 51,329 bytes, MPEG-4 + AAC, no omitted narration due to pilot truncation.
- MP4 SHA256: `dd46ad2ee210250874e98943b94c406cb782bf5ea057a18cd963f866d7d6fe56`. Both streams decoded with FFmpeg.
- **Three unsigned** approval request files saved with separate source-bound SHA subjects. Test HMAC signatures used only by QA engine harness; not user approvals.
- Job log: `runs/real-engine-97d26d2f6b/report.json` under the **new isolated Windows workspace**, not in GitHub. Full source media, WAV and signing test keys are NOT published.

## Test-driven bug finding

- Duplicate/fake source evidence and an unsupported actor/USB story are rejected or quarantined.
- Visual observations at the same time with conflicting captions cause unresolved marking rather than an unsupported direct visual assertion.
- Previously, `evidence_qc.validate_map` reused the `ids` variable for claim evidence and then crashed on the second sentence. A new test reproduced the issue, then the variable was renamed and the multi-sentence validator passed.
- Windows test read_text without explicit UTF-8 failed on Vietnamese accent encoding; test fixture now opens text explicitly as UTF-8. No product-code workaround was added.
- Synthetic pilot loop is explicitly labeled a test fixture only and rejects overwriting an existing MP4.

## Acceptance boundaries

The legacy model folder contains working pretrained weights and runtimes but no source long-film review assets in the previously audited analysis/review/shots/timeline/out folders. This phase **does NOT** certify long-form movie understanding, narrative creative accuracy, genuine voice/pilot user consent, scene selection accuracy on actual film or production OS sandboxing.

The source-first draft is intentionally conservative and may sound documentary/extractive rather than cinematic. QA N04 can index multiple events, but the Engine-backed QA N05 currently chooses one sentence while downstream TTS/matcher only accept one. Full multi-sentence end-to-end authoring/editing needs a separate implementation/film-sample review.

## Remaining release gates
- Separate written approval for a **named real-film source/sample**, with rights and test scope.
- Full multi-sentence narration audio alignment + footage selection tested on representative longer media, no invented shots.
- Host-operated genuine human approval interface/signer, project voice authorization, security isolation.
- Actual QA package and PR are **Draft**, never merge `main` without explicit approval.

## Final re-verification — pinned complete Stage4 code

The last run **after** extending provider SHA pinning to all imported Stage4 files and the legacy evidence validator is the authoritative technical acceptance for this branch. The prior 2.56s-voice run is retained in local QA history but is NOT the final acceptance run.

- Report under the isolated host root: `runs/real-engine-65508b3cc0/report.json`.
- **N00–N09 all DONE; 13/13 expected CLI outcomes**, including two denied missing-receipt attempts.
- N02 Whisper, N03 Qwen3-VL, N06 VieNeu, N07 CLIP used preinstalled real local GPU runtimes. N04/N05 remain source-extractive, not creative LLM.
- N05-to-N07 original sentence and claim/evidence IDs matched; source-bounded map verified independently (exit **0**).
- VieNeu narration **3.04 s**; final MP4 **3.041667 s**, 60,211 bytes, MPEG-4/AAC; independent FFprobe and FFmpeg full decode exit **0**.
- Final MP4 SHA256: `3c3cd56853cd99087b3327a1f2a257189450e5d7d0643428cb7697ef66a93bc2`.
- Three saved request files inspected directly: script, voice, pilot all have **no signature**, `human_approved:false`. Actual approval remains outstanding.
- Full source test discovery: **81 tests**, **80 passed, 1 Windows symlink privilege skip**, exit **0**.
- Clean source export: **86 files**, release validator PASS, git diff --check exit 0. Regenerate the export after documentation changes before publishing.

**Final verdict:** Phase4 evidence-first core, provenance matching, restricted approval-request channel and four real local AI runtimes are technically validated on generated input. Still NOT validated: real-film semantic fidelity, movie-length scene coverage, fully autonomous review writing, actual human approval or public video publication.
