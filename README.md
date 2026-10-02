# TinyCore Display-Diagnose / TDM-Vorbereitung

Zielgerät: **iMac 27 Zoll, Ende 2009**, Target Display Mode (TDM).
Der aktuelle Stand bootet TinyCore und sammelt Display-Diagnosen.
**Das Umschalten in den Target Display Mode ist noch nicht implementiert.**
DDC/CI-Helligkeitssteuerung und TDM-Umschaltung sind unterschiedliche Funktionen.

## USB-Stick unter Linux erstellen

Der Installer erstellt direkt einen bootfähigen USB-Stick aus den Dateien im
Repository; eine separate `.img`-Datei ist nicht erforderlich. **Alle Daten auf
dem gewählten USB-Laufwerk werden gelöscht.** Andere USB-Laufwerke möglichst
vorher abziehen. Ein Stick ab 512 MiB genügt für den enthaltenen Stand.

Unter Debian/Ubuntu die benötigten Werkzeuge installieren:

```sh
sudo apt install python3 util-linux parted dosfstools udev
```

Im Repository-Verzeichnis:

```sh
# Geräte mit Modell, Größe, Seriennummer und belegten Partitionen anzeigen:
python3 scripts/install-usb.py --list

# /dev/sdX durch das tatsächlich gewünschte ganze USB-Laufwerk ersetzen.
# Eingehängte Partitionen vorher über den Dateimanager aushängen.
python3 scripts/install-usb.py --device /dev/sdX --dry-run
sudo python3 scripts/install-usb.py --device /dev/sdX
```

Der Probelauf schreibt nichts. Die Installation verlangt zusätzlich die genaue
Eingabe `LOESCHEN /dev/sdX`. Sie verweigert interne Laufwerke, einzelne Partitionen,
eingehängte Geräte, aktiven Swap und verwendete Mapper-/RAID-Geräte. Sie hängt
vorhandene Dateisysteme nicht automatisch aus. Der Installer legt eine
GPT-Partitionstabelle mit einer FAT32-EFI-Systempartition und Label `TINYCORE` an,
kopiert die Bootdateien, vergleicht SHA-256-Prüfsummen und hängt den Stick aus.
Bei einem Fehler nach Beginn der Partitionierung kann der Stick unvollständig
sein; nach Behebung der Ursache die Installation erneut starten.

Am iMac beim Einschalten **Alt/Option** gedrückt halten und den USB-EFI-Boot wählen.
Falls das mitgelieferte GRUB zunächst sein Suchmenü zeigt, den Eintrag zum Finden
von `grub.cfg` auswählen. Der Installer wurde mit simulierten Geräten getestet;
ein realer Schreib- und Bootversuch am iMac steht noch aus.

## Funktionsumfang

| Funktion | Stand |
| --- | --- |
| Linux-USB-Installer mit Probelauf und Geräteprüfung | Implementiert, automatisiert getestet |
| TinyCore-Boot mit Diagnose- und Konsolenmodus | Konfiguriert, iMac-Bootprüfung offen |
| Backlight-, I2C-, DRM- und EDID-Diagnose | Implementiert; Ergebnisse hardwareabhängig |
| DDC/CI-Erkennung und Helligkeitsabfrage | Optional mit installiertem `ddcutil` |
| SSH | Optional mit installiertem und konfiguriertem Dropbear |
| Wechsel in TDM und zurück | Noch nicht implementiert |
| Tastenkürzel oder automatischer TDM-Start | Noch nicht implementiert |

Es gibt aktuell **keinen funktionierenden TDM-Umschaltbefehl** in diesem Image.
Insbesondere sind virtuelle Konsolen und die DDC-Diagnose keine Umschalter.
Die geplante SMC-Integration muss sowohl das Einschalten des externen Eingangs
als auch die Rückkehr zur internen Anzeige unterstützen. Ein Rückschaltweg per
Tastatur oder SSH muss am Zielgerät geprüft sein, bevor Autostart sinnvoll ist.

## Booten

Die Partition muss das Dateisystemlabel `TINYCORE` tragen. Auf einem bereits
UEFI-bootfähigen Stick müssen `EFI/`, `boot/`, `grub.cfg` und `tce/` im
Wurzelverzeichnis liegen. Dieses Repository ist kein fertiges Datenträger-Image.

GRUB lädt das originale `boot/corepure64.gz` und danach `boot/custom.gz`.
Das zweite Initramfs enthält die korrigierte `etc/inittab` sowie die beiden
Skripte aus `opt/`, jeweils mit den benötigten Linux-Dateirechten. Die losen
Dateien auf dem Stick allein würden TinyCores RAM-Dateisystem nicht verändern.

- **Display-Diagnose** startet Netzwerk-/Display-Diagnose und, falls installiert, SSH.
- **Safe Console Mode** überspringt `bootlocal.sh`; TinyCores normale
  Initialisierung und DHCP bleiben aktiv.
- Herunterfahren erfolgt ausdrücklich mit `sudo poweroff` in der Konsole.
  Die virtuellen Konsolen sind keine TDM-Tastenkürzel.

Änderungen an `opt/` oder `etc/inittab` erfordern einen Neubau:

```sh
python3 scripts/build-overlay.py
python3 -m unittest discover -s tests -v
```

Für die Tests werden Python 3, BusyBox und GNU cpio benötigt. Danach die neue
`boot/custom.gz` und gegebenenfalls `grub.cfg` auf den Stick kopieren.
Ein vorhandenes TinyCore-Backup (`tce/mydata.tgz`) kann Dateien aus dem
Zusatz-Image wieder überschreiben; alte angepasste Startdateien müssen aus
diesem Backup entfernt oder ebenfalls aktualisiert werden.

## Optionale Pakete und Logs

`ddcutil`, Dropbear und die deutsche Keymap sind nicht im Basis-Image enthalten.
Passende TinyCore-Erweiterungen müssen mit ihren Abhängigkeiten im persistenten
TCE-Verzeichnis installiert und für den Bootvorgang aktiviert werden.
Ohne deutsche Keymap bleibt das Standardlayout aktiv; das Startlog meldet dies.
Vor Installation/Aktivierung von Dropbear die Zugangsdaten bzw. SSH-Authentifizierung
konfigurieren; das TinyCore-Basissystem ist nicht für unveränderten Remotezugang gedacht.

Logs: `/var/log/bootlocal.log`, `/var/log/ddc_diag_*.txt` und
`/home/tc/ddc_diag_*.txt`. Bei persistentem TCE-Verzeichnis unter `/mnt/`
wird zusätzlich dort `ddc_diag_last.txt` abgelegt, normalerweise unter
`/mnt/sda1/tce/ddc_diag_last.txt`. Logs im RAM verschwinden beim Neustart.

## Noch offen: TDM auf dem Zielgerät

`tdm_on`, `tdm_off` und `tdm_toggle` fehlen weiterhin. Deshalb gibt es keinen
wirkungslosen `tdm_autostart`-Bootparameter mehr. Als Ausgangspunkt für die
SMC-Ansteuerung existiert [floe/smc_util](https://github.com/floe/smc_util),
dessen Autor Tests auf einem **27-Zoll-iMac von Mitte 2010** dokumentiert.
Das ist noch kein Nachweis für diesen iMac von 2009 oder dieses TinyCore-Image.
Vor einer Integration müssen die SMC-Steuerung und die Rückkehr zum internen
Display auf dem Zielgerät geprüft werden. Die Diagnose allein aktiviert TDM nicht.

Die automatischen Prüfungen decken Shellsyntax, Backlight-Erkennung sowie
Inhalt, Rechte und reproduzierbaren Bau des Zusatz-Images ab.
Ein UEFI-Boot und die Hardwarefunktionen wurden nicht auf einem iMac getestet.
