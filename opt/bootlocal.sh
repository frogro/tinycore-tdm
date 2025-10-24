#!/bin/sh
# TinyCore bootlocal.sh (DE-Layout + DHCP + SSH + DDC-Diag)

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
  /usr/local/sbin/dropbear -R -E -p 22 >> "$BOOTLOG" 2>&1
  echo "[ssh] dropbear läuft (Port 22)" >> "$BOOTLOG"
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

# 5) DDC-Log zusätzlich auf den USB-Stick kopieren (erstes gemountetes /mnt/sdX1)
for p in /mnt/sd?1 /mnt/sd??1; do
  # Fallback, falls BusyBox kein 'mountpoint' hat
  if command -v mountpoint >/dev/null 2>&1; then
    mountpoint -q "$p" || continue
  else
    grep -q " $p " /proc/mounts || continue
  fi
  cp -f "$DDCLOG" "$p/ddc_diag_last.txt" 2>>"$BOOTLOG" && \
    echo "[ddc] Log nach $p/ddc_diag_last.txt kopiert" >> "$BOOTLOG"
  break
done

echo "== bootlocal end: $(date) ==" >> "$BOOTLOG"
exit 0