#!/usr/bin/env python3
"""Update the checksummed installer payload after rebuilding custom.gz."""
import hashlib
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
names = ['EFI/BOOT/BOOTX64.EFI', 'boot/vmlinuz', 'boot/corepure64.gz', 'boot/custom.gz', 'grub.cfg']
entries = []
for name in names:
    data = (root / name).read_bytes()
    entries.append(dict(path=name, size=len(data), sha256=hashlib.sha256(data).hexdigest()))
optional = []
for name in ['tce/optional/kmaps.tcz', 'tce/optional/dropbear.tcz']:
    data = (root / name).read_bytes()
    optional.append(dict(path=name, size=len(data), sha256=hashlib.sha256(data).hexdigest()))
(root / 'install-manifest.json').write_text(json.dumps(dict(version=1, files=entries, optional_files=optional), indent=2) + '\n')
print('install-manifest.json')
