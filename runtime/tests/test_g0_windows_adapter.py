"""Synthetic contract tests for a narrow Windows G0 connector adapter."""
import hashlib
import unittest

from review_phim_runtime.g0_collector import G0_POWERSHELL_ARGV, G0_NVIDIA_ARGV
from review_phim_runtime.telemetry import TELEMETRY_CPU_ARGV, TELEMETRY_GPU_ARGV
from review_phim_runtime.g0_windows_adapter import FixedG0WindowsAdapter


class G0WindowsAdapterTests(unittest.TestCase):
    def setUp(self):
        self.calls=[]
        self.device_id='device-test'
        def transport(device, argv):
            self.calls.append((device,argv))
            return {'device_id':device, 'argv_sha256':hashlib.sha256(
                '\0'.join(argv).encode('utf-8')).hexdigest(),
                'returncode':0,'stdout':'{}','stderr':''}
        self.adapter=FixedG0WindowsAdapter(self.device_id, transport)

    def test_exact_fixed_metadata_commands_are_accepted(self):
        for argv in (G0_POWERSHELL_ARGV,G0_NVIDIA_ARGV,TELEMETRY_CPU_ARGV,TELEMETRY_GPU_ARGV):
            with self.subTest(argv=argv[0:2]):
                self.assertEqual(self.adapter(argv)['returncode'],0)
        self.assertEqual(len(self.calls),4)
        self.assertTrue(all(x[0]==self.device_id for x in self.calls))

    def test_unlisted_command_blocks_before_transport(self):
        for argv in (('powershell.exe','-Command','Get-Content D:\\film.mp4'),
                     ('ffprobe','-i','D:\\film.mp4'),
                     ('nvidia-smi','--query-gpu=name','--format=csv'),
                     ('cmd.exe','/c','dir')):
            with self.subTest(argv=argv),self.assertRaises(ValueError):
                self.adapter(argv)
        self.assertEqual(self.calls,[])

    def test_changed_argv_and_shell_form_block(self):
        for argv in (' '.join(G0_NVIDIA_ARGV),list(G0_NVIDIA_ARGV)+['--extra']):
            with self.subTest(argv=argv),self.assertRaises(ValueError):
                self.adapter(argv)
        self.assertEqual(self.calls,[])

    def test_returned_device_mismatch_blocks(self):
        def bad(device,argv):
            return {'device_id':'other','argv_sha256':hashlib.sha256(
                '\0'.join(argv).encode()).hexdigest(),'returncode':0,'stdout':'{}','stderr':''}
        with self.assertRaises(RuntimeError):
            FixedG0WindowsAdapter('device-test',bad)(G0_POWERSHELL_ARGV)

    def test_command_receipt_digest_mismatch_blocks(self):
        def bad(device,argv):
            return {'device_id':device,'argv_sha256':'0'*64,
                    'returncode':0,'stdout':'{}','stderr':''}
        with self.assertRaises(RuntimeError):
            FixedG0WindowsAdapter(self.device_id,bad)(G0_NVIDIA_ARGV)

    def test_output_size_limited_and_nontext_rejected(self):
        for output in ('x'*70000,b'not-text'):
            def bad(device,argv):
                return {'device_id':device,'argv_sha256':hashlib.sha256(
                    '\0'.join(argv).encode()).hexdigest(),
                    'returncode':0,'stdout':output,'stderr':''}
            with self.subTest(output=type(output)),self.assertRaises(RuntimeError):
                FixedG0WindowsAdapter(self.device_id,bad)(G0_POWERSHELL_ARGV)

    def test_missing_device_or_result_fields_block(self):
        with self.assertRaises(ValueError):
            FixedG0WindowsAdapter('',lambda *a:{})
        with self.assertRaises(RuntimeError):
            self.adapter_missing(G0_NVIDIA_ARGV)

    def adapter_missing(self,argv):
        return FixedG0WindowsAdapter(self.device_id,lambda *a: {'returncode':0})(argv)


if __name__=='__main__':
    unittest.main()
