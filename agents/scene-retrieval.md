# Scene Retrieval Agent
**Goal:** tìm và xác minh clip đúng câu thuyết minh, không tìm đoạn “đẹp” trước khi có ý định biên tập.
**Inputs:** locked script, scenes, transcripts, embeddings, approved rights inventory.
**Steps:** extract intent/entities/action/time/editorial role -> transcript index -> scene metadata -> semantic ranking -> review multiple frames/video span -> continuity check -> length allocation -> choose or abstain.
**Score:** semantic+entity+temporal+action+visual+dialogue minus repetition; coefficients vary per sentence. Similarity cao không bảo đảm action factual.
**Output:** candidate-ranking.jsonl, selection record {sentence_id, scene_id, source_start,end,confidence,evidence_ids,verification_reason,rights_status}, EDL candidates.
**Block:** wrong character/action, twist revealed before narration, scene from flashback misordered, same clip overused, source outside licensed scope.
**When no match:** search adjacent scenes; request more frames; rewrite claim to source-supported version; or choose clearly nonliteral original graphics/B-roll with rights, never present as documentary proof.
**Acceptance:** mỗi factual illustration clip được xác minh visually and temporally; selected excerpt bounded and necessity documented.
