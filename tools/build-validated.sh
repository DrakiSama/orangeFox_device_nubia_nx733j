#!/bin/bash
# Run from an official, synced fox_12.1 source root on Linux.
set -Ee -o pipefail
tree=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
root=$PWD
artifacts=${1:?Usage: bash tools/build-validated.sh /absolute/artifact-directory}
[[ "$artifacts" = /* ]] || { echo 'Artifact path must be absolute'; exit 1; }
[[ -f build/envsetup.sh && -f vendor/recovery/OrangeFox_A12.sh && -f vendor/twrp/config/common.mk ]]
grep -q 'orangefox_envsetup' build/make/envsetup.sh
[[ ! -e device/nubia/NX733J ]] || { echo 'Device destination already exists; use a separate build tree.'; exit 1; }
mkdir -p "$artifacts" device/nubia/NX733J
revision=$(git -C "$tree" rev-parse HEAD)
git -C "$tree" archive "$revision" | tar -x -C device/nubia/NX733J
device=$root/device/nubia/NX733J
python3 "$device/tools/apply-build-patches.py" "$root/build/make" | tee "$artifacts/build-compat.log"
python3 "$device/tools/apply-recovery-patches.py" "$root/bootable/recovery"
python3 "$device/tools/validate-port.py" "$root/bootable/recovery" | tee "$artifacts/tests.log"
python3 "$device/.github/tests/test-artifact-validation.py" "$device" "$root" | tee "$artifacts/boot-image-tools-test.log"
repo manifest -r -o "$artifacts/manifest.xml"
{
    printf 'device_tree=%s\n' "$revision"
    for project in bootable/recovery vendor/recovery vendor/twrp build/make system/update_engine; do
        printf '%s=%s\n' "$project" "$(git -C "$project" rev-parse HEAD)"
        git -C "$project" diff --binary > "$artifacts/${project//\//-}.patch"
    done
    printf 'sync=%s\n' "$(cat "$device/.github/sync-revision")"
} > "$artifacts/sources.txt"
export USE_CCACHE=1
export CCACHE_EXEC=$(command -v ccache)
export CCACHE_DIR=$root/out/ccache
export CCACHE_BASEDIR=$root
mkdir -p "$CCACHE_DIR"
ccache -M 10G
ccache -o compression=true
printf 'TW_DEVICE_VERSION := by Draki %s\n' "${revision:0:12}" > "$device/build-version.mk"
# The official envsetup ends with an optional [ -s ... ] && command,
# which returns 1 when its optional file is absent. It is not errexit-safe.
set +e
source build/envsetup.sh
set -e
declare -F lunch m >/dev/null
[[ "${NOT_ORANGEFOX:-}" != 1 ]]
source "$device/vendorsetup.sh"
if lunch ofrp_NX733J-eng > "$artifacts/lunch.log" 2>&1; then
    cat "$artifacts/lunch.log"
else
    cat "$artifacts/lunch.log"
    exit 1
fi
# Record only explicitly declared device flags; never export runner secrets.
while read -r name; do printf '%s=%s\n' "$name" "${!name}"; done \
    < <(sed -n 's/^export \(FOX_[A-Z0-9_]*\)=.*/\1/p' "$device/vendorsetup.sh") \
    > "$artifacts/fox-variables.txt"
m recoveryimage -j"${BUILD_JOBS:-4}" 2>&1 | tee "$artifacts/build.log"
image=out/target/product/NX733J/recovery.img
[[ -s "$image" ]] && (( $(stat -c %s "$image") <= 104857600 ))
python3 "$device/tools/verify-ramdisk.py" out/target/product/NX733J/recovery/root
python3 "$device/tools/verify-image.py" "$root" "$image"
cp "$image" "$artifacts/OrangeFox-NX733J-${revision:0:12}.img"
(cd "$artifacts" && sha256sum ./*.img > SHA256SUMS)
ccache -s > "$artifacts/ccache.txt"
if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
    {
        echo '### OrangeFox NX733J'
        printf 'Device tree: `%s`\n\n' "$revision"
        printf 'Recovery: `%s`\n\n' "$(git -C bootable/recovery rev-parse HEAD)"
        printf 'Image size: %s bytes\n\n' "$(stat -c %s "$image")"
        cat "$artifacts/SHA256SUMS"
        echo 'Tests and ramdisk checks passed. Physical NX733J validation is still required.'
    } >> "$GITHUB_STEP_SUMMARY"
fi
