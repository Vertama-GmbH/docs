title: One Pager / Flyer (HTML)
---

<style>
    .container {
        max-width: 1000px;
        margin: 0 auto;
        background: white;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
        min-height: 100vh;
    }

    .header {
        background: linear-gradient(135deg, #4a90e2, #357abd);
        color: white;
        padding: 40px;
        position: relative;
        overflow: hidden;
    }

    .header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 200px;
        height: 200px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 50%;
        animation: float 6s ease-in-out infinite;
    }

    @keyframes float {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(180deg); }
    }

    .header-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 20px;
        position: relative;
        z-index: 1;
    }

    .logo {
        font-size: 4rem;
        font-weight: 900;
        letter-spacing: 0.1em;
    }

    .vertama-logo {
        font-size: 1.5rem;
        font-weight: 300;
        opacity: 0.9;
        display: flex;
        align-items: center;
    }

    .vertama-logo::before {
        content: '⟐';
        margin-right: 10px;
        font-size: 1.8rem;
    }

    .subtitle {
        font-size: 1.8rem;
        font-weight: 600;
        margin-bottom: 10px;
    }

    .tagline {
        font-size: 1.2rem;
        opacity: 0.9;
        font-weight: 300;
    }

    .content {
        padding: 40px;
    }

    .intro-text {
        font-size: 1.1rem;
        margin-bottom: 40px;
        line-height: 1.7;
        color: #444;
        padding: 20px;
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 10px;
        border-left: 4px solid #4a90e2;
    }

    .intro-text strong {
        color: #2c3e50;
    }

    .two-column {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 40px;
        margin-bottom: 40px;
    }

    .section {
        background: white;
        border-radius: 15px;
        padding: 30px;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
    }

    .section:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.12);
    }

    .section h3 {
        color: #4a90e2;
        font-size: 1.4rem;
        margin-bottom: 20px;
        font-weight: 600;
    }

    .feature-list {
        list-style: none;
    }

    .feature-list li {
        margin-bottom: 15px;
        padding-left: 25px;
        position: relative;
        line-height: 1.6;
    }

    .feature-list li::before {
        content: '•';
        color: #4a90e2;
        font-size: 1.5rem;
        position: absolute;
        left: 0;
        top: -2px;
    }

    .feature-list li strong {
        color: #2c3e50;
    }

    .process-steps {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 15px;
        padding: 30px;
        margin-bottom: 40px;
    }

    .process-steps h3 {
        color: #4a90e2;
        font-size: 1.4rem;
        margin-bottom: 25px;
        text-align: center;
        font-weight: 600;
    }

    .steps-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
    }

    .step {
        background: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }

    .step:hover {
        transform: translateY(-3px);
    }

    .step-number {
        background: linear-gradient(135deg, #4a90e2, #357abd);
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-bottom: 10px;
    }

    .step h4 {
        color: #2c3e50;
        font-size: 1rem;
        margin-bottom: 8px;
        font-weight: 600;
    }

    .step p {
        font-size: 0.9rem;
        color: #666;
        line-height: 1.4;
    }

    .privacy-section {
        background: linear-gradient(135deg, #e8f4f8, #d1ecf1);
        border-radius: 15px;
        padding: 30px;
        margin-bottom: 40px;
        border: 2px solid #4a90e2;
    }

    .privacy-section h3 {
        color: #4a90e2;
        font-size: 1.4rem;
        margin-bottom: 20px;
        font-weight: 600;
    }

    .benefits {
        background: linear-gradient(135deg, #f0f8f0, #e8f5e8);
        border-radius: 15px;
        padding: 30px;
        margin-bottom: 40px;
    }

    .benefits h3 {
        color: #2c3e50;
        font-size: 1.5rem;
        margin-bottom: 25px;
        text-align: center;
        font-weight: 600;
    }

    .benefit-item {
        display: flex;
        align-items: flex-start;
        margin-bottom: 15px;
        padding: 15px;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }

    .benefit-item::before {
        content: '✓';
        color: #27ae60;
        font-size: 1.3rem;
        font-weight: bold;
        margin-right: 15px;
        margin-top: 2px;
    }

    .benefit-item strong {
        color: #2c3e50;
    }

    .cta-section {
        background: linear-gradient(135deg, #4a90e2, #357abd);
        color: white;
        text-align: center;
        padding: 40px;
        border-radius: 15px;
        margin-bottom: 30px;
    }

    .cta-section h3 {
        font-size: 1.6rem;
        margin-bottom: 15px;
        font-weight: 600;
    }

    .cta-section p {
        font-size: 1.1rem;
        opacity: 0.9;
    }

    .contact-info {
        text-align: center;
        padding: 20px;
        color: #666;
        border-top: 1px solid #e0e0e0;
    }

    .contact-info a {
        color: #4a90e2;
        text-decoration: none;
        margin: 0 10px;
    }

    .contact-info a:hover {
        text-decoration: underline;
    }

    @media (max-width: 768px) {
        .header {
            padding: 20px;
        }
        
        .logo {
            font-size: 2.5rem;
        }
        
        .subtitle {
            font-size: 1.3rem;
        }
        
        .tagline {
            font-size: 1rem;
        }
        
        .content {
            padding: 20px;
        }
        
        .two-column {
            grid-template-columns: 1fr;
            gap: 20px;
        }
        
        .steps-grid {
            grid-template-columns: 1fr;
        }
        
        .header-top {
            flex-direction: column;
            align-items: flex-start;
        }
        
        .vertama-logo {
            margin-top: 15px;
        }
    }
</style>

<div class="container">
    <div class="header">
        <div class="header-top">
            <div>
                <div class="logo">ELIM</div>
            </div>
            <div class="vertama-logo">VERTAMA</div>
        </div>
        <div class="subtitle">Elektronische Infektionsmeldung</div>
        <div class="tagline">Automatisiert. Sicher. Gesetzeskonform.</div>
    </div>

    <div class="content">
        <div class="intro-text">
            <strong>ELIM</strong> digitalisiert den Meldeprozess für meldepflichtige Infektionskrankheiten – <strong>direkt aus dem KIS</strong>, in Echtzeit und vollständig gesetzeskonform. Die cloudbasierte Lösung ist auf die Umsetzung der <strong>gesetzlichen Anforderungen gemäß § 6, 8, 9 IfSG</strong> ausgerichtet.
        </div>

        <div class="two-column">
            <div class="section">
                <h3>Warum ELIM?</h3>
                <ul class="feature-list">
                    <li><strong>Automatisiert & integriert:</strong> ELIM übernimmt den gesamten Meldeprozess – inklusive Formular, Versand, Empfangsquittung und Archivierung.</li>
                    <li><strong>Rechtssicher:</strong> Unterstützt sämtliche gesetzlichen Anforderungen – inkl. Sonderregelungen</li>
                    <li><strong>Alle Meldewege:</strong> DEMIS (FHIR) für digitale Arztmeldungen, Fax für gesetzlich vorgeschriebene Ausnahmefälle.</li>
                    <li><strong>Datenschutz garantiert:</strong> Keine Speicherung sensibler Daten, Memento-Verschlüsselung, zertifiziert durch SAP BTP.</li>
                    <li><strong>Flexibel konfigurierbar:</strong> Feste Faxziele oder individuelle Gesundheitsamt-regeln sind problemlos abbildbar.</li>
                    <li><strong>Schnell einsatzbereit:</strong> 1–2 Tage Implementierung – kein notwendiger Schulungsaufwand, intuitiv für Nutzer.</li>
                </ul>
            </div>

            <div class="section">
                <h3>So funktioniert ELIM im Klinikalltag</h3>
                <div class="steps-grid">
                    <div class="step">
                        <div class="step-number">1</div>
                        <h4>Meldung starten</h4>
                        <p>Über einen Button direkt aus der Patientenakte im KIS</p>
                    </div>
                    <div class="step">
                        <div class="step-number">2</div>
                        <h4>Datenübernahme</h4>
                        <p>Formular ist automatisch mit vorhandenen Patientendaten vorausgefüllt</p>
                    </div>
                    <div class="step">
                        <div class="step-number">3</div>
                        <h4>Ergänzen & Absenden</h4>
                        <p>Ein Klick genügt – ELIM erkennt den korrekten Meldeweg</p>
                    </div>
                    <div class="step">
                        <div class="step-number">4</div>
                        <h4>Empfang & Archivierung</h4>
                        <p>Quittung wird automatisch revisionssicher in der Patientenakte abgelegt</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="privacy-section">
            <h3>Datenschutz? Kein Thema – ELIM speichert nichts.</h3>
            <ul class="feature-list">
                <li><strong>Keine zentrale Datenspeicherung:</strong> Alle Daten werden nach erfolgreicher Übermittlung automatisch gelöscht</li>
                <li><strong>Ende-zu-Ende verschlüsselt:</strong> Sicherer Transport und Zugriffskontrolle</li>
                <li><strong>Revisionssicher & DSGVO-konform:</strong> Vollständige Protokollierung aller Vorgänge</li>
            </ul>
        </div>

        <div class="benefits">
            <h3>Ihre Vorteile auf einen Blick</h3>
            <div class="benefit-item">
                <div><strong>44 vordefinierte Meldeformulare</strong> - direkt im KIS wählbar</div>
            </div>
            <div class="benefit-item">
                <div><strong>DEMIS-Anbindung per FHIR</strong> - direkter, gesetzeskonformer Versand</div>
            </div>
            <div class="benefit-item">
                <div><strong>Fax-Funktion integriert</strong> - für Arztmeldungen außerhalb DEMIS Kompatibilität</div>
            </div>
            <div class="benefit-item">
                <div><strong>Revisionssichere Ablage</strong> - in Patientenakte & Archivsystem</div>
            </div>
            <div class="benefit-item">
                <div><strong>Kein zusätzlicher Personalaufwand</strong> - wartungsarm, updatesicher, intuitiv</div>
            </div>
        </div>

        <div class="cta-section">
            <h3>ELIM – Automatisch melden. Sicher dokumentieren.</h3>
            <p>Für ein Gesundheitssystem, das Infektionsschutz einfacher macht.</p>
        </div>

        <div class="contact-info">
            <p><strong>Jetzt mehr erfahren:</strong> 
            <a href="http://www.vertama.com">www.vertama.com</a> | 
            <a href="mailto:andre.sturm@vertama.com">andre.sturm@vertama.com</a></p>
        </div>
    </div>
</div>
