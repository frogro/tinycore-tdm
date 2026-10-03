#!/usr/bin/env python3
"""Build a deterministic additional Linux initramfs from the project files."""
import gzip
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def archive_entry(name, data, mode, inode):
    name = name.encode() + b'\0'
    fields = (inode, mode, 0, 0, 1, 0, len(data), 0, 0, 0, 0, len(name), 0)
    header = b'070701' + ''.join(f'{value:08x}' for value in fields).encode()
    record = header + name
    record += b'\0' * (-len(record) % 4)
    record += data + b'\0' * (-len(data) % 4)
    return record


def build():
    entries = [('etc', b'', stat.S_IFDIR | 0o755),
               ('opt', b'', stat.S_IFDIR | 0o755),
               ('usr', b'', stat.S_IFDIR | 0o755),
               ('usr/local', b'', stat.S_IFDIR | 0o755),
               ('usr/local/bin', b'', stat.S_IFDIR | 0o755)]
    for name, mode in [('etc/inittab', 0o644), ('opt/bootlocal.sh', 0o755),
                       ('opt/ddc_diag.sh', 0o755), ('opt/ssh-start.sh', 0o755)]:
        data = (ROOT / name).read_bytes()
        if b'\r' in data:
            raise ValueError(f'{name}: expected Unix LF line endings')
        entries.append((name, data, stat.S_IFREG | mode))
    for path in sorted((ROOT / 'usr/local/bin').iterdir()):
        entries.append((str(path.relative_to(ROOT)), path.read_bytes(), stat.S_IFREG | 0o755))
    entries.append(('TRAILER!!!', b'', 0))
    payload = b''.join(archive_entry(name, data, mode, i)
                       for i, (name, data, mode) in enumerate(entries, 1))
    payload += b'\0' * (-len(payload) % 512)
    output = ROOT / 'boot/custom.gz'
    with output.open('wb') as stream:
        with gzip.GzipFile(filename='', mode='wb', fileobj=stream, mtime=0) as archive:
            archive.write(payload)
    print(output.relative_to(ROOT))


if __name__ == '__main__':
    build()
