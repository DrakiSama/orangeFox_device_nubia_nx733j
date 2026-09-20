#!/usr/bin/env python3
"""Validate the entire patch series in a scratch directory before changing source."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

tree = Path(__file__).resolve().parents[1]
source = Path(sys.argv[1]).resolve()
expected = (tree / '.github/recovery-revision').read_text().strip()
def git(*args, cwd=source):
    return subprocess.check_output(['git', '-C', str(cwd), *args], stderr=subprocess.STDOUT)

if git('rev-parse', 'HEAD').decode().strip() != expected:
    sys.exit('Recovery HEAD differs from the reviewed fox_12.1 revision; review before updating the pin.')
patches = [tree / '.github/patches' / name for name in
           (tree / '.github/patches/series').read_text().splitlines() if name and not name.startswith('#')]
files = sorted({line[6:] for patch in patches for line in patch.read_text().splitlines()
                if line.startswith('--- a/')})
if git('status', '--porcelain', '--', *files).strip():
    sys.exit('Patched source files are dirty. Use a clean checkout; no reset is performed.')
with tempfile.TemporaryDirectory(prefix='fox-patch-check-') as tmp:
    scratch = Path(tmp)
    for name in files:
        path = scratch / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, path)
    for patch in patches:
        git('apply', '--check', str(patch), cwd=scratch)
        git('apply', str(patch), cwd=scratch)
        print('Checked:', patch.name)
    for patch in patches:
        git('apply', str(patch))
print('All reviewed patches applied.')
