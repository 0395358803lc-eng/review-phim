"""Host G0 and adaptive admission tests using synthetic runner responses only."""
import json
import unittest
from datetime import datetime, timedelta, timezone
from review_phim_runtime.g0_collector import collect_g0, G0_POWERSHELL_ARGV, G0_NVIDIA_ARGV, to_host_inventory
from review_phim_runtime.telemetry import collect_telemetry, TelemetrySnapshot, TELEMETRY_CPU_ARGV, TELEMETRY_GPU_ARGV
from review_phim_runtime.scheduler import BalancedScheduler
from review_phim_runtime.registry import resolve_capabilities

NOW = datetime(2026, 10, 31, 3, 0, tzinfo=timezone.utc)
SYNTHETIC_HOST = {
    'os': {'name': 'Windows 11 Pro', 'version': '10.0.26100', 'architecture':'64-bit'},
    'cpu': {'name': 'Intel Core i7-14700F', 'cores': 20, 'logical_processors': 28},
    'ram_bytes': 34132303872,
    'drives': [{'device': 'C:', 'total_bytes': 249108103168, 'free_bytes': 140000000000},
               {'device': 'D:', 'total_bytes': 1000204886016, 'free_bytes': 970000000000}],
    'tools': [{'name': 'python', 'path': r'C:\Python\python.exe'},
              {'name': 'node', 'path': r'C:\Program Files\nodejs\node.exe'}]
}
GPU_CSV = 'NVIDIA GeForce RTX 4060, 8188, 7332, 617.42, 6\n'

class ReadOnlyCollectorTests(unittest.TestCase):
    def setUp(self):
        self.commands = []
    def runner(self, argv):
        self.commands.append(argv)
        if argv == G0_POWERSHELL_ARGV:
            return {'returncode': 0, 'stdout': json.dumps(SYNTHETIC_HOST), 'stderr': ''}
        if argv == G0_NVIDIA_ARGV:
            return {'returncode': 0, 'stdout': GPU_CSV, 'stderr': ''}
        raise AssertionError('Unexpected command requested')
    def test_requires_explicit_g0_read_scope_before_any_probe(self):
        result = collect_g0('device-1', self.runner, approved=False)
        self.assertEqual(result.status,'BLOCKED_G0_APPROVAL')
        self.assertEqual(self.commands, [])
    def test_blank_device_id_blocks(self):
        result = collect_g0(' ', self.runner, approved=True)
        self.assertEqual(result.status,'BLOCKED_DEVICE')
        self.assertEqual(self.commands, [])
    def test_reads_hardware_software_metadata_without_media(self):
        result=collect_g0('device-1', self.runner, approved=True)
        self.assertEqual(result.status,'G0_OBSERVED')
        self.assertEqual(self.commands,[G0_POWERSHELL_ARGV,G0_NVIDIA_ARGV])
        self.assertEqual(result.snapshot.device_id,'device-1')
        self.assertEqual(result.snapshot.cpu_name,'Intel Core i7-14700F')
        self.assertEqual(result.snapshot.cpu_logical,28)
        self.assertEqual(result.snapshot.gpu_name,'NVIDIA GeForce RTX 4060')
        self.assertEqual(result.snapshot.vram_total_mib,8188)
        self.assertEqual(result.snapshot.vram_free_mib,7332)
        self.assertIsNone(result.snapshot.cuda_runtime_tested)
        self.assertEqual(result.snapshot.tool_paths['python'],r'C:\Python\python.exe')
        self.assertTrue(all('review-phim' not in part for argv in self.commands for part in argv))
    def test_g0_executable_presence_is_not_installed_usable(self):
        result=collect_g0('device-1',self.runner,approved=True)
        inventory=to_host_inventory(result)
        self.assertEqual(inventory.device_id,'device-1')
        self.assertEqual(inventory.total_vram_mib,8188)
        self.assertEqual(inventory.capabilities['python'].tested,False)
        self.assertEqual(resolve_capabilities(inventory,'balanced')['ffmpeg'],'INSTALL_PROPOSED')
    def test_no_nvidia_tool_does_not_invent_gpu(self):
        def runner(argv):
            self.commands.append(argv)
            if argv == G0_POWERSHELL_ARGV:
                return {'returncode':0,'stdout':json.dumps(SYNTHETIC_HOST),'stderr':''}
            return {'returncode':1,'stdout':'','stderr':'not installed'}
        result=collect_g0('device-1',runner,approved=True)
        self.assertEqual(result.status,'G0_PARTIAL')
        self.assertIsNone(result.snapshot.gpu_name)
        self.assertIsNone(result.snapshot.vram_total_mib)
        self.assertEqual(result.snapshot.cpu_logical,28)
        self.assertIsNone(to_host_inventory(result))
    def test_malformed_inventory_fails_closed(self):
        def malformed(argv):
            return {'returncode':0,'stdout':'{"ram_bytes":-8}','stderr':''}
        result=collect_g0('device-1',malformed,approved=True)
        self.assertEqual(result.status,'BLOCKED_G0_INVALID')
        self.assertIsNone(result.snapshot)
    def test_invalid_disk_and_tool_records_are_rejected(self):
        for change in [dict(drives=[{'device':'C:', 'total_bytes':100,'free_bytes':200}]),
                       dict(tools=[{'name':'ffprobe','path':''}])]:
            altered={**SYNTHETIC_HOST, **change}
            def fake(argv):
                return {'returncode':0,'stdout':json.dumps(altered),'stderr':''} if argv==G0_POWERSHELL_ARGV else {'returncode':0,'stdout':GPU_CSV,'stderr':''}
            with self.subTest(change=change):
                self.assertEqual(collect_g0('device-1',fake,approved=True).status,'BLOCKED_G0_INVALID')

class AdaptiveSchedulerTests(unittest.TestCase):
    def make(self,**kw):
        base=dict(device_id='device-1',observed_at=NOW,gpu_name='NVIDIA GeForce RTX 4060',
                  vram_total_mib=8188,vram_free_mib=7332,logical_processors=28,
                  cpu_utilization_pct=15,gpu_utilization_pct=10)
        return TelemetrySnapshot(**{**base,**kw})
    def test_fresh_measured_sample_admits_safe_gpu_work(self):
        s=BalancedScheduler()
        lease=s.acquire_measured('job1',gpu_mib=3200,cpu_workers=4,heavy_gpu=True,
                                 telemetry=self.make(),device_id='device-1',now=NOW+timedelta(seconds=3))
        self.assertIsNotNone(lease)
    def test_stale_or_other_device_gpu_sample_blocks(self):
        for kw in [dict(now=NOW+timedelta(seconds=20)),dict(device_id='device-2')]:
            s=BalancedScheduler()
            kw={**dict(telemetry=self.make(),device_id='device-1',now=NOW),**kw}
            if kw['device_id']=='device-2':kw['telemetry']=self.make()
            self.assertIsNone(s.acquire_measured('job1',3200,2,True,**kw))
    def test_high_gpu_busy_blocks_heavy_ai_even_with_vram(self):
        self.assertIsNone(BalancedScheduler().acquire_measured('job',2000,0,True,
             telemetry=self.make(gpu_utilization_pct=95),device_id='device-1',now=NOW))
    def test_high_cpu_utilization_reduces_worker_capacity(self):
        s=BalancedScheduler()
        self.assertIsNone(s.acquire_measured('a',0,6,False,
            telemetry=self.make(cpu_utilization_pct=90),device_id='device-1',now=NOW))
        self.assertIsNotNone(s.acquire_measured('b',0,2,False,
            telemetry=self.make(cpu_utilization_pct=90),device_id='device-1',now=NOW))
    def test_unknown_load_never_admits_measured_job(self):
        s=BalancedScheduler()
        for t in [self.make(cpu_utilization_pct=None),self.make(gpu_utilization_pct=float('nan')),
                  self.make(vram_free_mib=-1),self.make(observed_at=NOW+timedelta(seconds=5))]:
            with self.subTest(sample=t):
                self.assertIsNone(s.acquire_measured('x',200,0,True,telemetry=t,device_id='device-1',now=NOW))
    def test_snapshot_does_not_mutate_existing_scheduler_on_failed_attempt(self):
        s=BalancedScheduler()
        self.assertIsNone(s.acquire_measured('job',3200,0,True,telemetry=self.make(gpu_utilization_pct=99),device_id='device-1',now=NOW))
        self.assertIsNotNone(s.acquire_measured('job',3200,0,True,telemetry=self.make(),device_id='device-1',now=NOW))
    def test_telemetry_requires_read_approval_before_commands(self):
        calls=[]
        sample=collect_telemetry('device-1',lambda argv:calls.append(argv),approved=False,now=NOW)
        self.assertIsNone(sample)
        self.assertEqual(calls,[])
    def test_telemetry_sample_uses_fixed_readonly_commands(self):
        calls=[]
        def runner(argv):
            calls.append(argv)
            if argv==TELEMETRY_CPU_ARGV:
                return {'returncode':0,'stdout':'15\n','stderr':''}
            if argv==TELEMETRY_GPU_ARGV:
                return {'returncode':0,'stdout':GPU_CSV,'stderr':''}
            raise AssertionError(argv)
        sample=collect_telemetry('device-1',runner,approved=True,now=NOW,logical_processors=28)
        self.assertEqual(calls,[TELEMETRY_CPU_ARGV,TELEMETRY_GPU_ARGV])
        self.assertEqual((sample.vram_total_mib,sample.gpu_utilization_pct,sample.cpu_utilization_pct),(8188,6,15))
    def test_broken_gpu_telemetry_blocks_without_fake_numbers(self):
        def runner(argv):
            return {'returncode':0,'stdout':'10','stderr':''} if argv==TELEMETRY_CPU_ARGV else {'returncode':1,'stdout':'','stderr':'error'}
        self.assertIsNone(collect_telemetry('device-1',runner,approved=True,now=NOW,logical_processors=28))

if __name__=='__main__':unittest.main()
