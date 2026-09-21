#!/usr/bin/env python3
"""Apply the reviewed recovery-only keystore startup bound."""
from pathlib import Path
import hashlib
import subprocess
import sys

tree = Path(__file__).resolve().parents[1]
vold = Path(sys.argv[1]).resolve()
source = vold / 'Keymaster.cpp'
expected = (tree / '.github/vold-keymaster-sha256').read_text().strip()
if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
    sys.exit('Unreviewed vold Keymaster.cpp; review before patching')
patch = tree / '.github/vold-patches/bounded-keystore-startup.patch'
subprocess.run(['git', '-C', str(vold), 'apply', '--check', str(patch)], check=True)
subprocess.run(['git', '-C', str(vold), 'apply', str(patch)], check=True)
subprocess.run([sys.executable, str(tree / '.github/tests/test-keystore-startup.py'), str(source)], check=True)
