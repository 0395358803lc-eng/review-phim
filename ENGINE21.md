# Film Review Agent — Execution Engine 2.1 (Phase 1)

**Status: development preview.** The 11 Agent Skills remain unchanged. This is a bounded local execution core with authenticated approval checks, a per-film state ledger, and independent media/evidence verification. It is **not** a completed Whisper/Qwen/CLIP/TTS/FFmpeg production pipeline.

## Components

- `engine21/state.py` — source SHA256 lock, OS process lock (POSIX/Windows), atomic state, ordered N00–N09 dependencies, stale output/descendant invalidation and recovery of interrupted tasks.
- `engine21/gates.py` — approval verifier bound to job ID + actual artifact digest + expiry, artifact filename/path/hash validation, FFmpeg full media decoding for N00/N06/N08/N09, N07 sentence-shot-map checks.
- `engine21/runner.py` — trusted allowlisted executable and `argv`, pinned configuration/input SHA256, bounded timeout/retry, unique attempt folders, fail-closed gates. **No shell execution.**
- `engine21/__main__.py` — one-stage-at-a-time CLI. Does not sign approvals, automatically cascade tasks, install tools, start background jobs or merge branches.

## Install and smoke-test

From repository root, Python 3.10+ and FFmpeg/FFprobe on PATH:

```bash
python -m unittest discover -s tests -v
python scripts/validate_release.py .
python -m engine21 --help
```

Legacy intake remains unchanged:

```bash
python skills/film-review-orchestrator/scripts/jobctl.py init \
  --source /authorized/original.mp4 --workspace-root /authorized/jobs --title "Sample film"
```

For an authorized host-owned adapter configuration (stored **outside** the job workspace), use:

```bash
python -m engine21 init --job /authorized/jobs/film-... --config /trusted/adapters.json
python -m engine21 inspect --job /authorized/jobs/film-...
python -m engine21 run --job /authorized/jobs/film-... --config /trusted/adapters.json --stage N00
```

**Important:** `examples/engine21-adapters.example.json` intentionally contains no runnable adapters. The host must provide actual installed executable paths and artifact-producing command implementations after an explicit environment inspection. CLI accepts one stage at a time; dependency and source checks block unsafe stages.

### Adapter contract

`/trusted/adapters.json`:

```json
{
  "schema_version": "2.1.0",
  "stages": {
    "N00": {
      "executable": "/absolute/path/to/approved-adapter",
      "argv": ["--source", "{source}", "--output-dir", "{output_dir}"],
      "timeout_seconds": 300,
      "max_attempts": 2,
      "retry_safe": true
    }
  }
}
```

Paths such as `{source}`, `{job}`, `{stage}`, `{output_dir}`, `{source_sha256}` are provided as literal argv substitutions, never a shell. The program receives `FRA_JOB`, `FRA_STAGE`, `FRA_OUTPUT_DIR`, `FRA_SOURCE`, `FRA_SOURCE_SHA256`, `FRA_REQUIRED_OUTPUTS`, `FRA_REQUIRED_CHECKS`. It writes its **own** checked outputs and `evidence.json` into `FRA_OUTPUT_DIR`. The declared artifacts must use paths relative to the job root, must reside in the current attempt directory, and must include the stage's expected filenames listed in `engine21/state.py:REQUIRED_OUTPUTS`.

Phase 1 only permits a trusted host-configured adapter binary. SHA256 of configuration and adapter executable/scripts are pinned on first attempt and rechecked before accepting results. No execution of downloaded or agent-generated binaries without host authorization. This restricts accidental or opportunistic misuse; it is **not** an OS sandbox.

### Human approvals

Before N06, the external human-facing supervisor must create signed `script.json` bound to SHA256 of **N05 evidence** and signed `voice.json` bound to SHA256 of `voice/approved_sample.wav`. Before full N08, it must create signed `pilot.json` bound to the actual, decodable `edit/pilot.mp4`. The approval receipt fields are:

```json
{
  "job_id": "film-sample-...",
  "gate": "pilot",
  "subject_sha256": "64-lowercase-hex-digits",
  "issued_at_utc": "2026-11-22T00:00:00+00:00",
  "expires_at_utc": "2026-11-22T00:10:00+00:00",
  "signature": "hex-HMAC-SHA256"
}
```

The signature is HMAC-SHA256 over the **five unsigned fields**, UTF-8 JSON sorted by key with separators `(',', ':')`. Receipt production is an action performed **outside** this repo by the user's trusted host UI after actual authorization. There is deliberately no production signing CLI in this package. The external host must ensure the agent cannot read the signing secret or write trusted approvals; otherwise the signature gives no trustworthy proof of human consent. The 2.0 `jobctl approve --reference` record alone is not accepted as a trusted approval by engine 2.1.

A trusted supervisor, not an unrestricted AI-agent shell, may invoke:

```bash
python -m engine21 run --job /authorized/jobs/film-... \
  --config /trusted/adapters.json --stage N06 \
  --receipts-dir /host-owned/receipts --host-key-file /host-only/hmac.key
```

Host-controlled permissions and process isolation are required; the engine cannot force that an arbitrary locally privileged agent lacks access to the key. An invalid/missing/expired signature or mismatching audio/script/pilot digest blocks the step.

### Recovering work

`python -m engine21 inspect --job ...` revalidates source/evidence/output hashes and dependencies. An interrupted `RUNNING` stage becomes `INTERRUPTED`. DONE artifacts that no longer match their stored SHA256 turn `STALE` and invalidate descendants. No files are automatically removed or overwritten. A clean, `retry_safe` adapter may be explicitly retried up to `max_attempts`; stale outputs need `--rerun-stale` and remaining budget. Unsafe retries require a new revision and operator approval.

Outputs are append-only in `.engine21/attempts/Nxx/0001/`, `0002/`, etc. The main 2.0 `job_state.json` is still present for compatibility; **engine 2.1 authoritative state is `.engine21/state.json`.** Do not use 2.0 `jobctl complete-stage` to override 2.1 verification or count it as a 2.1 approval.

### Limits / next phases

N00/N06/N08/N09 use `ffprobe` followed by full `ffmpeg` decode; this proves basic technical decodability, **not** perfect cinematic accuracy. N07 checks semantic ledger structure and source references; it cannot verify every character identity or emotion without real source-frame review. Phase 1 adapters are not installed and no real film was analyzed by the engine. Phase 2 must implement per-tool media/AI adapters and end-to-end real-film tests. Final user acceptance is distinct from a machine PASS.
