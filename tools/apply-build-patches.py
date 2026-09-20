#!/usr/bin/env python3
"""Recognize stock system_dlkm for recovery; does not build or write super images."""
from pathlib import Path
import hashlib
import subprocess
import sys

tree = Path(__file__).resolve().parents[1]
build = Path(sys.argv[1]).resolve()
config = build / 'core/config.mk'
original = config.read_bytes()
# Exact reviewed variants: TeamWin base and the official OrangeFox post-hook.
expected = set((tree / '.github/build-config-sha256').read_text().split())
if hashlib.sha256(original).hexdigest() not in expected:
    sys.exit('Unreviewed build/make/core/config.mk; review before applying compatibility patch')
old = 'valid_super_partition_list := system vendor product system_ext odm vendor_dlkm odm_dlkm'
text = original.decode()
assert text.count(old) == 1
patched = text.replace(old, old + ' system_dlkm')
board = (tree / 'BoardConfig.mk').read_text()
partitions = board.split('BOARD_QTI_DYNAMIC_PARTITIONS_PARTITION_LIST :=', 1)[1].split('\n\n', 1)[0]
partitions = partitions.replace('\\\n', ' ').strip()
assert set(partitions.split()) == {'system', 'system_ext', 'product', 'vendor', 'odm', 'vendor_dlkm', 'system_dlkm'}

def check(source, names, success):
    section = source.split('# BOARD_*_PARTITION_LIST: a list of the following tokens', 1)[1]
    section = section.split('# Define BOARD_SUPER_PARTITION_PARTITION_LIST', 1)[0]
    fixture = 'to-upper = QTI_DYNAMIC_PARTITIONS\nBOARD_SUPER_PARTITION_GROUPS := qti_dynamic_partitions\n'
    fixture += 'BOARD_QTI_DYNAMIC_PARTITIONS_PARTITION_LIST := ' + names + '\n' + section
    fixture += '\n.PHONY: check\ncheck:\n\t@echo accepted\n'
    result = subprocess.run(['make', '--no-print-directory', '-f', '-', 'check'],
                            input=fixture, text=True, capture_output=True)
    assert (result.returncode == 0) == success, result.stderr
    if not success:
        assert 'invalid partition name' in result.stderr, result.stderr

check(text, partitions, False)
check(patched, partitions, True)
check(patched, partitions + ' invalid_partition', False)
makefile = build / 'core/Makefile'
make_expected = set((tree / '.github/build-makefile-sha256').read_text().split())
if hashlib.sha256(makefile.read_bytes()).hexdigest() not in make_expected:
    sys.exit('Unreviewed build/make/core/Makefile; review recovery property integration')
patches = [tree / '.github/build-patches/system-dlkm-name.patch',
           tree / '.github/build-patches/recovery-launch-properties.patch']
patch_args = list(map(str, patches))
subprocess.run(['git', '-C', str(build), 'apply', '--check', *patch_args], check=True)
subprocess.run(['git', '-C', str(build), 'apply', *patch_args], check=True)
assert config.read_bytes() == patched.encode()
print('Build compatibility: system_dlkm accepted; seven stock partitions preserved; invalid names still rejected')

subprocess.run([sys.executable, str(tree / '.github/tests/test-recovery-properties.py'), str(build)], check=True)
