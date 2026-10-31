"""TDD: source SHA-256 binds to exactly one approved opened handle (synthetic bytes)."""
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
from io import BytesIO
import unittest

from review_phim_runtime.source_binding import (
    SourceReadGrant, OpenSource, verify_bound_source,
)

NOW=datetime(2026,10,31,9,tzinfo=timezone.utc)
PAYLOAD=b"synthetic-content-not-a-film"
DIGEST=hashlib.sha256(PAYLOAD).hexdigest()
PATH=r"D:\review-phim\synthetic.mp4"


class Reader:
    def __init__(self, content=PAYLOAD, canonical_path=PATH, device_id="dev-1"):
        self.device_id=device_id
        self.content=content
        self.canonical_path=canonical_path
        self.opens=0

    @contextmanager
    def open_verified(self, path):
        self.opens+=1
        with BytesIO(self.content) as stream:
            yield OpenSource(self.canonical_path,"volume-id-99:file-7",stream)


class SourceBindingTests(unittest.TestCase):
    def setUp(self):
        self.reader=Reader()
        self.grant=SourceReadGrant(
            device_id="dev-1",job_id="job-1",path=PATH,
            source_sha256=DIGEST,source_bytes=len(PAYLOAD),
            operation="SOURCE_HASH",process_approval_ref="process-approval-1",
            not_before=NOW-timedelta(minutes=1),
            expires_at=NOW+timedelta(minutes=5),
        )

    def check(self,grant=None,reader=None,verifier=lambda *_:True):
        return verify_bound_source(grant or self.grant,reader or self.reader,
                  verifier,now=NOW,chunk_bytes=7)

    def test_hashes_once_from_one_bound_open_handle(self):
        result=self.check()
        self.assertEqual(result.status,"SOURCE_HASH_MATCH")
        self.assertEqual(result.actual_sha256,DIGEST)
        self.assertEqual(result.actual_bytes,len(PAYLOAD))
        self.assertEqual(result.file_identity,"volume-id-99:file-7")
        self.assertEqual(self.reader.opens,1)

    def test_unapproved_media_does_not_open_file(self):
        for grant in (replace(self.grant,process_approval_ref=""),
                      replace(self.grant,operation="G0_INVENTORY"),
                      replace(self.grant,device_id="different"),
                      replace(self.grant,expires_at=NOW),
                      replace(self.grant,source_sha256="not-sha")):
            with self.subTest(grant=grant):
                self.assertNotEqual(self.check(grant=grant).status,"SOURCE_HASH_MATCH")
        self.assertEqual(self.reader.opens,0)

    def test_verifier_failure_does_not_open_file(self):
        for verdict in (False,1,"True",None):
            with self.subTest(verdict=verdict):
                self.assertEqual(self.check(verifier=lambda *_:verdict).status,
                                 "BLOCKED_SOURCE_APPROVAL")
        self.assertEqual(self.reader.opens,0)

    def test_bytes_corruption_and_length_mismatch_are_blocked(self):
        for payload in (PAYLOAD.replace(b"synthetic",b"corrupted"),
                        PAYLOAD + b"more",PAYLOAD[:-1]):
            with self.subTest(payload=payload):
                self.assertNotEqual(self.check(reader=Reader(content=payload)).status,
                                    "SOURCE_HASH_MATCH")

    def test_path_switch_at_open_blocked_before_stream_is_hashed(self):
        result=self.check(reader=Reader(canonical_path=r"E:\private\secret.mp4"))
        self.assertEqual(result.status,"BLOCKED_SOURCE_IDENTITY")

    def test_unc_and_traversal_paths_denied(self):
        for path in (r"\\server\share\movie.mp4",r"D:\review-phim\..\private.mp4"):
            with self.subTest(path=path):
                self.assertNotEqual(self.check(grant=replace(self.grant,path=path)).status,
                                    "SOURCE_HASH_MATCH")

    def test_open_failure_fails_closed(self):
        class Broken:
            device_id="dev-1"
            def open_verified(self,path): raise OSError("file unavailable")
        self.assertEqual(self.check(reader=Broken()).status,"BLOCKED_SOURCE_READ")

    def test_reader_device_mismatch_blocks_before_open(self):
        other=Reader(device_id="dev-2")
        self.assertEqual(self.check(reader=other).status,"BLOCKED_SOURCE_DEVICE")
        self.assertEqual(other.opens,0)

    def test_no_source_file_bytes_in_result(self):
        result=self.check()
        self.assertFalse(hasattr(result,"content"))
        self.assertFalse(hasattr(result,"bytes"))


if __name__=="__main__":
    unittest.main()
