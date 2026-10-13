# Zertifikats-PIN prüfen

Mit dieser Anleitung prüfen Sie auf Ihrem eigenen Rechner, ob eine PIN Ihre
Zertifikatsdatei öffnet. Nutzen Sie sie, bevor Sie ein Postfach in V.ap
registrieren, oder wenn V.ap die Registrierung mit einer dieser Meldungen
ablehnt:

- „Zertifikat kann nicht gelesen werden - falsches Passwort oder ungültiges Format"
- „VHN-Zertifikat kann nicht geöffnet werden - falsche PIN oder ungültiges Format"

Zu einem Postfach gehören bis zu zwei Zertifikatsdateien, jede mit eigener PIN.
Prüfen Sie jede Datei mit ihrer PIN:

| Datei | Postfachart |
|---|---|
| Postfachzertifikat | eBO und beBPo |
| VHN-Zertifikat | nur beBPo |

Das Postfachzertifikat heißt je nach Quelle auch *Autorenzertifikat*; im
Registrierungsformular von V.ap steht *Author-Zertifikat*. Gemeint ist
jeweils dieselbe Datei.

!!! note "Ihre Daten bleiben auf Ihrem Rechner"
    Die Prüfung läuft vollständig lokal. Weder die Datei noch die PIN werden
    dabei übertragen.

## Voraussetzungen

- die Zertifikatsdatei (Endung `.p12` oder `.pfx`)
- die zugehörige PIN
- ein Befehlsfenster und ein Prüfprogramm, siehe [Benötigte Werkzeuge](#benotigte-werkzeuge)

## Benötigte Werkzeuge

Sie brauchen ein Befehlsfenster, in das Sie Befehle eingeben, und ein
Programm, das Zertifikatsdateien öffnen kann. Auf allen drei Systemen ist
beides in der Regel schon vorhanden.

| System | Befehlsfenster | Prüfprogramm | Vorhanden |
|---|---|---|---|
| Windows | *Windows PowerShell* | der Befehl `Get-PfxData` | unter Windows 10 und 11 immer |
| macOS | *Terminal* | `openssl` | immer |
| Linux | ein Terminal | `openssl` | meist; sonst nachinstallieren |

**Windows PowerShell** ist die Befehlszeile von Windows; `Get-PfxData`
gehört zu ihr. Ist zusätzlich das neuere *PowerShell 7* installiert,
erscheinen im Startmenü beide – diese Anleitung ist für *Windows PowerShell*
geschrieben.

**OpenSSL** ist ein weit verbreitetes Programm für Zertifikate und
Verschlüsselung. Ob es vorhanden ist, zeigt dieser Befehl im Terminal:

```
openssl version
```

Er gibt eine Versionsnummer aus, etwa `OpenSSL 3.0.13`, unter macOS etwa
`LibreSSL 3.3.6` – beides ist geeignet. Unter macOS ist `openssl` immer
vorhanden. Meldet Linux stattdessen `command not found` oder
„Befehl nicht gefunden", installieren Sie es über die Paketverwaltung Ihrer
Distribution:

| Distribution | Befehl |
|---|---|
| Debian, Ubuntu | `sudo apt install openssl` |
| Fedora, Red Hat | `sudo dnf install openssl` |
| openSUSE | `sudo zypper install openssl` |

Auf Arbeitsplatzrechnern übernimmt das in der Regel Ihre IT-Abteilung.

## Unter Windows prüfen

Sie geben zuerst an, welche Datei geprüft wird, und starten dann die
Prüfung mit einem Befehl, den Sie unverändert übernehmen.

1. Öffnen Sie *Windows PowerShell*: Startmenü, „PowerShell" eingeben,
   *Windows PowerShell* wählen.
1. **Pfad kopieren:** Klicken Sie die Zertifikatsdatei im Explorer mit
   gedrückter Umschalttaste rechts an und wählen Sie *Als Pfad kopieren*. Der
   Pfad liegt dann samt Anführungszeichen in der Zwischenablage.
1. **Datei angeben:** Tippen Sie in der PowerShell `$f = ` ein, fügen Sie den
   Pfad ein (Strg + V) und drücken Sie die Eingabetaste. Die Zeile sieht etwa
   so aus: `$f = "C:\Users\name\Downloads\VHN Zertifikat.p12"`. Die
   Anführungszeichen müssen dabei sein; *Als Pfad kopieren* setzt sie für Sie.
1. **Prüfen:** Kopieren Sie den folgenden Befehl – fahren Sie dazu mit der
   Maus über den Kasten und klicken Sie auf die Kopier-Schaltfläche, die oben
   rechts erscheint. Fügen Sie ihn in der PowerShell ein (Strg + V) und drücken
   Sie die Eingabetaste:

    ```powershell
    Get-PfxData -FilePath $f -Password (Read-Host -Prompt "PIN" -AsSecureString)
    ```

1. Bei `PIN:` geben Sie die PIN ein und drücken wieder die Eingabetaste. Die
   PIN erscheint dabei als Sternchen.

Für eine weitere Datei wiederholen Sie die Schritte 2 bis 5. Was die Ausgabe
bedeutet, steht unter [Ergebnis deuten](#ergebnis-deuten).

## Unter macOS prüfen

Sie geben zuerst an, welche Datei geprüft wird, und starten dann die
Prüfung mit einem Befehl, den Sie unverändert übernehmen.

1. Öffnen Sie das *Terminal*: Programme › Dienstprogramme › Terminal, oder
   über die Spotlight-Suche (⌘ + Leertaste) mit „Terminal".
1. **Datei angeben:** Tippen Sie `f=` ein, ohne Leerzeichen dahinter. Ziehen
   Sie dann die Zertifikatsdatei aus dem Finder in das Terminalfenster – ihr
   Pfad wird direkt hinter `f=` eingefügt – und drücken Sie die
   Eingabetaste. Die Zeile sieht etwa so aus:
   `f=/Users/name/Downloads/VHN\ Zertifikat.p12`
1. **Prüfen:** Kopieren Sie den folgenden Befehl – fahren Sie dazu mit der
   Maus über den Kasten und klicken Sie auf die Kopier-Schaltfläche, die oben
   rechts erscheint. Fügen Sie ihn im Terminal ein (⌘ + V) und drücken Sie die
   Eingabetaste:

    ```
    openssl pkcs12 -noout -in "$f" && echo "PIN passt"
    ```

1. Bei `Enter Import Password:` geben Sie die PIN ein und drücken wieder die
   Eingabetaste. Die PIN wird beim Tippen nicht angezeigt, auch keine
   Sternchen – das ist so gewollt.

Für eine weitere Datei wiederholen Sie die Schritte 2 bis 4. Was die Ausgabe
bedeutet, steht unter [Ergebnis deuten](#ergebnis-deuten).

## Unter Linux prüfen

Sie geben zuerst an, welche Datei geprüft wird, und starten dann die
Prüfung mit einem Befehl, den Sie unverändert übernehmen.

1. Öffnen Sie ein Terminal, etwa über das Anwendungsmenü mit „Terminal".
1. **Datei angeben:** Tippen Sie `f=` ein, ohne Leerzeichen dahinter. Ziehen
   Sie dann die Zertifikatsdatei aus der Dateiverwaltung in das
   Terminalfenster – ihr Pfad wird direkt hinter `f=` eingefügt – und drücken
   Sie die Eingabetaste. Die Zeile sieht etwa so aus:
   `f='/home/name/Downloads/VHN Zertifikat.p12'`.
   Lässt Ihr Terminal das Hineinziehen nicht zu, tippen Sie den Pfad in
   Anführungszeichen ein: `f="/home/name/Downloads/VHN Zertifikat.p12"`
1. **Prüfen:** Kopieren Sie den folgenden Befehl – fahren Sie dazu mit der
   Maus über den Kasten und klicken Sie auf die Kopier-Schaltfläche, die oben
   rechts erscheint. Fügen Sie ihn im Terminal ein (meist Strg + Umschalt + V)
   und drücken Sie die Eingabetaste:

    ```
    openssl pkcs12 -noout -in "$f" && echo "PIN passt"
    ```

1. Bei `Enter Import Password:` geben Sie die PIN ein und drücken wieder die
   Eingabetaste. Die PIN wird beim Tippen nicht angezeigt, auch keine
   Sternchen – das ist so gewollt.

Für eine weitere Datei wiederholen Sie die Schritte 2 bis 4. Was die Ausgabe
bedeutet, steht unter [Ergebnis deuten](#ergebnis-deuten).

## Ergebnis deuten

| Ausgabe | Bedeutung | Was tun |
|---|---|---|
| Windows: Angaben zum Zertifikat, darunter `EndEntityCertificates`<br>macOS, Linux: `PIN passt` (je nach Version davor `MAC verified OK`) | Die PIN öffnet die Datei. | Registrieren Sie das Postfach mit dieser PIN. |
| Windows: `Das angegebene Netzwerkkennwort ist falsch.`<br>macOS, Linux: `Mac verify error: invalid password?` | Die PIN passt nicht zu dieser Datei. | Siehe [Wenn die PIN nicht passt](#wenn-die-pin-nicht-passt). |
| macOS, Linux: eine Meldung mit `unsupported` | Die PIN stimmt, die Datei ist aber mit einem älteren Verfahren verschlüsselt, das neuere OpenSSL-Versionen nur auf Anforderung lesen. | Prüfen Sie mit dem Befehl unter dieser Tabelle. |
| Windows: eine Meldung, dass die Datei nicht gefunden wurde<br>macOS, Linux: `No such file or directory` | Unter dem angegebenen Pfad liegt keine Datei. | Geben Sie die Datei erneut an (Windows Schritte 2 und 3, macOS und Linux Schritt 2). |
| macOS, Linux: eine Meldung mit `asn1 encoding routines` | Die Datei ist keine gültige Zertifikatsdatei oder beschädigt. | Beziehen Sie die Datei erneut von der Stelle, die sie ausgestellt hat. |

Bei der Meldung `unsupported` prüfen Sie unter macOS und Linux mit diesem
Befehl statt des obigen:

```
openssl pkcs12 -legacy -noout -in "$f" && echo "PIN passt"
```

Meldet auch dieser Befehl einen Fehler, der `legacy` erwähnt, fehlt auf Ihrem
System die Unterstützung für ältere Verfahren. Prüfen Sie die Datei dann
unter Windows, oder wenden Sie sich an Ihre IT-Abteilung.

## Wenn die PIN nicht passt

Prüfen Sie zuerst die häufigsten Ursachen:

- **Groß- und Kleinschreibung**: Die PIN unterscheidet zwischen beiden.
- **Tastaturbelegung**: Auf einer englischen Tastatur sind unter anderem Y und Z
  vertauscht, Sonderzeichen liegen auf anderen Tasten.
- **Kopierte PIN**: Beim Kopieren geraten leicht Leerzeichen an den Anfang oder
  das Ende.
- **Vertauschte PINs**: Postfachzertifikat und VHN-Zertifikat haben
  verschiedene PINs. Prüfen Sie, ob Datei und PIN zusammengehören.

Passt die PIN danach immer noch nicht, wenden Sie sich an die Stelle, von der
Sie die Zertifikatsdatei erhalten haben. Vertama kann die PIN einer
Zertifikatsdatei nicht wiederherstellen.

!!! warning "Die PIN nicht in den Befehl schreiben"
    Geben Sie die PIN nur an der Eingabeaufforderung ein, nicht als Teil des
    Befehls. Was im Befehl steht, bleibt im Verlauf von Terminal oder
    PowerShell gespeichert.
