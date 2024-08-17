sudo -i
echo 0 > /proc/sys/kernel/nmi_watchdog
echo off > /sys/devices/system/cpu/smt/control
exit
