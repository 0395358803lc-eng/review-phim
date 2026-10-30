# Host integration & operator handoff

GitHub only stores instructions; machine executes with explicit permissions. To start a real job:
1. Invoke connected Remote Desktop Commander to list devices and select current device ID.
2. Collect input video path, source rights, chosen working root, output format and constraints.
3. READ-ONLY collect disk/CPU/GPU/VRAM/drivers/OS and installed executable/model versions; save a grounded inventory report outside Git.
4. Produce plan with precise dependencies, sizes, licenses and GPU validation tests; request approval for install/write.
5. Install/configure pinned dependencies in user-approved root only. If model lacks callable CLI/API, document missing adapter; obtain approval for a separate host runtime. Skill Markdown never self-executes.
6. Verify a 10–30 second licensed sample for probe, cut detection, ASR, frame generation and artifact transfer readable by ChatGPT.
7. Only then run full job by gates in ORCHESTRATION.md, recording commands, artifacts and QC.
8. Deliver output/local paths/sha256 and status; do not upload or publish without separate instruction.

**Location decision:** No host project path has been approved for this repo. Prior machines/paths from other work are not implicit authorization. All tooling/model/cache/temp/output must honor newly approved storage policy.

**Remote tool limits:** Connecting to device does not automatically make MP4 bytes or audio perceptible to ChatGPT. Supply keyframes/transcript clips through connector media-capable read operations when available, else mark observation limitations honestly.
