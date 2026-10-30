import tempfile
import unittest
from pathlib import Path
from scripts.validate_docs import validate

class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'docs').mkdir()
        (self.root / 'SKILL.md').write_text('---\nname: example-skill\ndescription: Use when doing tests.\n---\n\n[guide](docs/guide.md)\n', encoding='utf-8')
        (self.root / 'docs/guide.md').write_text('~~~json\n{"schema_version":"1.0","job_id":"J","source_sha256":"' + 'a'*64 + '","generator":{"name":"x","version":"1","config_hash":"h"},"produced_at":"2026-10-30T00:00:00Z"}\n~~~\n', encoding='utf-8')

    def tearDown(self): self.tmp.cleanup()
    def test_valid_bundle(self): self.assertEqual(validate(self.root), [])
    def test_broken_link(self):
        (self.root / 'docs/guide.md').unlink()
        self.assertTrue(any('Missing target' in x for x in validate(self.root)))
    def test_invalid_json(self):
        (self.root / 'docs/guide.md').write_text('~~~json\n{not-json}\n~~~', encoding='utf-8')
        self.assertTrue(any('Invalid JSON' in x for x in validate(self.root)))
    def test_missing_envelope(self):
        (self.root / 'docs/guide.md').write_text('~~~json\n{"schema_version":"1.0"}\n~~~', encoding='utf-8')
        self.assertTrue(any('Missing envelope' in x for x in validate(self.root)))
    def test_directory_and_external_link(self):
        (self.root / 'SKILL.md').write_text('---\nname: demo\ndescription: Use when demo.\n---\n[dir](docs/) [site](https://example.com) [anchor](#heading)', encoding='utf-8')
        self.assertEqual(validate(self.root), [])
    def test_traversal_outside_repo(self):
        (self.root / 'SKILL.md').write_text('---\nname: demo\ndescription: Use when demo.\n---\n[x](../../outside.txt)', encoding='utf-8')
        self.assertTrue(any('Outside repository' in x for x in validate(self.root)))

if __name__ == '__main__': unittest.main()
