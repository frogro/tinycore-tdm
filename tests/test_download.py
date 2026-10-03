import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('download_installer', Path(__file__).resolve().parents[1] / 'scripts/install-usb.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.data = {name: ('payload:' + name).encode() for name in installer.REQUIRED}
        self.manifest = {'version': 1, 'files': [dict(path=name, size=len(data), sha256=hashlib.sha256(data).hexdigest())
                                               for name, data in sorted(self.data.items())]}
        self.commit = 'a' * 40

    def fake_fetch(self, url, limit):
        if '/commits/' in url:
            return json.dumps({'sha': self.commit}).encode()
        prefix = f'https://raw.githubusercontent.com/{installer.REPOSITORY}/{self.commit}/'
        self.assertTrue(url.startswith(prefix), url)
        name = url.removeprefix(prefix)
        if name == 'install-manifest.json':
            return json.dumps(self.manifest).encode()
        return self.data[name]

    def test_resolves_branch_once_and_checks_all_payload_files(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(installer, 'fetch', side_effect=self.fake_fetch) as fetch:
            destination = Path(tmp)
            files = installer.download_payload(destination, 'main')
            self.assertEqual(len(files), 5)
            self.assertEqual((destination / 'SOURCE-COMMIT.txt').read_text().strip(), self.commit)
            self.assertEqual(sum('/commits/' in call.args[0] for call in fetch.call_args_list), 1)
            for name, data in self.data.items():
                self.assertEqual((destination / name).read_bytes(), data)

    def test_optional_downloads_follow_selection(self):
        self.manifest['optional_files'] = []
        for name in sorted(installer.OPTIONAL):
            data = ('optional:' + name).encode()
            self.data[name] = data
            self.manifest['optional_files'].append(dict(path=name, size=len(data), sha256=hashlib.sha256(data).hexdigest()))
        for layout, ssh, count in [('us', False, 5), ('de', False, 6), ('us', True, 6), ('de', True, 7)]:
            with self.subTest(layout=layout, ssh=ssh), tempfile.TemporaryDirectory() as tmp, patch.object(installer, 'fetch', side_effect=self.fake_fetch):
                root = Path(tmp)
                self.assertEqual(len(installer.download_payload(root, 'main', layout, ssh)), count)
                self.assertEqual((root / 'tce/optional/kmaps.tcz').exists(), layout == 'de')
                self.assertEqual((root / 'tce/optional/dropbear.tcz').exists(), ssh)

    def test_invalid_manifest_paths_duplicates_and_missing_files(self):
        for name in ['../../etc/shadow', '/etc/shadow', 'tce/mydata.tgz', 'boot/../grub.cfg']:
            manifest = copy.deepcopy(self.manifest)
            manifest['files'][0]['path'] = name
            with self.subTest(name=name), self.assertRaises(ValueError):
                installer.manifest_entries(manifest)
        for entries in [self.manifest['files'][:-1], self.manifest['files'] + [self.manifest['files'][0]]]:
            with self.assertRaises(ValueError):
                installer.manifest_entries({'version': 1, 'files': entries})

    def test_corrupt_download_aborts_without_publishing_directory(self):
        self.data['boot/custom.gz'] = b'corrupt'
        with tempfile.TemporaryDirectory() as tmp, patch.object(installer, 'fetch', side_effect=self.fake_fetch), \
             patch.object(installer, 'install') as install:
            output = Path(tmp) / 'payload'
            with self.assertRaises(ValueError):
                installer.main(['--download-only', str(output)])
            self.assertFalse(output.exists())
            install.assert_not_called()

    def test_local_modification_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(installer, 'fetch', side_effect=self.fake_fetch):
            root = Path(tmp)
            installer.download_payload(root, self.commit)
            (root / 'grub.cfg').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                installer.payload_files(root)

    def test_repository_manifest_is_current(self):
        self.assertEqual(len(installer.payload_files()), 5)


if __name__ == '__main__':
    unittest.main()
