# Endpunkte & Infrastruktur

Diese Seite enthält alle notwendigen technischen Informationen, um eine reibungslose und sichere Verbindung zu unseren Systemen zu gewährleisten.

---

## elim.vertamob.de

### 🛡️ SSL-Zertifikat
Um eine verschlüsselte Kommunikation zu garantieren, nutzen wir aktuelle SSL/TLS-Standards.

### Aktuelles Zertifikat
* **Gültig bis:** 25.02.2027

**Downloads der aktuellen Zertifikate:**

 - [elim.vertamob.de.ca-bundle](endpoints-and-infrastructure/certs/2026/elim.vertamob.de.ca-bundle)
 - [elim.vertamob.de.crt](endpoints-and-infrastructure/certs/2026/elim.vertamob.de.crt)
 - [elim.vertamob.de.p7b](endpoints-and-infrastructure/certs/2026/elim.vertamob.de.p7b)

### 🌐 IP-Adressen

#### Ausgehender Datenverkehr (Ihr Netzwerk → Vertama/ingress)
Falls Ihr Unternehmensnetzwerk durch eine Firewall geschützt ist, müssen die folgenden IP-Adressen und Ports für den ausgehenden Datenverkehr freigeschaltet werden:

`18.197.24.114`, `63.178.126.231` und `63.178.152.244`

#### Eingehender Datenverkehr (Vertama/egress → Ihr Netzwerk)
Wenn Ihre Systeme eingehende Verbindungen von Vertama empfangen (z.B. Callbacks, Webhooks), müssen die folgenden Egress-IPs unseres Kyma-Clusters in Ihrer Firewall zugelassen werden:

`18.158.198.237`, `18.196.237.158` und `3.127.250.96`

**Hinweis:** _Dies sind die NAT-Gateway-IPs unseres SAP/BPT Kyma-Clusters. Sie sind leider noch als Übergangslösung zu verstehen! Wir sind in Planung und Absprachen zu neuen Hosting Lösungen, auch um die Anforderungen einer souveränen und sicheren Cloudumgebungen noch besser zu unterstützen, als dass dies bereits jetzt schon in den BTP Rechenzentren der SAP möglich ist. Über die sich daraus ergebenden Änderungen der relevanten IP Adressen informieren wir Sie rechtzeitig, so dass sie Ihre Firewall entsprechend anpassen können._

---

**Stand**: April 2026<br>
**Nächste Überprüfung**: Januar 2027
