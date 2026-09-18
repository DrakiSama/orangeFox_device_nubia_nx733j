#!/system/bin/sh
# Run after mounting the active slot's modem firmware read-only.
# qti_battery_charger requires the ADSP firmware to expose battery/USB supplies.
# Never change firmware selection, load arbitrary modules, or restart a running DSP.
report() { echo "nx733j-recovery: $*" > /dev/kmsg; }
if [ ! -r /firmware/image/adsp.mdt ]; then
    report 'ADSP firmware missing; battery initialization skipped'
    exit 1
fi
for attempt in 1 2 3 4 5; do
    for processor in /sys/class/remoteproc/remoteproc*; do
        [ -r "$processor/name" ] || continue
        [ "$(cat "$processor/name")" = '3000000.remoteproc-adsp' ] || continue
        [ "$(cat "$processor/firmware")" = 'adsp.mdt' ] || {
            report 'Unexpected ADSP firmware selection; refusing to start'
            exit 1
        }
        state=$(cat "$processor/state")
        case "$state" in
            running) ;;
            offline)
                echo start > "$processor/state" || {
                    report 'ADSP start failed'
                    exit 1
                }
                ;;
            *) report "ADSP state $state; leaving unchanged"; exit 1 ;;
        esac
        for poll in 1 2 3 4 5 6 7 8 9 10; do
            if [ -r /sys/class/power_supply/battery/capacity ]; then
                report 'ADSP ready; battery capacity interface available'
                exit 0
            fi
            sleep 1
        done
        report 'ADSP started but battery interface did not appear'
        exit 1
    done
    sleep 1
done
report 'ADSP remoteproc not found'
exit 1
