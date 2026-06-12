# V.connect Fremdaufruf — Übersicht

V.connect Fremdaufruf ermöglicht es einem KIS, ein vorausgefülltes
V.ap-Produktformular (DUBA, ELIM+, …) im Browser des Arbeitsplatzes
zu öffnen — auch dann, wenn das KIS selbst den HTTPS-POST-Aufruf,
den V.ap normalerweise erwartet, nicht ausführen kann. Die Komponente
läuft neben dem KIS auf dem Arbeitsplatz, nimmt die GET-URL entgegen,
die das KIS erzeugen kann, und überbrückt die Lücke zu V.aps
POST-basierter Sitzungsinitialisierung.

Dieses Dokument ist die kundenorientierte Übersicht: wofür die
Komponente da ist, was sie leistet und was ihre Einführung umfasst.
Für die tiefergehende Architektur und Designentscheidungen siehe
[Architecture](solution-outline.md) (englischsprachig). Für den
Arbeitsablauf des KIS-Integrators beim Erzeugen von URL-Vorlagen
mit dem V.ap-URL-Vorlagen-Werkzeug siehe das
[Benutzerhandbuch](user-manual.md).

---

## 1. Zweck

V.ap-Produktmodule stellen POST-Endpunkte bereit, die strukturierte
JSON-Daten (Patientenidentifikation, Berichts­daten,
Justizmeldungs-Referenzen, …) entgegennehmen und mit einem
einmaligen Login-Link auf ein vorausgefülltes Formular antworten.
KIS-Systeme, die HTTPS-POST-Aufrufe ausführen können, integrieren
sich direkt mit diesen Endpunkten.

Viele KIS-Konfigurationen können das nicht. Die
Integrationsschnittstelle, die sie bereitstellen, kennt nur ein
einziges Primitiv: *"Öffne diese URL mit den angehängten
Parametern"*. Der naheliegende Umweg — denselben Inhalt per GET
auf einem V.ap-Endpunkt entgegen zu nehmen — scheitert aus
Datenschutzgründen: URLs hinterlassen Spuren in Browser-Verläufen,
in Proxy-Protokollen, in Server-Zugriffs-Logs und im Referer-Header
jedes nachfolgend angeklickten Links.

Fremdaufruf schließt diese Lücke **auf der Arbeitsplatzseite**. Die
Komponente läuft lokal, nimmt die vom KIS erzeugte GET-URL entgegen,
übersetzt sie in den von V.ap erwarteten authentifizierten POST-Aufruf
und leitet den Browser per 303-Redirect auf den resultierenden
Login-Link weiter. Die V.ap-Module selbst bleiben unverändert; nur
die lokale Komponente kommt hinzu.

---

## 2. Auf einen Blick

<figure>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 280" role="img" aria-labelledby="diagramTitle" style="max-width: 100%; height: auto;">
  <title id="diagramTitle">Wo Fremdaufruf läuft — auf dem Arbeitsplatz, zwischen KIS und V.ap</title>
  <defs>
    <marker id="ovArrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#1565c0"/>
    </marker>
  </defs>

  <!-- Krankenhausnetz -->
  <rect x="20" y="40" width="460" height="220" rx="14" fill="#fafafa" stroke="#bdbdbd" stroke-dasharray="4,3"/>
  <text x="38" y="62" font-family="system-ui, sans-serif" font-size="12" fill="#757575" font-weight="500" font-style="italic">Krankenhausnetz · KIS-Arbeitsplatz</text>

  <!-- KIS -->
  <rect x="50" y="100" width="170" height="130" rx="10" fill="#ffffff" stroke="#9e9e9e" stroke-width="1.5"/>
  <text x="135" y="135" font-family="system-ui, sans-serif" font-size="16" fill="#424242" font-weight="600" text-anchor="middle">KIS</text>
  <text x="135" y="160" font-family="system-ui, sans-serif" font-size="11" fill="#757575" text-anchor="middle">Anwendung +</text>
  <text x="135" y="176" font-family="system-ui, sans-serif" font-size="11" fill="#757575" text-anchor="middle">eingebetteter Browser</text>

  <!-- Fremdaufruf (hervorgehoben) -->
  <rect x="285" y="115" width="170" height="100" rx="10" fill="#fff3e0" stroke="#ef6c00" stroke-width="2.5"/>
  <text x="370" y="145" font-family="system-ui, sans-serif" font-size="11" fill="#3e2723" font-weight="500" text-anchor="middle">V.connect</text>
  <text x="370" y="170" font-family="system-ui, sans-serif" font-size="17" fill="#3e2723" font-weight="700" text-anchor="middle">Fremdaufruf</text>
  <text x="370" y="192" font-family="system-ui, sans-serif" font-size="10" fill="#5d4037" font-style="italic" text-anchor="middle">einzelnes, statisches Binary</text>

  <!-- Vertama-Cloud -->
  <rect x="510" y="40" width="200" height="220" rx="14" fill="#e3f2fd" stroke="#1565c0" stroke-dasharray="4,3"/>
  <text x="530" y="62" font-family="system-ui, sans-serif" font-size="12" fill="#0d47a1" font-weight="500" font-style="italic">Vertama-Cloud</text>

  <!-- V.ap -->
  <rect x="545" y="115" width="130" height="100" rx="10" fill="#bbdefb" stroke="#1565c0" stroke-width="2"/>
  <text x="610" y="175" font-family="system-ui, sans-serif" font-size="22" fill="#0d47a1" font-weight="700" text-anchor="middle">V.ap</text>

  <!-- Pfeile -->
  <line x1="220" y1="165" x2="283" y2="165" stroke="#1565c0" stroke-width="2" marker-end="url(#ovArrow)"/>
  <text x="251" y="156" font-family="system-ui, sans-serif" font-size="11" fill="#1565c0" font-weight="500" text-anchor="middle">GET-URL</text>

  <line x1="455" y1="165" x2="543" y2="165" stroke="#1565c0" stroke-width="2" marker-end="url(#ovArrow)"/>
  <text x="499" y="156" font-family="system-ui, sans-serif" font-size="11" fill="#1565c0" font-weight="500" text-anchor="middle">HTTPS POST</text>
</svg>
<figcaption style="font-size: 0.85em; color: #616161; margin-top: 0.4rem; text-align: center;">
Auf dem Arbeitsplatz nimmt Fremdaufruf die GET-URL des KIS entgegen und übersetzt sie in den authentifizierten HTTPS-POST-Aufruf, den V.ap erwartet. Der Browser folgt anschließend der V.ap-Weiterleitung zum vorausgefüllten Formular.
</figcaption>
</figure>

Was die Komponente dem Kunden bietet:

- **Ein einzelnes, schlankes Binary** auf jedem KIS-Arbeitsplatz
  oder ein Container im Krankenhausnetz — als Windows-Dienst oder
  Linux-Container betrieben. Einstellige MB Arbeitsspeicher, keine
  Laufzeit-Abhängigkeiten.
- **Kompatibilität mit KIS-Systemen, die nur die einfache
  "Externe URL öffnen"-Funktion bieten** — keine KIS-seitige
  Entwicklung erforderlich.
- **Endnutzer-Erlebnis bleibt erhalten**: das vorausgefüllte
  Formular erscheint im eingebetteten Browser des KIS, kein
  Fenster-Wechsel, keine separate Anmeldung.
- **Modul-unabhängig**: eine Komponente, alle V.ap-Module. Ein
  zusätzliches Modul in die Integration aufzunehmen ist eine
  Konfigurationsänderung, keine neue Bereitstellung.

---

## 3. Integrationsfreiheit

Das Integrations-Primitiv, auf dem Fremdaufruf aufsetzt — eine
externe URL mit angehängten Parametern öffnen — ist eine der am
weitesten verbreiteten KIS-Fähigkeiten. Praktisch jedes
Klinik-Informationssystem unterstützt sie; sie ist älter als jede
anbieterspezifische Integrations-API. Dadurch hängen Integrationen
mit V.ap-Modulen nicht davon ab, dass der KIS-Anbieter
modul-spezifische Unterstützung bereitstellt, eigene Adapter baut
oder kostenpflichtige Integrations-Stufen freischaltet. Das
Krankenhaus entscheidet, welche Module integriert werden; der
KIS-Anbieter steuert diese Entscheidung weder, noch stellt er sie
in Rechnung.

---

## 4. Bereitstellungsvarianten

V1 unterstützt zwei Varianten aus demselben Binary, unterschieden
durch die Konfiguration:

**Pro Arbeitsplatz, Loopback-gebunden.** Jeder KIS-Arbeitsplatz
betreibt eine eigene Instanz, gebunden an `127.0.0.1`. Betrieblich
einfach — ein Arbeitsplatz, eine Installation. Vertrauensgrenze:
das Betriebssystem des Arbeitsplatzes. Bereitgestellt als
signierter Windows-Installer, der einen nativen Windows-Dienst
registriert.

**Zentral im Krankenhausnetz.** Eine einzige Installation im
Krankenhausnetz, an eine routbare Adresse gebunden, bedient mehrere
KIS-Arbeitsplätze. Vertrauensgrenze: ein konfiguriertes Access
Secret, das jeder Aufrufer in jeder Anfrage mitliefern muss.
Bereitgestellt als Container-Image unter
`ghcr.io/mcp-health/v.connect/fremdaufruf` (linux/amd64), mit einer
Docker-Compose-Beispieldatei als Ausgangspunkt.

Beide Varianten nutzen dasselbe Binary, dasselbe
Konfigurations-Schema und denselben Upstream-Vertrag mit V.ap. Die
Wahl ist eine betriebliche Entscheidung, keine Produkt-Entscheidung.

---

## 5. Einführung

### 5.1 Voraussetzungen

| Punkt | Anforderung |
|-------|-------------|
| **Plattform** | Windows 10 oder neuer (x64) für Arbeitsplatz-Bereitstellungen; Linux x86-64 über Container (Docker / Podman) für zentrale Bereitstellungen. macOS ausschließlich für Entwicklung. |
| **Ausgehendes Netzwerk** | HTTPS-Erreichbarkeit vom Arbeitsplatz (oder LAN-Host) zur V.ap-Basis-URL. |
| **V.ap-API-Benutzer** | Bereitgestellt durch Ihren Vertama-Kontakt, mit den Modul-Berechtigungen, die die Integration erfordert. |
| **Dienst-Installationsrechte** | Administrator (Windows) bzw. root (Linux) für die Dienst-Registrierung. Der reguläre Betrieb läuft unprivilegiert. |
| **Festplatte** | Weniger als 50 MB für das Binary, die Konfiguration und das Audit-Log. |

Die Komponente ist ein einzelnes, statisches Binary ohne
Laufzeit-Abhängigkeiten — kein JRE, keine .NET-Runtime, keine
gemeinsam genutzten Bibliotheken über das Betriebssystem hinaus.

### 5.2 Installationswege

- **Windows.** Signierter Installer registriert den Windows-Dienst,
  legt das Binary in `%PROGRAMFILES%` ab und schreibt eine
  Konfigurations-Vorlage. Authenticode-Signatur ist vor der
  Installation überprüfbar.
- **Linux / Container.** Container-Image mit einer
  Docker-Compose-Beispieldatei als Ausgangspunkt. Konfiguration per
  Umgebungsvariablen (12-Faktor) oder per eingebundener
  Konfigurationsdatei.
- **macOS.** Nur Entwicklung.

### 5.3 Im laufenden Betrieb

Nach der Installation läuft die Komponente als langlaufender Dienst
und stellt ein browserbasiertes **Admin-Dashboard** unter
`http://127.0.0.1:8811/admin` auf dem Host bereit. Der Administrator
legt den Admin-Zugangscode fest, passt die Konfiguration an die
V.ap-Instanz an, lädt die Konfiguration aus dem Dashboard neu und
bestätigt, dass der V.ap-Konnektivitätstest erfolgreich ist. Die
Installation ist in wenigen Minuten abgeschlossen; der erste
erfolgreiche KIS-Aufruf erfolgt in der Regel am selben Tag, sobald
die Konfiguration steht.

Der tägliche Betrieb läuft ohne aktive Begleitung. Das Dashboard
zeigt aktuelle Aktivitäts-Zähler, die effektive Konfiguration (mit
redigierten Geheimnissen) und die jüngsten Aufrufe.

Das vollständige Betriebshandbuch — Installationsablauf, vollständiges
Konfigurations-Schema, Fehlersuche, Audit-Log-Details — wird mit dem
Binary ausgeliefert als **Betriebshandbuch** und ist über das
Admin-Dashboard erreichbar. Vertama stellt es auf Anfrage bereits
vor der Bereitstellung für die IT-Sicherheits-Prüfung zur Verfügung.

---

## 6. Sicherheit & Compliance — Zusammenfassung

Drei unabhängige Steuerungen regeln, was über Fremdaufruf möglich
ist:

- **V.ap-seitige Autorisierung** (primär) — der Geltungsbereich des
  konfigurierten API-Benutzers bei V.ap bestimmt, welche
  V.ap-Aktionen überhaupt erreichbar sind.
- **Lokale Pfad-Allowlist** (zusätzliche Absicherung) —
  Krankenhaus-Administratoren können die Oberfläche auf eine Liste
  zulässiger Upstream-Pfade einschränken.
- **Access Secret** (Vertrauensgrenze im Intranet) — erforderlich
  für nicht-Loopback-Bereitstellungen; jede Anfrage muss den
  passenden `_s`-Parameter mitliefern.

Auf der Übertragungsebene: HTTPS ausschließlich zur konfigurierten
V.ap-Basis-URL; TLS-Verifizierung gegen den System-Trust-Store;
Parameter-Werte und -Schlüssel werden auf keiner Log-Stufe
protokolliert (ausschließlich deren Anzahl); Anmeldedaten und
Access Secrets werden niemals protokolliert.

Für die vollständige Sicherheitsbetrachtung —
Autorisations­modell, Wire-Level-Garantien je
Bereitstellungs­variante, Vertrauensgrenzen, Audit-Log-Garantien —
siehe [Architecture §8](solution-outline.md#8-security-posture)
(englischsprachig).

---

## 7. Support

Vertama unterstützt Fremdaufruf direkt. Das Team dahinter ist
klein, was bedeutet: wenn Sie uns erreichen, erreichen Sie das
Engineering, keine Ticket-Warteschlange. Reaktion erfolgt zügig bei
installations-blockierenden Problemen; funktionale Verbesserungen
fließen in die reguläre Release-Kadenz ein.

---

## 8. In V1 enthalten — und was nicht

**In V1 enthalten:**

- Beide Bereitstellungs-Varianten (pro Arbeitsplatz Loopback,
  zentral im Krankenhausnetz).
- Signierter Windows-Installer und Linux-Container-Distribution.
- Browserbasiertes Admin-Dashboard für Status, Konfigurations-
  Neuladen und V.ap-Konnektivitäts-Test.
- TOML-Konfiguration mit Umgebungsvariablen-Überschreibungen.
- Stderr- und Datei-Audit-Log-Ziele.
- URL-Vorlagen-Werkzeug bei V.ap für die vom Kunden gewählten
  Module (DUBA, ELIM+ und weitere V.ap-Module nutzen denselben
  URL-Vorlagen-Workflow ohne zusätzliche Komponenten-Kosten).

Was bewusst nicht im aktuellen Umfang ist, mit Begründung, siehe
[Architecture §9](solution-outline.md#9-scope-and-roadmap)
(englischsprachig).

---

**Begleitdokumente:**

- [Architecture](solution-outline.md) — vollständige
  Design-Begründung, Bereitstellungs-Details, Sicherheits-Posture,
  Umfang und Roadmap (englisch).
- [Benutzerhandbuch](user-manual.md) — KIS-Integrator-Anleitung
  für das V.ap-URL-Vorlagen-Werkzeug.
- **Betriebshandbuch** — Betriebsanleitung; wird mit dem Binary
  ausgeliefert und ist nach der Installation über das Admin-Dashboard
  erreichbar.

---

**Stand:** 11.06.2026
**Gilt für:** V.connect Fremdaufruf V1
