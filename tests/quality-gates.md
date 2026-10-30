# Quality gates and blocking logic

| Gate | Required evidence | Blocking failure |
|---|---|---|
| G0 | online device + observed CPU/RAM/GPU/VRAM/OS/driver/disk **and installed tool/model inventory** in approved scope | offline/wrong device; critical inventory unknown -> BLOCKED |
| G1 | G0-grounded host compatibility matrix, versions/license/size/backend/fallback, explicit user-approved missing-tool installation plan | generic install list before G0; incompatible candidate; unapproved write/download |
| G2 | media probe, decoded sample, full shot coverage, hash | corrupt source/gaps |
| G3 | speech coverage; frame scene cards; narrative event references | unsupported critical event |
| G4 | script sentence-to-evidence, spoiler/rights signoff | fabricated factual sentence |
| G5 | VO actual durations; valid EDL; render/probe/subtitles | missing track/frames/wrong ratio |
| G6 | factual/editorial/technical/rights QC | unresolved critical fail or rights |
| G7 | source/job/final hashes, status and handoff manifest | missing file/non-verifiable outcome |

Per-check values measured wherever applicable: ASR word-error sample, scene retrieval top-k accuracy by manually labeled clips, subtitle timing error sample, max AV drift, silence/clipping detection, fps/duration/resolution, GPU memory/time. Thresholds must be set from sample/media requirements at G1 and reported; no invented universal numbers.

Status PASS = all required checks executed and passed with evidence; PARTIAL = some validated but blockers remain; FAIL = executed and did not pass; NOT_TESTED = not executed; BLOCKED = precondition absent. Global PASS requires stage-specific + rights signoff. Manual creative quality must cite examples, not numeric guarantees.
