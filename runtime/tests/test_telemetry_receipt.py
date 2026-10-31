"""Trust-boundary tests for end-of-sample timestamps and bounded observation lag."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import unittest
from review_phim_runtime.g0_security import G0ReadGrant
from review_phim_runtime.telemetry_receipt import read_bound_telemetry

NOW=datetime(2026,10,31,6,0,tzinfo=timezone.utc)
@dataclass
class Device:
    device_id: str='device-A'
    def __post_init__(self):self.calls=0
    def __call__(self,argv):
        self.calls+=1
        return {'returncode':0,'stdout':'unimportant'}

class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.device=Device()
        self.grant=G0ReadGrant('device-A','scope-1',frozenset({'G0_TELEMETRY'}),NOW-timedelta(seconds=30),NOW+timedelta(seconds=30),'auth')
        self.fake_calls=0
    def collector(self,device_id,runner,*,approved,now,logical_processors):
        self.fake_calls+=1
        runner(['read-only-snapshot'])
        return {'sample_at':now,'device_id':device_id,'logical_processors':logical_processors}
    def test_timestamp_is_after_sampling_not_caller_provided_start(self):
        ticks=iter([100.0,100.25]); stamps=iter([NOW,NOW+timedelta(milliseconds=250)])
        result=read_bound_telemetry('device-A',self.grant,self.device,lambda *_: True,
           now=NOW,logical_processors=28,monotonic=lambda:next(ticks),utcnow=lambda:next(stamps),collector=self.collector)
        self.assertEqual(result.status,'G0_TELEMETRY_OBSERVED')
        self.assertEqual(result.sample['sample_at'],NOW)
        self.assertEqual(result.sample['observed_at'],NOW+timedelta(milliseconds=250))
        self.assertEqual(self.fake_calls,1)
    def test_sample_exceeding_five_seconds_is_not_fresh(self):
        ticks=iter([10.0,16.0]); stamps=iter([NOW,NOW+timedelta(seconds=6)])
        result=read_bound_telemetry('device-A',self.grant,self.device,lambda *_: True,
          now=NOW,logical_processors=28,monotonic=lambda:next(ticks),utcnow=lambda:next(stamps),collector=self.collector)
        self.assertEqual(result.status,'BLOCKED_TELEMETRY_SLOW')
        self.assertIsNone(result.sample)
    def test_denied_grant_executes_nothing(self):
        result=read_bound_telemetry('device-A',self.grant,self.device,lambda *_: False,
          now=NOW,logical_processors=28,monotonic=lambda: 1.0,utcnow=lambda:NOW,collector=self.collector)
        self.assertEqual(result.status,'BLOCKED_G0_VERIFICATION')
        self.assertEqual(self.device.calls,0)
    def test_clock_rollback_or_skew_is_rejected(self):
        for ticks,stamps in [(iter([3.,2.]),iter([NOW,NOW])),
                             (iter([1.,2.]),iter([NOW,NOW-timedelta(seconds=1)]))]:
            with self.subTest():
                res=read_bound_telemetry('device-A',self.grant,self.device,lambda *_:True,
                  now=NOW,logical_processors=28,monotonic=lambda:next(ticks),utcnow=lambda:next(stamps),collector=self.collector)
                self.assertEqual(res.status,'BLOCKED_TELEMETRY_CLOCK')
    def test_other_device_and_non_approved_operation_block(self):
        self.device.device_id='device-B'
        result=read_bound_telemetry('device-A',self.grant,self.device,lambda *_:True,
          now=NOW,logical_processors=28,monotonic=lambda: 1.,utcnow=lambda:NOW,collector=self.collector)
        self.assertEqual(result.status,'BLOCKED_G0_DEVICE')
        self.assertEqual(self.device.calls,0)

if __name__=='__main__':unittest.main()
