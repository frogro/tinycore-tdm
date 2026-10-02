# Rekonstruktion des funktionierenden USB-Sticks

Untersucht am 2026-10-03: TINYCORE auf /dev/sdc1, nur lesend.
Die Gerätebezeichnung gilt nur für diesen Untersuchungslauf.

## Plausibler Hauptpfad

1. iMac-EFI startet `EFI/BOOT/BOOTX64.EFI` (Standardpfad für Wechselmedien).
2. Dieser eigenständige GRUB lädt seine eingebettete Konfiguration aus einer
   TAR-Memdisk. Das erste Menü startet nach zwei Sekunden und sucht der Reihe nach
   `/grub.cfg`, `/boot/grub.cfg`, `/boot/grub/grub.cfg` auf sichtbaren Laufwerken.
3. Auf dem Stick existiert `/grub.cfg`. Diese Konfiguration sucht das Label
   `TINYCORE` und lädt `/boot/vmlinuz` sowie `/boot/corepure64.gz`.
4. TinyCore lädt Erweiterungen aus `tce/onboot.lst`, darunter `tdm.tcz`.
   Dessen Startskript enthält bereits einen eigenen TDM-Start.
5. TinyCore stellt anschließend `tce/mydata.tgz` wieder her. Dieses Archiv
   enthält die neueren Programme unter `/usr/local/bin`, `etc/inittab` und
   `opt/bootlocal.sh`. Das Startskript führt nach zehn Sekunden erneut TDM ON aus.

Das Backup, nicht der lose Ordner `tce/mydata/`, ist maßgeblich. Beispielsweise
enthält das archivierte bootlocal.sh noch Diagnose und Logkopie, die in der losen
Kopie fehlen. Viele Dateien stehen mehrfach im TAR; beim Wiederherstellen zählt
normalerweise der letzte Eintrag.

Die EFI-Datei sucht nicht ausschließlich auf dem USB-Stick. Ein anderes sichtbares
Laufwerk mit `/grub.cfg` kann die Suche beeinflussen. Welchen Pfad die Firmware
beim historischen Boot tatsächlich startete, kann diese Dateianalyse nicht beweisen.

## Die anderen EFI-Dateien

`EFI/GRUB/grubx64.efi` und `GRUB/grubx64.efi` sind bytegleich:
SHA-256 `52b8b3503d3efabfac8793f07e1db5d22c51d90ebb5b6319962fab5d02f49956`.
Sie enthalten einen Ubuntu-GRUB 2.12 mit einer SquashFS-Memdisk. Dessen Konfiguration
sucht nach Ubuntu-Medienmarkern und lädt bevorzugt Konfigurationen aus `/boot/grub`,
sonst `$cmdpath/grub.cfg`.

Auf diesem Stick fehlen die erwarteten `/boot/grub`-Konfigurationen und
`EFI/GRUB/grub.cfg`. Die Datei `GRUB/grub.cfg` existiert, enthält aber
**rEFInd-Syntax** (`scanfor`, `loader`, `ostype`), keine gültige entsprechende
GRUB-Konfiguration. Der tatsächlich vorhandene `BOOTX64.EFI` ist GRUB, nicht rEFInd.
Es wurde kein rEFInd-Programm auf dem Stick gefunden. Diese Dateien passen somit
nicht zu einer geschlossenen alternativen Bootkette und wirken wie alte Versuche.

`EFI/BOOT/BOOTX64.EFI` hat dagegen SHA-256
`63f293c7b0f86d889b34137139e96dbcb32aaa021736e13fb66001a1ecf62a9b`.
Die beiden extrahierten eingebetteten Konfigurationen stehen in `boot-reference/`.

## Unsaubere Stellen im alten Stand

- Zwei konkurrierende TDM-Starts: Erweiterung und wiederhergestelltes bootlocal.sh.
- Das alte bootlocal.sh wertet `tdm_autostart`/`text` nicht aus: Auch der angebliche
  Safe Console Mode kann TDM automatisch einschalten.
- `tdm_status` ruft `SmcDumpKey MVMR 2` auf: Das liest nicht nur, sondern schreibt.
- `tdm_off` lädt applesmc zurück; das alte `tdm_on` entlädt den Treiber selbst nicht.
- Die Erweiterung legt pauschal `/dev/sda` mit `hdparm -Y` schlafen.
- Das Backup enthält private Hostschlüssel und Passwortdaten und darf nicht
  unverändert in das öffentliche Repository übernommen werden.

## Konkrete TDM-Pfadkonflikte

Die letzten Einträge des aktiven `tce/mydata.tgz` enthalten:

| Pfad | Typ / Ziel |
| --- | --- |
| `/usr/local/bin/tdm_on` | Neuere reguläre Datei |
| `/usr/local/bin/tdm_off` | Neuere reguläre Datei |
| `/usr/local/bin/tdm_toggle` | Neuere reguläre Datei |
| `/usr/bin/tdm_on` | Symlink auf `/tmp/tcloop/tdm/usr/bin/tdm_on` (alte Erweiterung) |
| `/usr/bin/tdm_off` | Symlink auf `/usr/local/bin/tdm_off` |
| `/usr/bin/tdm_toggle` | Symlink auf `/usr/local/bin/tdm_toggle` |
| `/usr/bin/SmcDumpKey` | Symlink auf `/tmp/tcloop/tdm/usr/bin/SmcDumpKey` (alte Erweiterung) |

Damit vermischten Aufrufe unter `/usr/bin` alte und neue Implementierungen.
Die wiederhergestellte inittab und bootlocal.sh verwenden dagegen ausdrücklich
`/usr/local/bin`. Im bereinigten Repository ist deshalb `/usr/local/bin` der
zentrale Installationspfad für alle TDM-Programme einschließlich Status,
Shutdown und SmcDumpKey. Das Zusatz-Initramfs liefert sie dort aus; weder die
alte Erweiterung noch deren `/usr/bin`-Verknüpfungen werden übernommen.

## Bereinigter Repository-Stand

Der bekannte `BOOTX64.EFI` bleibt erhalten; `/grub.cfg` ist die zentrale Konfiguration.
Das Zusatz-Initramfs enthält nur die ausgewählten Skripte und das SMC-Programm.
Der Altbestand `tdm.tcz` und das persönliche Backup werden nicht ausgeliefert.
Autostart wird nur mit `tdm_autostart=1` ausgeführt. Safe Console Mode überspringt
projektspezifische Startaufgaben. Das bereinigte Repository liefert nur den in QEMU getesteten BOOTX64.EFI aus;
die ungenutzte alternative EFI-Kopie wurde entfernt. Am Originalstick wurde nichts geändert.
