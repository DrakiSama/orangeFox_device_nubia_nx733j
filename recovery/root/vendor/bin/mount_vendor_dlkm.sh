#!/system/bin/sh
# Only use a logical mapping already prepared by TWRP/liblp.
# Do not create mappings here: Virtual A/B snapshots belong to libsnapshot.
SLOT=$(getprop ro.boot.slot_suffix)
case "$SLOT" in
    _a|_b) ;;
    *) echo "vendor_dlkm: missing or invalid slot suffix" >&2; exit 1 ;;
esac

for i in 1 2 3 4 5 6 7 8 9 10; do
    if grep -q " /vendor_dlkm " /proc/mounts 2>/dev/null; then
        break
    fi
    sleep 1
done

if ! grep -q " /vendor_dlkm " /proc/mounts 2>/dev/null; then
    DEV="/dev/block/mapper/vendor_dlkm${SLOT}"
    if [ -b "$DEV" ]; then
        mkdir -p /vendor_dlkm
        # Stock is EROFS. The ext4 fallback is read-only without journal replay.
        mount -t erofs -o ro "$DEV" /vendor_dlkm 2>/dev/null ||
            mount -t ext4 -o ro,noload "$DEV" /vendor_dlkm || exit 1
    else
        echo "vendor_dlkm: logical mapping not available: $DEV" >&2
        exit 1
    fi
fi

exit 0
