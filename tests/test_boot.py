import gzip
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BootTests(unittest.TestCase):
    def test_shell_syntax(self):
        for script in list((ROOT / 'opt').glob('*.sh')) + list((ROOT / 'usr/local/bin').glob('tdm_*')):
            with self.subTest(script=script.name):
                self.assertNotIn(b'\r', script.read_bytes())
                subprocess.run(['busybox', 'sh', '-n', str(script)], check=True)
                self.assertTrue(script.stat().st_mode & 0o111)

    def test_overlay_contents_and_reproducibility(self):
        image = ROOT / 'boot/custom.gz'
        committed = image.read_bytes()
        subprocess.run(['python3', str(ROOT / 'scripts/build-overlay.py')], check=True)
        self.assertEqual(committed, image.read_bytes(), 'Rebuild and commit custom.gz')
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(['cpio', '-id', '--quiet', '--no-preserve-owner'],
                           cwd=directory, input=gzip.decompress(image.read_bytes()), check=True)
            for name, mode in [('etc/inittab', 0o644), ('opt/bootlocal.sh', 0o755),
                               ('opt/ddc_diag.sh', 0o755)]:
                extracted = Path(directory) / name
                self.assertEqual(extracted.read_bytes(), (ROOT / name).read_bytes())
                self.assertEqual(extracted.stat().st_mode & 0o777, mode)
            for source in (ROOT / 'usr/local/bin').iterdir():
                extracted = Path(directory) / source.relative_to(ROOT)
                self.assertEqual(extracted.read_bytes(), source.read_bytes())
                self.assertEqual(extracted.stat().st_mode & 0o777, 0o755)
        config = (ROOT / 'grub.cfg').read_text()
        self.assertEqual(config.count('initrd /boot/corepure64.gz /boot/custom.gz'), 2)
        init = (ROOT / 'etc/inittab').read_text()
        self.assertIn('::sysinit:/etc/init.d/rcS', init)
        self.assertNotIn('respawn:/sbin/poweroff', init)

    def test_backlight_requires_a_device(self):
        source = (ROOT / 'opt/ddc_diag.sh').read_text()
        function = source[source.index('has_backlight() {'):source.index('\n# Start')]
        with tempfile.TemporaryDirectory() as directory:
            script = function.replace('/sys/class/backlight', directory) + '\nhas_backlight\n'
            def detected():
                return subprocess.run(['busybox', 'sh'], input=script.encode()).returncode == 0
            self.assertFalse(detected())
            device = Path(directory) / 'device'
            device.mkdir()
            self.assertFalse(detected())
            (device / 'brightness').write_text('50')
            (device / 'max_brightness').write_text('100')
            self.assertTrue(detected())


if __name__ == '__main__':
    unittest.main()
