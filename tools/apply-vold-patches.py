#!/usr/bin/env python3
"""Apply reviewed recovery keystore startup and provisioning-keyring fixes."""
from pathlib import Path
import hashlib
import subprocess
import sys

tree = Path(__file__).resolve().parents[1]
vold = Path(sys.argv[1]).resolve()
changes = [
    ('Keymaster.cpp', 'vold-keymaster-sha256', 'bounded-keystore-startup.patch', 'test-keystore-startup.py'),
    ('KeyUtil.cpp', 'vold-keyutil-sha256', 'recovery-fscrypt-keyring.patch', 'test-fscrypt-keyring.py'),
]
# Validate all source hashes and patches before mutating either file.
for name, digest, patch, test in changes:
    expected = (tree/'.github'/digest).read_text().strip()
    if hashlib.sha256((vold/name).read_bytes()).hexdigest() != expected:
        sys.exit('Unreviewed vold ' + name + '; review before patching')
    subprocess.run(['git', '-C', str(vold), 'apply', '--check', str(tree/'.github/vold-patches'/patch)], check=True)
for name, digest, patch, test in changes:
    subprocess.run(['git', '-C', str(vold), 'apply', str(tree/'.github/vold-patches'/patch)], check=True)
    subprocess.run([sys.executable, str(tree/'.github/tests'/test), str(vold/name)], check=True)
