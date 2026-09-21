#!/usr/bin/env python3
"""Validate contents; resolve absolute symlinks inside the ramdisk root."""
from pathlib import Path, PurePosixPath
import os
import re
import sys
import xml.etree.ElementTree as ET

root = Path(sys.argv[1]).absolute()
assert root.is_dir(), root
def resolve(name):
    parts = list(PurePosixPath('/' + name.lstrip('/')).parts[1:])
    done = []
    hops = 0
    while parts:
        part = parts.pop(0)
        if part == '..':
            assert done, 'Symlink escapes ramdisk'
            done.pop()
            continue
        if part == '.': continue
        candidate = root.joinpath(*done, part)
        if candidate.is_symlink():
            hops += 1
            assert hops < 40, 'Symlink cycle'
            target = PurePosixPath(os.readlink(candidate))
            if target.is_absolute():
                done = []
                parts = list(target.parts[1:]) + parts
            else:
                parts = list(target.parts) + parts
        else:
            done.append(part)
    path = root.joinpath(*done)
    assert path.exists(), name
    return path

for name in ['sbin/init_nx733j_hardware.sh', 'sbin/init_nx733j_cpu.sh',
             'sbin/nx733j-diagnose.sh', 'sbin/mount_vendor_dlkm.sh', 'sbin/nx733j-keymint.sh',
             'system/lib64/hw/android.hardware.boot@1.0-impl-1.2-qti.so',
             'vendor/etc/init/nx733j.bootctrl.rc',
             'init.recovery.qcom.rc', 'init.recovery.usb.rc', 'system/etc/recovery.fstab',
             'system/etc/twrp.flags', 'vendor/firmware/haptic_ram.bin',
             'system/etc/vintf/manifest.xml', 'vendor/etc/vintf/manifest.xml']:
    resolve(name)
for path in root.rglob('*'):
    if path.is_symlink() or not path.is_file(): continue
    if path.suffix == '.xml' and 'vintf' in path.parts:
        xml = ET.parse(path).getroot()
        if xml.tag == 'manifest':
            assert float(xml.attrib['version']) <= 4.0, path
            expected = 'framework' if 'system' in path.relative_to(root).parts else 'device'
            assert xml.attrib.get('type') == expected, path
    with path.open('rb') as stream:
        first = stream.readline(4096)
    if first.startswith(b'#!'):
        assert b'\r' not in first, path
        interpreter = first[2:].decode().strip().split()[0]
        resolve(interpreter)
    if path.suffix == '.rc':
        for line in path.read_text().splitlines():
            if re.match(r'^\s*(service|exec|exec_background)\s', line):
                for shell in re.findall(r'/(?:sbin|system/bin|vendor/bin)/\w*sh\b', line): resolve(shell)
props = resolve('prop.default').read_text().splitlines()
for name in ['ro.product.first_api_level', 'ro.board.first_api_level']:
    values = [line.split('=', 1)[1].strip() for line in props if line.startswith(name + '=')]
    assert values and set(values) == {'35'}, (name, values)
fstab = resolve('system/etc/recovery.fstab').read_text()
assert 'odm_dlkm' not in fstab
for part in ['system', 'system_ext', 'product', 'vendor', 'odm', 'vendor_dlkm', 'system_dlkm']:
    assert re.search(r'^' + part + r'\s+\S+\s+erofs\s', fstab, re.M), part
# Modules are loaded from stock vendor_dlkm; their presence needs device validation.
print('Ramdisk: scripts, shells/symlinks, fstab, VINTF and haptic firmware verified')

boot_rc = resolve('vendor/etc/init/nx733j.bootctrl.rc').read_text()
assert 'service boot-hal-1-2 /system/bin/android.hardware.boot@1.2-service' in boot_rc
assert '    override' in boot_rc
assert 'setenv LD_PRELOAD /vendor/lib64/libcxx.so:/vendor/lib64/libbase-sdk35.so' in boot_rc
