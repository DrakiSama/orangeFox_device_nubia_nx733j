#!/usr/bin/env python3
"""Exercise real GRF validation and the recovery-only Make property append rule."""
from pathlib import Path
import subprocess
import sys
import tempfile

build = Path(sys.argv[1]).resolve()
tree = Path(__file__).resolve().parents[2]
post = build / 'tools/post_process_props.py'
makefile = (build / 'core/Makefile').read_text()
assignment = next(line for line in makefile.splitlines() if line.startswith('$(INSTALLED_RECOVERY_BUILD_PROP_TARGET): PRIVATE_DEVICE_RECOVERY_PROPERTIES :='))
recipe = next(line for line in makefile.splitlines() if '$(foreach prop,$(PRIVATE_DEVICE_RECOVERY_PROPERTIES),' in line)
board = (tree / 'BoardConfig.mk').read_text()
fragment = board.split('# BEGIN NX733J recovery-only launch properties')[1].split('# END NX733J recovery-only launch properties')[0]
with tempfile.TemporaryDirectory() as directory:
    directory = Path(directory)
    vendor = directory / 'build.prop'
    vendor.write_text('ro.vendor.build.version.sdk=32\nro.board.first_api_level=35\n')
    command = [sys.executable, str(post), '--sdk-version', '32', str(vendor)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode != 0 and 'ro.board.first_api_level(35)' in result.stderr
    vendor.write_text('ro.vendor.build.version.sdk=32\n')
    subprocess.run(command, check=True)
    assert 'ro.board.first_api_level=' not in vendor.read_text()
    for sdk in [32, 35]:
        recovery = directory / f'recovery-{sdk}.prop'
        fixture = f'PLATFORM_SDK_VERSION := {sdk}\n' + fragment
        fixture += f'INSTALLED_RECOVERY_BUILD_PROP_TARGET := {recovery}\nhide := @\n'
        fixture += assignment + '\n$(INSTALLED_RECOVERY_BUILD_PROP_TARGET):\n'
        fixture += f'\t@cat {vendor} > $@\n' + recipe + '\n'
        subprocess.run(['make', '--no-print-directory', '-f', '-'], input=fixture, text=True, check=True)
        properties = dict(line.split('=', 1) for line in recovery.read_text().splitlines() if line and not line.startswith('#'))
        if sdk == 32:
            assert properties['ro.product.first_api_level'] == '35'
            assert properties['ro.board.first_api_level'] == '35'
        else:
            assert 'ro.board.first_api_level' not in properties
        assert properties['ro.vendor.build.version.sdk'] == '32'
print('Properties: real SDK-32 vendor validator kept; launch API 35 appended only to standalone recovery')
