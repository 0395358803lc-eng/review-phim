# Acceptance scenarios (must be run on a real authorized host; currently NOT_TESTED)

| ID | Case | Steps | Expected pass evidence |
|---|---|---|---|
| AT01 | media with dialogue | ingest/ASR/frames | probe valid + timed transcript verified sample |
| AT02 | silent visual video | ingest/vision, skip ASR | no fabricated dialogue, scene cards complete |
| AT03 | multiple speakers | diarize + compare source | cluster IDs stable, unknown names flagged |
| AT04 | fast scene changes | PySceneDetect + sample review | monotonic shots and no unexplained gaps |
| AT05 | intentionally ambiguous action | try retrieval | abstain/re-review, not assert false action |
| AT06 | nonlinear narrative | graph screen/story order | no false causal link; chronology notes |
| AT07 | wrong visual candidate | rank and inspect | reject high similarity but wrong action |
| AT08 | vertical 9:16 | crop+caption preview | main subject safe and captions visible |
| AT09 | interrupted render | process status + resume | no duplicate job, outputs checked |
| AT10 | GPU unavailable | backend detection + fallback | CPU path logged, no false GPU claim |
| AT11 | missing rights proof | rights gate | blocked publish, DRAFT labeled |
| AT12 | end-to-end permitted sample | all stages + QC | final MP4 exists + hashes/probe + approvals |
| AT13 | no connected host/inventory | ask for machine-specific installation list | UNKNOWN/BLOCKED, no guessed list |
| AT14 | CPU-only host | run hardware-first candidate selection | CPU-compatible stack and explicit limitations; no fake CUDA/NVENC PASS |
| AT15 | working tool already present | inspect installed version and state | reuse, do not reinstall |
| AT16 | hardware strong but disk/license inadequate | assess tool candidates | incompatible or conditional candidates excluded from proposed installation; approval blocked |

Test report includes device, source SHA256, versions, fixtures, exact commands, start/end, logs paths, expected/actual, reviewer and verdict. Do not mark PASS without executing.
