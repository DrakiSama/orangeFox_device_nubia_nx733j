#!/usr/bin/env python3
"""Run all source and simulated runtime tests; never connects to a phone."""
from pathlib import Path
import subprocess
import sys

tree = Path(__file__).resolve().parents[1]
source = Path(sys.argv[1]).resolve()
tests = tree / '.github/tests'
jobs = [
    ('test-cli-result.py', source),
    ('test-keymint-linkage.py', source),
    ('test-cpu-discovery.py', tree / 'recovery/root/vendor/bin/init_nx733j_cpu.sh'),
    ('test-late-cpu-sensor.py', source / 'data.cpp'),
    ('test-image-preflight.py', source / 'partition.cpp'),
    ('test-logical-image.py', source / 'partition.cpp'),
    ('test-flags-parser.py', source / 'partitionmanager.cpp'),
    ('test-device-tree.py', tree),
    ('test-bootctrl-init.py', source/'etc/init/android.hardware.boot@1.2-service.rc'),
    ('test-crypto-startup.py', tree),
    ('test-artifact-validation.py', tree),
]
failed = []
for name, arg in jobs:
    print('\n=== ' + name + ' ===', flush=True)
    if subprocess.run([sys.executable, str(tests / name), str(arg)]).returncode:
        failed.append(name)
if failed:
    sys.exit('FAILED: ' + ', '.join(failed))
print('\nAll eleven test suites passed. Hardware and full Android build are separate validations.')
