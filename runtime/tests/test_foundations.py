import dataclasses
import datetime as dt
import unittest
from review_phim_runtime.contracts import (NICHE_IDS, STAGES, SourceInterval, FactClaim,
                                           WorkItem, HostInventory, Capability)
from review_phim_runtime.scope import ApprovalScope, validate_scope
from review_phim_runtime.runner import SafeRunner
from review_phim_runtime.registry import resolve_capabilities
from review_phim_runtime.scheduler import BalancedScheduler, ResourceSnapshot, retry_after_oom

NOW = dt.datetime(2026, 10, 31, 2, 0, tzinfo=dt.timezone.utc)

class ContractTests(unittest.TestCase):
    def test_five_niche_routing_preserved(self):
        self.assertEqual(NICHE_IDS, ('review','recap','review-recap','film-explained','character-theme'))
    def test_g0_precedes_g1(self):
        self.assertLess(STAGES.index('G0'), STAGES.index('G1'))
    def test_factual_verified_requires_direct_review(self):
        with self.assertRaises(ValueError):
            FactClaim('VERIFIED', direct_media_reviewed=False)
    def test_source_half_open_interval_rejected_if_invalid(self):
        for a,b in ((1,1),(3,2),(-1,3)):
            with self.subTest(start=a,end=b), self.assertRaises(ValueError):
                SourceInterval(a,b)

class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.scope = ApprovalScope('device','job',r'D:\films',frozenset({'PROBE'}),SourceInterval(0,20),4096,NOW+dt.timedelta(hours=1))
        self.item = WorkItem('device','job',r'D:\films\source.mp4','PROBE',SourceInterval(0,10),128,'run-1')
        self.resolve = lambda p: p
    def check(self, item=None, scope=None, resolver=None, now=NOW):
        return validate_scope(item or self.item,scope or self.scope,now=now,resolver=resolver if resolver is not None else self.resolve)
    def test_missing_process_approval_blocks_ffprobe(self):
        bad=dataclasses.replace(self.scope, allowed_operations=frozenset())
        self.assertEqual(self.check(scope=bad).reason,'BLOCKED_OPERATION')
    def test_reparse_point_escape_blocks(self):
        def resolving(path):
            return r'E:\secret\source.mp4' if path.endswith('source.mp4') else path
        self.assertEqual(self.check(resolver=resolving).reason,'BLOCKED_SOURCE_OR_SCOPE')
    def test_no_resolver_fail_closed(self):
        self.assertEqual(validate_scope(self.item,self.scope,now=NOW).reason,'BLOCKED_CANONICAL_UNAVAILABLE')
    def test_expired_scope_blocks(self):
        self.assertEqual(self.check(now=NOW+dt.timedelta(days=2)).reason,'BLOCKED_EXPIRED')
    def test_bytes_quota_blocks(self):
        bad=dataclasses.replace(self.item,estimated_bytes=5000)
        self.assertEqual(self.check(item=bad).reason,'BLOCKED_QUOTA')
    def test_window_bounds(self):
        bad=dataclasses.replace(self.item,interval=SourceInterval(19,25))
        self.assertEqual(self.check(item=bad).reason,'BLOCKED_INTERVAL')
    def test_traversal_blocks(self):
        bad=dataclasses.replace(self.item,path=r'D:\films\..\secret.mp4')
        self.assertEqual(self.check(item=bad).reason,'BLOCKED_SOURCE_OR_SCOPE')
    def test_other_device_blocks(self):
        bad=dataclasses.replace(self.item,device_id='other')
        self.assertEqual(self.check(item=bad).reason,'BLOCKED_DEVICE_OR_JOB')
    def test_shell_metachar_in_path_is_data(self):
        bad=dataclasses.replace(self.item,path=r'D:\films\;echo pwned.mp4')
        self.assertTrue(self.check(item=bad).allowed)

class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.item=WorkItem('dev','job',r'D:\films\one.mp4','PROBE',SourceInterval(0,1),100,'one')
        self.scope=ApprovalScope('dev','job',r'D:\films',frozenset({'PROBE'}),SourceInterval(0,2),1000,NOW+dt.timedelta(hours=1))
    def test_argument_injection_not_interpreted(self):
        calls=[]
        def launch(argv,**kwargs):
            calls.append((argv,kwargs))
            return dict(returncode=0,stdout='ok',stderr='')
        runner=SafeRunner({'ffprobe':r'C:\tools\ffprobe.exe'},launch)
        item=dataclasses.replace(self.item,path=r'D:\films\one;evil.mp4')
        result=runner.run('ffprobe',item,['-v','error',item.path],self.scope,now=NOW,resolver=lambda s:s)
        self.assertEqual(result.status,'TECHNICAL_PASS')
        self.assertFalse(calls[0][1]['shell'])
        self.assertIn(';evil',calls[0][0][-1])
    def test_timeout_does_not_spawn_duplicate_process(self):
        calls=[]
        def timeout(*args,**kw):
            calls.append(True)
            raise TimeoutError()
        runner=SafeRunner({'ffprobe':r'C:\tools\ffprobe.exe'},timeout)
        self.assertEqual(runner.run('ffprobe',self.item,[],self.scope,now=NOW,resolver=lambda s:s).status,'BLOCKED_INDETERMINATE')
        self.assertEqual(runner.run('ffprobe',self.item,[],self.scope,now=NOW,resolver=lambda s:s).status,'BLOCKED_INDETERMINATE')
        self.assertEqual(len(calls),1)
    def test_not_allowlisted_blocks(self):
        runner=SafeRunner({},lambda *args,**kwargs: self.fail('Must not execute'))
        self.assertEqual(runner.run('powershell',self.item,[],self.scope,now=NOW,resolver=lambda s:s).status,'BLOCKED_EXECUTABLE')

class InventoryTests(unittest.TestCase):
    def test_installed_does_not_mean_usable(self):
        inv=HostInventory('dev','Windows',8188,{'ffmpeg': Capability('ffmpeg','9.0.2',r'C:\ffmpeg.exe',False)})
        self.assertEqual(resolve_capabilities(inv,'balanced')['ffmpeg'],'CONDITIONAL')
    def test_unknown_backend_not_gpu_pass(self):
        inv=HostInventory('dev','Windows',8188,{'asr_gpu': Capability('asr_gpu','1.2.1','asr',False)})
        self.assertNotEqual(resolve_capabilities(inv,'balanced')['asr_gpu'],'INSTALLED_USABLE')
    def test_missing_install_proposed(self):
        inv=HostInventory('dev','Windows',8188,{})
        self.assertEqual(resolve_capabilities(inv,'balanced')['ffmpeg'],'INSTALL_PROPOSED')

class SchedulerTests(unittest.TestCase):
    def test_no_two_heavy_gpu_jobs(self):
        s=BalancedScheduler()
        snap=ResourceSnapshot(8188,7332,28)
        self.assertIsNotNone(s.acquire('gpu-a',600,0,True,snap))
        self.assertIsNone(s.acquire('gpu-b',600,0,True,snap))
    def test_out_of_budget_queues(self):
        s=BalancedScheduler()
        self.assertIsNone(s.acquire('gpu-x',7000,0,True,ResourceSnapshot(8188,7332,28)))
    def test_cpu_reserve_preserved(self):
        s=BalancedScheduler()
        self.assertIsNone(s.acquire('cpu',0,25,False,ResourceSnapshot(8188,7332,28)))
    def test_gpu_lease_released_after_crash(self):
        s=BalancedScheduler()
        snap=ResourceSnapshot(8188,7332,28)
        self.assertIsNotNone(s.acquire('a',400,0,True,snap))
        s.release('a');s.release('a')
        self.assertIsNotNone(s.acquire('b',400,0,True,snap))
    def test_oom_shrinks_once_then_2b_fallback(self):
        self.assertEqual(retry_after_oom('qwen3-vl:4b',0),'REDUCE_BATCH')
        self.assertEqual(retry_after_oom('qwen3-vl:4b',1),'FALLBACK_QWEN3_VL_2B')
        self.assertEqual(retry_after_oom('qwen3-vl:2b',1),'BLOCKED_OOM')

if __name__=='__main__':
    unittest.main()
