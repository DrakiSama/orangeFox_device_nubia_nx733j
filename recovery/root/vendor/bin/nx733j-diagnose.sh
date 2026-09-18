#!/system/bin/sh
# Read-only support report. No serials, user files, writes, mounts or settings.
export PATH=/sbin:/system/bin
echo 'NX733J recovery diagnostics'
for property in ro.twrp.version ro.twrp.device.version ro.boot.slot_suffix sys.usb.config sys.usb.state init.svc.vendor.recovery-hardware init.svc.vendor.recovery-cpu; do
    printf '%s: ' "$property"
    getprop "$property"
done
printf 'Kernel: '; uname -r
printf 'UTC clock: '; date -u
printf 'CPU link: '
if [ -L /tmp/nx733j-cpu-temp ]; then
    readlink /tmp/nx733j-cpu-temp
    printf 'CPU linked reading (millidegrees C): '
    cat /tmp/nx733j-cpu-temp 2>/dev/null || echo 'unavailable'
else
    echo 'absent'
fi
[ -r /sys/class/power_supply/battery/capacity ] || echo 'Battery interface: absent'
echo 'Battery temp below is in tenths of a degree C; CPU uses millidegrees C.'
for value in capacity status temp; do
    file="/sys/class/power_supply/battery/$value"
    if [ -r "$file" ]; then printf 'Battery %s: ' "$value"; cat "$file"; fi
done
for processor in /sys/class/remoteproc/remoteproc*; do
    [ -r "$processor/name" ] || continue
    printf 'Remoteproc '; cat "$processor/name"
    cat "$processor/state"
done
if [ -r /sys/class/leds/vibrator/ram_num ]; then
    printf 'Haptics: '; cat /sys/class/leds/vibrator/ram_num
fi
cpu_found=false
for zone in /sys/class/thermal/thermal_zone*; do
    [ -r "$zone/type" ] || continue
    [ "$(cat "$zone/type")" = cpuss-0-0 ] || continue
    cpu_found=true
    printf 'CPU cpuss-0-0 (millidegrees C): '; cat "$zone/temp"
done
$cpu_found || echo 'CPU sensor cpuss-0-0: absent'
slot=$(getprop ro.boot.slot_suffix)
case "$slot" in _a|_b) ;; *) echo 'Invalid slot'; exit 1 ;; esac
for part in boot init_boot vendor_boot recovery dtbo; do
    device="/dev/block/by-name/${part}${slot}"
    printf '%s: ' "$part"
    readlink -f "$device"
    blockdev --getsize64 "$device"
done
for part in system system_ext product vendor odm vendor_dlkm system_dlkm; do
    device="/dev/block/mapper/${part}${slot}"
    printf '%s: ' "$part"
    if [ -b "$device" ]; then
        readlink -f "$device"
        blockdev --getsize64 "$device"
        printf 'Read-only: '; blockdev --getro "$device"
    else
        echo 'mapping absent'
    fi
done
echo 'Relevant mounts:'
grep -E ' /(data|metadata|firmware|vendor_dlkm|system_dlkm) ' /proc/mounts
echo 'Hardware initialization log:'
dmesg | grep -E 'nx733j-recovery:|nx733j-cpu:|vendor.recovery-hardware|vendor.recovery-cpu' | tail -12

# An empty optional log/mount section is not a failed report.
exit 0
