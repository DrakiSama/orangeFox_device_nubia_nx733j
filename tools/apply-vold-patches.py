#!/usr/bin/env python3
"""Apply reviewed recovery keystore startup and provisioning-keyring fixes."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys

tree = Path(__file__).resolve().parents[1]
vold = Path(sys.argv[1]).resolve()
changes = [
    ('Keymaster.cpp', 'vold-keymaster-sha256', 'bounded-keystore-startup.patch', 'test-keystore-startup.py'),
    ('KeyUtil.cpp', 'vold-keyutil-sha256', 'recovery-fscrypt-keyring.patch', 'test-fscrypt-keyring.py'),
    ('Decrypt.cpp', 'vold-decrypt-sha256', 'gatekeeper-aidl-decrypt.patch', None),
    ('Android.bp', 'vold-android-bp-sha256', 'gatekeeper-aidl-build.patch', None),
]
if (vold/'nx733j').exists():
    sys.exit('vold/nx733j already exists; use a clean checkout')
# Validate all source hashes and patches before mutating either file.
for name, digest, patch, test in changes:
    expected = (tree/'.github'/digest).read_text().strip()
    if hashlib.sha256((vold/name).read_bytes()).hexdigest() != expected:
        sys.exit('Unreviewed vold ' + name + '; review before patching')
    subprocess.run(['git', '-C', str(vold), 'apply', '--check', str(tree/'.github/vold-patches'/patch)], check=True)
for name, digest, patch, test in changes:
    subprocess.run(['git', '-C', str(vold), 'apply', str(tree/'.github/vold-patches'/patch)], check=True)
    if test:
        subprocess.run([sys.executable, str(tree/'.github/tests'/test), str(vold/name)], check=True)
shutil.copytree(tree/'.github/vold-support', vold/'nx733j')
# Keep the template invisible to Soong while it lives in the device tree.
(vold/'nx733j/gatekeeper/Android.bp.in').rename(vold/'nx733j/gatekeeper/Android.bp')
subprocess.run([sys.executable, str(tree/'.github/tests/test-gatekeeper-aidl.py'), str(vold)], check=True)
