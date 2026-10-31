"""Windows CI only: exercise real filesystem canonicalization without source movies."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from review_phim_runtime.winpaths import canonical_windows_path
from review_phim_runtime.scope import _windows_under


@unittest.skipUnless(os.name == 'nt', 'Windows host-only synthetic test')
class RealWindowsPathTests(unittest.TestCase):
    def test_existing_file_resolves_and_nonexistent_file_is_rejected(self):
        with TemporaryDirectory() as directory:
            film = Path(directory) / 'synthetic.txt'
            film.write_text('safe synthetic data', encoding='utf-8')
            final = canonical_windows_path(str(film))
            root = canonical_windows_path(directory)
            self.assertTrue(_windows_under(final, root))
            self.assertTrue(os.path.samefile(final, film))
            with self.assertRaises(ValueError):
                canonical_windows_path(str(film.parent/'missing.txt'))

if __name__ == '__main__':
    unittest.main()
