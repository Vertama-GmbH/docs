# V.connect Fremdaufruf — Overview

V.connect Fremdaufruf lets a KIS open a pre-filled V.ap product form
(DUBA, ELIM+, …) in the workstation's browser, even when the KIS
itself cannot make the HTTPS POST call V.ap normally expects. It
runs adjacent to the KIS on the workstation, accepts the GET URL the
KIS knows how to emit, and bridges to V.ap's POST-based session
initialisation.

This document is the customer-direction overview: what the component
is for, what it gives you, and what adopting it involves. For the
deeper architecture and design rationale, see the
[Architecture](solution-outline.md). For the KIS-integrator workflow
of generating URL templates, see the
[V.ap Fremdaufruf URL-Builder](url-builder.md).

---

## 1. Purpose

V.ap product modules expose POST endpoints that accept structured
JSON (patient identification, report data, court-message references,
…) and respond with a one-time login link to a pre-filled form. KIS
systems that can make HTTPS POST calls integrate with these
endpoints directly.

Many KIS configurations cannot. The integration mechanism they
expose is a single primitive: *"open this URL, with these
parameters appended"*. The naïve workaround — accept the same
payload via GET on a V.ap endpoint — fails on data protection: URLs
leak into browser history, into proxy logs, into server access
logs, and into the Referer header of any link the user clicks
afterwards.

Fremdaufruf closes this gap **on the workstation side**. The
component runs locally, accepts the GET URL the KIS emits, transforms
it into the authenticated POST V.ap expects, and 303-redirects the
browser to the resulting login link. The V.ap modules themselves are
unchanged; only the local component is added.

---

## 2. At a glance

<figure>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 280" role="img" aria-labelledby="diagramTitle" style="max-width: 100%; height: auto;">
  <title id="diagramTitle">Where Fremdaufruf sits — on the workstation, between the KIS and V.ap</title>
  <defs>
    <marker id="ovArrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#1565c0"/>
    </marker>
  </defs>

  <!-- Hospital network zone -->
  <rect x="20" y="40" width="460" height="220" rx="14" fill="#fafafa" stroke="#bdbdbd" stroke-dasharray="4,3"/>
  <text x="38" y="62" font-family="system-ui, sans-serif" font-size="12" fill="#757575" font-weight="500" font-style="italic">Hospital network · KIS workstation</text>

  <!-- KIS box -->
  <rect x="50" y="100" width="170" height="130" rx="10" fill="#ffffff" stroke="#9e9e9e" stroke-width="1.5"/>
  <text x="135" y="135" font-family="system-ui, sans-serif" font-size="16" fill="#424242" font-weight="600" text-anchor="middle">KIS</text>
  <text x="135" y="160" font-family="system-ui, sans-serif" font-size="11" fill="#757575" text-anchor="middle">application +</text>
  <text x="135" y="176" font-family="system-ui, sans-serif" font-size="11" fill="#757575" text-anchor="middle">embedded browser</text>

  <!-- Fremdaufruf (highlighted) -->
  <rect x="285" y="115" width="170" height="100" rx="10" fill="#fff3e0" stroke="#ef6c00" stroke-width="2.5"/>
  <text x="370" y="145" font-family="system-ui, sans-serif" font-size="11" fill="#3e2723" font-weight="500" text-anchor="middle">V.connect</text>
  <text x="370" y="170" font-family="system-ui, sans-serif" font-size="17" fill="#3e2723" font-weight="700" text-anchor="middle">Fremdaufruf</text>
  <text x="370" y="192" font-family="system-ui, sans-serif" font-size="10" fill="#5d4037" font-style="italic" text-anchor="middle">single static binary</text>

  <!-- Vertama cloud zone -->
  <rect x="510" y="40" width="200" height="220" rx="14" fill="#e3f2fd" stroke="#1565c0" stroke-dasharray="4,3"/>
  <text x="530" y="62" font-family="system-ui, sans-serif" font-size="12" fill="#0d47a1" font-weight="500" font-style="italic">Vertama Cloud</text>

  <!-- V.ap -->
  <rect x="545" y="115" width="130" height="100" rx="10" fill="#bbdefb" stroke="#1565c0" stroke-width="2"/>
  <text x="610" y="175" font-family="system-ui, sans-serif" font-size="22" fill="#0d47a1" font-weight="700" text-anchor="middle">V.ap</text>

  <!-- Arrows -->
  <line x1="220" y1="165" x2="283" y2="165" stroke="#1565c0" stroke-width="2" marker-end="url(#ovArrow)"/>
  <text x="251" y="156" font-family="system-ui, sans-serif" font-size="11" fill="#1565c0" font-weight="500" text-anchor="middle">GET URL</text>

  <line x1="455" y1="165" x2="543" y2="165" stroke="#1565c0" stroke-width="2" marker-end="url(#ovArrow)"/>
  <text x="499" y="156" font-family="system-ui, sans-serif" font-size="11" fill="#1565c0" font-weight="500" text-anchor="middle">HTTPS POST</text>
</svg>
<figcaption style="font-size: 0.85em; color: #616161; margin-top: 0.4rem; text-align: center;">
On the workstation, Fremdaufruf receives the KIS's GET URL and translates it into the authenticated HTTPS POST V.ap expects. The browser then follows V.ap's redirect to the pre-filled form.
</figcaption>
</figure>

What the customer gets:

- **A single small binary** on each KIS workstation, or one
  container on the hospital LAN — running as a Windows service or
  Linux container. Single-digit MB memory, no runtime dependencies.
- **Compatibility with KIS systems that have only the basic
  "open external URL" capability** — no KIS-side development needed.
- **End-user experience preserved**: the pre-filled form renders
  inside the KIS's embedded browser, no window switching, no
  separate login.
- **Module-agnostic**: one component, all V.ap modules. Adding a
  module to the integration is a configuration change, not a new
  deployment.

---

## 3. Integration independence

The integration mechanism Fremdaufruf relies on — opening an external
URL with parameters appended — is one of the most universal KIS
capabilities. Almost every clinical information system supports it;
it predates any vendor-specific integration API. By relying on this
primitive, integrations with V.ap modules don't require the KIS
vendor to provide module-specific support, build custom adapters,
or unlock paid integration tiers. The hospital chooses what to
integrate; the KIS vendor neither gates nor prices that decision.

---

## 4. Deployment shapes

V1 supports two shapes from the same binary, distinguished by
configuration:

**Per-workstation, loopback-bound.** Each KIS workstation runs its
own instance bound to `127.0.0.1`. Operationally simple — one
workstation, one install. Trust boundary: the workstation operating
system. Distributed as a signed Windows installer that registers a
native Windows service.

**Hospital-network central.** A single installation on the hospital
LAN, bound to a routable address, serves multiple KIS workstations.
Trust boundary: a configured access secret that every caller must
supply on every request. Distributed as a container image at
`ghcr.io/mcp-health/v.connect/fremdaufruf` (linux/amd64), with a
Docker Compose example as a starting point.

Both shapes use the same binary, the same configuration schema, and
the same upstream contract with V.ap. The choice is a deployment
decision, not a product decision.

---

## 5. What adopting looks like

### 5.1 Prerequisites

| Item | Requirement |
|------|-------------|
| **Platform** | Windows 10 or later (x64) for per-workstation deployments; Linux x86-64 via container (Docker / Podman) for central deployments. macOS is development-only. |
| **Outbound network** | HTTPS reachability from the workstation (or LAN host) to the V.ap base URL. |
| **V.ap API user** | Provisioned by your Vertama contact, with the module scopes the integration requires. |
| **Service-installation rights** | Administrator (Windows) or root (Linux) for service registration. Day-to-day operation runs unprivileged. |
| **Disk** | Less than 50 MB for the binary, configuration, and audit log. |

The component is a single static binary with no runtime dependencies
— no JRE, no .NET runtime, no shared libraries beyond the OS itself.

### 5.2 Installation paths

- **Windows.** Signed installer registers the Windows service,
  drops the binary in `%PROGRAMFILES%`, and writes a configuration
  template. Authenticode signature is verifiable before install.
- **Linux / container.** Container image with a Docker Compose
  example as a starting point. Configuration via environment
  variables (12-factor) or a mounted config file.
- **macOS.** Development only.

### 5.3 Operationally

Once installed, the component runs as a long-running service and
exposes a browser-based **admin dashboard** at
`http://127.0.0.1:8811/admin` on the host. The administrator sets
the admin access code, edits the configuration to point at the V.ap
instance, reloads the configuration from the dashboard, and confirms
the V.ap connectivity test passes. Installation completes in
minutes; first successful KIS call typically same day once
configuration is in place.

Day-to-day operation is hands-off. The dashboard shows live activity
counters, the effective configuration (with secrets redacted), and
the recent request history.

The complete operations manual — installation procedure, full
configuration schema, troubleshooting, audit-log details — ships
with the binary as the **Betriebshandbuch** and is reachable from
the admin dashboard. Vertama supplies it on request prior to
deployment for IT-security review.

---

## 6. Security & compliance — summary

Three independent controls govern what can be done through
Fremdaufruf:

- **V.ap-side authorisation** (primary) — the configured API user's
  scope at V.ap governs which V.ap actions are reachable at all.
- **Local path allowlist** (defense in depth) — hospital admins may
  narrow the surface to a list of permitted upstream paths.
- **Access secret** (intranet trust boundary) — required for
  non-loopback deployments; every request must supply the matching
  `_s` parameter.

Wire-level: HTTPS to the configured V.ap base URL only; TLS
verification against the system trust store; parameter values and
keys are never logged at any log level (only the count); credentials
and access secrets are never logged.

For the full security posture — authority model, wire-level
guarantees per deployment shape, trust boundaries, audit-log
guarantees — see [Architecture §8](solution-outline.md#8-security-posture).

---

## 7. Support

Vertama supports Fremdaufruf directly. The team behind it is small,
which means: when you reach us, you reach engineering, not a ticket
queue. Response is fast for installation-blocking issues; functional
improvements roll into the regular release cadence.

---

## 8. What's in V1 — and what's not

**In V1:**

- Both deployment shapes (per-workstation loopback, hospital-network
  intranet).
- Signed Windows installer and Linux container distribution.
- Browser-based admin dashboard for status, configuration reload,
  and V.ap-connectivity testing.
- TOML configuration with environment-variable overrides.
- Stderr and file audit-log destinations.
- URL-builder tooling at V.ap for the customer's chosen modules
  (DUBA, ELIM+, and other V.ap modules use the same URL-builder
  workflow at no additional component cost).

For what is deliberately not in scope today, with rationale, see
[Architecture §9](solution-outline.md#9-scope-and-roadmap).

---

**Companion documents:**

- [Architecture](solution-outline.md) — full design rationale,
  deployment-shape detail, security posture, scope and roadmap.
- [V.ap Fremdaufruf URL-Builder](url-builder.md) — KIS-integrator
  guide to generating URL templates.
- **Betriebshandbuch** — operations manual; ships with the binary,
  reachable from the admin dashboard after install.

---

**Last updated:** 2026-06-11
**Applies to:** V.connect Fremdaufruf V1
