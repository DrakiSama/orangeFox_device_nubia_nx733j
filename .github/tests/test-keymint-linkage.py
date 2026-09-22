#!/usr/bin/env python3
"""Guard Make consumers of libvold's generated Gatekeeper/KeyMint parcel code."""
from pathlib import Path
import re
import sys
root = Path(sys.argv[1])
consumers = []
for path in root.rglob('Android.mk'):
    text = path.read_text(encoding='utf-8').replace('\\\n', ' ')
    for module in re.split(r'^include \$\(CLEAR_VARS\)', text, flags=re.M):
        static = ' '.join(re.findall(r'^\s*LOCAL_(?:WHOLE_)?STATIC_LIBRARIES\s*[:+]?=([^\n]*)', module, re.M))
        if 'libvold' not in static.split(): continue
        shared = ' '.join(re.findall(r'^\s*LOCAL_SHARED_LIBRARIES\s*[:+]?=([^\n]*)', module, re.M)).split()
        for dependency in ['android.hardware.security.keymint-V1-ndk_platform',
                           'android.hardware.security.secureclock-V1-ndk_platform']:
            assert dependency in shared, (path, dependency)
        consumers.append(path.relative_to(root).as_posix())
assert {'Android.mk', 'libtar/Android.mk'} <= set(consumers), consumers
print('KeyMint linkage: all libvold Make consumers link KeyMint and SecureClock:', ', '.join(consumers))
