"""Local human review web page with audio/video, unsigned feedback export.

All displayed ASR/Qwen/film descriptions are UNTRUSTED and HTML-escaped.
A reviewer's browser-side response is NEVER a signed workflow approval.
"""
from __future__ import annotations
from html import escape
from stage5.translation import HEX64,EVIDENCE_ID

def h(value)->str:
    return escape(str(value),quote=True)

def _uri(value:str)->str:
    if not isinstance(value,str) or not value.startswith("file:///"):
        raise ValueError("Only trusted local file source references are allowed")
    return h(value)

def render_review_html(dialogue:dict,packet:dict,
                       clip_uris:dict[str,str],frame_uris:dict[str,str])->str:
    if not isinstance(dialogue,dict) or not isinstance(packet,dict):
        raise ValueError("Invalid audio/review packet")
    movie_sha=dialogue.get("source_sha256")
    if not isinstance(movie_sha,str) or not HEX64.fullmatch(movie_sha) or packet.get("source_sha256")!=movie_sha:
        raise ValueError("Source SHA mismatch in HTML inputs")
    if not isinstance(clip_uris,dict) or not isinstance(frame_uris,dict):
        raise ValueError("Missing source clip/frame URI map")
    rows=dialogue.get("rows",[])
    claims=packet.get("visual_claims",[])
    if not isinstance(rows,list) or not isinstance(claims,list):
        raise ValueError("Invalid review rows")
    parts=[r'''<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Film Review Phase6 — review queue (UNSIGNED)</title>
<style>
:root{color-scheme:dark;font-family:system-ui,Segoe UI,sans-serif}
body{max-width:1040px;margin:0 auto;padding:28px 18px;background:#10141d;color:#f1f4f8;line-height:1.55}
h1{font-size:1.8rem}h2{margin-top:2.4rem}h3{font-size:1.06rem}
article{background:#1a2331;border:1px solid #344151;border-radius:12px;padding:16px;margin:15px 0}
small,summary{color:#bfccd8}.warning{color:#f4cf78}.tag{color:#9dd7e3}
audio,video{width:100%;max-width:800px;margin:.6rem 0}
video{max-height:360px}img{max-width:420px;max-height:260px;object-fit:contain}
label{display:block;margin-top:.6rem}select,textarea,button{background:#202c3d;color:white;border:1px solid #71839c;border-radius:6px;padding:.5rem}
textarea{width:95%;min-height:64px}button{cursor:pointer;padding:.7rem 1rem}a{color:#a7e0ff}
</style></head><body>
<h1>Fatman — Bảng kiểm chứng lời thoại và cảnh phim</h1>
<p class="warning"><b>UNSIGNED · PENDING HUMAN REVIEW.</b> Đây là dữ liệu AI đề xuất, KHÔNG phải nội dung review đã duyệt.
Phản hồi xuất ra từ trang này chỉ để ghi chú; không phải chữ ký phê duyệt script, voice hoặc pilot.</p>''']
    parts.append("<p>Mã SHA-256 phim gốc: <code>"+h(movie_sha)+"</code></p>")
    parts.append("<h2>A. Xem các đoạn phim nguồn</h2>")
    for sample,uri in sorted(clip_uris.items()):
        parts.append("<article><h3>"+h(sample)+" — đoạn nguồn cần kiểm tra</h3>")
        parts.append('<video controls preload="metadata" src="'+_uri(uri)+'"></video></article>')
    parts.append('<h2>B. Nghe đối chiếu lời thoại Anh → bản dịch Việt</h2>')
    for row in rows:
        id=row.get("id")
        if not isinstance(id,str) or not EVIDENCE_ID.fullmatch(id):
            raise ValueError("Unsafe ASR evidence ID")
        sample=row.get("source_sample_id")
        if sample not in clip_uris:
            raise ValueError("Original source clip missing for dialogue row")
        start,end=row.get("start_s"),row.get("end_s")
        if type(start) not in (int,float) or type(end) not in (int,float) or start>=end:
            raise ValueError("Invalid ASR source times")
        parts.append('<article data-kind="audio" data-id="'+h(id)+'">')
        parts.append("<h3>"+h(id)+" · "+h(sample)+" · "+h(f"{start:.2f}–{end:.2f}")+"s</h3>")
        parts.append("<p><b>Tiếng Anh (Whisper, chưa nghe xác nhận):</b> "+h(row.get("original_english",""))+"</p>")
        parts.append("<p><b>Tiếng Việt (Qwen, đề xuất):</b> "+h(row.get("translation_vi_candidate") or "(chưa có)")+"</p>")
        parts.append('<p class="warning">Ưu tiên: '+h(row.get("priority","CHECK"))+
            " · Lỗi cần xem: "+h(", ".join(row.get("risk_flags",[])) or "đối chiếu từng câu")+"</p>")
        parts.append('<audio controls preload="none" src="../media/audio/'+h(id)+'.wav"></audio>')
        parts.append('<label>Kết quả sau khi nghe <select data-result><option value="UNREVIEWED">Chưa kiểm tra</option>'+
            '<option value="LOOKS_CORRECT">Phù hợp (ghi chú, chưa duyệt)</option>'+
            '<option value="NEEDS_CORRECTION">Sai/cần sửa</option>'+
            '<option value="UNCERTAIN">Chưa chắc</option></select></label>')
        parts.append('<label>Ghi chú sửa lời thoại/bản dịch <textarea data-notes></textarea></label></article>')
    parts.append("<h2>C. Xác minh cảnh cho lời review nhiều câu</h2>")
    for row in claims:
        id=row.get("claim_id")
        if not isinstance(id,str) or not EVIDENCE_ID.fullmatch(id):
            raise ValueError("Unsafe claim ID")
        parts.append('<article data-kind="visual" data-id="'+h(id)+'">')
        parts.append("<h3>"+h(id)+" / "+h(row.get("sentence_id",""))+
            " · "+h(row.get("scene_id",""))+"</h3>")
        parts.append("<p><b>Lời review Việt chưa duyệt:</b> "+h(row.get("review_vi_candidate",""))+"</p>")
        parts.append("<p><b>Mô tả Qwen nguồn:</b> "+h(row.get("source_frame_observation",""))+"</p>")
        parts.append("<p><b>Timecode gợi ý:</b> "+h(row.get("scene_interval_s",[]))+
            " (phải mở video kiểm tra cảnh chuyển động)</p>")
        parts.append("<p class=\"warning\"><b>Trạng thái:</b> "+h(row.get("review_status","PENDING"))+
            " · Các cảnh cạnh điểm cắt: "+h(", ".join(row.get("candidate_scene_ids",[])))+
            " · KHÔNG tự quyết định cảnh nguồn</p>")
        fid=row.get("source_evidence_id")
        if fid in frame_uris:
            parts.append('<img loading="lazy" alt="Khung phim nguồn chưa xác minh" src="'+_uri(frame_uris[fid])+'">')
        parts.append('<label>Đối chiếu nguyên clip <select data-result><option value="UNREVIEWED">Chưa xem</option>'+
          '<option value="LOOKS_CORRECT">Có vẻ khớp (chưa duyệt)</option>'+
          '<option value="NEEDS_CORRECTION">Cảnh/lời bình cần sửa</option>'+
          '<option value="UNCERTAIN">Chưa chắc</option></select></label>')
        parts.append('<label>Ghi chú chỉnh sửa <textarea data-notes></textarea></label></article>')
    parts.append(r'''<button type="button" onclick="exportNotes()">Export ghi chú chưa ký (.json)</button>
<p class="warning">Mọi dữ liệu phản hồi ở trên đều KHÔNG PHẢI chữ ký, không mở khoá TTS/dựng phim.</p>
<script>
function exportNotes() {
 const rows=[...document.querySelectorAll("article[data-kind]")].map(el=>({
   kind:el.dataset.kind,id:el.dataset.id,
   reviewer_feedback:el.querySelector("[data-result]").value,
   notes:el.querySelector("[data-notes]").value,
   human_approval_signature:null,
   release_authorized:false
 }));
 const obj={kind:"UNSIGNED_REVIEW_NOTES_ONLY",signed:false,
   source_sha256:document.querySelector("code").textContent,
   rows,script_approved:false,voice_approved:false,pilot_approved:false};
 const blob=new Blob([JSON.stringify(obj,null,2)],{type:"application/json"});
 const url=URL.createObjectURL(blob);
 const a=document.createElement("a");a.href=url;
 a.download="phase6_private_unsigned_review_notes.json";a.click();
 URL.revokeObjectURL(url);
}
</script></body></html>''')
    return "\n".join(parts)
