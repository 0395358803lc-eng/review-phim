# Installed-plugin versus repository reconciliation (2026-10-31)

**Status:** discrepancy documented; migration NOT complete. No device G1 permission or media permission follows from this branch.

## Evidence reviewed
- Repository main: README.md, SKILL.md, ORCHESTRATION.md, ARCHITECTURE.md and TOOL-REGISTRY.md fetched via linked GitHub connector.
- Installed skill: review-phim/ai-video-review-agent skill.md, LOCAL-AI-FIRST.md, CHATGPT-REVIEW-GATE.md, EVIDENCE-BRIDGE-CONTRACT.md, HOST-INTEGRATION.md, PRODUCTION-CONFIG-AFTER-G0.md.
- Device G0 in conversation: Windows 11 / i7-14700F / RTX 4060 ~8GiB / 31.79GiB RAM. No G1 install or media processing was authorized.

| Requirement | Installed plugin | Repository main | Migration rule |
|---|---|---|---|
| Five video-review niches | Required step 4 | Older source workflow | Preserve all five; no inference from filename |
| Source folder -> single video -> niche -> G0 | Strict sequence | Earlier G0-first intake | Adopt installed order |
| G1 and media processing approvals | Separate scopes | Existing broad gates | Keep the stricter installed gates |
| LOCAL_AI_FIRST workers | Documented | LOCAL-AI-FIRST.md absent | Port after review, never claim workers exist |
| Review after each stage | Required | Not fully specified | Port gate/receipts after review |
| Textual AI evidence vs direct media verification | Strict distinction | Partly described | Never mark text-only as film VERIFIED |
| Host runtime | Skill documentation only | No production daemon | New code stays uninstalled and inactive |

## Safe migration sequence
1. Compare exact plugin-release file contents with current repository; record hashes and differences before replacing any old document.
2. Add contracts and isolated runtime modules with mock-only tests to a feature branch.
3. Port selected installed-plugin safety documents with provenance and review; never delete restrictions in main to simplify implementation.
4. Deploy or connect runtime only under separate G1 installation/write scope. Source processing requires PROCESS_APPROVED; private media transfer, VO/render, and publication are separate.

**Important:** The code in runtime/ is a synthetic-only foundation; it contains no real Windows path resolver, durable job journal, installed model adapter or authorization issuer. Do NOT wire SafeRunner to arbitrary process inputs or advertise it as ready for live media.
