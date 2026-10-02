# TinyCore TDM für den iMac 27″ (Ende 2009)

Ein kleines Linux-Bootsystem für den **Target Display Mode**: Der iMac kann über
seinen Mini-DisplayPort-Eingang als Bildschirm verwendet werden. Dieses Repository
enthält den USB-Installer, EFI-Bootloader, TinyCore und die vom funktionierenden
Originalstick wiederhergestellten **64-Bit-SMC-Programme**.

## USB-Stick unter Linux installieren

Benötigt werden ein Linux-Rechner, Internet, Python 3 und ein USB-Stick ab **512 MiB**.
Der Download der fünf Bootdateien umfasst ungefähr **22 MiB**. Das Repository muss
nicht geklont werden; eine zusätzliche Image-Datei ist nicht nötig.

**Die Installation löscht alle Partitionen und Daten des ausgewählten USB-Laufwerks.**
Den funktionierenden Originalstick als Referenz behalten und einen zweiten Stick
verwenden. Der Installer zeigt Gerät, Größe, Modell und Seriennummer und verlangt
vor dem ersten Schreibzugriff die Eingabe `LOESCHEN /dev/sdX`.

### 1. Werkzeuge installieren und Installer herunterladen

Debian/Ubuntu:

```sh
sudo apt install python3 curl ca-certificates util-linux parted dosfstools udev
curl --fail --location --output install-usb.py \
  https://raw.githubusercontent.com/frogro/tinycore-tdm/main/scripts/install-usb.py
```

Auf anderen Linux-Distributionen die entsprechenden Pakete installieren.
Der Installer benötigt keine zusätzlichen Python-Pakete.

### 2. Zielgerät bestimmen

```sh
python3 install-usb.py --list
```

**`/dev/sdX` in den folgenden Beispielen durch das richtige ganze USB-Laufwerk
ersetzen**, beispielsweise `/dev/sdc`. Keine Partitionsnummer anhängen. Die
angezeigten Partitionen dieses Sticks zunächst im Dateimanager aushängen.

### 3. Prüfen und installieren

```sh
# Lädt und prüft die Dateien, schreibt aber nichts auf den Stick:
python3 install-usb.py --device /dev/sdX --dry-run

# Lädt die Dateien erneut und verlangt danach die Löschbestätigung:
sudo python3 install-usb.py --device /dev/sdX
```

Der Installer:

1. verweigert interne Laufwerke, einzelne Partitionen, schreibgeschützte oder
   eingehängte Geräte sowie aktiven Swap und verwendete Mapper-/RAID-Geräte;
2. löst `main` einmal zu einer Commit-ID auf und lädt alle Dateien genau dieses
   Standes von GitHub;
3. prüft Dateigröße und SHA-256 anhand von `install-manifest.json`, bevor er nach
   der Löschbestätigung fragt;
4. erstellt GPT und eine FAT32-EFI-Systempartition mit dem Label **TINYCORE**;
5. kopiert die Bootdateien, erstellt `tce/`, prüft die kopierten Dateien und hängt
   den Stick aus.

Ein Download- oder Prüfsummenfehler beendet den Vorgang vor der Partitionierung.
Ein Fehler nach Beginn der Partitionierung kann einen unvollständigen Stick
hinterlassen; nach Behebung der Ursache erneut installieren. Vorhandene Geräte
werden niemals automatisch ausgehängt. Die Prüfsummen erkennen beschädigte oder
vermischte Dateien; sie sind keine unabhängige Signatur des Repository-Inhalts.

### Nur herunterladen oder offline installieren

```sh
# Neues Zielverzeichnis angeben; bestehende Verzeichnisse werden nicht überschrieben:
python3 install-usb.py --download-only downloaded-payload

# Danach ohne Internet installieren:
sudo python3 install-usb.py --source downloaded-payload --device /dev/sdX
```

Mit `--ref <Commit-ID>` lässt sich ein bestimmter Stand installieren oder
herunterladen. Ohne diese Option wird `main` verwendet. Der Downloadordner enthält
`SOURCE-COMMIT.txt` zur späteren Zuordnung. `--source` funktioniert ebenfalls mit
einem vollständigen lokalen Checkout und aktuellem Manifest.

## Am iMac starten

1. USB-Stick und eine Tastatur am **iMac** anschließen.
2. Beim Einschalten **Alt/Option** halten und den USB-EFI-Eintrag wählen.
3. Der enthaltene GRUB sucht automatisch `/grub.cfg`. Falls sein Suchmenü sichtbar
   bleibt, „Find /grub.cfg …“ wählen.
4. **TDM Auto-Start** führt die Startdiagnose aus und ruft nach weiteren zehn
   Sekunden `tdm_on` auf. Die gesamte Bootzeit ist länger als zehn Sekunden.
5. **Safe Console Mode** startet ohne projektspezifische Dienste und ohne
   TDM-Autostart. Manuelles Umschalten bleibt möglich.

Der 2009er-iMac benötigt ein geeignetes **DisplayPort-Signal** am Mini-DisplayPort.
Die Mini-DisplayPort-Buchse dieses Modells ist kein Thunderbolt-Anschluss.

## TDM einschalten und zurückschalten

Die Tastatur muss am iMac angeschlossen sein. In der Linux-Textkonsole:

| Aktion | Tastatur | Befehl in der Konsole |
| --- | --- | --- |
| TDM einschalten | **Alt+F3**, danach **Enter** | `sudo /usr/local/bin/tdm_on` |
| Zur internen Anzeige zurück | **Alt+F4**, danach **Enter** | `sudo /usr/local/bin/tdm_off` |
| Umschalten | Alt+F2, danach Enter | `sudo /usr/local/bin/tdm_toggle` |
| Status abfragen | — | `sudo /usr/local/bin/tdm_status` |
| Herunterfahren | Alt+F5, danach Enter | `sudo /usr/local/bin/tdm_shutdown` |
| Normale Konsole auswählen | Alt+F1 | — |

Je nach Tastatur zusätzlich **Fn** drücken. Enter ist erforderlich, weil die
Konsolen `askfirst` verwenden. Beim externen Bildsignal können die Konsolentasten
blind bedient werden. Für den ersten Hardwaretest die expliziten ON-/OFF-Befehle
verwenden: Die vom Stick übernommene Statusinterpretation (`MVMR=0x02` als aktiv)
ist noch nicht am Gerät bestätigt. Die Statusabfrage wurde auf reines Lesen
korrigiert; der alte Aufruf schrieb bei jeder Abfrage zusätzlich `MVMR=2`.

Alle TDM-Programme liegen einheitlich unter **`/usr/local/bin`**. Die alten
`/usr/bin`-Varianten aus `tdm.tcz` und die alte 32-Bit-SMC-Binärdatei werden nicht
installiert. Die tatsächlichen Konsolenaufrufe des Originalstands wurden in QEMU
mit Markern nachverfolgt; sie verwenden ebenfalls `/usr/local/bin`.

## Diagnose und optionale Fernwartung

**Für den reinen Monitorbetrieb sind keine Zusatzpakete, kein SSH und keine
Schlüsseldateien erforderlich.** Das Umschalten erfolgt mit den oben beschriebenen
Tasten am iMac. Nach der Installation wird dafür keine Internetverbindung benötigt.

SSH wäre nur für Fernwartung nützlich: Von einem anderen Rechner ließen sich Logs
ansehen oder TDM-Befehle ausführen, wenn die lokale Konsole gerade nicht sichtbar
ist. SSH ist nicht vorinstalliert. Die dafür erwähnten Hostschlüssel identifizieren
den SSH-Server und werden bei dessen Einrichtung automatisch erzeugt. Sie sind
keine Voraussetzung für TDM.

Die enthaltene Diagnose sammelt Informationen zu Display und Helligkeitssteuerung.
`ddcutil` wäre ein zusätzliches Diagnose-/Steuerwerkzeug für DDC/CI; es wird für die
TDM-Umschaltung nicht benötigt. Weitere TinyCore-Erweiterungen müssen für den
Monitorbetrieb nicht installiert werden.

Die Textkonsole verwendet standardmäßig das US-Tastaturlayout. Ein deutsches Layout
wäre nur für die Eingabe von Textbefehlen hilfreich; die TDM-Funktionstasten
funktionieren auch ohne dieses Zusatzpaket.

Bei Problemen liegt das Startprotokoll unter `/var/log/bootlocal.log`. Die letzte
Displaydiagnose wird bei vorhandenem persistentem TCE-Verzeichnis zusätzlich als
`tce/ddc_diag_last.txt` auf dem Stick gespeichert.
