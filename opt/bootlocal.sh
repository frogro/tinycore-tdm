#!/bin/sh
# TinyCore bootlocal.sh (DHCP + optionales SSH + DDC-Diag)

# Safe Console Mode überspringt alle projektspezifischen Dienste.
if grep -qw 'tdm_safe=1' /proc/cmdline; then
  exit 0
fi

# --- Logging vorbereiten ---
LOGDIR=/var/log
mkdir -p "$LOGDIR"
BOOTLOG="$LOGDIR/bootlocal.log"
echo "== bootlocal start: $(date) ==" >> "$BOOTLOG"

# 0) Netz-Interface (falls nicht eth0, z.B. enp2s0)
IFACE="eth0"

# 2) DHCP nur starten, wenn noch keine IPv4 vorhanden ist
if ip addr show "$IFACE" 2>/dev/null | grep -q 'inet '; then
  echo "[net] $IFACE hat bereits IPv4" >> "$BOOTLOG"
else
  echo "[net] starte DHCP auf $IFACE" >> "$BOOTLOG"
  /sbin/udhcpc -b -i "$IFACE" -s /usr/share/udhcpc/default.script \
    >> "$LOGDIR/udhcpc.log" 2>&1
fi

# SSH nur mit expliziter Installer-Konfiguration starten.
/opt/ssh-start.sh >> "$BOOTLOG" 2>&1

# 4) DDC-Diagnose (falls Skript vorhanden) + Log ablegen
DDCLOG="$LOGDIR/ddc_diag_$(date +%Y%m%d_%H%M%S).txt"

if [ -x /usr/local/bin/ddc_diag.sh ]; then
  echo "[ddc] /usr/local/bin/ddc_diag.sh" >> "$BOOTLOG"
  /usr/local/bin/ddc_diag.sh 2>&1 | tee -a "$BOOTLOG" > "$DDCLOG"
elif [ -x /opt/ddc_diag.sh ]; then
  echo "[ddc] /opt/ddc_diag.sh" >> "$BOOTLOG"
  sh /opt/ddc_diag.sh 2>&1 | tee -a "$BOOTLOG" > "$DDCLOG"
else
  echo "[ddc] kein ddc_diag.sh gefunden" >> "$BOOTLOG"
fi

# 5) Nur das konfigurierte persistente TCE-Verzeichnis verwenden.
# /tmp/tce ist flüchtig; kein beliebiges anderes Laufwerk beschreiben.
TCEDIR=$(readlink -f /etc/sysconfig/tcedir)
case "$TCEDIR" in
  /mnt/*)
    if [ -f "$DDCLOG" ] && [ -d "$TCEDIR" ]; then
      cp -f "$DDCLOG" "$TCEDIR/ddc_diag_last.txt" 2>>"$BOOTLOG" &&
        echo "[ddc] Log nach $TCEDIR/ddc_diag_last.txt kopiert" >> "$BOOTLOG"
    fi
    ;;
esac

# TDM nur im ausdrücklich ausgewählten Autostart-Menü einschalten.
if grep -qw 'tdm_autostart=1' /proc/cmdline; then
  sleep 10
  /usr/local/bin/tdm_on >> "$BOOTLOG" 2>&1
fi

echo "== bootlocal end: $(date) ==" >> "$BOOTLOG"
exit 0
