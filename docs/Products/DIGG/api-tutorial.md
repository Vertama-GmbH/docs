# ZEAG API Integration Guide

A practical guide for integration partners using the ZEAG (Zusätzliche Elternangaben zur Geburt) API.

**Version:** 0.1.1
**Last Updated:** 2026-09-07

!!! info "Pre-production module"
    ZEAG is not yet in production. The API is published here so integration
    partners can build against it; the endpoint paths and the RFC 9457 error
    contract are stable, but field-level details may still move before the
    first production release.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [Core Concepts](#core-concepts)
4. [Memento Endpoint](#memento-endpoint)
5. [Report Retrieval Endpoints](#report-retrieval-endpoints)
6. [Error Handling](#error-handling)
7. [Reference](#reference)

---

## Introduction

The ZEAG API enables clinical information systems (KIS) and portal software to pre-fill the parents' supplementary birth data delivery (**portal2StA.Geburt.081021** — *Zusätzliche Datenlieferung der Eltern*) for the civil registry office (Standesamt) via xPersonenstand integration. This API allows integration partners to:

- **Create form mementos** to generate pre-filled form URLs from case data
- **Enable user review** — the parents (or staff acting with them) complete and dispatch the form
- **Retrieve report results** and status after end users submit forms to the Standesamt

### Use Case

ZEAG covers the parents' half of a digital birth registration. The institution reports the birth itself (the *Geburtsanzeige*, 081020 — see [DIGG](../DIGG/api-tutorial.md)); ZEAG delivers the data only the parents can supply: the child's names, marital status, nationalities, certificate orders, and the optional forwarding of data to the Elterngeldstelle.

1. **Source system (KIS / portal)** holds the birth case, but the parents must supply and confirm the remaining data
2. **System calls API** with the known data as JSON — only `id` is mandatory
3. **API returns** an encrypted memento string and a magic link
4. **System uses the `magicLink`** to open a pre-filled form
5. **Parents review, complete missing info, and submit** to the Standesamt
6. **System automatically polls** for the delivery status and confirmation PDF

```
KIS / Portal Software
    ↓
[1] POST /api/zeag/v1/memento  (API user credentials)
    ↓
[2] Receives { "memento": "...", "magicLink": "/mtl/...?m=..." }
    ↓
[3] Constructs absolute URL: https://elim.vertamob.de + magicLink
    ↓
[4] Opens URL in browser — authenticated via MTL token
    ↓
End User (parents)
    ↓
[5] Reviews pre-filled data, completes form → submits to Standesamt
    ↓
KIS / Portal Software (asynchronous)
    ↓
[6] GET /api/zeag/v1/reports/{id}  → status (PENDING, SUCCESS, FAILURE) + receipt PDF
```

**Benefits:**

- No direct automated submission — the parents keep control and can review/correct their data
- Form validation happens in the browser (immediate feedback)
- Secure, encrypted mementos protect sensitive personal data

### Prerequisites

Before using the API, you need:

- **API User Credentials**: Username and password provided by your administrator

### OpenAPI Specification

The complete OpenAPI specification is available at:
```
https://elim.vertamob.de/api/docs/swagger-ui/index.html?urls.primaryName=ZEAG
```

---

## Authentication

The API uses **HTTP Basic Authentication** with your API user credentials (the service account provided by your administrator). End users accessing the form do not need separate credentials — the magic link authenticates them.

### Example

```bash
curl -u "api-username:api-password" -X POST -H "Content-Type: application/json" -d '{"id":"ZEAG-2026-001"}' https://elim.vertamob.de/api/zeag/v1/memento
```

Missing or invalid credentials return **401 Unauthorized** with a `WWW-Authenticate` header and an **empty body** — there is no problem-details payload on 401.

See [Basic Auth Login (BAL)](../../Authentication/basic-auth-login.md) for details.

---

## Core Concepts

### Zusätzliche Elternangaben zur Geburt

The main data structure (`ZeagMementoRequest`) mirrors the xPersonenstand message 081021. Key fields:

- **id** (required): Unique report identifier for tracking
- **anschriftAutor**: Postal address of the sending author — either a building address *or* a P.O. box
- **ansprechpartner**: Contact person
- **vorgangsidentifikation**: Event identification (`ereignis.zeitpunkt`, `ereignis.zeichen`)
- **geburtsangaben**: Place, day and time of the birth
- **kind**: The newborn's gender and names
- **mutter**: The mother's names, birth, nationality, address, and child/stillbirth counts
- **elternteil2**: The second parent's data
- **elternVerheiratet** / **ehe**: Marital status and, if married, the marriage details
- **vorangegangenesKind**: A previous child of both parents (joint custody case)
- **kontaktdaten**: One or more contact channels of the parents
- **urkundenbestellung**: How many certificates to order, per format
- **auftragsnummer**: Human-readable order number correlating the parents' Elterngeld application to the notification sent to the Elterngeldstelle
- **zuordnungGeburtsanzeige**: The id pairing this delivery with the institution's Geburtsanzeige (see below)
- **zustimmungElterngeldstelle** / **zustaendigeElterngeldstelle**: Consent to forward the data, and the responsible Elterngeldstelle

### Pairing with the Geburtsanzeige (081020 ↔ 081021)

`zuordnungGeburtsanzeige` links the two halves of a birth registration: the institution's *Anzeige der Einrichtung* (081020) and the parents' supplementary delivery (081021, this module). The Standesamt uses it to join the two messages.

The value must be **transmitted identically in both messages**. If your system also produces the 081020 message, carry the same identifier across; if another system produces it, obtain the identifier from there before creating the ZEAG memento.

### Memento Pattern

A **memento** is an encrypted, URL-safe string that contains form pre-fill data:

- Generated from JSON report data
- Tamper-proof and URL-safe
- Used as query parameter: `?m={memento}`

Creating a memento does **not** submit anything. It only produces a pre-fill token for the interactive HTML form; the report comes into existence when the end user dispatches that form.

### Magic Token Link (MTL)

The `magicLink` field in the API response is a server-issued, time-limited URL that:

- Authenticates the end user automatically (no login page)
- Redirects to the pre-filled ZEAG form (`/zeag/form?m={memento}`) on success
- Is a **relative path** — prepend your instance host to make it absolute

magicLink: "/mtl/eyJ...token.../zeag/form?m=eyJ...memento..."

Full URL: https://elim.vertamob.de/mtl/eyJ...token.../zeag/form?m=eyJ...memento...


Treat the returned string as **opaque**: hand it out or prepend your host, but do not parse, rewrite, or reassemble it. See [Magic Token Link (MTL)](../../Authentication/magic-token-link.md) for security details and token lifetime.

### Report ID

The `id` field must be unique per API user. It serves multiple purposes:

1. **Form pre-fill and correlation**: Correlates your case data to the form
2. **Status retrieval key**: After submission, used to retrieve delivery status via `GET /api/zeag/v1/reports/{id}`

### Choice fields ("either/or")

Several xPersonenstand types are *choices* — populate exactly one branch and leave the other absent:

| Type | Branch A | Branch B |
|------|----------|----------|
| `PostalischeInlandsanschrift` (`anschriftAutor`, `zustaendigeElterngeldstelle.anschrift`) | `gebaeude` — street address | `postfach` — P.O. box |
| `Staatsangehoerigkeit` | `code` — code from the nationality code list | `nichtGelisteterWert` — free text for an unlisted state |
| `AllgemeinerNamePersonenstandswesen` (the child's name parts) | `name` — the name as a string | `nichtVorhanden: true` — no such name exists |

`zustaendigeElterngeldstelle.anschrift` uses the **same** `PostalischeInlandsanschrift` choice type as `anschriftAutor` — not a plain street address object.

### True-only booleans

`elternVerheiratet`, `zustimmungElterngeldstelle` and `nichtVorhanden` accept **`true` only**. There is no `false` — **omit the field** to express the negative:

```json
{ "elternVerheiratet": true }
```

```json
{ }
```

The first says the parents are married; the second (field absent) says they are not. Consequently, `ehe` is only meaningful together with `elternVerheiratet: true`.

### The child's name

`kind.name` uses `PersonNameVeraenderung`, which nests each name part as a choice object:

- Given names → `vornamen.name`
- The child's birth name → `familienname.name`
- A separate birth-name field does not exist for a newborn — `PersonNameVeraenderung` has no `geburtsname`

```json
{
  "kind": {
    "geschlecht": "w",
    "name": {
      "vornamen": { "name": "Emma Sophie" },
      "familienname": { "name": "Mustermann" }
    }
  }
}
```

`namensartCode` is available on each name part (a code from the Namensart code list) for name forms under foreign law. There is no free-text fallback for an unlisted Namensart — only codes from the list are accepted.

---

## Memento Endpoint

**Endpoint:** `POST /api/zeag/v1/memento`

**Purpose:** Create an encrypted memento string and magic link to pre-fill the ZEAG form.

This endpoint does **not** submit the report — it only creates a pre-fill token for the interactive HTML form.

### Request Body

Only `id` is required; all other fields are optional to allow partial pre-filling (see [Formal API Definition](#reference) for the complete schema). Send what you know and leave the rest to the parents — the form enforces the full xPersonenstand rule set before dispatch.

**Minimal Example:**
```json
{
  "id": "ZEAG-2026-00001"
}
```

**Extended Example:**
```json
{
  "id": "ZEAG-2026-00123",
  "anschriftAutor": {
    "gebaeude": {
      "postleitzahl": "10117",
      "strasse": "Musterstraße",
      "hausnummer": "1",
      "wohnort": "Berlin"
    }
  },
  "ansprechpartner": "Anna Schmidt",
  "vorgangsidentifikation": {
    "ereignis": {
      "zeitpunkt": "2026-02-23T14:30:00Z",
      "zeichen": "GB-2026-0815"
    }
  },
  "geburtsangaben": {
    "tag": "2026-02-23",
    "uhrzeit": "14:30",
    "ort": {
      "strasse": "Klinikstraße",
      "hausnummer": "1",
      "ort": "Musterstadt"
    }
  },
  "kind": {
    "geschlecht": "w",
    "name": {
      "vornamen": { "name": "Emma Sophie" },
      "familienname": { "name": "Mustermann" }
    }
  },
  "mutter": {
    "namen": {
      "vornamen": "Anna",
      "familienname": "Mustermann",
      "geburtsname": "Schmidt"
    },
    "geburt": {
      "tag": "1994-05-15",
      "ort": { "ort": "Musterstadt" }
    },
    "geschlecht": "w",
    "staatsangehoerigkeit": { "code": "221" },
    "anschrift": {
      "strasse": "Musterweg",
      "hausnummer": "12",
      "postleitzahl": "12345",
      "wohnort": "Musterstadt"
    },
    "anzahlKinder": 2,
    "anzahlTotgeburten": 0
  },
  "elternteil2": {
    "namen": {
      "vornamen": "Jonas",
      "familienname": "Mustermann"
    },
    "geburt": {
      "tag": "1991-11-02",
      "ort": { "ort": "Berlin" }
    },
    "geschlecht": "m",
    "staatsangehoerigkeit": { "code": "221" },
    "anschrift": {
      "strasse": "Musterweg",
      "hausnummer": "12",
      "postleitzahl": "12345",
      "wohnort": "Musterstadt"
    }
  },
  "elternVerheiratet": true,
  "ehe": {
    "ereignis": {
      "tag": "2019-06-14",
      "ort": { "ort": "Musterstadt" }
    },
    "kinderDerEhe": 2,
    "totgeburtenDerEhe": 0
  },
  "kontaktdaten": [
    { "kanal": "01", "kennung": "familie.mustermann@example.org" },
    { "kanal": "02", "kennung": "+49 30 1234567", "zusatz": "tagsüber erreichbar" }
  ],
  "urkundenbestellung": {
    "anzahlStandardformat": 2,
    "anzahlStammbuchformat": 1,
    "anzahlCIEC16": 0,
    "anzahlCIEC34": 0
  },
  "auftragsnummer": "EG-2026-4711",
  "zuordnungGeburtsanzeige": "DIGG-2026-00123",
  "zustimmungElterngeldstelle": true,
  "zustaendigeElterngeldstelle": {
    "name": "Elterngeldstelle Musterstadt",
    "anschrift": {
      "gebaeude": {
        "strasse": "Rathausplatz",
        "hausnummer": "3",
        "postleitzahl": "12345",
        "wohnort": "Musterstadt"
      }
    }
  }
}
```

### Response

Returns a JSON object containing the encrypted memento and a ready-to-use magic link:

```json
{
  "memento": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..DGG5lQvJC8OpYrCt.Xm8YR...",
  "magicLink": "/mtl/eyJ...token.../zeag/form?m=eyJ...memento..."
}
```

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `memento` | string | No | Encrypted, URL-safe string containing report data. Use as `?m={memento}` query parameter. |
| `magicLink` | string | Yes | Relative URL for authenticated single-click access. Prepend your instance host: `https://elim.vertamob.de + magicLink` |

If you deliver the form to an already-authenticated user, you can use the bare `memento` on the form URL (`?m={memento}`) instead of the magic link.

---

## Report Retrieval Endpoints

ZEAG reports are delivered asynchronously via xPersonenstand/XTA2 transport. A report only exists once the end user has dispatched the form — until then, retrieval returns 404 (see [report-not-found](problems/report-not-found.md)).

### GET /reports — List pending report IDs

**Endpoint:** `GET /api/zeag/v1/reports`

Returns an array of `id` strings for reports that have been submitted by your API user but not yet retrieved (unpolled). Reports disappear from this list once retrieved without `?peek=true`.

**Request:**
```bash
curl -u "api-user:api-pass" https://elim.vertamob.de/api/zeag/v1/reports
```

**Response (200):**
```json
["ZEAG-2026-00123", "ZEAG-2026-00124"]
```

An empty array `[]` means no submissions are pending retrieval.

---

### GET /reports/{id} — Retrieve report result

**Endpoint:** `GET /api/zeag/v1/reports/{id}`

**Parameters:**

- `id` (path, required): The report ID from the original memento
- `peek` (query, optional): `true` for a non-destructive read. Default: `false`.

**Non-destructive peek:**
```bash
curl -u "api-user:api-pass" "https://elim.vertamob.de/api/zeag/v1/reports/ZEAG-2026-00123?peek=true"
```

**Response (200 — SUCCESS):**
```json
{
  "id": "ZEAG-2026-00123",
  "status": "SUCCESS",
  "module": "ZEAG",
  "submittedAt": "2026-02-23T14:32:00Z",
  "portal": "GOVCONNECT",
  "receiptPdf": "JVBERi0xLjQK...",
  "failureReason": null
}
```

**Status semantics:**

- `PENDING`: Sent, but the transport acknowledgement has not arrived yet. Never marked as polled.
- `SUCCESS`: Successfully delivered. Contains `receiptPdf` (base64-encoded confirmation PDF).
- `FAILURE`: Transport failed. Contains `failureReason`.

**Note:** By default, reading a SUCCESS or FAILURE report is destructive — it is marked as polled, leaves the pending list, and is not delivered again ([report-already-retrieved](problems/report-already-retrieved.md)). Use `?peek=true` and consume the report only once you have durably stored the result.

### Recommended polling loop

1. `GET /reports` to learn which of your submissions have results waiting.
2. For each id, `GET /reports/{id}?peek=true`.
3. On `PENDING`, do nothing — it stays in the list and resolves later.
4. On `SUCCESS` / `FAILURE`, store the result (and decode `receiptPdf`), then re-read **without** `peek` to consume it.

Poll well inside the retention window: results that are never fetched are eventually removed by the retention cleanup and return 410 ([report-expired](problems/report-expired.md)).

---

## Error Handling

### HTTP Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| 200 | OK | Request successful |
| 400 | Bad Request | Request validation failed (e.g. missing `id`, malformed value) |
| 401 | Unauthorized | Missing or invalid API credentials — empty body, `WWW-Authenticate` header |
| 404 | Not Found | No retrievable report under this id for your API user |
| 410 | Gone | Report already retrieved, or aged out of the retention window |

### Problem Details (RFC 9457)

Except for 401, errors are returned as [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) problem details with `Content-Type: application/problem+json`. **Branch on the `type` URI** — it is the stable machine-readable discriminator; `title` and `detail` are developer diagnostics and may be reworded.

| `type` URI | Status | Documentation |
|---|---|---|
| `…/problems/validation-error` | 400 | [validation-error](../../problems/validation-error.md) |
| `…/Products/ZEAG/problems/report-not-found` | 404 | [report-not-found](problems/report-not-found.md) |
| `…/Products/ZEAG/problems/report-already-retrieved` | 410 | [report-already-retrieved](problems/report-already-retrieved.md) |
| `…/Products/ZEAG/problems/report-expired` | 410 | [report-expired](problems/report-expired.md) |

Note that **the two 410 cases share a status code but differ in `type`** — one means "someone already consumed this", the other "it aged out". Distinguish them by `type`, never by status alone.

### Validation Errors

A rejected memento request returns 400 with one `errors` entry per violated constraint, each carrying a JSON Pointer to the offending member of your request body:

```json
{
  "type": "https://docs.vertama.com/problems/validation-error",
  "title": "Request validation failed",
  "status": 400,
  "detail": "1 violation",
  "instance": "/api/zeag/v1/memento",
  "errors": [
    { "detail": "must not be null", "pointer": "#/id" }
  ]
}
```

Every violation is listed, so one round trip shows all problems at once. `pointer` is absent for violations of the request as a whole (an unparseable body, or a rule spanning several fields).

### Not-found is normal

A 404 between memento creation and the parents dispatching the form is the **expected** state, not a fault in your integration — keep polling. See [report-not-found](problems/report-not-found.md) for the full case list (not yet submitted, unknown id, id belonging to another API user, id of a different module).

---

## Reference

### Formal API Definition

- [OpenAPI](./api.yml)
- [API Viewer (Swagger)](https://elim.vertamob.de/api/docs/swagger-ui/index.html?urls.primaryName=ZEAG)

### API Endpoints Summary

| Method | Endpoint                    | Description                     |
|--------|-----------------------------|---------------------------------|
| POST   | `/api/zeag/v1/memento`      | Create memento                  |
| GET    | `/api/zeag/v1/reports`      | List pending report IDs         |
| GET    | `/api/zeag/v1/reports/{id}` | Retrieve report delivery status |

### Date & Time Format

- **Date** (`tag`, `geburtsdatumVorherigesKind`): ISO 8601 (`YYYY-MM-DD`, e.g. `2026-02-23`)
- **Date-time** (`vorgangsidentifikation.ereignis.zeitpunkt`): ISO 8601 (`YYYY-MM-DDThh:mm:ss±hh:mm`, e.g. `2026-02-23T14:30:00+01:00`)
- **Time of birth** (`geburtsangaben.uhrzeit`): pattern `^[0-2][0-9AB]:[0-5][0-9]$`. Ordinary times are plain digits (`14:30`); the pattern additionally admits `A` / `B` in the second position — use those only where your xPersonenstand mapping prescribes it.

### Enumerations

| Field | Values |
|-------|--------|
| `kind.geschlecht`, `mutter.geschlecht`, `elternteil2.geschlecht` | `m` (männlich), `w` (weiblich), `x` (keine Angabe), `d` (divers) — codes from XÖV codelist `urn:xoev-de:xinneres:codeliste:geschlecht` |
| `status` (report result) | `PENDING`, `SUCCESS`, `FAILURE` |
| `elternVerheiratet`, `zustimmungElterngeldstelle`, `nichtVorhanden` | `true` only — omit for the negative |

### Codes vs. free text

Some fields take a **code from a fixed list**, not free text:

| Field | Source | Example |
|-------|--------|---------|
| `kind.geschlecht`, `mutter.geschlecht`, `elternteil2.geschlecht` | XÖV codelist `urn:xoev-de:xinneres:codeliste:geschlecht` | `w` |
| `staatsangehoerigkeit.code`, `weitereStaatsangehoerigkeit.code` | Destatis Staatsangehörigkeits-Schlüssel — **not** ISO 3166 | `221` (Germany) |
| `kontaktdaten[].kanal`, `zustaendigeElterngeldstelle.erreichbarkeit[].kanal` | XÖV codelist `urn:de:xoev:codeliste:erreichbarkeit` | `01` |
| `name.namensartCode` | XÖV codelist Namensart | — |

If a value isn't in the relevant codelist, use the choice type's free-text branch where one exists (`nichtGelisteterWert` for `Staatsangehoerigkeit`); `geschlecht`, `kanal` and `namensartCode` have no free-text fallback.

### Counts

| Field | Minimum | Meaning |
|-------|---------|---------|
| `mutter.anzahlKinder` | 1 | Number of the mother's children |
| `mutter.anzahlTotgeburten` | 0 | Number of stillbirths |
| `ehe.kinderDerEhe` | 1 | Which child of this marriage — stillbirths counted |
| `ehe.totgeburtenDerEhe` | 0 | Stillbirths in this marriage, including a present stillbirth |
| `urkundenbestellung.anzahl*` | 0 | Certificates ordered per format (Standard, Stammbuch, CIEC 16, CIEC 34) |

### Legal Basis

The 081021 message is the parents' supplementary data delivery under § 18 (1) i.V.m. § 20 i.V.m. § 19 PStG.

---

**Document Version:** 0.2.0
**Last Updated:** 2026-09-07
**API Version:** v1get
