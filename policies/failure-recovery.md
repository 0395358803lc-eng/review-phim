# Failure & recovery playbook

- ASR low confidence: replay segment, inspect, retry limited larger/specialist ASR; don't invent words.
- Speaker ambiguous: nearby shots and voice evidence; label UNKNOWN if unresolved.
- Visual action ambiguous: inspect multiple time-adjacent frames or brief clip, not single frame inference.
- No clip matching sentence: retrace evidence, rewrite to supported claim or permitted conceptual B-roll.
- Narrative contradiction: inspect earlier/later scene, compare time vs causal order; block disputed assertion.
- TTS pronunciation or subtitle drift: regenerate affected sentence, align final audio and re-render impacted portion.
- Encoder failure: inspect available encoders; CPU fallback after approval of performance/quality change.
- OOM/disk full: free resources within permitted root only, reduce batch/temp; never delete source or unrelated cache.
- Remote command timeout: check process list/pending call and artifact hashes; don't duplicate side effects.
- Rights unresolved: prevent publication, mark DRAFT / RIGHTS_REVIEW.
- Multiple retries same failure: FAIL/BLOCKED with logs and clear human action. Max automatic retries and timeouts specified per job approval.

For every recovery: record cause, attempted mitigation, command scope, input/output hashes, measurements, final status. No success message based solely on initiating a process.
