# Brain-Only Documentation Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce verifiable documentation checks and plugin/remote integration contracts without replacing Brain-Only.

**Architecture:** Keep Markdown as normative skill instructions and add standalone Python standard-library validation for docs. Execute external tools only through a separately authorized connector; host media actions remain out of scope.

**Tech Stack:** Markdown, Python 3 standard library, GitHub Actions.

**Spec:** docs/superpowers/specs/2026-10-30-brain-only-hardening-design.md

## Global constraints
- Preserve hardware-first and evidence-first gates.
- Never use repo instructions as host permissions.
- Do not install software, process source media, publish or merge main.
- Do not mislabel documentation checks as runtime tests.

## Review Focus
- Link to a directory must resolve, not be rejected for lack of file extension.
- Inline/external links must not be incorrectly considered missing files.
- Malformed JSON examples must produce a failing exit code.
- Invalid source hash/envelope must be detected without treating a synthetic fixture as live evidence.
- Missing connected host must not turn into a claimed successful runtime test.

## Task 1: Documentation validator and regression tests
**Files:** create `scripts/validate_docs.py`, `tests/test_validate_docs.py`; create `.github/workflows/docs-validation.yml`.
**Interfaces:** `validate(root: Path) -> list[str]` returns error messages; `main() -> int` reports check status.
- [ ] Write tests covering valid links, missing links, JSON syntax, and mandatory envelope fields; run failing tests.
- [ ] Implement validator with standard library; run unit tests green.
- [ ] Run validator against current repository and fix genuine docs defects.
- [ ] Add CI invocation of the same command.

## Task 2: Document practical plugin and evidence bridge contracts
**Files:** create `docs/PLUGIN-PACKAGING.md`, `docs/EVIDENCE-BRIDGE-CONTRACT.md`; update `SKILL.md`, `docs/USAGE-GUIDE.md`, `docs/HOST-INTEGRATION.md`.
**Interfaces:** Exact transfer records use job/device/source hashes, source interval, artifact hash, rights/scope, verification state and error status.
- [ ] Document packaging and connector responsibilities including a tested no-host outcome.
- [ ] Define permitted evidence transfer and independent verification versus model description.
- [ ] Link from entrypoint and host guide; verify documents.

## Task 3: Repair and verify documentation
**Files:** update `docs/IMPLEMENTATION-ROADMAP.md` and `README.md`.
- [ ] Fix roadmap table syntax and clarify scope of automated checks.
- [ ] Run unit tests and repository validator; record results.
- [ ] Review diff, leave branch for human PR approval; do not merge.
