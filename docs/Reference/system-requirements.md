# Systemanforderungen

## Unterstützte Browser

Die Vertama-Anwendungen (ELIM, DUBA, DIVI, etc.) sind webbasiert und erfordern einen modernen Browser mit Unterstützung für aktuelle Web-Standards.

### Mindestanforderungen

| Browser | Minimale Version | Empfohlene Version |
|---------|------------------|-------------------|
| **Chrome / Chromium** | 105+ (Aug 2022) | Neueste stabile Version |
| **Microsoft Edge** | 105+ (Aug 2022) | Neueste stabile Version |
| **Firefox** | 121+ (Dez 2023) | Neueste stabile Version |
| **Safari** | 15.4+ (März 2022) | Neueste stabile Version |

### Nicht unterstützt

- **Internet Explorer** (alle Versionen) - wird seit Juni 2022 nicht mehr von Microsoft unterstützt
- Ältere Browser-Versionen ohne Unterstützung für moderne CSS-Features

## Technische Hintergrund

Die Anwendungen nutzen moderne CSS-Features wie die `:has()` Pseudo-Klasse für eine verbesserte Benutzeroberfläche. Diese Features sind in älteren Browsern nicht verfügbar.

### Verhalten in älteren Browsern

Die Anwendungen funktionieren grundsätzlich auch in älteren Browsern, jedoch mit Einschränkungen:

- **Pflichtfeld-Kennzeichnung**: Der rote Stern (*) bei Pflichtfeldern wird möglicherweise nicht angezeigt
- **Formulare**: Bleiben funktional - Browser-eigene Validierung zeigt Pflichtfelder beim Absenden an
- **Visuelle Darstellung**: Kann in Details abweichen

### Empfehlung

Für die beste Benutzererfahrung empfehlen wir:

1. Verwendung der **neuesten stabilen Version** Ihres Browsers
2. Aktivierung automatischer Browser-Updates
3. In Unternehmensumgebungen: **Chrome** oder **Edge** (Chromium-basiert)

## Weitere Anforderungen

### JavaScript

- **Erforderlich**: JavaScript muss im Browser aktiviert sein
- Die Anwendungen verwenden JavaScript für interaktive Formulare und dynamische Inhalte

### Bildschirmauflösung

- **Minimum**: 1024 × 768 Pixel
- **Empfohlen**: 1920 × 1080 Pixel oder höher
- **Responsive Design**: Die Anwendungen passen sich automatisch an verschiedene Bildschirmgrößen an

### Internetverbindung

- Stabile Internetverbindung erforderlich
- Empfohlene Bandbreite: mindestens 1 Mbit/s

## Barrierefreiheit

Die Vertama-Anwendungen werden kontinuierlich hinsichtlich Barrierefreiheit verbessert. Bei Fragen zur Zugänglichkeit wenden Sie sich bitte an den Support.

---

**Stand**: Januar 2026
**Nächste Überprüfung**: Juli 2026
