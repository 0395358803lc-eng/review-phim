# Hợp đồng truyền dữ liệu giữa các bước

## Hợp đồng tiền xử lý: host tool selection
Trước công đoạn Ingest của job thật cần có báo cáo inventory READ_ONLY theo device_id và [host compatibility report](templates/TOOL-COMPATIBILITY-REPORT.md) nêu rõ dữ liệu quan sát, lựa chọn công cụ phù hợp, tool/model đã có, những thứ cần cài, giới hạn và trạng thái phê duyệt. Không được suy diễn bằng chứng kiểm kê từ một catalog tĩnh. Xem [Hardware-First](HARDWARE-FIRST-SELECTION.md).

## 1. Artifact chain (reference, not files generated yet)

| Stage | Bắt buộc vào | Bắt buộc ra | Consumer |
|---|---|---|---|
| Ingest | source authorized | media.json, source hash | visual / audio |
| Shot / Scene | media, optional transcript | shots.jsonl, scenes.jsonl, frame manifest | narrative, retrieval |
| ASR | media audio | transcript.jsonl, alignment flags | narrative, script |
| Evidence | scenes, transcript, frames | evidence.jsonl + source refs | narrative, script, QC |
| Narrative | evidence + scene timeline | narrative.json (events, edges, identities) | script |
| Script | narrative, evidence, brief | script.json with claims | retrieval, TTS |
| Retrieval | script, evidence, rights | candidate list, selection manifest | editing |
| TTS / Captions | locked script | voice segments, alignment and SRT | editing |
| Editing | EDL, approved clips/VO | preview/final media + probe | QC |
| QC | all upstream artifacts | qc.json, handoff manifest | user approval |

## 2. Mandatory envelope
Each JSON document should include schema_version, job_id, source_sha256, generator metadata, produced_at. JSONL records need either the same fields per row or a manifest that makes the contract unambiguous; consumers must know which representation they are reading. Use the [schemas](../schemas/) documents as normative definitions, noting example payloads marked synthetic.

### Referential integrity
- Every evidence_id refers to an observable item and exact source/time window.
- Every scene_id refers to one or more real shot_id records and keyframes when available.
- Every factual sentence_id links verified evidence or becomes blocked/rewritten.
- EDL selection maps to sentence_id, rights_status and source interval.
- No source media, images or personally sensitive logs committed to this public repository.

## 3. Uncertainties and contradictions
- VERIFIED means evidence directly supports the specific claim, not model's confidence.
- INFERRED is a justified inference and must remain qualified.
- UNSUPPORTED is disallowed for essential factual script beats.
- Distinguish confidence, source provenance, character identity and editorial approval.
- Each unresolved question has impact and needed follow-up evidence.
- A pipeline run may be technically PASS and still fail editorial or rights QC.

## 4. Versioning and compatibility
- Schema changes affecting mandatory fields require schema_version update and migration mapping in docs.
- Downstream parser refuses unknown breaking major versions unless adapter validated.
- Tool/model revision and config hash travel with artifacts; stale input hash invalidates dependent outputs.
- All time values are source-video-clock seconds, half-open ranges [start, end). Convert any VFR or sample-based offset explicitly.

## 5. Future handoff contract
A completed run must include source hash, chain of artifact hashes, logs with actual versions/commands, editorial and technical evaluation, rights inventory, owner approvals where needed, final media probe, and unanswered issues. For documentation-only delivery, the handoff consists of GitHub commit and DOC-QA, not media evidence.
