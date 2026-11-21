# Execution Engine 2.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Tasks use tests before implementation, and all changes stay on feature/execution-engine-2.1.

**Goal:** Implement verified Task Runner, State & Recovery Manager, and Evidence & Approval Gate.

**Architecture:** A new `engine21` Python stdlib package coordinates N00..N09 and reads the immutable 2.0 job manifest. Authenticated approvals, allowlisted adapters and fresh hash/media verification protect stage transitions. Each attempt is append-only and state writes are atomic.

**Tech Stack:** Python 3.10+ unittest, json, subprocess, hashlib, hmac, ffmpeg/ffprobe for stage-level media proof.

**Spec:** docs/superpowers/specs/2026-11-22-execution-engine-2.1-design.md

## Global Constraints
- Do not change any of the 11 `skills/*/SKILL.md` files, original media, or existing jobctl 2.0 behavior.
- Do not push to main. No production-grade claim until real media/AI integration tests pass.
- No user approval forged by CLI; approvals need an external trusted host signer.

## Review Focus
- Malformed adapter configuration cannot launch shell commands or escape output path.
- Crash recovery doesn't double-run side-effecting adapters.
- Changed DONE artifact always invalidates descendants without rewriting accepted outputs.
- HMAC signature, timing and subject hashes are verified independently.
- Stage-level claims cannot bypass real media decode and source/hash checks.

### Task 1: State & Recovery
**Files:** engine21/state.py, tests/test_engine21.py.
- [ ] Write tests for job startup, source hash change, stale artifact, DAG and interrupted run.
- [ ] Run tests, record failing RED.
- [ ] Implement atomic state, locks, reconciling and inherited invalidations.
- [ ] Verify GREEN tests.

### Task 2: Approval & Evidence Gate
**Files:** engine21/gates.py, tests/test_engine21.py.
- [ ] Write tests for bad signature, wrong subject, expiry and genuine receipt.
- [ ] Run RED.
- [ ] Implement host-signed HMAC verification and real artifact/media validators.
- [ ] Verify GREEN tests.

### Task 3: Bounded Task Runner
**Files:** engine21/runner.py, engine21/__main__.py, tests/test_engine21.py.
- [ ] Write tests for subprocess success/failure/timeout, allowed adapters, retries, resumability.
- [ ] Run RED.
- [ ] Implement safe argv executor and atomic state transitions.
- [ ] Verify GREEN tests and original suite.

### Task 4: Operational docs, independent review and branch delivery
**Files:** ENGINE21.md, README.md (append-only), tests and GitHub branch.
- [ ] Document host trust boundary, approval issuance, command examples and limits.
- [ ] Test from a clean checkout with FFmpeg fixture; run all unit tests and validate_release.py.
- [ ] Review security and file changes; verify 11 skills byte-for-byte.
- [ ] Push development branch and open PR, leaving main unchanged.
