import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('options_installer', Path(__file__).resolve().parents[1] / 'scripts/install-usb.py')
i = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i)


class OptionTests(unittest.TestCase):
    def test_optional_packages_verified_and_selected(self):
        self.assertEqual(len(i.payload_files(i.ROOT)), 5)
        self.assertEqual(len(i.payload_files(i.ROOT, 'de')), 6)
        self.assertEqual(len(i.payload_files(i.ROOT, 'de', True)), 7)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            import shutil
            for p in i.payload_files(i.ROOT, 'de', True) + [i.ROOT / 'install-manifest.json']:
                target = root / p.relative_to(i.ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, target)
            (root / 'tce/optional/dropbear.tcz').write_bytes(b'corrupt')
            i.payload_files(root)
            with self.assertRaises(ValueError):
                i.payload_files(root, ssh=True)

    def test_private_key_and_invalid_public_key_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'key'
            for content in ['-----BEGIN OPENSSH PRIVATE KEY-----', 'ssh-ed25519 !!!!', 'ssh-ed25519 YWJj', 'ssh-ed25519 abc\nsecond key']:
                p.write_text(content)
                with self.subTest(content=content), self.assertRaises(ValueError):
                    i.public_key(p)

    def test_personalization_keeps_source_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)
            i.configure_payload(i.ROOT, i.payload_files(i.ROOT, 'de', True), destination, 'de', key='public-key\n')
            self.assertEqual((destination / 'tce/onboot.lst').read_text(), 'kmaps.tcz\ndropbear.tcz\n')
            self.assertEqual((destination / 'tce/tdm/ssh-mode').read_text(), 'key\n')
            self.assertFalse((destination / 'tce/tdm/password.hash').exists())
            self.assertEqual((destination / 'grub.cfg').read_text().count('kmap=qwertz/de-latin1'), 2)
            i.payload_files(i.ROOT, 'de', True)
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)
            i.configure_payload(i.ROOT, i.payload_files(i.ROOT), destination)
            self.assertEqual((destination / 'tce/onboot.lst').read_text(), '')
            self.assertFalse((destination / 'tce/tdm').exists())

    def test_password_confirmation_and_hash(self):
        with patch.object(i.getpass, 'getpass', side_effect=['short']):
            with self.assertRaises(ValueError):
                i.password_hash()
        with patch.object(i.getpass, 'getpass', side_effect=['example-test-password', 'different']):
            with self.assertRaises(ValueError):
                i.password_hash()
        with patch.object(i.getpass, 'getpass', return_value='example-test-password'):
            first, second = i.password_hash(), i.password_hash()
            self.assertTrue(first.startswith('$6$'))
            self.assertNotEqual(first, second)
            self.assertNotIn('example-test-password', first)
