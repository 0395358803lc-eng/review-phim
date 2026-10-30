# Brain-Only Validation and Plugin Readiness Design (2026-10-30)

## Intent
Make the existing documentation-only review-phim skill easier to package, audit, and safely execute through a separately connected host without pretending that Markdown is a video runtime.

## Keep unchanged
One root SKILL.md with selectively loaded agents/workflows; ChatGPT is orchestrator; Remote Desktop Commander is a separate authorized bridge; hardware-first inventory and distinct READ_ONLY/INSTALL/PROCESS/PUBLISH approvals. No model weights, media files, host access, publishing, auto-merge or unapproved installation.

## Approaches
A. Replace Markdown with a Python video pipeline: stronger runtime but violates Brain-Only and forces dependencies. Rejected.
B. Documentation-only wording edits: smallest change but misses objective regressions. Rejected.
C. Preserve Markdown and add a dependency-free validation harness, explicit plugin packaging contract, host adapter/evidence protocol, and targeted docs repairs. Selected.

## Deliverables
- Automated document validation: required entrypoint/frontmatter, Markdown links, fenced JSON examples, stage roles, and basic envelope contracts. Explicitly distinguish syntax checks from video runtime tests.
- Plugin integration guide: bundle root SKILL.md plus referenced files, ensure paths remain resolvable, test discovery and no implicit permissions. A GitHub URL is a source, not an installed plugin.
- Host adapter/evidence bridge contracts: precise inputs, outputs, failure/unknown states, allowed scopes, command-result observations, media verification requirements and no false VERIFIED claims.
- Fix the roadmap table formatting. Test the validation harness on this repo, record actual outcomes.
- GitHub Actions lightweight docs-only checks, without requiring any private host or film.

## Non-goals
No full implementation of ASR, FFmpeg adapters, video processing, model benchmarking, rights certification or plugin installation. These remain separate host-approved projects.

## Acceptance
Validator returns exit 0 for compliant repository and nonzero on deliberately broken fixture; every claim about test success is backed by an actual command. Changes remain isolated from main for review.
