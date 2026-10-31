"""TDD for durable authorization, not a real process launch."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest
from review_phim_runtime.contracts import SourceInterval, WorkItem
from review_phim_runtime.scope import ApprovalScope, validate_scope
from review_phim_runtime.runner import SafeRunner
from review_phim_runtime.ffprobe_policy import build_ffprobe_argv, validate_ffprobe_argv
from review_phim_runtime.journal import OperationJournal

NOW=datetime(2026,10,31,tzinfo=timezone.utc)

class JournalRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db=str(Path(self.temp.name)/'jobs.db')
        self.grant=ApprovalScope('dev','job',r'D:\films',frozenset({'PROBE'}), SourceInterval(0,50),100,NOW+timedelta(hours=1),scope_id='scope-1')
        self.item=WorkItem('dev','job',r'D:\films\movie.mp4','PROBE',SourceInterval(0,4),70,'op-1')
        self.argv=build_ffprobe_argv(self.item)
        self.launch_count=0

    def launcher(self, argv, **kwargs):
        self.launch_count+=1
        return {'pid':1234, 'returncode':0, 'stdout':'{}', 'stderr':''}

    def runner(self, journal=None):
        return SafeRunner({'ffprobe':r'C:\tools\ffprobe.exe'},self.launcher,
                          arg_validator=validate_ffprobe_argv,journal=journal)

    def test_unconfigured_journal_blocks_process(self):
        result=self.runner().run('ffprobe',self.item,self.argv,self.grant,now=NOW,resolver=lambda s:s)
        self.assertEqual(result.status,'BLOCKED_JOURNAL_UNAVAILABLE')
        self.assertEqual(self.launch_count,0)
    def test_no_scope_id_blocks_process(self):
        grant=replace(self.grant,scope_id='')
        result=self.runner(OperationJournal(self.db)).run('ffprobe',self.item,self.argv,grant,now=NOW,resolver=lambda s:s)
        self.assertEqual(result.status,'BLOCKED_SCOPE_ID')
        self.assertEqual(self.launch_count,0)
    def test_success_recorded_durably_across_new_runner(self):
        runner=self.runner(OperationJournal(self.db))
        result=runner.run('ffprobe',self.item,self.argv,self.grant,now=NOW,resolver=lambda s:s)
        self.assertEqual(result.status,'TECHNICAL_PASS')
        entry=OperationJournal(self.db).get('scope-1','op-1')
        self.assertEqual((entry.status,entry.pid,entry.returncode),('EXITED',1234,0))
        result=self.runner(OperationJournal(self.db)).run('ffprobe',self.item,self.argv,self.grant,now=NOW,resolver=lambda s:s)
        self.assertEqual(result.status,'BLOCKED_DUPLICATE')
        self.assertEqual(self.launch_count,1)
    def test_cumulative_quota_blocks_second_operation(self):
        journal=OperationJournal(self.db)
        self.assertEqual(self.runner(journal).run('ffprobe',self.item,self.argv,self.grant,now=NOW,resolver=lambda s:s).status,'TECHNICAL_PASS')
        other=replace(self.item,idempotency_key='op-2', estimated_bytes=40)
        self.assertEqual(self.runner(journal).run('ffprobe',other,build_ffprobe_argv(other),self.grant,now=NOW,resolver=lambda s:s).status,'BLOCKED_QUOTA')
        self.assertEqual(self.launch_count,1)
    def test_timeout_remains_reserved_after_restart(self):
        def timeout(argv,**kwargs):
            self.launch_count+=1
            raise TimeoutError('Remote result unknown')
        journal=OperationJournal(self.db)
        r=SafeRunner({'ffprobe':r'C:\tools\ffprobe.exe'},timeout,validate_ffprobe_argv,journal)
        self.assertEqual(r.run('ffprobe',self.item,self.argv,self.grant,now=NOW,resolver=lambda s:s).status,'BLOCKED_INDETERMINATE')
        self.assertEqual(self.runner(OperationJournal(self.db)).run('ffprobe',self.item,self.argv,self.grant,now=NOW,resolver=lambda s:s).status,'BLOCKED_DUPLICATE')
        self.assertEqual(self.launch_count,1)
    def test_no_pid_cannot_claim_technical_pass(self):
        r=SafeRunner({'ffprobe':r'C:\tools\ffprobe.exe'},lambda argv,**kw: {'returncode':0,'stdout':'{}'},validate_ffprobe_argv,OperationJournal(self.db))
        self.assertEqual(r.run('ffprobe',self.item,self.argv,self.grant,now=NOW,resolver=lambda s:s).status,'BLOCKED_INDETERMINATE')
    def test_unapproved_args_do_not_consume_quota(self):
        journal=OperationJournal(self.db)
        status=self.runner(journal).run('ffprobe',self.item,['-o','evil.mp4'],self.grant,now=NOW,resolver=lambda s:s).status
        self.assertEqual(status,'BLOCKED_ARGUMENTS')
        self.assertIsNone(journal.get('scope-1','op-1'))
    def test_unc_paths_must_not_qualify_as_local_even_if_resolver_is_wrong(self):
        grant=replace(self.grant,allowed_root=r'\\server\share')
        item=replace(self.item,path=r'\\server\share\film.mp4')
        self.assertEqual(validate_scope(item,grant,now=NOW,resolver=lambda s:s).reason,'BLOCKED_SOURCE_OR_SCOPE')

if __name__=='__main__':unittest.main()
