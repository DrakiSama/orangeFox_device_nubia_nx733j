#!/usr/bin/env python3
"""Run the real startup script against fake mounts/properties; no phone access."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

tree = Path(sys.argv[1]).resolve()
source = (tree/'recovery/root/vendor/bin/nx733j-keymint.sh').read_text()
for case in ['slot_a', 'slot_b', 'missing_device', 'bad_slot', 'bad_patch', 'bad_os', 'mount_failure']:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        base = tmp/'props'
        (base/'system/system').mkdir(parents=True)
        (base/'vendor').mkdir()
        release = 'invalid' if case == 'bad_os' else '16'
        patch = 'invalid' if case == 'bad_patch' else '2026-02-01'
        (base/'system/system/build.prop').write_text(f'ro.build.version.release={release}\nro.build.version.security_patch={patch}\n')
        (base/'vendor/build.prop').write_text('ro.vendor.build.security_patch=2025-12-01\n')
        slot = '_b' if case == 'slot_b' else '_a'
        if case != 'missing_device':
            for part in ['system', 'vendor']: (tmp/(part+slot)).touch()
        if case == 'bad_slot': slot = ''
        script = source.replace('/tmp/nx733j-crypto-props', base.as_posix())
        script = script.replace('/dev/block/mapper/', tmp.as_posix()+'/').replace('[ ! -b ', '[ ! -e ')
        script = script.replace('/dev/kmsg', (tmp/'error').as_posix())
        script = script.replace('exec /vendor/bin/hw/android.hardware.security.keymint-service-qti', 'echo KEYMINT_STARTED')
        mocks = f"getprop() {{ printf '%s' '{slot}'; }}\n"
        mocks += 'sleep() { :; }\nresetprop() { echo "PROP $*"; }\numount() { echo "UMOUNT $*"; }\n'
        mocks += ('mount() { return 1; }\n' if case == 'mount_failure' else 'mount() { echo "MOUNT $*"; }\n')
        result = subprocess.run(['bash'], input=mocks+script, text=True, capture_output=True)
        ok = case in ['slot_a', 'slot_b']
        assert (result.returncode == 0) == ok, (case, result.stdout, result.stderr)
        assert ('KEYMINT_STARTED' in result.stdout) == ok, case
        if ok:
            assert 'PROP ro.build.version.release 16' in result.stdout
            assert 'PROP ro.build.version.security_patch 2026-02-01' in result.stdout
            assert 'PROP ro.vendor.build.security_patch 2025-12-01' in result.stdout
            assert result.stdout.index('UMOUNT') < result.stdout.index('PROP') < result.stdout.index('KEYMINT_STARTED')
            assert 'MOUNT -t erofs -o ro' in result.stdout
        else:
            assert 'PROP ' not in result.stdout, case
for p in (tree/'recovery/root').rglob('*.xml'):
    if 'vintf' not in p.parts: continue
    root = ET.parse(p).getroot()
    if root.tag != 'manifest': continue
    assert float(root.attrib['version']) <= 4
    assert root.attrib['type'] == ('framework' if 'system' in p.relative_to(tree/'recovery/root').parts else 'device')
assert not (tree/'recovery/root/system/etc/vintf/manifest/nx733j-hals.xml').exists()
print('Crypto startup: both slots, missing devices, malformed properties, mount failure and VINTF ownership passed')
