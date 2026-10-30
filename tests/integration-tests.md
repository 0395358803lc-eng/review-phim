# Cross-stage integration contract tests

**IT01:** Media duration bounds all shot, transcript, evidence, EDL timestamps. Expected no negative/out-of-range intervals.
**IT02:** All narrative event references resolve to evidence and scene IDs. Causes/interpretation labeled.
**IT03:** Each script FACT sentence maps to VERIFIED evidence or is explicitly qualified; unsupported critical fact -> FAIL.
**IT04:** Every selected scene matches character, action and source chronology; reject merely similar frame.
**IT05:** VO sentence IDs and subtitle word IDs match script and final audio; no orphan segments.
**IT06:** EDL output duration matches actual narrated timing and source clip bounds, aspect from target profile.
**IT07:** State resume honors sha/config hash, stale outputs invalidated, pending remote task polled not duplicated.
**IT08:** Rights status carries from source to EDL to final QC, unresolved leads to BLOCKED publish.
**IT09:** Missing remote connector/missing model yields BLOCKED report, no fake success.
**IT10:** Incorrect filename with shell metacharacters stays data, never executable command.

Artifacts in repo are instructions and synthetic fixtures, not a real test execution. Mark this suite NOT_TESTED until real connector, dependencies and permitted video are available.
