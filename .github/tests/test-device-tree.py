#!/usr/bin/env python3
"""Check device invariants and integration that do not require hardware."""
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

tree = Path(sys.argv[1])
board = (tree / 'BoardConfig.mk').read_text()
assert not re.search(r'^FOX_\w+\s*[:?+]?=', board, re.M)
assert re.search(r'BOARD_RECOVERYIMAGE_PARTITION_SIZE\s*:=\s*104857600\b', board)
assert re.search(r'BOARD_SUPER_PARTITION_SIZE\s*:=\s*17179869184\b', board)
assert 'TW_CUSTOM_CPU_TEMP_PATH := "/tmp/nx733j-cpu-temp"' in board
assert 'TW_NO_HAPTICS := false' in board
for flag in ['TW_INCLUDE_CRYPTO', 'TW_INCLUDE_CRYPTO_FBE', 'TW_INCLUDE_FBE_METADATA_DECRYPT']:
    assert flag + ' := true' in board
assert 'OF_SUPPORT_ALL_BLOCK_OTA_UPDATES := 1' not in board
assert 'FOX_VERSION=' not in (tree / 'vendorsetup.sh').read_text()
# Evaluate the actual Make fragment, including inherited shipping API values.
api = (tree / 'device.mk').read_text().split('# BEGIN NX733J recovery API contract')[1].split('# END NX733J recovery API contract')[0]
for sdk in [32, 35, 36]:
    fixture = f'PLATFORM_SDK_VERSION := {sdk}\nPRODUCT_SHIPPING_API_LEVEL := 35\n' + api
    fixture += '\n.PHONY: check\ncheck:\n\t@echo "$(BOARD_SHIPPING_API_LEVEL)|$(PRODUCT_SHIPPING_API_LEVEL)|$(PRODUCT_VENDOR_PROPERTIES)"\n'
    result = subprocess.check_output(['make', '--no-print-directory', '-f', '-', 'check'], input=fixture, text=True).strip()
    assert result == ('35||ro.product.first_api_level=35' if sdk == 32 else '35|35|'), result
fstab = (tree / 'recovery.fstab').read_text()
rows = [line.split() for line in fstab.splitlines() if line.strip() and not line.startswith('#')]
logical = {r[0] for r in rows if 'logical' in r[-1].split(',')}
assert logical == {'system', 'system_ext', 'product', 'vendor', 'odm', 'vendor_dlkm', 'system_dlkm'}
assert all(r[2] == 'erofs' and 'slotselect' in r[-1] for r in rows if r[0] in logical)
assert all(r[1] != '/super' for r in rows)
flags = (tree / 'recovery/root/system/etc/twrp.flags').read_text()
assert flags == (tree / 'recovery/root/twrp.flags').read_text()
for mount in ['/firmware', '/persist', '/misc', '/persistent', '/vbmeta', '/vbmeta_system']:
    row = next(l for l in flags.splitlines() if l.startswith(mount + ' '))
    assert 'flashimg=0' in row and 'wipeingui=0' in row
rcs = list((tree / 'recovery/root').rglob('*.rc'))
services = {m for p in rcs for m in re.findall(r'^service\s+(\S+)', p.read_text(), re.M)}
init = (tree / 'recovery/root/init.recovery.qcom.rc').read_text()
for service in re.findall(r'^\s+start\s+(\S+)', init, re.M):
    assert service in services, service
assert 'start vendor.qti.vibrator' not in init
assert 'twrp.variant.files_copied' not in '\n'.join(l for l in init.splitlines() if not l.lstrip().startswith('#'))
for p in (tree / 'recovery/root').rglob('*.xml'):
    ET.parse(p)
for p in (tree / 'recovery/root').rglob('*.sh'):
    assert b'\r' not in p.read_bytes(), p
    assert p.read_text().splitlines()[0] in ['#!/system/bin/sh', '#!/sbin/sh'], p
    subprocess.run(['bash', '-n', str(p)], check=True)
subprocess.run(['bash', '-n', str(tree / 'vendorsetup.sh')], check=True)
mount = (tree / 'recovery/root/vendor/bin/mount_vendor_dlkm.sh').read_text()
assert 'mapper/vendor_dlkm' in mount and 'ro,noload' in mount and 'echo "_a"' not in mount
charger = (tree / 'recovery/root/vendor/etc/charger_fw_fstab.qti').read_text()
assert 'slotselect' in charger and '/modem_a' not in charger
print('Device: partition/FBE invariants, protected targets, init service references, XML and shell checks passed')
