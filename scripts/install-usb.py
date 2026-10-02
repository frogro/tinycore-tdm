#!/usr/bin/env python3
"""Install this repository onto an explicitly selected USB disk (Linux only)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = 'NAME,PATH,TYPE,SIZE,TRAN,RO,MODEL,SERIAL,MAJ:MIN,MOUNTPOINTS'


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def inventory():
    result = run('lsblk', '--json', '--bytes', '--tree', '--output', COLUMNS,
                 capture_output=True, text=True)
    return json.loads(result.stdout)['blockdevices']


def walk(device):
    yield device
    for child in device.get('children', []):
        yield from walk(child)


def find_disk(devices, path):
    for device in devices:
        for node in walk(device):
            if node['path'] == path:
                return node
    raise ValueError(f'Gerät nicht gefunden: {path}')


def validate(device):
    if device['type'] != 'disk' or device.get('tran') != 'usb':
        raise ValueError('Nur ein vollständiges USB-Laufwerk ist erlaubt, keine Partition.')
    if device.get('ro') or int(device['size']) < 512 * 1024 * 1024:
        raise ValueError('Das Ziel muss beschreibbar und mindestens 512 MiB groß sein.')
    for node in walk(device):
        if any(node.get('mountpoints') or []):
            raise ValueError(f"{node['path']} ist eingehängt oder als Swap aktiv. Erst aushängen.")
        if node['type'] not in ('disk', 'part'):
            raise ValueError('Das Ziel wird von RAID, LVM oder einem anderen Mapper verwendet.')
        holders = Path('/sys/class/block') / Path(node['path']).name / 'holders'
        if holders.exists() and any(holders.iterdir()):
            raise ValueError(f"{node['path']} wird von einem anderen Blockgerät verwendet.")


def identity(device):
    return tuple(device.get(k) for k in ('path', 'size', 'model', 'serial', 'maj:min'))


def describe(device):
    return (f"{device['path']} | {int(device['size']) / 1024**3:.2f} GiB | "
            f"{(device.get('model') or '').strip()} | Seriennummer: {device.get('serial') or 'unbekannt'}")


def payload_files():
    required = ('EFI/BOOT/BOOTX64.EFI', 'boot/vmlinuz', 'boot/corepure64.gz',
                'boot/custom.gz', 'grub.cfg')
    for name in required:
        if not (ROOT / name).is_file() or not (ROOT / name).stat().st_size:
            raise ValueError(f'Bootdatei fehlt oder ist leer: {name}')
    files = [ROOT / 'grub.cfg']
    for folder in ('EFI', 'boot', 'tce'):
        for path in sorted((ROOT / folder).rglob('*')):
            if path.is_symlink():
                raise ValueError(f'Symlinks werden nicht auf FAT32 kopiert: {path}')
            if path.is_file():
                if path.stat().st_size >= 2**32:
                    raise ValueError(f'Datei zu groß für FAT32: {path}')
                files.append(path)
    return files


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.digest()


def install(device, files):
    path = device['path']
    # Recheck after the user prompt, before the first write.
    fresh = find_disk(inventory(), path)
    validate(fresh)
    if identity(fresh) != identity(device):
        raise ValueError('Das Zielgerät hat sich seit der Auswahl geändert.')
    run('parted', '--script', '--align', 'optimal', path,
        'mklabel', 'gpt', 'mkpart', 'TINYCORE', 'fat32', '1MiB', '100%',
        'set', '1', 'esp', 'on')
    run('partprobe', path)
    run('udevadm', 'settle')
    fresh = find_disk(inventory(), path)
    validate(fresh)
    if identity(fresh) != identity(device):
        raise ValueError('Das Zielgerät hat sich während der Installation geändert.')
    partitions = fresh.get('children', [])
    if len(partitions) != 1 or partitions[0]['type'] != 'part':
        raise ValueError('Die neue Partition ist nicht eindeutig sichtbar. Abbruch.')
    partition = partitions[0]['path']
    run('mkfs.vfat', '-F', '32', '-n', 'TINYCORE', partition)
    directory = tempfile.mkdtemp(prefix='tinycore-usb-')
    destination = Path(directory)
    mounted = False
    try:
        run('mount', '-t', 'vfat', '-o', 'nosuid,nodev,noexec', partition, directory)
        mounted = True
        (destination / 'tce').mkdir(exist_ok=True)
        for source in files:
            target = destination / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        run('sync', '-f', directory)
        for source in files:
            if digest(source) != digest(destination / source.relative_to(ROOT)):
                raise ValueError(f'Prüfsummenfehler: {source.relative_to(ROOT)}')
    finally:
        if mounted:
            # If unmount fails, leave the mount and its files intact for recovery.
            try:
                run('umount', directory)
            except BaseException:
                print(f'Aushängen fehlgeschlagen. Mount bleibt unter {directory}.', file=sys.stderr)
                raise
        destination.rmdir()  # Never recursively delete a possible mount point.
    print('Fertig: Dateien geprüft und USB-Stick ausgehängt. Am iMac mit Alt/Option booten.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list', action='store_true', help='USB-Laufwerke anzeigen')
    parser.add_argument('--device', help='Ganzes USB-Laufwerk, z. B. /dev/sdb')
    parser.add_argument('--dry-run', action='store_true', help='Nur prüfen und Plan anzeigen')
    args = parser.parse_args(argv)
    if not sys.platform.startswith('linux'):
        parser.error('Dieser Installer unterstützt Linux.')
    if not shutil.which('lsblk'):
        raise ValueError('lsblk fehlt (Paket util-linux).')
    if args.list:
        for device in inventory():
            if device.get('tran') == 'usb' and device['type'] == 'disk':
                print(describe(device))
                for node in walk(device):
                    if any(node.get('mountpoints') or []):
                        print(f"  Belegt: {node['path']} {node['mountpoints']}")
        return
    if not args.device:
        parser.error('--device oder --list angeben')
    path = str(Path(args.device).resolve())
    if not Path(path).exists() or not stat.S_ISBLK(Path(path).stat().st_mode):
        raise ValueError('Das Ziel ist kein vorhandenes Blockgerät.')
    device = find_disk(inventory(), path)
    validate(device)
    files = payload_files()
    if sum(p.stat().st_size for p in files) + 64 * 1024**2 > int(device['size']):
        raise ValueError('Nicht genügend Platz für die Bootdateien.')
    print(describe(device))
    print('Plan: Alle Partitionen löschen; GPT + FAT32-ESP mit Label TINYCORE erstellen;')
    print(f'{len(files)} Dateien kopieren, SHA-256 prüfen und aushängen.')
    if args.dry_run:
        print('Probelauf: Es wurde nichts geschrieben.')
        return
    for command in ('parted', 'partprobe', 'udevadm', 'mkfs.vfat', 'mount', 'umount', 'sync'):
        if not shutil.which(command):
            raise ValueError(f'Benötigter Befehl fehlt: {command}')
    if os.geteuid() != 0:
        raise ValueError('Installation benötigt root: mit sudo starten.')
    if not sys.stdin.isatty():
        raise ValueError('Installation benötigt eine interaktive Bestätigung im Terminal.')
    phrase = f'LOESCHEN {path}'
    if input(f'ALLE DATEN AUF {path} GEHEN VERLOREN. Zum Bestätigen "{phrase}" eingeben: ') != phrase:
        raise ValueError('Abgebrochen; nichts geschrieben.')
    install(device, files)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError, EOFError, KeyboardInterrupt) as error:
        print(f'Abbruch: {error}', file=sys.stderr)
        sys.exit(1)
