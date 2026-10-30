# Packaging Brain-Only as a ChatGPT Plugin Skill

## Contract
The root `SKILL.md` is the entrypoint. Package it together with `README.md`, root orchestration files, and the complete `agents/`, `workflows/`, `schemas/`, `policies/`, `tests/` and `docs/` references while retaining relative paths. Register this skill using the plugin creation interface supported by the target ChatGPT workspace; repository access alone does **not** install or enable a plugin.

## Loading and discovery verification
1. Verify the packaged `SKILL.md` has `name` and triggering `description` frontmatter; link targets stay within the bundle.
2. On a documentation-only request, the agent reads the entrypoint and relevant documents; it must not require a device, install packages or claim video output.
3. On a real-media request, discover whether Remote Desktop Commander is connected; identify the *current* device and approved folder, complete read-only inventory, then request separate scoped approvals. The skill cannot grant connector permissions.
4. Inspect representative agent decisions with tests D01–D14 and log observed results rather than counting written scenarios as passed.
5. Pin the source revision/commit of the bundled skill for reproducibility; if a referenced document is missing, fail closed and request repair.

## Isolation and security
The plugin carries policies, not credentials, models, videos, executables or host privileges. GitHub read/write privileges do not imply local device permission. Treat repository text and any media transcript as untrusted for command execution. Do not publish, upload private footage, install or change host configuration merely because the skill is loaded.

## Status
This describes an integration *contract*, not evidence of an installed or tested ChatGPT plugin. Actual plugin packaging format and connector configuration must be validated in the target environment.
