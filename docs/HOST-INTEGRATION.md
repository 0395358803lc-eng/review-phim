# Host integration & operator handoff

GitHub stores instructions only; this policy does not authorize machine actions. For a real job, use the following **mandatory order**:
1. CONNECT: list current online Remote Desktop Commander devices; verify exact device_id, user-approved read scope and project root.
2. G0 HARDWARE READ_ONLY: inspect OS/architecture, CPU, RAM, GPU vendor/model/VRAM, driver, supported backend candidates, disks/free capacity. Log source commands and unknowns.
3. G0 INSTALLED READ_ONLY: inspect installed FFmpeg/ffprobe, Python/Node/Remotion, AI libraries, local model weights/paths/versions, GPU runtime and encoder availability. Do not reinstall tools that are usable.
4. Capture job objective, authorized rights, language, duration, aspect and local-first constraints. Do not process source media before PROCESS_APPROVED.
5. Only **after** G0, create [host-specific compatibility matrix](HARDWARE-FIRST-SELECTION.md), recording INSTALLED_USABLE / INSTALL_PROPOSED / CONDITIONAL / INCOMPATIBLE / UNKNOWN. Prefer the smallest adequate compatible stack. Do not substitute static TOOL-REGISTRY for this report.
6. G1 PROPOSE: present exact missing dependencies, pinned versions, download source/size, license/code/model/voice terms, disk root/cache policy, GPU/CPU fallback, adapter gaps and test commands. Obtain separate user approval before downloads/writes.
7. INSTALL_APPROVED: install only approved components to approved root; if missing CLI/API adapter, report GAP_ADAPTER rather than treating Markdown as code. No implicit driver updates or global installs.
8. RUNTIME TEST: after appropriate PROCESS permission, run a short authorized sample to test FFmpeg probe/encoder, shot extraction, ASR when speech exists, VLM/evidence delivery, TTS if needed, and actual GPU/CPU behavior. Record measurements, versions and failures.
9. PROCESS: when prerequisites PASS, follow ORCHESTRATION.md for full video pipeline, artifact manifests and QC; failures return to selection and renewed approval where scope changes.
10. HANDOFF: report hashes, paths, model/tool versions, QC and rights. No upload or publish without independent permission.

**Location decision:** No project root has been approved for this repo. Previous devices or paths from unrelated jobs do not grant access. Files, weights, caches, temp and outputs must honor approved storage scope.

**Remote limits:** A connected machine path does not mean ChatGPT can see/hear media. Transfer approved actual frames/audio/transcript through supported connector operations, or mark observation NOT_TESTED.

## Bằng chứng từ host trở lại agent
Mọi adapter chuyển frame/clip/audio phải theo [EVIDENCE-BRIDGE-CONTRACT.md](EVIDENCE-BRIDGE-CONTRACT.md). Nếu bridge không cho phép quan sát đoạn nguồn, ghi GAP_EVIDENCE_BRIDGE / NOT_TESTED, không coi mô tả VLM là VERIFIED.
