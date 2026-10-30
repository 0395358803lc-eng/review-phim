# AI Video Review Skill Implementation Plan

> For agentic workers: implement one task per review gate, using working host evidence when applicable.

**Goal:** deliver a reusable Brain-Only skill in GitHub, then prove its orchestration with a real, user-authorized video on a selected machine.

**Architecture:** Markdown skill roles and workflows orchestrate local tools by authorized remote connector; time-aligned JSON evidence is source of truth. Software/model artifacts remain outside git.

**Tech Stack:** Markdown, JSON contracts, FFmpeg, PySceneDetect, faster-whisper/WhisperX, optional local VLM/pyannote/SigLIP, Piper or verified TTS, Remotion, Remote Desktop Commander.

**Spec:** docs/superpowers/specs/2026-10-30-review-skill-design.md

## Global constraints
- No host mutation or install until explicit approval.
- Brain-Only, local-first; all primary factual claims evidence grounded.
- No publishing, secrets or copyrighted video assets in public repository.
- Separate READ_ONLY/INSTALL/PROCESS/PUBLISH permissions.

## Review focus
- Silent inputs skip speech, no invented dialogue.
- Nonlinear/flashback scene order remains distinct from narrative order.
- VLM hallucinations produce INFERRED/UNSUPPORTED, never automatic verified.
- Mismatched clip selected on semantic score alone must be rejected.
- Remote command timeout must not cause duplicate side effects.

## Tasks & acceptance
- [x] **Task 1: Repo inventory + independent feature branch.** Proof: initial README-only tree; branch feature/agent-orchestrated-brain-v1.
- [x] **Task 2: Brain + architecture and operator policies.** Files: SKILL.md, ARCHITECTURE.md, ORCHESTRATION.md, TOOL-REGISTRY.md, ENVIRONMENT-POLICY.md. Verify links by listing GitHub tree.
- [x] **Task 3: Agent roles and workflows.** Files: agents/*.md, workflows/*.md. Verify each contains inputs/output/acceptance or defers to common stage machine.
- [x] **Task 4: JSON data contracts, rights/gpu/error policies, QA templates.** Files: schemas/*.md, policies/*.md, tests/*.md. Verify syntactic examples and internal references.
- [ ] **Task 5: Remote READ-ONLY inventory on approved device/root.** Record device, versions, capabilities, logs; no write.
- [ ] **Task 6: Select/install tool stack after approved manifest.** Validate licenses/checksums, GPU smoke tests.
- [ ] **Task 7: Audio+vision and evidence store on rights-cleared video.** Run ASR/keyframe/scene tests and verify outputs against source.
- [ ] **Task 8: Narrative graph and script/clip retrieval.** Run AT05/AT06/AT07; inspect errors.
- [ ] **Task 9: Local TTS/EDL/Remotion/FFmpeg render.** Produce output with technical reports.
- [ ] **Task 10: Complete QC and handoff.** Run AT01–AT12 as relevant, record actual results, release ZIP and human approval.

## Execution handoff
The GitHub phase is documentary implementation, NOT a proven host video pipeline. Choose machine and paths before Task 5; do not claim tasks 5–10 completed merely because plan exists. Review branch through PR; no auto-merge.
