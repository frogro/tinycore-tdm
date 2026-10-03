# QEMU-Boottest, 2026-10-03

Umgebung: QEMU 10.2.1, KVM, Q35, 1 GiB RAM, 2 vCPUs, OVMF x86-64 ohne
Secure Boot. Virtuelles USB-Massenspeichergerät, keine Netzwerkkarte.

Zwei lokale 512-MiB-GPT-Images mit FAT32-EFI-Systempartition wurden getestet:

1. Dateikopie des Originalsticks: alle 349 Dateien per SHA-256 geprüft.
2. Bereinigter Repository-Stand c3411d0: EFI, Kernel, Basis- und Zusatz-Initramfs,
   grub.cfg und tce-Verzeichnis, ohne das persönliche mydata.tgz.

Die Images wurden über beschreibbare QCOW2-Overlays gestartet. Der Originalstick
und die RAW-Referenzen wurden nicht beschrieben. Persönliche Images und Logs
bleiben im ignorierten lokalen qemu-Verzeichnis und werden nicht veröffentlicht.

## Beobachtungen

- Beide Images booten über OVMF und den USB-EFI-Einstieg bis zum automatischen
  TinyCore-Login (Core 15.0, Kernel 6.6.8-tinycore64).
- Das Original zeigt die TDM-Tastenhilfe. Die aus mydata.tgz wiederhergestellte
  inittab und die drei Programme unter /usr/local/bin wurden in der VM ausgelesen.
- Das bereinigte Image enthält dieselben SMC-Binärdaten und die angepassten
  TDM-Skripte aus dem Zusatz-Initramfs, ohne ein persönliches Backup zu benötigen.
- Beim Original wird die deutsche Tastatur geladen und Dropbear gestartet.
  Im bereinigten Image fehlen diese optionalen Pakete erwartungsgemäß.
  Netzwerk/SSH-Verbindungen wurden wegen der bewusst fehlenden Netzwerkkarte
  nicht getestet.
- Beide Autostarts erreichen SmcDumpKey. Die Zugriffe scheitern am nicht emulierten
  SMC-Port mit `read_smc get_key_type error`. Das ist kein TDM-Funktionstest.
- Die Diagnose suchte noch unter /usr/bin und meldete die tatsächlich unter
  /usr/local/bin vorhandenen TDM-Programme als fehlend. Dieser Pfad wurde nach
  dem Boottest korrigiert und das Zusatz-Initramfs neu gebaut; Shell- und
  Archivtests bestehen. Die Korrektur wurde anschließend im direkt von GitHub heruntergeladenen Payload erneut gebootet.

- Ein zweiter Boot des bereinigten Images über den Safe Console Mode erreicht
  die Konsole mit `text tdm_safe=1`. `/var/log/bootlocal.log` existiert danach
  nicht; die projektspezifischen Startaufgaben wurden übersprungen.

## Test des GitHub-Download-Installers

Der Installer wurde separat von GitHub heruntergeladen und außerhalb seines
ursprünglichen scripts-Verzeichnisses ausgeführt. Mit `--download-only` lud und
prüfte er die fünf Dateien von Commit 0b614e9. Daraus wurde ein neues lokales
512-MiB-Testimage gebaut, ohne die alternative EFI-Datei.

Dieses Image bootete bis zur Konsole. Das Startlog meldet die drei TDM-Programme
nun korrekt unter `/usr/local/bin` als vorhanden. Beim ersten VM-Kaltstart meldete
OVMF einmal `Not Found`; nach einem Reset startete es. Ein anschließender Neustart
mit einer frischen OVMF-VARIABLES-Datei startete ebenfalls erfolgreich. Die Ursache
des einzelnen Fehlstarts wurde nicht festgestellt; die zweite EFI-Datei wurde
für keinen dieser Versuche wieder hinzugefügt.

GitHub Actions und die lokale Testsuite bestehen mit 13 Tests. Download-Prüfsummen,
unerlaubte Manifestpfade, beschädigte Dateien, Gerätewahl, Bestätigungsabbruch und
simulierter Installationsablauf sind abgedeckt. Ein physischer USB-Schreibtest und
der Hardwaretest am iMac bleiben offen.

## Ausgeführte TDM-Pfade im Originalsystem

Die Originalreferenz wurde erneut gebootet. Nach dem Boot wurden ausschließlich
im flüchtigen VM-Dateisystem die drei Skripte unter `/usr/bin` und
`/usr/local/bin` durch unterscheidbare Marker-Skripte ersetzt. Init und die
wiederhergestellte inittab blieben unverändert. Über QEMU-Tastaturereignisse wurden
die Konsolen ausgewählt und jeweils Enter gedrückt:

| Tastatur | Ausgeführter Pfad (Marker nachgewiesen) |
| --- | --- |
| Alt+F3, Enter | `/usr/local/bin/tdm_on` |
| Alt+F4, Enter | `/usr/local/bin/tdm_off` |
| Alt+F2, Enter | `/usr/local/bin/tdm_toggle` |

Auch `command -v` löst die drei Befehle in dieser Sitzung nach `/usr/local/bin`
auf. Das bestätigt die tatsächlich verwendeten Einstiegspfade des vorhandenen
Stickstands, nicht nur den Text einer Konfigurationsdatei. Der ursprüngliche
Aufruf der SMC-Programme wurde separat im vorangegangenen Boottest beobachtet;
die Markerprüfung selbst führt keine Hardwareumschaltung aus.

Das alte `SmcDumpKey` aus `tdm.tcz` ist ein 32-Bit-i386-ELF mit Interpreter
`/lib/ld-linux.so.2`. Dieser Loader fehlt im gestarteten Originalsystem. Die
wiederhergestellte Version unter `/usr/local/bin` ist x86-64 mit
`/lib/ld-linux-x86-64.so.2`. Damit ist der alte `/usr/bin/SmcDumpKey`-Pfad in diesem
System nicht ausführbar. Ein historisch anders konfigurierter Stickstand lässt
sich damit nicht beurteilen.

Die VM wurde ohne Dateibackup beendet; die Marker wurden weder auf den
Originalstick noch in das schreibgeschützte Referenzimage übernommen.

## Grenzen

OVMF ist keine iMac-Firmware. Der Test bestätigt den Standard-USB-EFI-Bootpfad
in QEMU, nicht die historische Firmwareauswahl des iMac. DisplayPort-Eingang,
Bildumschaltung, Rückschalten und Helligkeit müssen am echten Gerät getestet werden.
Die zwei alternativen grubx64.efi-Dateien wurden statisch untersucht, aber nicht
als separate Firmware-Bootziele gestartet.

## Installer-Optionen für Tastatur und SSH

Die Installation mit `--keymap de --ssh-key …` wurde zusätzlich in QEMU/UEFI
mit einem emulierten USB-Datenträger und E1000-Netzwerk gebootet. SSH-Anmeldung
als `tc` mit einem temporären Ed25519-Schlüssel war erfolgreich;
`/etc/sysconfig/keymap` meldete `qwertz/de-latin1`. Nach einem Neustart gelang
auch eine Verbindung mit strikter Prüfung des zuvor gespeicherten Hostschlüssels.
Die Passwortvariante wurde mit einem zufälligen Testpasswort und dem vom Installer
erzeugten SHA-512-crypt-Hash geprüft. Testschlüssel und Passwörter liegen nicht
im Repository. Diese Tests prüfen die Einrichtung, nicht die physische TDM-Umschaltung.
