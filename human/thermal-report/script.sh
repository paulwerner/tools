#!/usr/bin/env bash
#
# thermal-report.sh — Linux thermal & load diagnostic report generator
#
# Collects temperatures, fan state, CPU frequency / C-state residency, top CPU and
# memory consumers, interrupt activity, and power-management configuration into a
# single shareable text report.
#
# Tuned for Intel-based ThinkPads (reads thinkpad_acpi fan data when present) but
# works on any Linux box; sections requiring unavailable tools are skipped with a
# note rather than failing the run.
#
# Usage:
#   chmod +x thermal-report.sh
#   sudo ./thermal-report.sh        # recommended: enables turbostat / dmesg / GPU power
#   ./thermal-report.sh             # works without root, but a few sections are limited
#
set -u

REPORT="./thermal-report-$(date +%Y%m%d-%H%M%S).txt"

have() { command -v "$1" >/dev/null 2>&1; }

hr()      { printf '%s\n' "------------------------------------------------------------"; }
section() { printf '\n'; hr; printf '## %s\n' "$1"; hr; }
note()    { printf '   [note] %s\n' "$1"; }

IS_ROOT=0
[ "${EUID:-$(id -u)}" -eq 0 ] && IS_ROOT=1

main() {
  printf '================================================================\n'
  printf ' THERMAL / LOAD DIAGNOSTIC REPORT\n'
  printf ' generated: %s\n' "$(date)"
  printf ' host:      %s\n' "$(hostname)"
  printf ' as root:   %s\n' "$([ "$IS_ROOT" -eq 1 ] && echo yes || echo 'no (some sections limited)')"
  printf '================================================================\n'

  section "SYSTEM / HARDWARE"
  printf 'Model:   %s %s\n' \
    "$(cat /sys/class/dmi/id/sys_vendor 2>/dev/null)" \
    "$(cat /sys/class/dmi/id/product_version 2>/dev/null || cat /sys/class/dmi/id/product_name 2>/dev/null)"
  printf 'Kernel:  %s\n' "$(uname -srmo)"
  printf 'Uptime/load: %s\n' "$(uptime | sed 's/^ *//')"
  if ls /sys/class/power_supply/AC*/online >/dev/null 2>&1; then
    printf 'AC online:   %s (1=plugged in, 0=battery)\n' "$(cat /sys/class/power_supply/AC*/online 2>/dev/null | head -1)"
  fi

  section "CPU"
  if have lscpu; then
    lscpu | grep -Ei 'model name|^CPU\(s\)|core|thread|^CPU MHz|max MHz|min MHz|virtualiz' || true
  fi
  printf '\nCurrent per-core frequency (MHz):\n'
  if grep -q MHz /proc/cpuinfo 2>/dev/null; then
    awk -F: '/MHz/{printf "  cpu%-2d %8.0f\n", n++, $2}' /proc/cpuinfo
  fi
  printf '\nScaling governor / pstate:\n'
  printf '  governor:        %s\n' "$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo n/a)"
  printf '  intel_pstate:    %s\n' "$(cat /sys/devices/system/cpu/intel_pstate/status 2>/dev/null || echo n/a)"
  printf '  turbo disabled:  %s\n' "$(cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null || echo n/a)"

  section "TEMPERATURES (sensors)"
  if have sensors; then
    sensors 2>/dev/null || note "sensors present but returned an error"
  else
    note "lm-sensors not installed -> sudo apt install lm-sensors && sudo sensors-detect --auto"
  fi
  printf '\nKernel thermal zones:\n'
  found_zone=0
  for z in /sys/class/thermal/thermal_zone*; do
    [ -e "$z/temp" ] || continue
    found_zone=1
    t=$(cat "$z/temp" 2>/dev/null)
    ty=$(cat "$z/type" 2>/dev/null)
    printf '  %-22s %d.%d C\n' "$ty" "$((t/1000))" "$(( (t%1000)/100 ))"
  done
  [ "$found_zone" -eq 0 ] && note "no thermal zones exposed under /sys/class/thermal"

  section "FAN"
  if [ -r /proc/acpi/ibm/fan ]; then
    cat /proc/acpi/ibm/fan
  else
    note "/proc/acpi/ibm/fan not readable (thinkpad_acpi not loaded, or not a ThinkPad)"
  fi
  if have sensors; then
    printf '\nFan RPM from sensors:\n'
    sensors 2>/dev/null | grep -i fan || note "no fan RPM line reported by sensors"
  fi

  section "TOP CPU CONSUMERS (instantaneous)"
  if have top; then
    # second sample = instantaneous usage (first sample is averaged since boot)
    top -bn2 -d1 2>/dev/null | awk '/%Cpu/{c++} c==2' | head -25
  fi
  printf '\nps view (avg %%cpu since each process started):\n'
  ps -eo pid,ppid,user,pcpu,pmem,stat,comm --sort=-pcpu 2>/dev/null | head -16

  section "TOP MEMORY CONSUMERS"
  free -h 2>/dev/null
  printf '\n'
  swapon --show 2>/dev/null || true
  printf '\n'
  ps -eo pid,user,pcpu,pmem,rss,comm --sort=-pmem 2>/dev/null | head -16

  section "INTERRUPT ACTIVITY (delta over 3s)"
  printf 'Sampling /proc/interrupts ...\n'
  INT_A=$(mktemp 2>/dev/null) || INT_A=/tmp/.int_a
  INT_B=$(mktemp 2>/dev/null) || INT_B=/tmp/.int_b
  cp /proc/interrupts "$INT_A" 2>/dev/null
  sleep 3
  cp /proc/interrupts "$INT_B" 2>/dev/null
  if [ -r "$INT_A" ] && [ -r "$INT_B" ]; then
    printf 'Top interrupt sources by rate (delta  IRQ line):\n'
    awk '
      NR==FNR {
        s=0; for(i=2;i<=NF;i++) if($i ~ /^[0-9]+$/) s+=$i
        a[$1]=s; next
      }
      {
        s=0; for(i=2;i<=NF;i++) if($i ~ /^[0-9]+$/) s+=$i
        d=s-a[$1]
        if(d>0){ line=$0; gsub(/[ \t]+/," ",line); printf "%8d  %s\n", d, line }
      }
    ' "$INT_A" "$INT_B" | sort -rn | head -15
  else
    note "could not read /proc/interrupts"
  fi
  rm -f "$INT_A" "$INT_B" 2>/dev/null

  section "C-STATE RESIDENCY & PACKAGE POWER (turbostat, ~5s)"
  if [ "$IS_ROOT" -eq 1 ] && have turbostat; then
    { timeout 12 turbostat --quiet --interval 2 --num_iterations 2 2>&1 \
        || timeout 8 turbostat --quiet sleep 5 2>&1 \
        || note "turbostat failed (kernel/version mismatch or msr module missing)"; } | head -40
  elif ! have turbostat; then
    note "turbostat not installed -> sudo apt install linux-tools-common linux-tools-generic"
  else
    note "needs root -> re-run with sudo for C-state residency and package wattage"
  fi

  section "POWER-MANAGEMENT DAEMONS"
  printf 'thermald:                 %s\n' "$(systemctl is-active thermald 2>/dev/null || echo 'not present')"
  if have powerprofilesctl; then
    printf 'power-profiles-daemon:    active, profile = %s\n' "$(powerprofilesctl get 2>/dev/null)"
  else
    printf 'power-profiles-daemon:    not present\n'
  fi
  if have tlp-stat; then
    printf '\nTLP summary:\n'
    tlp-stat -s 2>/dev/null | sed 's/^/  /'
  else
    note "TLP not installed"
  fi
  if have tlp-stat && systemctl is-active --quiet power-profiles-daemon 2>/dev/null; then
    note "BOTH tlp and power-profiles-daemon look active — they conflict; keep only one."
  fi

  section "GPU"
  printf 'Graphics devices:\n'
  if have lspci; then
    lspci 2>/dev/null | grep -Ei 'vga|3d|display' | sed 's/^/  /' || note "no GPU lines from lspci"
  fi
  if have nvidia-smi; then
    printf '\nNVIDIA dGPU status (a powered-up dGPU at idle is a common heat source):\n'
    nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,power.draw,pstate \
      --format=csv 2>/dev/null || nvidia-smi 2>/dev/null | head -20
  fi
  if [ "$IS_ROOT" -eq 1 ] && have intel_gpu_top; then
    printf '\nIntel iGPU activity (sampled):\n'
    timeout 6 intel_gpu_top -l -o - -s 2000 2>/dev/null | head -6 \
      || note "intel_gpu_top sample failed"
  fi

  section "RECENT KERNEL THERMAL / THROTTLE EVENTS"
  thermal_log="$(dmesg 2>/dev/null | grep -iE 'thermal|throttl|temperature|over.?heat|mce|hardware error' | tail -25)"
  if [ -n "$thermal_log" ]; then
    printf '%s\n' "$thermal_log"
  elif [ "$IS_ROOT" -ne 1 ]; then
    note "dmesg empty/restricted — re-run with sudo to read kernel thermal messages"
  else
    note "no thermal/throttle messages in dmesg (good sign)"
  fi

  printf '\n'
  hr
  printf 'END OF REPORT\n'
  hr
}

main 2>&1 | tee "$REPORT"

# hand the file back to the invoking user when run via sudo
if [ -n "${SUDO_USER:-}" ]; then
  chown "$SUDO_USER" "$REPORT" 2>/dev/null || true
fi

printf '\nReport written to: %s\n' "$(readlink -f "$REPORT" 2>/dev/null || echo "$REPORT")"
printf 'Share that file (or paste its contents) for analysis.\n'