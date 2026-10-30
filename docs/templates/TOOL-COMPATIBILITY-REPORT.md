# Host Tool/Model Compatibility Report — G0 to G1

**Documentation template only. Do not fill with assumptions. No host -> BLOCKED/NOT_TESTED.**

## Host and evidence
- Live device ID / hostname / connector:
- G0 read scope, observed_at and supporting command/log:
- OS / architecture / CPU / RAM:
- GPU vendor, model, VRAM / driver:
- Runtime candidate and actual backend test evidence (mark NOT_TESTED until approved):
- Disks and free space / planned tool-model-cache-temp budget:
- Installed tools, paths, versions, model weights, licenses:
- Desired workflow, language, duration, 9:16/16:9:
- Missing required inventory facts, status and reason:

## Dynamically selected candidates (populate only after G0)
| Capability | Installed path/version/test | Candidate selected | Status | Compatibility evidence OS/CPU/GPU/VRAM/disk | License/language | Download estimate | Why / fallback | Next required gate |
|---|---|---|---|---|---|---|---|---|
| ffprobe/FFmpeg | UNKNOWN | NOT_SELECTED | UNKNOWN | UNKNOWN | CHECK | UNKNOWN | after G0 | G0 |
| Shot detection | UNKNOWN | NOT_SELECTED | UNKNOWN | UNKNOWN | CHECK | UNKNOWN | after G0 | G0 |
| ASR if speech | UNKNOWN | NOT_SELECTED | UNKNOWN | UNKNOWN | CHECK | UNKNOWN | after G0 | G0 |
| Vision/retrieval | UNKNOWN | NOT_SELECTED | UNKNOWN | UNKNOWN | CHECK | UNKNOWN | after G0 | G0 |
| TTS if needed | UNKNOWN | NOT_SELECTED | UNKNOWN | UNKNOWN | CHECK | UNKNOWN | after G0 | G0 |
| Edit/Remotion if needed | UNKNOWN | NOT_SELECTED | UNKNOWN | UNKNOWN | CHECK | UNKNOWN | after G0 | G0 |

Statuses: INSTALLED_USABLE / INSTALL_PROPOSED / CONDITIONAL / INCOMPATIBLE / UNKNOWN. "Installed but not yet tested" is CONDITIONAL, never GPU PASS.

## G1 install proposal, separately authorized
- Reused installed components (no reinstallation):
- Proposed missing components, pinned revisions and official sources:
- Rejected/conditional candidates and reason:
- Licensing of software, model weights, voices and footage:
- Bandwidth/download size and disk cap:
- Exact destination and temp/cache/weights paths:
- Inference GPU/CPU and encoder test plan:
- Tool/API adapter gaps:
- User install approval: NOT_APPROVED
- Installation actions performed during G0: NONE
