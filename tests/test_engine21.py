"""Phase-1 engine contracts; fixtures are synthetic or generated with FFmpeg."""
from __future__ import annotations
import hashlib
import hmac
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/film-review-orchestrator/scripts'))
import jobctl
from engine21 import state as estate, gates, runner


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_movie(path):
    if not shutil.which('ffmpeg'):
        raise unittest.SkipTest('FFmpeg unavailable')
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-f', 'lavfi', '-i',
         'color=c=blue:s=128x72:r=12:d=0.6', '-f', 'lavfi', '-i',
         'sine=frequency=500:sample_rate=16000:duration=0.6', '-shortest',
         '-c:v', 'mpeg4', '-c:a', 'aac', '-y', str(path)],
         check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)


STAGE_SCRIPT = '''import os,json,hashlib,shutil,subprocess
from pathlib import Path
out=Path(os.environ["FRA_OUTPUT_DIR"]);out.mkdir(parents=True,exist_ok=True)
stage=os.environ["FRA_STAGE"]
source=os.environ["FRA_SOURCE"]
artifacts=[]
for name in json.loads(os.environ["FRA_REQUIRED_OUTPUTS"]):
 p=out/name
 if p.suffix=='.mp4':shutil.copyfile(source,p)
 elif p.suffix=='.wav':
  subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','sine=duration=0.4','-y',str(p)],check=True)
 elif name=='sentence_shot_map.json':
  p.write_text(json.dumps({'source_movie_sha256':os.environ['FRA_SOURCE_SHA256'],'source_duration_s':100,
   'narration_duration_s':2,'sentences':[{'sentence_id':'S1','review_text':'test',
   'voice_start_s':0,'voice_end_s':2,'atomic_claims':[{'claim_id':'C1','text':'x','verdict':'CONTEXT_ONLY','evidence_ids':[]}],
   'chosen_shots':[{'source_start_s':1,'source_end_s':3,'voice_start_s':0,'voice_end_s':2,
    'visual_evidence_ids':[],'asr_evidence_ids':[],'verdict':'CONTEXT_ONLY','qualifier':'context'}],
   'unresolved_claims':[]}]}))
 elif name=='source_manifest.json':p.write_text(json.dumps({'source_sha256':os.environ['FRA_SOURCE_SHA256']}))
 elif p.suffix=='.json':p.write_text('{}')
 elif p.suffix=='.jsonl':p.write_text('{"synthetic":true}\\n')
 else:p.write_text('synthetic data',encoding='utf8')
 artifacts.append({'path':str(p.relative_to(Path(os.environ['FRA_JOB']))),
 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
checks=json.loads(os.environ['FRA_REQUIRED_CHECKS'])
doc={'stage':stage,'outcome':'PASS','source_sha256':os.environ['FRA_SOURCE_SHA256'],
 'reviewed_at_utc':'2026-11-22T00:00:00Z','checks':{k:True for k in checks},
 'artifacts':artifacts,'limitations':['SYNTHETIC; not semantic certification']}
(out/'evidence.json').write_text(json.dumps(doc),encoding='utf8')
'''



def sign_receipt(job_id,gate,digest,key,ttl_seconds=120):
    now=datetime.now(timezone.utc)
    payload={'job_id':job_id,'gate':gate,'subject_sha256':digest,
             'issued_at_utc':now.isoformat(),
             'expires_at_utc':(now+timedelta(seconds=ttl_seconds)).isoformat()}
    sig=hmac.new(key,json.dumps(payload,sort_keys=True,ensure_ascii=False,
                        separators=(',',':')).encode('utf8'),hashlib.sha256).hexdigest()
    return {**payload,'signature':sig}


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.top = Path(self.tmp.name)
        movie = self.top/'source.mp4'
        make_movie(movie)
        self.job = jobctl.create_job(movie, self.top/'jobs', 'sample', probe=False)
        self.adapter = self.top/'stage_adapter.py'
        self.adapter.write_text(STAGE_SCRIPT, encoding='utf-8')
        self.config = self.top/'adapters.json'
        self.config.write_text(json.dumps({'schema_version':'2.1.0', 'stages': {
            stage:{'executable':sys.executable,'argv':[str(self.adapter)],
                   'timeout_seconds':20,'max_attempts':2,'retry_safe':True}
            for stage in jobctl.STAGES}}), encoding='utf8')
        self.key = b'trusted-host-secret-key'
        self.approvals = self.top/'trusted_receipts'
        self.approvals.mkdir()

    def test_init_reconcile_and_order_are_fail_closed(self):
        s=estate.load_or_init(self.job, self.config)
        self.assertEqual(s['stages']['N00']['status'],'PENDING')
        with self.assertRaises(ValueError):
            runner.run(self.job, self.config, 'N01')
        result=runner.run(self.job,self.config,'N00')
        self.assertEqual(result['status'],'DONE')
        self.assertEqual(runner.run(self.job,self.config,'N00')['status'],'ALREADY_DONE')
        self.assertEqual(estate.reconcile(self.job)['stages']['N00']['status'],'DONE')

    def test_source_tamper_invalidates_stage(self):
        runner.run(self.job,self.config,'N00')
        Path(jobctl.read_job(self.job)['source']['absolute_path']).write_bytes(b'BAD')
        s=estate.reconcile(self.job)
        self.assertEqual(s['stages']['N00']['status'],'STALE')
        with self.assertRaises(ValueError):
            runner.run(self.job,self.config,'N01')

    def test_artifact_tamper_invalidates_parent_and_child(self):
        runner.run(self.job,self.config,'N00')
        runner.run(self.job,self.config,'N01')
        s=estate.load_or_init(self.job,self.config)
        artifact=self.job/s['stages']['N00']['artifacts'][0]['path']
        artifact.write_text('corrupted',encoding='utf8')
        s=estate.reconcile(self.job)
        self.assertEqual(s['stages']['N00']['status'],'STALE')
        self.assertEqual(s['stages']['N01']['status'],'STALE')
        with self.assertRaises(ValueError):
            runner.run(self.job,self.config,'N03')

    def test_config_pinning_prevents_unapproved_change(self):
        estate.load_or_init(self.job,self.config)
        config=json.loads(self.config.read_text())
        config['stages']['N00']['argv'].append('--unexpected')
        self.config.write_text(json.dumps(config), encoding='utf8')
        with self.assertRaises(ValueError):
            runner.run(self.job,self.config,'N00')

    def test_adapter_must_not_use_shell_or_relative_executable(self):
        for executable in ['python','/missing/unsafe-executable']:
            config=json.loads(self.config.read_text())
            config['stages']['N00']['executable']=executable
            c=self.top/'badconfig.json';c.write_text(json.dumps(config))
            with self.assertRaises(ValueError):
                runner.run(self.job,c,'N00')

    def test_untrusted_output_evidence_cannot_be_passed_as_media(self):
        # Even a forged PASS manifest cannot prove the source film is decodable.
        runner.run(self.job,self.config,'N00')
        s=estate.load_or_init(self.job,self.config)
        out=self.job/s['stages']['N00']['artifacts'][0]['path']
        self.assertTrue(out.is_file())
        source=Path(jobctl.read_job(self.job)['source']['absolute_path'])
        source.write_bytes(b'not a valid movie')
        with self.assertRaises(ValueError):
            runner.run(self.job,self.config,'N02')

    def test_approval_signature_subject_and_expiry(self):
        job_id=jobctl.read_job(self.job)['job_id']
        target='a'*64
        valid=sign_receipt(job_id,'script',target,self.key, ttl_seconds=120)
        self.assertTrue(gates.verify_receipt(valid,'script',job_id,target,self.key))
        with self.assertRaises(ValueError):
            gates.verify_receipt(valid,'script',job_id,'b'*64,self.key)
        with self.assertRaises(ValueError):
            gates.verify_receipt(valid,'script',job_id,target,b'wrong-secret')
        past=sign_receipt(job_id,'script',target,self.key,ttl_seconds=-120)
        with self.assertRaises(ValueError):
            gates.verify_receipt(past,'script',job_id,target,self.key)

    def test_no_fabricated_approval_before_n06(self):
        self.seed_done('N00','N01','N02','N03','N04','N05')
        (self.job/'voice').mkdir(exist_ok=True)
        sample=self.job/'voice'/'approved_sample.wav'
        sample.write_bytes(b'sample-fixture')
        with self.assertRaises((PermissionError,ValueError)):
            runner.run(self.job,self.config,'N06',receipts_dir=self.approvals,key=self.key)
        s=estate.load_or_init(self.job,self.config)
        doc=self.job/s['stages']['N05']['evidence_path']
        self.write_receipt('script',sha(doc))
        with self.assertRaises((PermissionError,ValueError)):
            runner.run(self.job,self.config,'N06',receipts_dir=self.approvals,key=self.key)
        self.write_receipt('voice',sha(sample))
        self.assertEqual(runner.run(self.job,self.config,'N06',receipts_dir=self.approvals,key=self.key)['status'],'DONE')

    def test_invalid_pilot_approval_denies_full_edit(self):
        self.seed_done(*jobctl.STAGES[:8])
        with self.assertRaises((PermissionError,ValueError)):
            runner.run(self.job,self.config,'N08',receipts_dir=self.approvals,key=self.key)

    def test_interrupted_requires_retry_safe(self):
        runner.run(self.job,self.config,'N00')
        s=estate.load_or_init(self.job,self.config)
        s['stages']['N01']['status']='RUNNING'
        estate.atomic_state(self.job,s)
        rec=estate.reconcile(self.job)
        self.assertEqual(rec['stages']['N01']['status'],'INTERRUPTED')
        c=json.loads(self.config.read_text())
        c['stages']['N01']['retry_safe']=False
        # Frozen configuration check tests this independently with fresh job.
        other=self.top/'fresh-config.json';other.write_text(json.dumps(c))
        s['config_sha256']=sha(other)
        estate.atomic_state(self.job,s)
        with self.assertRaises(ValueError):
            runner.run(self.job,other,'N01')

    def test_finite_timeout_records_failure(self):
        p=self.top/'slow.py'
        p.write_text('import time;time.sleep(5)')
        c=json.loads(self.config.read_text())
        c['stages']['N00']['argv']=[str(p)]
        c['stages']['N00']['timeout_seconds']=1
        c['stages']['N00']['max_attempts']=1
        new=self.top/'slow-config.json';new.write_text(json.dumps(c))
        result=runner.run(self.job,new,'N00')
        self.assertEqual(result['status'],'FAILED')
        self.assertEqual(estate.reconcile(self.job)['stages']['N00']['status'],'FAILED')

    def test_missing_required_output_is_not_a_valid_stage(self):
        missing=self.top/'missing.py'
        missing.write_text(STAGE_SCRIPT.replace('for name in json.loads(os.environ["FRA_REQUIRED_OUTPUTS"]):',
               'for name in ["wrong-product.txt"]:'),encoding='utf8')
        config=json.loads(self.config.read_text())
        config['stages']['N00']['argv']=[str(missing)]
        conf=self.top/'missing.json';conf.write_text(json.dumps(config))
        result=runner.run(self.job,conf,'N00')
        self.assertEqual(result['status'],'FAILED')
        self.assertIn('source_manifest.json',result['reason'])

    def test_reusing_previous_source_manifest_is_not_stage_output(self):
        # A pre-existing jobctl file is not proof the attempted adapter produced it.
        rogue=self.top/'rogue.py'
        rogue.write_text("""import os,json,hashlib
from pathlib import Path
job=Path(os.environ['FRA_JOB']);out=Path(os.environ['FRA_OUTPUT_DIR'])
p=job/'ingest'/'source_manifest.json'
doc={'stage':os.environ['FRA_STAGE'],'outcome':'PASS','source_sha256':os.environ['FRA_SOURCE_SHA256'],
'reviewed_at_utc':'2026-11-22T00:00:00Z','checks':{k:True for k in json.loads(os.environ['FRA_REQUIRED_CHECKS'])},
'artifacts':[{'path':str(p.relative_to(job)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}
(out/'evidence.json').write_text(json.dumps(doc))
""",encoding='utf8')
        config=json.loads(self.config.read_text())
        config['stages']['N00']['argv']=[str(rogue)]
        conf=self.top/'rogue.json';conf.write_text(json.dumps(config))
        result=runner.run(self.job,conf,'N00')
        self.assertEqual(result['status'],'FAILED')
        self.assertIn('attempt',result['reason'])

    def test_modified_source_during_run_cannot_publish_done(self):
        runner.run(self.job,self.config,'N00')
        attack=self.top/'mutate-source.py'
        attack.write_text(STAGE_SCRIPT+"\nPath(os.environ['FRA_SOURCE']).write_bytes(b'changed-by-adapter')\n",encoding='utf8')
        cfg=json.loads(self.config.read_text())
        cfg['stages']['N01']['argv']=[str(attack)]
        replacement=self.top/'source-mutation.json';replacement.write_text(json.dumps(cfg))
        s=estate.read_state(self.job);s['config_sha256']=sha(replacement)
        estate.atomic_state(self.job,s)
        result=runner.run(self.job,replacement,'N01')
        self.assertEqual(result['status'],'FAILED')
        self.assertIn('source',result['reason'].lower())

    def test_modified_config_during_run_cannot_publish_done(self):
        runner.run(self.job,self.config,'N00')
        attack=self.top/'mutate-config.py'
        attack.write_text(STAGE_SCRIPT+'\nPath('+repr(str(self.config))+').write_text("UNTRUSTED")\n',encoding='utf8')
        cfg=json.loads(self.config.read_text())
        cfg['stages']['N01']['argv']=[str(attack)]
        self.config.write_text(json.dumps(cfg))
        s=estate.read_state(self.job);s['config_sha256']=sha(self.config)
        estate.atomic_state(self.job,s)
        result=runner.run(self.job,self.config,'N01')
        self.assertEqual(result['status'],'FAILED')
        self.assertIn('config',result['reason'].lower())

    def test_stale_stage_with_exhausted_budget_fails_before_mutation(self):
        runner.run(self.job,self.config,'N00')
        s=estate.read_state(self.job)
        a=self.job/s['stages']['N00']['artifacts'][0]['path']
        a.write_text('corrupted output')
        cfg=json.loads(self.config.read_text())
        cfg['stages']['N00']['max_attempts']=1
        one=self.top/'one.json';one.write_text(json.dumps(cfg))
        s['config_sha256']=sha(one)
        estate.atomic_state(self.job,s)
        with self.assertRaises(ValueError):
            runner.run(self.job,one,'N00',rerun_stale=True)
        self.assertEqual(estate.reconcile(self.job)['stages']['N00']['status'],'STALE')

    def test_n00_manifest_cannot_claim_wrong_source_sha(self):
        fake=self.top/'fake-hash.py'
        fake.write_text(STAGE_SCRIPT+"""
# maliciously amend the stage manifest and recompute its declared checksum
manifest=out/'source_manifest.json'
manifest.write_text(json.dumps({'source_sha256':'0'*64}))
artifacts[0]['sha256']=hashlib.sha256(manifest.read_bytes()).hexdigest()
doc['artifacts']=artifacts
(out/'evidence.json').write_text(json.dumps(doc))
""",encoding='utf8')
        cfg=json.loads(self.config.read_text());cfg['stages']['N00']['argv']=[str(fake)]
        c=self.top/'fakehash.json';c.write_text(json.dumps(cfg))
        result=runner.run(self.job,c,'N00')
        self.assertEqual(result['status'],'FAILED')
        self.assertIn('source',result['reason'].lower())

    def write_receipt(self,gate,digest):
        receipt=sign_receipt(jobctl.read_job(self.job)['job_id'],gate,digest,self.key,ttl_seconds=120)
        (self.approvals/f'{gate}.json').write_text(json.dumps(receipt),encoding='utf8')

    def seed_done(self,*stages):
        s=estate.load_or_init(self.job,self.config)
        for stage in stages:
            work=self.job/'.engine21'/'attempts'/stage/'0001'
            work.mkdir(parents=True,exist_ok=True)
            product=work/'product.txt';product.write_text(stage)
            evidence=work/'evidence.json';evidence.write_text(json.dumps({'stage':stage}))
            s['stages'][stage].update(status='DONE',attempts=1,
                artifacts=[{'path':str(product.relative_to(self.job)), 'sha256':sha(product)}],
                evidence_path=str(evidence.relative_to(self.job)),evidence_sha256=sha(evidence))
        estate.atomic_state(self.job,s)

if __name__=='__main__':unittest.main()
