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

## Tastaturlayout und SSH im Installer auswählen

Ohne weitere Optionen verwendet die Konsole das US-Layout und SSH bleibt aus.
Für eine deutsche Tastatur ergänze `--keymap de`:

```sh
sudo python3 install-usb.py --device /dev/sdX --keymap de
```

Der Installer lädt das passende Tastaturpaket automatisch mit herunter. Für den
reinen Monitorbetrieb genügt diese Installation; SSH ist freiwillig.

### Wozu SSH?

Mit SSH kannst du den iMac über das lokale Netzwerk von einem anderen Rechner
bedienen, auch während er ein externes Bild zeigt. Zum Beispiel kannst du so
zur internen Anzeige zurückschalten oder den iMac herunterfahren. Verbinde den
iMac dafür per Netzwerkkabel mit deinem Router.

### Zugang mit Passwort

```sh
sudo python3 install-usb.py --device /dev/sdX --keymap de --ssh-password
```

Der Installer fragt zweimal verdeckt nach einem neuen Passwort für den Benutzer
`tc`. Auf dem Stick liegt nur dessen gesalzener Prüfwert, nicht das Klartextpasswort.
Auf dem Linux-Rechner wird dafür zusätzlich das Paket `openssl` benötigt.

### Zugang mit SSH-Schlüssel

Wenn du bereits einen SSH-Schlüssel besitzt, übergib dessen **öffentliche `.pub`-Datei**:

```sh
sudo python3 install-usb.py --device /dev/sdX --keymap de --ssh-key ~/.ssh/id_ed25519.pub
```

Falls du noch keinen hast, kannst du auf deinem eigenen Rechner mit
`ssh-keygen -t ed25519` einen erzeugen. Die Datei **ohne** `.pub` ist privat und
bleibt auf diesem Rechner. In dieser Variante ist die Anmeldung per Passwort
ausgeschaltet. Wähle bei der Installation entweder Schlüssel oder Passwort.

Der iMac erzeugt beim ersten Start zusätzlich seinen eigenen SSH-Hostschlüssel
und behält ihn auf dem Stick. Damit erkennt dein Rechner denselben iMac bei
späteren Verbindungen wieder. Du musst diese Datei nicht selbst erstellen.

### Verbinden und schalten

Die IP-Adresse des iMac findest du in der Geräteliste deines Routers. Ersetze
`IP-DES-IMAC` entsprechend und starte auf deinem anderen Rechner:

```sh
ssh tc@IP-DES-IMAC
```

Nach der Anmeldung schaltet `sudo /usr/local/bin/tdm_off` zurück zur internen
Anzeige, `sudo /usr/local/bin/tdm_on` zum externen Eingang.
Mit `sudo /usr/local/bin/tdm_shutdown` fährst du den iMac herunter.
Der SSH-Zugang erlaubt auch administrative Befehle; teile Passwort oder privaten
Schlüssel deshalb nur mit Personen, die den iMac verwalten dürfen.

Im **Safe Console Mode** startet SSH nicht.
Bei `--dry-run` werden die gewählten Pakete geprüft, aber kein Passwort abgefragt.
Für eine Offline-Installation dieselben Optionen beim Herunterladen und beim
Installieren angeben, zum Beispiel:

```sh
python3 install-usb.py --download-only downloaded-payload --keymap de --ssh-password
sudo python3 install-usb.py --source downloaded-payload --device /dev/sdX --keymap de --ssh-password
```

Das Passwort wird erst bei der eigentlichen Installation festgelegt.
