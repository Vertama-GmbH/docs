# HL7-Anbindung: Dokumentenübermittlung ins KIS

V.ap-Produktmodule (z. B. DUBA, DIGG) erzeugen im Abschluss ihrer Fachprozesse
archivierbare Dokumente — immer als PDF. Optional, je Kundenkonfiguration, stellt
Vertama diese Dokumente zusätzlich **per HL7-Nachricht direkt in Ihr KIS bzw.
Archivsystem** zu. Das ist das gesamte Prinzip: Fachprozess → PDF-Dokument →
optionale HL7-Zustellung über die V.connect-Anbindung (Site-to-Site-VPN).

## Die Nachricht

| | |
|---|---|
| Nachrichtentyp | `MDM^T02` (Neuanlage eines Dokuments), HL7 v2.5 |
| Quittung | Enhanced Acknowledgement (`AL\|NE`) — Ihr System bestätigt den Empfang |
| Dokument | PDF, Base64-eingebettet |
| Zeichensatz, Formatdetails | je Empfänger konfigurierbar (Dialekt-Einstellungen) |

**Dokumententyp (TXA-2):** je Produkt und Dokumentart ein **fester, abgestimmter
Wert** — geeignet als stabiler Schlüssel für Ihr Archiv-Mapping (z. B. KDL).
Derzeit übermittelt jedes Produkt genau eine Dokumentart; die konkreten Werte
werden bei der Anbindung abgestimmt und ändern sich danach nicht — beispielsweise
`Geburtsbescheinigung` (DIGG) oder `Betreuungsantrag` (DUBA).

## Feld-Mapping

Welche fachlichen Attribute in welche HL7-Felder gelangen (z. B. Patienten-ID in
`PID-3`, Fallnummer in `PV1-19`), wird **pro Kunde konfiguriert** — auf Basis der
Attribute, die das jeweilige Produkt bereitstellt. Zusammengesetzte Werte können
dabei zerlegt werden (z. B. `<PatientenID>|<Fallnummer>` aus einem Feld).

Beispiel — Ihr System belegt beim Aufruf `clientReference` mit `4711|0815` vor;
die HL7-Nachricht zum zurückgespielten Dokument trägt dann:

| HL7-Feld | Wert | Quelle |
|---|---|---|
| PID-3 (Patienten-ID) | `4711` | `clientReference`, erster Teil |
| PV1-19 (Fallnummer) | `0815` | `clientReference`, zweiter Teil |
| TXA-12 (Dokument-ID) | `1725007…` | `reportId` |

Verfügbare Attribute:

**Alle Produkte**

| Attribut | Bedeutung |
|---|---|
| `reportId` | Eindeutige Vorgangs-ID (Korrelationsschlüssel) |
| `reportName` | Bezeichnung des Dokuments |

**DUBA** (gerichtliche Meldungen)

| Attribut | Bedeutung |
|---|---|
| `aktenzeichen` | Aktenzeichen des Vorgangs (Fallnummer) |
| `absenderSafeId` / `empfaengerSafeId` | SAFE-IDs der EGVP-Übermittlung |
| `egvpMessageId` | EGVP-Nachrichten-ID der versandten Meldung |

**DIGG** (digitale Geburtsanzeige)

| Attribut | Bedeutung |
|---|---|
| `clientReference` | Frei durch das aufrufende System vorbelegbares Feld — wird mit dem Dokument zurückgespielt (z. B. für Patienten-/Fallzuordnung) |
| `zuordnungGeburtsanzeige` | Zuordnungskennzeichen der Geburtsanzeige |
| `standesamtKennung` / `standesamtName` | Zuständiges Standesamt |
| `standortId` | Standort des meldenden Krankenhauses |
| `portal` | Übermittlungsweg (Standesamtportal) |

Weitere Produkte folgen demselben Muster.

## Transport

Die Zustellung erfolgt über unsere V.connect-Anbindung an die HL7-Endpunkte
Ihres Hauses — in der Regel ein Site-to-Site-VPN, abgestimmt mit Ihrer
Netzwerk-/Security-Abteilung.
*(Eigenes Kapitel zur Netzanbindung folgt.)*

## FAQ

**Wird ein Storno von Dokumenten über die HL7-Schnittstelle unterstützt?**

!!! info "Derzeit nicht vorgesehen"
    Übermittelt werden ausschließlich Neuanlagen (`MDM^T02`). Ein Storno-Ereignis
    ist aktuell nicht Teil der Produktabläufe. Fachlich vorstellbar ist es —
    sprechen Sie uns bei Bedarf an.

**Welche Dokumenttypen werden übermittelt?**

Je angebundenem Produkt derzeit genau eine Dokumentart (siehe
[Dokumententyp](#die-nachricht)); der TXA-2-Wert wird bei der Anbindung
abgestimmt und bleibt stabil.
