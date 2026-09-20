#!/usr/bin/env python3
"""Unpack the final boot-image ramdisk and validate what will actually be flashed."""
from pathlib import Path
import gzip
import subprocess
import sys
import tempfile

build, image = map(lambda s: Path(s).resolve(), sys.argv[1:3])
assert 0 < image.stat().st_size <= 104857600
with tempfile.TemporaryDirectory(prefix='fox-final-image-') as tmp:
    tmp = Path(tmp)
    subprocess.run([sys.executable, str(build/'tools/mkbootimg/unpack_bootimg.py'),
                    '--boot_img', str(image), '--out', str(tmp/'unpacked')], check=True)
    ramdisk = tmp/'unpacked/ramdisk'
    assert ramdisk.is_file() and ramdisk.stat().st_size > 0, 'Missing final ramdisk'
    data = ramdisk.read_bytes()
    if data[:2] == b'\x1f\x8b': data = gzip.decompress(data)
    elif data[:4] in [b'\x04\x22\x4d\x18', b'\x02\x21\x4c\x18']:
        data = subprocess.check_output(['lz4', '-dc', str(ramdisk)])
    root = tmp/'root'
    root.mkdir()
    offset = 0
    while True:
        header = data[offset:offset+110]
        assert header[:6] in [b'070701', b'070702'], 'Unsupported cpio archive'
        fields = [int(header[i:i+8], 16) for i in range(6, 110, 8)]
        mode, size, namesize = fields[1], fields[6], fields[11]
        name = data[offset+110:offset+110+namesize-1].decode()
        offset = (offset+110+namesize+3) & ~3
        payload = data[offset:offset+size]
        offset = (offset+size+3) & ~3
        if name == 'TRAILER!!!': break
        relative = Path(name)
        assert not relative.is_absolute() and '..' not in relative.parts
        path = root/relative
        assert not any(p.is_symlink() for p in path.parents if p != root.parent)
        kind = mode & 0o170000
        if kind == 0o040000: path.mkdir(parents=True, exist_ok=True)
        elif kind in [0o100000, 0o120000]:
            path.parent.mkdir(parents=True, exist_ok=True)
            if kind == 0o120000: path.symlink_to(payload.decode())
            else:
                path.write_bytes(payload)
                path.chmod(mode & 0o777)
    subprocess.run([sys.executable, str(Path(__file__).with_name('verify-ramdisk.py')), str(root)], check=True)
