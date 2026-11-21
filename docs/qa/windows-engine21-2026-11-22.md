# Windows acceptance report — Execution Engine 2.1 (Phase 2)

**Date:** 2026-11-22 (Asia/Bangkok)  
**Machine:** DESKTOP-2GP3E41, Windows x64, Python 3.13.15  
**Base commit:** 1390a0e19e1a9dc28242470de6d64720c98f7813  
**Target:** Draft PR #5 on feature/execution-engine-2.1; main is not merged.

## Isolation

- QA directory: D:\Phim\__ENGINE21_QA_20261122 (new, separate from film workspaces).
- No user movie footage, timelines, source files or prior project outputs modified.
- No software installations, global PATH/driver/OS changes.
- Used existing Python 3.13.15, Git 2.55.0.windows.5, FFmpeg/FFprobe 9.0.2 via process-local PATH.
- Test generated a synthetic 1.2 s MPEG-4/AAC MP4 and WAV, not a real movie.
- HMAC approval receipts are entirely **test-only**, not proof of human consent.

## Acceptance results

| Check | Observed |
| --- | --- |
| Initial Windows unit suite | 29 discovered; 1 ERROR due missing optional PyYAML; 1 Windows symlink test skipped |
| After stdlib-only test correction | **29 discovered; OK (skipped=1); exit 0** |
| Independent CLI full synthetic N00–N09 | PASS |
| N01 prior to N00 | Blocked as expected |
| N06 absent/forged/test-only valid HMAC receipts | Blocked / blocked / DONE |
| N08 missing / test-only valid pilot approval | Blocked / DONE |
| N00/N06/N08/N09 real FFmpeg media checks | PASS |
| N07 source-anchored synthetic semantic evidence map | PASS (not proof of movie semantics) |
| Tamper N01 output after DONE | N01 + descendants STALE, independent N02 stays DONE |
| Tamper synthetic source after DONE | source_intact=false, prior DONE results invalidated |
| Simulated RUNNING interruption + inspect | INTERRUPTED, resumed via retry attempt 2 to DONE |
| Actual subprocess 1 s timeout | FAILED without false success |
| Windows NTFS junction escaping job workspace | Rejected; no lock file written outside job |
| Eleven original Agent Skills | Byte-for-byte unchanged from branch baseline |

**Integrated QA:** 25/25 scenarios passed, zero skipped, on machine DESKTOP-2GP3E41. Full machine-specific report stays outside the repository at D:\Phim\__ENGINE21_QA_20261122\runs\qa-00040d4fd6de\qa_result.json.

**Independent N09 media verification:** FFprobe detects MPEG-4 video + AAC audio, duration 1.200000 s, 10318 bytes. FFmpeg full decode -xerror exited 0. SHA256: 99c8e57743d6e891d33b7f189a71bf4904021f52a391a7fd107f035d5a0dd56f.

## Reproduce on an authorized Windows machine

Run from a clean clone with Python + FFmpeg already installed, keeping all QA content in a **new isolated folder**.

~~~powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:TEMP = "D:\Phim\__ENGINE21_QA_20261122\tmp"
$env:TMP = $env:TEMP
$env:PATH = "<already-installed-ffmpeg-bin>;" + $env:PATH

python -B -X utf8 -m unittest discover -s tests -v
python -B -X utf8 qa\windows_acceptance.py --qa-root "D:\Phim\__ENGINE21_QA_20261122"
python -B -m engine21 --help
~~~

Run the release validator against a **clean export** of Git-tracked and intended new source files, not against a test working copy containing ignored __pycache__. Strict ZIP validation still rejects packaged cache, raw films, models and user data.

## Defect and regression correction

The test-only PyYAML import in tests/test_skillpack.py caused Windows baseline failure because PyYAML was not installed (and is not a production requirement). Replaced the two-field frontmatter read with a standard-library parser consistent with scripts/validate_release.py. Existing test demonstrated RED; rerunning produced GREEN, without installing dependencies. This changes only the test, not any of the 11 skill instructions.

## Remaining risks and scope boundary

1. This phase tests **synthetic execution behavior** only, not actual Whisper/CLIP/Qwen3-VL/VieNeu/FFmpeg editing adapters or semantic alignment of a full movie.
2. Production signing authority requires true OS isolation: an unrestricted agent must not read the HMAC key or create trusted approval receipts. Test signatures are explicitly not user approvals.
3. Host-configured adapters can execute arbitrary code with their granted OS rights; the engine is **not** a sandbox.
4. Original symlink test skips due Windows privileges; Windows junction/path-escape test ran and passed.
5. Adapter installation and full real-film integration remain subsequent phases, separate from this engine-core QA.
6. No merges to main. Request manual review of Draft PR #5 first.

**Verdict:** Synthetic Windows acceptance PASSED within the stated boundaries. No claim of automated real-film readiness.