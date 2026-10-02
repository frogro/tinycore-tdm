# TinyCore Display-Diagnose / TDM-Vorbereitung

Zielgerät: **iMac 27 Zoll, Ende 2009**, Target Display Mode (TDM).
Die TDM-Programme wurden vom funktionierenden USB-Stick des Besitzers wiederhergestellt.
Sie waren im ursprünglichen GitHub-Upload nicht enthalten, sondern in `tce/mydata.tgz`.
Der neue, bereinigte Repository-Build muss noch auf dem iMac getestet werden.
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
| Wechsel in TDM und zurück | Programme vom funktionierenden Stick übernommen |
| Tastenkürzel oder automatischer TDM-Start | Wiederhergestellt; siehe Bedienung |

## TDM bedienen

Die Tastatur muss am **iMac** angeschlossen sein. In der Linux-Textkonsole:

| Aktion | Tastatur | Konsole/SSH |
| --- | --- | --- |
| TDM einschalten | Alt+F3, danach Enter | `sudo /usr/local/bin/tdm_on` |
| Zur internen Anzeige zurück | Alt+F4, danach Enter | `sudo /usr/local/bin/tdm_off` |
| Umschalten | Alt+F2, danach Enter | `sudo /usr/local/bin/tdm_toggle` |
| Status abfragen | — | `sudo /usr/local/bin/tdm_status` |
| Herunterfahren | Alt+F5, danach Enter | `sudo /usr/local/bin/tdm_shutdown` |

Je nach Tastatur zusätzlich Fn drücken. Unter einer grafischen Sitzung kann
Strg+Alt+Fn erforderlich sein. `askfirst` verlangt Enter vor dem Befehl; die
Befehle werden nicht automatisch durch Init ausgeführt.

Das erste GRUB-Menü aktiviert TDM nach den Startaufgaben und zehn Sekunden Wartezeit.
**Safe Console Mode** aktiviert TDM nicht automatisch; manuelles Umschalten bleibt möglich.
Die virtuelle Konsole kann auch bei externem Bildsignal blind ausgewählt werden.

`SmcDumpKey` steuert den Apple-SMC: Einschalten schreibt `MVHR=1`, danach `MVMR=2`;
Ausschalten schreibt `MVHR=0`, danach `MVMR=2`. Beim Ausschalten wird `applesmc`
wieder geladen und, falls verfügbar, auf Konsole 1 gewechselt. Vor jedem erneuten
Einschalten wird der Treiber entladen. `xrandr` ist optional.

Die vom Stick übernommene Statusinterpretation behandelt `MVMR=0x02` als aktiv.
Die Statusabfrage wurde auf reines Lesen korrigiert: Der alte Aufruf schrieb bei
jeder Abfrage zusätzlich `MVMR=2`. Status und Toggle müssen deshalb am Gerät geprüft
werden; die expliziten Ein-/Aus-Befehle stehen unabhängig davon zur Verfügung.

## Booten

Die Partition muss das Dateisystemlabel `TINYCORE` tragen. Auf einem bereits
UEFI-bootfähigen Stick müssen `EFI/`, `boot/`, `grub.cfg` und `tce/` im
Wurzelverzeichnis liegen. Dieses Repository ist kein fertiges Datenträger-Image.

GRUB lädt das originale `boot/corepure64.gz` und danach `boot/custom.gz`.
Das zweite Initramfs enthält die korrigierte `etc/inittab` sowie die beiden
Skripte aus `opt/`, jeweils mit den benötigten Linux-Dateirechten. Die losen
Dateien auf dem Stick allein würden TinyCores RAM-Dateisystem nicht verändern.

- **TDM Auto-Start** startet Diagnose, optional SSH und danach TDM.
- **Safe Console Mode** überspringt `bootlocal.sh`; TinyCores normale
  Initialisierung und DHCP bleiben aktiv.
- Die virtuellen Konsolen verwenden die oben beschriebenen TDM-Befehle mit Enter-Bestätigung.

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

Die rekonstruierte Bootkette und die doppelten EFI-Dateien sind in
[docs/boot-chain.md](docs/boot-chain.md) dokumentiert.

## Herkunft und Wiederherstellung

Die Programme unter `usr/local/bin/` stammen aus dem aktiven `tce/mydata.tgz`
des funktionierenden Sticks. Kernel, Basis-Initramfs und beide EFI-Dateien sind
bytegleich mit dem ursprünglichen Repository. Die alte Erweiterung `tdm.tcz`
wird nicht benötigt: Ihre zusätzlich ausgeführten Energiesparbefehle und das
pauschale `hdparm -Y /dev/sda` werden nicht übernommen.

Das ausführbare `SmcDumpKey` ist die unveränderte x86-64-Datei vom Stick; zugehöriger
Quellcode und GPLv2-Lizenz liegen unter `src/smc/`. Ursprünglicher Autor:
Gabriel L. Somlo; TDM-Fassung aus [floe/smc_util](https://github.com/floe/smc_util).
Neubau auf einem passenden TinyCore-System:

```sh
gcc -O2 -Wall -o usr/local/bin/SmcDumpKey src/smc/SmcDumpKey.c
python3 scripts/build-overlay.py
```

Passwortdateien, private SSH-Hostschlüssel, Shell-Historien und persönliche Dateien
vom Stick wurden nicht übernommen. SSH und deutsche Keymaps bleiben optionale
Erweiterungen; für die direkte SMC-Umschaltung reichen die enthaltenen Programme.
Der funktionierende Originalstick wurde bei der Wiederherstellung nur gelesen.
Die integrierte neue Fassung ist automatisiert geprüft, aber noch nicht auf dem
iMac gebootet worden.
