"""Security regression tests. No access to a user's device or media."""
import concurrent.futures
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from review_phim_runtime.winpaths import canonical_windows_path
from review_phim_runtime.journal import OperationJournal
from review_phim_runtime.ffprobe_policy import build_ffprobe_argv, validate_ffprobe_argv
from review_phim_runtime.contracts import WorkItem, SourceInterval

class WindowsPathTests(unittest.TestCase):
    def test_canonical_path_is_verified_against_actual_reparse_destination(self):
        def fake_realpath(path):
            if path == r'D:\approved\junction\film.mp4':
                return r'E:\private\film.mp4'
            return path
        self.assertEqual(canonical_windows_path(r'D:\approved\junction\film.mp4', realpath=fake_realpath),r'E:\private\film.mp4')
    def test_refuses_unc_unc_device_relative_stream_and_traversal(self):
        bad=[r'\\server\films\a.mp4',r'\\?\D:\films\a.mp4',r'D:relative.mp4',r'..\escape.mp4',r'D:\films\..\secret.mp4',r'D:\films\a.mp4:extra',r'D:\films\bad.\x.mp4',r'D:\films\bad \x.mp4']
        for path in bad:
            with self.subTest(path=path), self.assertRaises(ValueError):
                canonical_windows_path(path, realpath=lambda p:p)
    def test_rejects_nonexistent_target_from_realpath(self):
        def no_file(path): raise FileNotFoundError(path)
        with self.assertRaises(ValueError):
            canonical_windows_path(r'D:\films\missing.mp4', realpath=no_file)
    def test_without_windows_runtime_does_not_guess_paths(self):
        import os
        if os.name != 'nt':
            with self.assertRaises(RuntimeError):
                canonical_windows_path(r'D:\films\movie.mp4')

class JournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db=str(Path(self.tmp.name)/'op.sqlite3')
        self.journal=OperationJournal(self.db)
    def test_durable_quota_across_reopening_and_completed_tasks(self):
        self.assertEqual(self.journal.reserve('scope','first',80,100).status,'RESERVED')
        self.assertTrue(self.journal.mark_running('scope','first',1234))
        self.assertTrue(self.journal.mark_completed('scope','first',0))
        reopened=OperationJournal(self.db)
        self.assertEqual(reopened.reserve('scope','second',21,100).status,'BLOCKED_QUOTA')
        self.assertEqual(reopened.reserve('scope','second',20,100).status,'RESERVED')
    def test_duplicate_request_cannot_reserve_or_execute_twice(self):
        self.assertEqual(self.journal.reserve('scope','key',10,100).status,'RESERVED')
        self.assertEqual(self.journal.reserve('scope','key',10,100).status,'BLOCKED_DUPLICATE')
    def test_running_task_survives_restart_and_requires_reconciliation(self):
        self.journal.reserve('scope','key',5,100)
        self.assertTrue(self.journal.mark_running('scope','key',321))
        reopened=OperationJournal(self.db)
        self.assertEqual(reopened.get('scope','key').status,'RUNNING')
        self.assertEqual(reopened.get('scope','key').pid,321)
        self.assertEqual(reopened.reserve('scope','key',5,100).status,'BLOCKED_DUPLICATE')
    def test_negative_or_zero_limit_rejected(self):
        for amount,limit in [(-1,100),(0,-1),(2,0)]:
            with self.subTest(amount=amount,limit=limit):
                self.assertEqual(self.journal.reserve('scope','key',amount,limit).status,'BLOCKED_QUOTA')
    def test_scope_isolation(self):
        self.journal.reserve('scope1','key',80,100)
        self.assertEqual(self.journal.reserve('scope2','key',80,100).status,'RESERVED')
    def test_concurrent_reservations_cannot_exceed_quota(self):
        def reserve(i):return self.journal.reserve('scope',str(i),10,50).status
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(reserve, range(15)))
        self.assertEqual(results.count('RESERVED'),5)
        self.assertEqual(results.count('BLOCKED_QUOTA'),10)
    def test_pid_must_be_positive_and_known(self):
        self.assertFalse(self.journal.mark_running('scope','missing',123))
        self.journal.reserve('scope','key',10,100)
        self.assertFalse(self.journal.mark_running('scope','key',0))
        self.assertFalse(self.journal.mark_completed('scope','key',0))
        self.assertTrue(self.journal.mark_running('scope','key',4312))
        self.assertTrue(self.journal.mark_completed('scope','key',1))
        self.assertEqual(self.journal.get('scope','key').status,'EXITED')
        self.assertEqual(self.journal.get('scope','key').returncode,1)

class FFprobePolicyTests(unittest.TestCase):
    def setUp(self):
        self.item=WorkItem('d','j',r'D:\films\film.mp4','PROBE',SourceInterval(0,1),100,'key')
    def test_only_allow_readonly_probe_argument_grammar(self):
        argv=build_ffprobe_argv(self.item)
        self.assertEqual(argv, ['-v','error','-show_format','-show_streams','-of','json',r'D:\films\film.mp4'])
        self.assertTrue(validate_ffprobe_argv('ffprobe',self.item,argv))
    def test_blocks_other_input_network_output_and_extra_flag(self):
        argv=build_ffprobe_argv(self.item)
        for evil in [argv[:-1]+['https://bad.example/file.mp4'],argv+['-i','other.mp4'],argv+['-o',r'D:\other.json'],['-v','error',self.item.path]]:
            with self.subTest(argv=evil):
                self.assertFalse(validate_ffprobe_argv('ffprobe',self.item,evil))
    def test_mismatched_operation_blocks(self):
        item=WorkItem('d','j',r'D:\films\film.mp4','RENDER',SourceInterval(0,1),100,'key')
        self.assertFalse(validate_ffprobe_argv('ffprobe',item,build_ffprobe_argv(self.item)))

if __name__ == '__main__': unittest.main()
