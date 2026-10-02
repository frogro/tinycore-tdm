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
  Archivtests bestehen. Diese kleine Korrektur wurde nicht erneut voll gebootet.

- Ein zweiter Boot des bereinigten Images über den Safe Console Mode erreicht
  die Konsole mit `text tdm_safe=1`. `/var/log/bootlocal.log` existiert danach
  nicht; die projektspezifischen Startaufgaben wurden übersprungen.

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
