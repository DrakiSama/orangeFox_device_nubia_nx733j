#!/usr/bin/env python3
"""Exercise production sensor discovery with isolated sysfs and a virtual clock."""
from pathlib import Path
import subprocess, tempfile, sys, os
source=Path(sys.argv[1]).read_text()
for scenario in ["immediate","late","missing","pmic-only","link-error"]:
    with tempfile.TemporaryDirectory(prefix="twrp-cpu-test-") as temp:
        root=Path(temp)
        thermal=root/"sys/class/thermal"
        thermal.mkdir(parents=True)
        (root/"tmp").mkdir()
        (root/"dev").mkdir()
        (root/"bin").mkdir()
        def zone(name,kind):
            d=thermal/name
            d.mkdir(exist_ok=True)
            (d/"type").write_text(kind)
            (d/"temp").write_text("45100\n")
        zone("thermal_zone1","pm8010m_tz")
        if scenario in ["immediate","link-error"]:
            zone("thermal_zone25","cpuss-0-0")
        # Test-only sleep advances a counter and optionally hot-adds the sensor.
        sleep="""#!/bin/sh
n=0
[ ! -f "$TEST_ROOT/ticks" ] || n=$(cat "$TEST_ROOT/ticks")
n=$((n + 1))
echo "$n" > "$TEST_ROOT/ticks"
if [ "$TEST_SCENARIO" = late ] && [ "$n" -eq 3 ]; then
    mkdir -p "$TEST_ROOT/sys/class/thermal/thermal_zone28"
    echo cpuss-0-0 > "$TEST_ROOT/sys/class/thermal/thermal_zone28/type"
    echo 45100 > "$TEST_ROOT/sys/class/thermal/thermal_zone28/temp"
fi
"""
        (root/"bin/sleep").write_text(sleep)
        (root/"bin/sleep").chmod(0o755)
        if scenario=="link-error":
            (root/"bin/ln").write_text("#!/bin/sh\nexit 1\n")
            (root/"bin/ln").chmod(0o755)
        # Only path substitution; the production control flow runs unchanged.
        script=source.replace("/sys/class/thermal",str(thermal)).replace("/tmp/nx733j-cpu-temp",str(root/"tmp/nx733j-cpu-temp")).replace("/dev/kmsg",str(root/"dev/kmsg"))
        env=dict(os.environ,PATH=str(root/"bin")+":"+os.environ["PATH"],TEST_ROOT=str(root),TEST_SCENARIO=scenario)
        r=subprocess.run(["sh","-c",script],env=env,capture_output=True,timeout=30)
        ticks=int((root/"ticks").read_text()) if (root/"ticks").exists() else 0
        link=root/"tmp/nx733j-cpu-temp"
        if scenario in ["immediate","late"]:
            assert r.returncode==0 and link.is_symlink(),(scenario,r)
            assert link.read_text()=="45100\n"
            assert ticks==(3 if scenario=="late" else 0)
            assert link.resolve().parent.name==("thermal_zone28" if scenario=="late" else "thermal_zone25")
        else:
            assert r.returncode!=0 and not link.exists(),(scenario,r)
            assert ticks==(0 if scenario=="link-error" else 29)
print("CPU discovery: 5 scenarios passed (late probe, missing sensor, PMIC rejection, link failure)")
