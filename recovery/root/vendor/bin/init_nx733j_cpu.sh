#!/system/bin/sh
# Probe order varies. Wait independently of ADSP and never substitute a PMIC sensor.
report() { echo "nx733j-cpu: $*" > /dev/kmsg; }
attempt=0
while [ "$attempt" -lt 30 ]; do
    attempt=$((attempt + 1))
    for zone in /sys/class/thermal/thermal_zone*; do
        [ -r "$zone/type" ] || continue
        [ "$(cat "$zone/type")" = cpuss-0-0 ] || continue
        [ -r "$zone/temp" ] || continue
        if ln -sfn "$zone/temp" /tmp/nx733j-cpu-temp; then
            report "CPU sensor available: $zone"
            exit 0
        fi
        report 'Unable to create CPU sensor link'
        exit 1
    done
    [ "$attempt" -eq 30 ] || sleep 1
done
report 'CPU sensor cpuss-0-0 not available after 30 probes'
exit 1
