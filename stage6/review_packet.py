"""Unapproved, evidence-locked human review request; never a production signature."""
from __future__ import annotations
import math
import re
from stage5.translation import HEX64,EVIDENCE_ID

# We cannot prove causality or these actions from a still. This is not a
# vocabulary-based 'truth checker': everything permitted is ALSO unapproved.
_UNSEEN_ACTION=re.compile(
    r"\b(killed|murdered|steal|stole|shoots?|fired|gunfire|exploded)\b"
    r"|bắn\s+chết|đã\s+bắn|nổ\s+súng|giết\s+người|đánh\s+cắp|thủ\s+tiêu|sát\s+hại",
    re.I)

def _number(v):
    return type(v) in (int,float) and math.isfinite(v)

def build_review_packet(source_sha256:str,storyboard:dict,catalog:dict,
                       proposed_scenes:dict,dialogue_queue:dict)->dict:
    if not isinstance(source_sha256,str) or not HEX64.fullmatch(source_sha256):
        raise ValueError("Invalid original movie SHA")
    if not isinstance(storyboard,dict) or storyboard.get("source_sha256")!=source_sha256:
        raise ValueError("Storyboard source SHA mismatch")
    if storyboard.get("ready_to_render") is not False:
        raise ValueError("No real script, voice or video approval")
    if not isinstance(proposed_scenes,dict) or proposed_scenes.get("source_sha256")!=source_sha256:
        raise ValueError("Scene source SHA differs")
    if not isinstance(dialogue_queue,dict) or dialogue_queue.get("source_sha256")!=source_sha256:
        raise ValueError("Audio review source SHA differs")
    if dialogue_queue.get("script_or_voice_approved") is not False:
        raise ValueError("Forbidden untrusted approval in dialogue queue")
    if not isinstance(catalog,dict) or not isinstance(storyboard.get("shots"),list) or not storyboard["shots"]:
        raise ValueError("Missing source catalog or storyboard shots")
    scenes=proposed_scenes.get("scenes")
    if not isinstance(scenes,list) or not scenes:
        raise ValueError("Missing source scene candidates")
    cuts={}
    for sc in scenes:
        if not isinstance(sc,dict):raise ValueError("Malformed scene")
        sid=sc.get("scene_id")
        if not isinstance(sid,str) or not EVIDENCE_ID.fullmatch(sid) or sid in cuts:
            raise ValueError("Duplicate or malformed source scene ID")
        if sc.get("status")!="AUTO_SCENE_CANDIDATE_PENDING_VIDEO_REVIEW":
            raise ValueError("Scene unexpectedly human approved")
        a,b=sc.get("source_interval_s",[None,None])
        if not _number(a) or not _number(b) or not 0<=a<b:
            raise ValueError("Scene source time invalid")
        cuts[sid]=sc
    reviews=[]
    seen_sentence=set()
    seen_claim=set()
    for shot in storyboard["shots"]:
        if not isinstance(shot,dict):raise ValueError("Malformed original N05 shot")
        sid=shot.get("sentence_id")
        cid=shot.get("claim_id")
        evid=shot.get("source_evidence_id")
        if (not isinstance(sid,str) or not EVIDENCE_ID.fullmatch(sid)
            or not isinstance(cid,str) or not EVIDENCE_ID.fullmatch(cid)):
            raise ValueError("Missing original sentence or claim ID")
        if sid in seen_sentence or cid in seen_claim:
            raise ValueError("duplicate original N05 sentence or claim ID")
        seen_sentence.add(sid);seen_claim.add(cid)
        if shot.get("source_sha256")!=source_sha256:
            raise ValueError("Original shot source SHA differs")
        if not isinstance(evid,str) or evid not in catalog:
            raise ValueError("Selected frame evidence absent in original catalog")
        row=catalog[evid]
        if row.get("kind")!="visual" or row.get("source_sha256")!=source_sha256:
            raise ValueError("Selected source evidence from wrong modality or movie")
        a,b=row.get("start_s"),row.get("end_s")
        if not _number(a) or not _number(b) or not 0<=a<b:
            raise ValueError("Source frame evidence time invalid")
        bounds=shot.get("source_interval_s")
        if not isinstance(bounds,list) or len(bounds)!=2 or not all(_number(v) for v in bounds):
            raise ValueError("Missing exact source evidence time")
        if abs(bounds[0]-a)>.001 or abs(bounds[1]-b)>.001:
            raise ValueError("Stage5 source frame timestamp was replaced")
        text=shot.get("review_text")
        if not isinstance(text,str) or not text.strip() or len(text)>3000:
            raise ValueError("Original review sentence missing")
        if _UNSEEN_ACTION.search(text):
            raise ValueError("Unsupported action/causal claim cannot be proved from one still")
        if shot.get("model_source_visual_verification")!="QWEN_TENTATIVE_NOT_HUMAN":
            raise ValueError("Source visual model review not tentative")
        # Require a single *actual* detected shot candidate containing the
        # whole original frame range; a global movie segment must not be used
        # to silently swap footage from another authorized sample.
        containing=[sc for sc in cuts.values()
            if sc["source_interval_s"][0]<=a+.001 and b<=sc["source_interval_s"][1]+.001]
        overlaps=sorted((sc for sc in cuts.values()
            if sc["source_interval_s"][0]<b-.000001 and sc["source_interval_s"][1]>a+.000001),
            key=lambda sc:sc["source_interval_s"][0])
        if len(containing)==1:
            matched=containing
            sc=matched[0]
            scene_id=sc["scene_id"]
            scene_range=sc["source_interval_s"][:]
            scene_sample=sc["source_sample_id"]
            status="PENDING_HUMAN_VIDEO_REVIEW"
        elif len(containing)==0 and len(overlaps)>=2 and len({x["source_sample_id"] for x in overlaps})==1:
            # The prior Stage4 +/-0.1s still-frame window can straddle a
            # *real* FFmpeg cut. This DOES NOT permit us to choose either shot.
            matched=overlaps
            scene_id=None
            scene_range=[min(x["source_interval_s"][0] for x in overlaps),
                         max(x["source_interval_s"][1] for x in overlaps)]
            scene_sample=overlaps[0]["source_sample_id"]
            status="PENDING_HUMAN_CUT_BOUNDARY_REVIEW"
        else:
            raise ValueError("Original frame cannot be located in a source scene")
        reviews.append({"sentence_id":sid,"claim_id":cid,"source_evidence_id":evid,
            "source_frame_observation":row["text"],
            "source_frame_interval_s":[float(a),float(b)],
            "review_vi_candidate":text,
            "scene_id":scene_id,"scene_interval_s":scene_range,
            "scene_sample_id":scene_sample,
            "candidate_scene_ids":[x["scene_id"] for x in matched],
            "source_sha256":source_sha256,
            "review_status":status,
            "claim_human_verified":False,"scene_human_verified":False,
            "speaker_verified":False,
            "model_visual_check_only":True})
    sound=dialogue_queue.get("rows")
    if not isinstance(sound,list):raise ValueError("Missing dialogue review rows")
    seen_audio=set()
    audio=[]
    for row in sound:
        if not isinstance(row,dict) or row.get("source_sha256")!=source_sha256:
            raise ValueError("Audio source SHA mismatch")
        aid=row.get("id")
        if not isinstance(aid,str) or aid in seen_audio:
            raise ValueError("duplicate/invalid dialogue review ID")
        if row.get("review_status")!="PENDING_HUMAN_LISTEN":
            raise ValueError("Untrusted audio reviewer decision")
        seen_audio.add(aid)
        audio.append({"id":aid,"review_status":"PENDING_HUMAN_LISTEN",
                      "source_sha256":source_sha256})
    return {"schema_version":"6.0","source_sha256":source_sha256,
            "status":"PENDING_HUMAN_CONTENT_AND_SCENE_REVIEW",
            "visual_claims":reviews,"pending_audio_count":len(audio),
            "pending_audio_ids":[x["id"] for x in audio],
            "review_gates":{"script":"PENDING","voice":"PENDING","pilot":"PENDING"},
            "can_tts":False,"can_render":False,"signed_by_human":False,
            "visual_scene_accuracy_certified":False,
            "warning":"Model source matches and scene cuts are NOT narrative truth or voice/pilot approval"}
