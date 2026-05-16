# V.connect Fremdaufruf — Overview

The V.connect Fremdaufruf Service is a small local component that
lets KIS systems initiate a V.ap session — opening a pre-filled
product form (DUBA, ELIM+, …) inside the workstation's browser —
even when the KIS cannot issue an HTTP POST. It runs adjacent to the
KIS, accepts the GET URL the KIS knows how to emit, and bridges to
V.ap's POST-based session-initialisation flow.

This document describes the architecture and the responsibility
split. Configuration and operations live in the
[Installation Manual](installation.md); KIS integrators configuring
their first integration start with the
[Benutzerhandbuch](user-manual.md).

---

## 1. Purpose

V.ap product modules expose POST endpoints that accept structured
JSON data (patient identification, report data, court-message
references, …) and respond with an encrypted `memento` plus a
`magicLink` — an authenticated single-use URL the end user opens in
a browser to land on the pre-filled form.

This flow works for KIS systems that can issue an HTTP POST with a
JSON body, authenticate with Basic Auth, and then open a browser at
the returned URL. Many KIS systems cannot. In particular, some KIS
configurations expose **only a single integration primitive**:
"open this external URL, with these parameters appended to the
query string." No POST verb, no request body, no programmatic
header control.

The naïve adaptation — accept the same payload via GET on a V.ap
endpoint — is rejected for data-protection reasons. URLs leak: into
browser history, into server access logs, into HTTP proxy logs, and
into the `Referer` header of any link the user clicks after landing
on the form. V.ap therefore declines to receive sensitive payload
via GET URLs, on its own endpoints or anywhere else.

A second motivation is UX-shaped. In many of these KIS systems the
"open external URL" primitive specifically uses the KIS's
**embedded browser pane**, which renders the target *inside* the
KIS UI rather than in a separate window. The Fremdaufruf approach
preserves this property end-to-end: the embedded browser issues the
loopback GET, follows the 303 redirect to V.ap, and renders the
pre-filled form inside the KIS — no window switching, no
external-browser handoff, no separate session. A KIS that prefers
to launch an external browser process (its other common option) is
supported by the same flow without changes.

The Fremdaufruf Service closes this gap by intermediating locally
on the KIS side. It runs adjacent to the KIS (per-workstation
localhost in the primary deployment), receives the GET request from
the KIS, performs the actual POST to V.ap on behalf of the KIS, and
returns an HTTP 303 redirect to the resulting `magicLink`. The
browser follows the redirect and reaches the same end state as the
direct-POST case.

The V.ap modules themselves are **unchanged**. The Fremdaufruf
Service is the only addition.

---

## 2. Architecture

### Component topology

```mermaid
flowchart LR
    subgraph H["Hospital network"]
        subgraph W["KIS workstation"]
            subgraph K["KIS application"]
                APP["application<br/>logic"]
                EB("embedded<br/>browser")
            end
            F(["V.c Fremdaufruf<br/>127.0.0.1:PORT"])
        end
    end

    subgraph V["Vertama cloud"]
        VAP(["V.ap"])
    end

    APP -.->|"load URL"| EB
    EB ==>|"HTTP<br/>GET (loopback)"| F
    F ==>|"HTTPS<br/>POST"| VAP
    EB ==>|"HTTPS<br/>GET (magicLink)"| VAP

    classDef added fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#3e2723
    class F added

    style H fill:#fafafa,stroke:#bdbdbd
    style W fill:#f5f5f5,stroke:#9e9e9e
    style K fill:#eeeeee,stroke:#757575
    style V fill:#e3f2fd,stroke:#1976d2,color:#0d47a1

    linkStyle 0 stroke:#999
    linkStyle 1 stroke:#1976d2,stroke-width:2px
    linkStyle 2 stroke:#1976d2,stroke-width:2px
    linkStyle 3 stroke:#1976d2,stroke-width:2px
```

The browser shown is the KIS's **embedded browser pane** — the
typical case and the principal UX motivation for this design. The
"load URL" arrow is an in-process instruction inside the KIS
application, not an OS-level launch; the embedded browser then
drives all subsequent HTTP exchanges. A KIS that launches an
external browser process instead follows the same protocol path
with no difference at the wire level — that arrow simply becomes a
process spawn rather than an in-process load.

Beyond KIS and embedded browser, the Fremdaufruf Service (added by
this design) is the only new component on the workstation. It binds
to the loopback interface and is not reachable from outside the
workstation.

Two HTTPS sessions cross the boundary between the Hospital network
and the Vertama cloud: the component's POST to V.ap (carrying the
patient payload and using the stored API-user credentials), and the
browser's subsequent GET of the `magicLink` to obtain the
pre-filled form. No other Vertama-cloud traffic originates from
the workstation in this flow.

Admin tooling for generating URL templates lives in V.ap itself; it
is not depicted here because it is not part of the runtime path.

### Runtime flow — baseline (POST-capable KIS, for reference)

```mermaid
%%{init: {'theme':'base','themeVariables':{'actorBkg':'#f5f5f5','actorBorder':'#757575','actorTextColor':'#212121','actorLineColor':'#bdbdbd','signalColor':'#1976d2','signalTextColor':'#0d47a1','sequenceNumberColor':'#ffffff'},'sequence':{'boxMargin':5,'boxTextMargin':2,'height':40}}}%%
sequenceDiagram
    autonumber
    participant K as KIS workstation
    participant B as Embedded browser
    participant V as V.ap

    K->>V: POST /api/{module}/v1/memento<br/>(JSON body, Basic Auth)
    V-->>K: { memento, magicLink }
    K->>B: open(base + magicLink)
    B->>V: GET magicLink (MTL token)
    V-->>B: pre-filled form
```

### Runtime flow — with V.connect Fremdaufruf (GET-only KIS)

```mermaid
%%{init: {'theme':'base','themeVariables':{'actorBkg':'#f5f5f5','actorBorder':'#757575','actorTextColor':'#212121','actorLineColor':'#bdbdbd','signalColor':'#1976d2','signalTextColor':'#0d47a1','sequenceNumberColor':'#ffffff'},'sequence':{'boxMargin':5,'boxTextMargin':2,'height':40}}}%%
sequenceDiagram
    autonumber
    participant K as KIS workstation
    participant B as Embedded browser
    participant F as V.c Fremdaufruf<br/>(localhost)
    participant V as V.ap

    K->>B: open(http://127.0.0.1:PORT/l/{path}?params)
    B->>F: GET /l/{path}?params
    F->>V: POST /api/{module}/v1/memento<br/>(params→JSON, stored Basic Auth)
    V-->>F: { memento, magicLink }
    F-->>B: 303 Location: base + magicLink
    B->>V: GET magicLink (MTL token)
    V-->>B: pre-filled form
```

The only addition is the local component between browser and V.ap.
The KIS-opens-browser step and the final magic-link GET are
identical to the baseline.

### Admin-config flow

```mermaid
%%{init: {'theme':'base','themeVariables':{'actorBkg':'#f5f5f5','actorBorder':'#757575','actorTextColor':'#212121','actorLineColor':'#bdbdbd','signalColor':'#1976d2','signalTextColor':'#0d47a1','sequenceNumberColor':'#ffffff'},'sequence':{'boxMargin':5,'boxTextMargin':2,'height':40}}}%%
sequenceDiagram
    autonumber
    actor A as Integrator
    participant T as V.ap URL-builder tooling
    participant KC as KIS configuration

    A->>T: open URL-template builder for {module}
    T-->>A: form with all parameters of the POST endpoint,<br/>each with an input for the KIS-native placeholder
    A->>T: fill placeholders (e.g. %PatientVorname%, ~dob~)
    T-->>A: complete GET URL template<br/>(prefix /l/, aliases, type manifest, data params)
    A->>KC: paste template into KIS external-call configuration
```

The URL template is constant across workstations. An integrator
generates it once per module and per KIS placeholder convention,
then pastes it into every KIS that should expose the integration.
The full integrator-facing walkthrough is in the
[Benutzerhandbuch](user-manual.md).

### Responsibility split

| Concern                                | Owner                       |
|----------------------------------------|-----------------------------|
| Product module endpoints, OpenAPI      | V.ap (unchanged)            |
| URL-template builder UI                | V.ap                        |
| Placeholder substitution at run time   | KIS (existing mechanism)    |
| GET → JSON translation, POST, redirect | Fremdaufruf Service         |
| API-user credentials at rest           | Fremdaufruf Service config  |
| Form rendering, MTL authentication     | V.ap (unchanged)            |

All product-specific knowledge (schemas, field names, required
fields) stays in V.ap. The component carries no module-specific
code.

---

## 3. Component contract — summary

The component is a single executable exposing one HTTP listener
and one forwarding rule. It is module-agnostic: adding a new
product module to V.ap requires no change to the component. The
sections below describe the customer-visible surface; the protocol
between the component and V.ap is a Vertama-internal contract and
is not documented here.

### 3.1 URL scheme

```
GET http://127.0.0.1:PORT/l/<vap-endpoint-path>?<query>
```

- `/l/` is a fixed prefix reserved by the component. All requests
  not matching the prefix return 404.
- `<vap-endpoint-path>` is used verbatim as the path of the V.ap
  POST request.
- `<query>` carries data parameters and two optional reserved meta
  parameters:
    - `_a` — a path-segment alias map that compacts repeated
      dotted prefixes (e.g. `P:Patient,S:Standard`) so URLs stay
      short.
    - `_t` — a type manifest declaring which parameters are
      booleans, integers, numbers, dates, or datetimes (everything
      else is a string).

The V.ap URL-builder tooling emits all of this automatically for
the integrator; the
[Benutzerhandbuch §3](user-manual.md#3-schritt-fur-schritt-url-vorlage-erstellen)
walks through it step by step.

### 3.2 Response semantics

| Trigger                                      | Component response                                            |
|----------------------------------------------|---------------------------------------------------------------|
| Successful POST, V.ap returns 200            | **303 See Other** with `Location: <vap-base><magicLink>`      |
| Caller fails the access-secret check (intranet deployment, §6) | 403 Forbidden                            |
| Caller's path is not on the configured allowlist (§6)          | 404 Not Found                            |
| Malformed URL, coercion failure, …           | 400 Bad Request                                               |
| V.ap returns 400 (validation)                | 422 Unprocessable Entity, with V.ap's `errors[]` propagated   |
| V.ap returns 401 / 403 / 5xx, or unreachable | 502 Bad Gateway                                               |

The component never returns 401 itself. Upstream auth failures
(401/403 from V.ap) surface as 502; a 403 from the component
itself indicates the caller failed the access-secret check (§6),
not an upstream auth failure.

---

## 4. Deployment model

V1 supports two deployment shapes; both run from the same binary
with different configuration.

**Per-workstation, loopback-bound.** Each KIS workstation runs its
own instance bound to `127.0.0.1`. Trust boundary: the workstation
operating system. Operationally simple — one workstation, one
install — fits when each workstation is a self-contained
integration point.

**Hospital-network-bound (intranet-shared).** A single installation
inside the hospital network, bound to a routable address, serves
many KIS workstations. Trust boundary: a configured **access
secret** that every caller must supply on every request (§6).
Operationally lighter when many workstations need the same
integration.

Both shapes use the same binary, the same configuration schema,
and the same upstream contract with V.ap. The choice of shape is a
deployment decision, not a product decision. The
[Installation Manual](installation.md) covers both.

**Future: container packaging** — formal container distribution
with signed image, deployment guide, and operations runbook for
hospital IT. The binary itself supports both deployment shapes
today; only the formal container distribution surface is deferred.

---

## 5. Tech stack

The component is a **single static binary** (~10 MB), no runtime
dependency on the workstation. Standard-library HTTP server and
client, JSON, TLS — minimal third-party surface. Cross-compiled
from one source tree for Windows, Linux, and macOS. Operates as a
Windows service via `sc.exe` / NSSM, or as a systemd unit on
Linux, without any additional runtime supervisor. Sub-second
startup, single-digit MB resident memory.

---

## 6. Security posture

### Authority model

What can be done through the Fremdaufruf component is governed by
three independent controls:

| Control                                                  | Owner            |
|----------------------------------------------------------|------------------|
| What an API user may do at V.ap                          | Vertama (V.ap)   |
| Which upstream paths this installation may reach         | Hospital admin   |
| Whether a caller is allowed to reach the component       | Hospital admin   |

**V.ap-side authorisation is the primary control.** The configured
API user has a defined scope at V.ap, and what that scope permits
is governed by V.ap's per-API-user authorisation. The component is
not the gatekeeper for which V.ap actions can be performed — V.ap
is.

**Hospital admins may narrow the surface locally** by configuring
an optional path allowlist in the component's configuration. With
the allowlist set, paths outside the list are rejected by the
component (404) before any upstream call is made. Without an
allowlist, all paths the configured API user is V.ap-authorised
for remain reachable.

**For intranet-bound deployments**, every caller must supply a
configured access secret on every request (`_s` URL parameter). On
mismatch the component returns 403 before any upstream call. The
secret is the trust-boundary control for non-loopback deployments,
playing the role the workstation OS plays for loopback ones.
Configuration is covered in the
[Installation Manual](installation.md).

### Wire-level guarantees

- **Inbound scope:** the listener binds only to the address
  configured. The component never accepts connections beyond what
  the bind address itself permits.
- **Outbound scope:** HTTPS to the configured V.ap base URL only.
  Other destinations are not reachable from component logic.
- **Credentials:** stored at rest in a file-permission-restricted
  TOML config (or via OS environment variables, for transient
  overrides). Sent only to the configured V.ap base URL over TLS,
  never logged.
- **Audit logging:** every request logs timestamp, target endpoint
  path, parameter count, V.ap status code, and outcome. **Parameter
  values and parameter keys are never logged**, regardless of log
  level — only the count. The configured access secret and any
  `_s` URL parameter value are likewise never logged.
- **TLS:** verification against the system trust store is
  mandatory by default. Disabling verification is permitted only
  for local development against a self-signed V.ap and the
  component emits a startup warning when it is in that mode.
- **Loopback deployment trust boundary:** GET URLs from the KIS to
  the component contain patient data in the URL but travel only
  over loopback, never the network. The trust boundary is the
  workstation OS, the same boundary the KIS itself operates
  within.
- **Intranet deployment trust boundary:** GET URLs traverse the
  hospital network between caller and component. The trust
  boundary is the hospital network plus the access secret; the
  secret travels in the URL alongside the patient data and is
  exposed to whatever observes intranet traffic. As with the
  loopback case, the data-protection improvement is over
  *internet-facing* leakage paths (V.ap server logs, intermediate
  proxy logs, `Referer`) — not over intranet observation.

---

## 7. V1 scope — what's in and what's deferred

**In V1:**

- The component as described above, in the per-workstation
  loopback deployment.
- TOML configuration with environment variable overrides.
- Stderr and file audit-log destinations.
- The V.ap URL-builder tooling for one or more product modules
  (DUBA available at V1 launch; further modules follow the same
  pattern).

**Deferred to a later iteration:**

- Hospital-network central deployment and the corresponding
  container packaging.
- Array-typed parameters in the POST body. No currently shipping
  V.ap module needs them; revisited when one does.
- Signed URL templates (V.ap-issued signature the component
  verifies, so a tampered template is rejected at the component).
- OS credential-store integration (Windows DPAPI / Linux
  secret-tool).
- Syslog and Windows eventlog audit-log destinations.

---

**Last updated:** 2026-05-15
**Applies to:** V.connect Fremdaufruf V1
