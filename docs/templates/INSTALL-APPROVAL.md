# Installation proposal — user approval required
## Scope
Device name/id:
Project root (approved drive):
Source path read-only:
Installation/write paths:
Disk cap (models + tools + cache + temp):
Need Internet? exact domains/purposes:
Permission window and operations:

## Dependencies
| component | current? | proposed pinned version | download size estimate | license/weights terms | target path | GPU backend | smoke test |
|---|---|---|---|---|---|---|---|
| FFmpeg | UNKNOWN | PROPOSED | UNKNOWN | CHECK | tools/bin | CPU/encoder test | ffprobe + short encode |
| PySceneDetect | UNKNOWN | PROPOSED | UNKNOWN | CHECK | tools/envs | CPU | sample shot table |
| ASR model | UNKNOWN | PROPOSED | UNKNOWN | CHECK | tools/models | TESTED BACKEND ONLY | sample transcript |
| Remotion | UNKNOWN | PROPOSED | UNKNOWN | CHECK | tools/envs | renderer check | sample template |

## Required decisions
- [ ] Approve exact device and writable root
- [ ] Approve model/library versions & licenses
- [ ] Approve downloads and bandwidth/disk budget
- [ ] Approve required secrets/credentials approach (never print)
- [ ] Approve GPU fallback quality and speed tradeoffs
- [ ] Approve development of any missing adapters outside Brain-Only skill

No boxes checked by the assistant; only explicit user authorization unlocks the scope.
