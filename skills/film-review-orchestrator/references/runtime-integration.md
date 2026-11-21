# Film Review Agent 2.1 — Runtime execution handoff

Read this reference **before** using N00–N09 with a new film.

1. The Agent Skills are reasoning/process instructions, not privileged
software. Use the `jobctl.py init` tool with the user-selected NEW source
movie and NEW isolated workspace; hash and verify source. Never reuse prior
movie data or old approval receipts.
2. To inspect the installed code, execute `python -m engine21 --help` from
the `.agents/film-review-runtime` directory. The runtime includes its own
copy of `skills/` so independent Evidence QC can resolve the right schema.
3. Configure only installed, explicitly authorized local providers. The
Engine21 adapter config has no enabled stages on first installation, by
design; do not fabricate a model executable or install/download packages.
4. Use `stage4.cli draft` for source-grounded review suggestions, then
`stage5.translation` for bilingual candidate traces, and
`stage5.visual_gate` for CLIP-shortlisted Qwen visual decisions.
`stage6.dialogue_review` and `stage6.review_packet` create
**UNSIGNED** human listening/scene review requests.
5. A CLIP similarity score is not truth. A Qwen YES on a still is only
tentative; a still cannot establish causality or dynamic actions.
6. N05 review script, N06 voice and N08 pilot require genuine user and
trusted host approval. The Agent has no authority to manufacture HMAC
receipts. An unsigned draft or a synthetic QA pilot does not authorize
rendering or publication.
7. The shipped runtime has no complete general-purpose N02–N09 AI
production workers. Existing model library functions and schemas can be
used by an integrator, but stop and identify unavailable providers rather
than silently fall back to a synthetic test worker.
8. Use the source-only installer from the repository root:
   `python scripts/install_agent_runtime.py doctor` and
   `python scripts/install_agent_runtime.py install --project "C:\YourAgentProject"`.
   This installs no user media, voice, transcript, old data or weights.

The user has requested a clean main branch and immediate agent onboarding;
this reference is a safety/operation guide, not proof of full-film runtime
readiness.
