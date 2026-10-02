#!/bin/sh
# TinyCore bootlocal.sh (DE-Layout + DHCP + SSH + DDC-Diag)

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

# 1) Deutsches Tastaturlayout (Konsole)
if [ -f /usr/share/kmap/qwertz/de-latin1.kmap ]; then
  busybox loadkmap < /usr/share/kmap/qwertz/de-latin1.kmap
  echo "[kbd] de-latin1 geladen" >> "$BOOTLOG"
else
  echo "[kbd] /usr/share/kmap/qwertz/de-latin1.kmap fehlt" >> "$BOOTLOG"
fi

# 2) DHCP nur starten, wenn noch keine IPv4 vorhanden ist
if ip addr show "$IFACE" 2>/dev/null | grep -q 'inet '; then
  echo "[net] $IFACE hat bereits IPv4" >> "$BOOTLOG"
else
  echo "[net] starte DHCP auf $IFACE" >> "$BOOTLOG"
  /sbin/udhcpc -b -i "$IFACE" -s /usr/share/udhcpc/default.script \
    >> "$LOGDIR/udhcpc.log" 2>&1
fi

# 3) SSH (Dropbear) starten – Hostkeys ggf. erzeugen
if [ -x /usr/local/sbin/dropbear ]; then
  mkdir -p /usr/local/etc/dropbear
  [ -s /usr/local/etc/dropbear/dropbear_rsa_host_key ]     || /usr/local/bin/dropbearkey -t rsa     -f /usr/local/etc/dropbear/dropbear_rsa_host_key
  [ -s /usr/local/etc/dropbear/dropbear_ecdsa_host_key ]   || /usr/local/bin/dropbearkey -t ecdsa   -f /usr/local/etc/dropbear/dropbear_ecdsa_host_key
  [ -s /usr/local/etc/dropbear/dropbear_ed25519_host_key ] || /usr/local/bin/dropbearkey -t ed25519 -f /usr/local/etc/dropbear/dropbear_ed25519_host_key
  if /usr/local/sbin/dropbear -R -E -p 22 >> "$BOOTLOG" 2>&1; then
    echo "[ssh] dropbear gestartet (Port 22)" >> "$BOOTLOG"
  else
    echo "[ssh] dropbear konnte nicht gestartet werden" >> "$BOOTLOG"
  fi
else
  echo "[ssh] dropbear nicht installiert" >> "$BOOTLOG"
fi

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

echo "== bootlocal end: $(date) ==" >> "$BOOTLOG"
exit 0