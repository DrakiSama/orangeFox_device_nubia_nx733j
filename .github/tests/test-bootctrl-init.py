#!/usr/bin/env python3
"""Check the source service actually packaged by OrangeFox, not a vendor override."""
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
assert s.count('service boot-hal-1-2 ') == 1
assert '    override' not in s
for version in ['1.0', '1.1', '1.2']:
    assert 'interface android.hardware.boot@' + version + '::IBootControl default' in s
assert 'setenv LD_PRELOAD /vendor/lib64/libcxx.so:/vendor/lib64/libbase-sdk35.so' in s
assert 'seclabel u:r:recovery:s0' in s
print('BootControl: platform service contains scoped preload and all HIDL interfaces')
