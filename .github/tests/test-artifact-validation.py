#!/usr/bin/env python3
"""Test our ramdisk checks with synthetic CPIO; this is not a device image build."""
from pathlib import Path
import gzip
import shutil
import subprocess
import sys
import tempfile

tree = Path(sys.argv[1]).resolve()
def run(tool, *args, success=True):
    result = subprocess.run([sys.executable, str(tree/'tools'/tool), *map(str, args)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert (result.returncode == 0) == success, result.stderr.decode()

with tempfile.TemporaryDirectory() as temp:
    temp = Path(temp)
    root = temp/'root'
    source = tree/'recovery/root'
    for name in ['init.recovery.qcom.rc', 'init.recovery.usb.rc',
                 'system/etc/twrp.flags', 'vendor/firmware/haptic_ram.bin',
                 'system/etc/vintf/manifest.xml', 'vendor/etc/vintf/manifest.xml']:
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source/name, path)
    boot_rc = root/'system/etc/init/android.hardware.boot@1.2-service.rc'
    boot_rc.parent.mkdir(parents=True, exist_ok=True)
    boot_rc.write_text('service boot-hal-1-2 /system/bin/android.hardware.boot@1.2-service\n'
                       '    setenv LD_PRELOAD /vendor/lib64/libcxx.so:/vendor/lib64/libbase-sdk35.so\n')
    (root/'sbin').mkdir()
    for name in ['init_nx733j_hardware.sh', 'init_nx733j_cpu.sh', 'nx733j-diagnose.sh', 'mount_vendor_dlkm.sh', 'nx733j-keymint.sh']:
        shutil.copyfile(source/'vendor/bin'/name, root/'sbin'/name)
    shutil.copyfile(tree/'recovery.fstab', root/'system/etc/recovery.fstab')
    (root/'system/lib64/hw').mkdir(parents=True)
    (root/'system/lib64/hw/android.hardware.boot@1.0-impl-1.2-qti.so').write_bytes(b'\x7fELF-test-only')
    (root/'system/bin').mkdir()
    shell = root/'system/bin/mksh'
    shell.write_bytes(b'\x7fELF-test-only')
    (root/'system/bin/sh').symlink_to('/system/bin/mksh')
    props = root/'prop.default'
    props.write_text('ro.product.first_api_level=35\nro.board.first_api_level=35\n')
    run('verify-ramdisk.py', root)
    manifest = root/'system/etc/vintf/manifest.xml'
    duplicate = root/'vendor/etc/init/duplicate-boot.rc'
    duplicate.parent.mkdir(parents=True, exist_ok=True)
    duplicate.write_text(boot_rc.read_text() + '    override\n')
    run('verify-ramdisk.py', root, success=False)
    duplicate.unlink()
    valid_manifest = manifest.read_text()
    manifest.write_text('<manifest version="9.0" type="framework"/>')
    run('verify-ramdisk.py', root, success=False)
    manifest.write_text('<manifest version="4.0" type="device"/>')
    run('verify-ramdisk.py', root, success=False)
    manifest.write_text(valid_manifest)
    props.write_text('ro.product.first_api_level=32\nro.board.first_api_level=35\n')
    run('verify-ramdisk.py', root, success=False)
    props.write_text('ro.product.first_api_level=35\nro.board.first_api_level=35\n')
    shell.unlink()
    run('verify-ramdisk.py', root, success=False)
    shell.write_bytes(b'\x7fELF-test-only')
    payload = bytearray()
    def add(name, content, mode):
        encoded = name.encode() + b'\0'
        fields = [1, mode, 0, 0, 1, 0, len(content), 0, 0, 0, 0, len(encoded), 0]
        payload.extend(b'070701' + ''.join(f'{v:08x}' for v in fields).encode() + encoded)
        payload.extend(b'\0' * (-len(payload) % 4))
        payload.extend(content)
        payload.extend(b'\0' * (-len(payload) % 4))
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            add(path.relative_to(root).as_posix(), path.readlink().as_posix().encode(), 0o120777)
        elif path.is_file():
            add(path.relative_to(root).as_posix(), path.read_bytes(), 0o100755)
    add('TRAILER!!!', b'', 0)
    image = temp/'synthetic.img'
    image.write_bytes(gzip.compress(payload))
    build = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else temp/'build'
    if len(sys.argv) > 2:
        ramdisk = temp/'ramdisk.gz'
        ramdisk.write_bytes(image.read_bytes())
        subprocess.run([sys.executable, str(build/'system/tools/mkbootimg/mkbootimg.py'),
                        '--header_version', '4', '--ramdisk', str(ramdisk),
                        '--output', str(image)], check=True)
    else:
        # Isolated extractor tests; CI additionally exercises the real Android tools.
        unpack = build/'system/tools/mkbootimg/unpack_bootimg.py'
        unpack.parent.mkdir(parents=True)
        unpack.write_text('import sys, pathlib, shutil\n'
                          'out=pathlib.Path(sys.argv[sys.argv.index("--out")+1]); out.mkdir()\n'
                          'shutil.copyfile(sys.argv[sys.argv.index("--boot_img")+1],out/"ramdisk")\n')
    run('verify-image.py', build, image)
    image.write_bytes(b'not cpio')
    run('verify-image.py', build, image, success=False)
    with image.open('wb') as stream: stream.truncate(104857601)
    run('verify-image.py', build, image, success=False)
print('Artifacts: valid root, absolute shell symlink, missing shell, CPIO extraction, invalid archive and oversize rejection passed')
