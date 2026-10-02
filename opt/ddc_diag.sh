#!/bin/sh
# ddc_diag.sh – Diagnose für Helligkeit/Display-Steuerung auf TinyCore
# - prüft Backlight-Interface (/sys/class/backlight)
# - lädt i2c-dev, listet /dev/i2c-* und DRM-Connector-Status
# - zeigt EDID (Header) an
# - nutzt ddcutil (falls installiert) für detect/getvcp 0x10 (Brightness)
# - prüft TDM-Hilfsbefehle
# Ergebnis: /home/tc/ddc_diag_YYYYmmdd_HHMMSS.txt

ts="$(date +%Y%m%d_%H%M%S)"
out="/home/tc/ddc_diag_${ts}.txt"

log() { printf "%s\n" "$*" | tee -a "$out" ; }
hdr() { printf "\n==== %s ====\n" "$*" | tee -a "$out"; }

# Ein existierendes, aber leeres Klassenverzeichnis ist kein Backlight.
has_backlight() {
  for backlight in /sys/class/backlight/*; do
    [ -r "$backlight/brightness" ] && [ -r "$backlight/max_brightness" ] && return 0
  done
  return 1
}

# Start
echo "# ddc_diag – $(date)" > "$out"

hdr "System"
uname -a       | tee -a "$out"
id             | tee -a "$out"
command -v sudo >/dev/null 2>&1 && sudo -V 2>/dev/null | head -n1 | tee -a "$out"

hdr "Kernel-Module laden (i2c-dev)"
if command -v modprobe >/dev/null 2>&1; then
  sudo modprobe i2c-dev 2>>"$out"
  log "modprobe i2c-dev: $?"
else
  log "modprobe nicht gefunden."
fi

hdr "/sys/class/backlight"
if has_backlight; then
  ls -l /sys/class/backlight | tee -a "$out"
  for b in /sys/class/backlight/*; do
    [ -d "$b" ] || continue
    printf "%s: " "$b" | tee -a "$out"
    printf "brightness=%s max=%s\n" "$(cat "$b/brightness" 2>/dev/null)" "$(cat "$b/max_brightness" 2>/dev/null)" | tee -a "$out"
  done
else
  log "(leer) – kein Kernel-Backlight-Interface gefunden."
fi

hdr "/dev/i2c-*"
if ls /dev/i2c-* 1>/dev/null 2>&1; then
  ls -l /dev/i2c-* | tee -a "$out"
else
  log "keine /dev/i2c-* Geräte sichtbar."
fi

hdr "I2C-Busnamen"
for d in /sys/bus/i2c/devices/i2c-*; do
  [ -r "$d/name" ] && printf "%s : %s\n" "$d" "$(cat "$d/name")" | tee -a "$out"
done

hdr "DRM-Connector-Status"
for s in /sys/class/drm/card*-*/status; do
  [ -f "$s" ] || continue
  printf "%s: %s\n" "$s" "$(cat "$s" 2>/dev/null)" | tee -a "$out"
done

hdr "EDID (Header, falls vorhanden)"
for e in /sys/class/drm/card*-*/edid; do
  [ -f "$e" ] || continue
  echo "$e" | tee -a "$out"
  hexdump -C "$e" 2>/dev/null | head -n 8 | tee -a "$out"
done

hdr "ddcutil"
if command -v ddcutil >/dev/null 2>&1; then
  ddcutil --version 2>/dev/null | head -n1 | tee -a "$out"
  echo "-- detect --" | tee -a "$out"
  sudo ddcutil detect 2>&1 | tee -a "$out"
  echo "-- getvcp 0x10 (Brightness) --" | tee -a "$out"
  sudo ddcutil getvcp 10 2>&1 | tee -a "$out"
else
  log "ddcutil nicht installiert (kein .tcz vorhanden)."
fi

hdr "TDM-Befehle vorhanden?"
for c in /usr/bin/tdm_on /usr/bin/tdm_off /usr/bin/tdm_toggle; do
  if [ -x "$c" ]; then
    printf "%s: vorhanden\n" "$c" | tee -a "$out"
  else
    printf "%s: fehlt\n" "$c" | tee -a "$out"
  fi
done

hdr "Fazit (Kurz)"
if has_backlight; then
  log "Backlight-Interface gefunden → brightnessctl/sysfs-Steuerung möglich."
else
  log "Kein Backlight-Interface. Wenn i2c/devices & EDID vorhanden: DDC/CI möglich (ddcutil nötig)."
fi

echo ""
echo ">> Diagnose gespeichert: $out"
