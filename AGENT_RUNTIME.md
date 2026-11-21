# Film Review Agent 2.1 — SOURCE-ONLY Agent Integration

This main branch distributes **runnable skills, runtime modules and schemas only**.
It does not ship ANY prior movie, transcript, audio, video,
model weights, embeddings, approval receipt, signing key, generated scenes or test
fixtures. Source code is not the same as a ready-to-run local AI provider.

## One-time integration for a NEW agent project

From this repository (Python 3.10+ required):

```powershell
python scripts/install_agent_runtime.py doctor
python scripts/install_agent_runtime.py install --project "C:\YourAgentProject"
```

The project directory must already exist. The installer refuses to overwrite
previously installed skills or a runtime. It copies 11 skills to
`C:\YourAgentProject\.agents\skills` and installs matching runtime code to
`C:\YourAgentProject\.agents\film-review-runtime`.

To verify after installation:

```powershell
cd "C:\YourAgentProject\.agents\film-review-runtime"
python -m engine21 --help
python -m stage4.cli --help
```

Give your AI agent the `film-review-orchestrator` skill and ask it to read
`references/runtime-integration.md` first.

## Start a truly NEW movie workspace (never reuse old project artifacts)

```powershell
cd "C:\YourAgentProject\.agents\film-review-runtime"
python skills\film-review-orchestrator\scripts\jobctl.py init --source "X:\movies\NEW_MOVIE.mp4" --workspace-root "X:\NEW_WORKSPACES" --title "My movie"
```

Run `jobctl.py status` and `verify-source` with the returned NEW job path.

Execution Engine 2.1 can inspect and advance individual stages **only when**
a trusted host has configured local executable adapters and external approvals:

```powershell
python -m engine21 init --job "X:\NEW_WORKSPACES\my-movie-job" --config "X:\TRUSTED_HOST\adapters.json"
python -m engine21 inspect --job "X:\NEW_WORKSPACES\my-movie-job"
python -m engine21 run --job "X:\NEW_WORKSPACES\my-movie-job" --config "X:\TRUSTED_HOST\adapters.json" --stage N00
```

Paths are examples, **not bundled settings**. The adapter config must remain
outside the movie job; `examples/engine21-adapters.example.json` has an empty
`stages` map by design. Never put host approval secrets in that config or
give an AI agent a signing key. No other software or AI models are installed
by the setup script.

## Verified components vs. limits

| Component | Evidence-based status |
| --- | --- |
| 11 SKILL.md + jobctl, evidence schema | Importable/copyable instruction/CLI source, not 11 separate AI executables |
| Engine21 N00–N09 state, subprocess, SHA/recovery, gate checks | Ran 10/10 stages with explicitly configured local QA workers; not a fully automatic real-film pipeline |
| stage3 FFprobe, FFmpeg scene indexing, render and provider-contract adapter | Actual local FFmpeg runtime tested; only N00/N01/technical media jobs runnable without external AI |
| stage4 source-grounded timeline, extractive review draft and unsigned approval requests | Tested on user-approved samples; generated text must be independently checked for story accuracy |
| stage5 bilingual provenance, CLIP/Qwen visual gate, temporal hypotheses, multi-sentence storyboard | Tested with installed local AI models; source libraries are usable by an integrator but do not include a general production provider |
| stage6 SHA-bound audio review queue, video cut candidates, unsigned HTML viewer | Tested with original media/audio on authorized host; cannot confer real user approval |
| Real-model speech, vision, VieNeu TTS, semantic matching | Verified in local QA runs on host with installed model weights, **not automatically configured in this distribution** |
| Fully automatic 90–120s review of an arbitrary real film | **NOT YET VERIFIED**; real human script/voice/pilot approvals and production workers still required |

Run local AI model inventories and configure trusted adapter executables as
needed. Never claim model validity from `doctor`: it verifies importable code
and the local FFmpeg presence, NOT AI model inference or genuine approval.

## No old data rule

Use only the movie path and workspace selected for the new task. Never
automatically import directories from `D:\Phim`, previous ASR files,
storyboards, QA pilot clips, model caches or approval receipts. Runtime
output must stay under the **new isolated job**. Approval requests remain
unsigned until a person and authorized host explicitly approve them.

## Source tree policy

Included: `skills/`, `engine21/`, `stage3/`, `stage4/`, `stage5/`,
`stage6/`, `stage3_adapter.py`, reusable private
`qa/phase6_workbench.py`, two **empty** config examples and the
source-only installer.

Excluded from the source-only installer and ZIP (not necessarily old Git history): `tests/`,
`docs/qa/`, `docs/superpowers/`, synthetic demo workflows,
`qa/legacy_offline_worker.py`, prior state/approval files, prior movie
data, audio, video and model weights. The generic source code in
`qa/phase6_workbench.py` needs fresh inputs; it does not bundle them.
