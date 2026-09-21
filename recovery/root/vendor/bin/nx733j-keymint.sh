#!/system/bin/sh
# Read the installed OS identity before KeyMint configures its TEE connection.
# Never use fabricated future patches or mount stock partitions over the ramdisk.
fail() { echo "NX733J KeyMint: $*" > /dev/kmsg; exit 1; }
slot=$(getprop ro.boot.slot_suffix)
case "$slot" in _a|_b) ;; *) fail "invalid slot suffix" ;; esac
base=/tmp/nx733j-crypto-props
mkdir -p "$base/system" "$base/vendor" || exit 1
n=0
while [ ! -b "/dev/block/mapper/system$slot" ] || [ ! -b "/dev/block/mapper/vendor$slot" ]; do
    n=$((n + 1))
    [ "$n" -lt 30 ] || fail "logical devices unavailable"
    sleep 1
done
mount -t erofs -o ro "/dev/block/mapper/system$slot" "$base/system" || fail "system mount"
if ! mount -t erofs -o ro "/dev/block/mapper/vendor$slot" "$base/vendor"; then
    umount "$base/system"
    fail "vendor mount"
fi
read_prop() { sed -n "s/^$1=//p" "$2" | head -n 1; }
os=$(read_prop 'ro\.build\.version\.release' "$base/system/system/build.prop")
patch=$(read_prop 'ro\.build\.version\.security_patch' "$base/system/system/build.prop")
vpatch=$(read_prop 'ro\.vendor\.build\.security_patch' "$base/vendor/build.prop")
umount "$base/vendor"
umount "$base/system"
printf '%s\n' "$os" | grep -Eq '^[0-9]+(\.[0-9]+)*$' || fail "invalid OS version"
for date in "$patch" "$vpatch"; do
    printf '%s\n' "$date" | grep -Eq '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' || fail "invalid security patch"
done
resetprop ro.build.version.release "$os" || exit 1
resetprop ro.build.version.security_patch "$patch" || exit 1
resetprop ro.vendor.build.security_patch "$vpatch" || exit 1
exec /vendor/bin/hw/android.hardware.security.keymint-service-qti
