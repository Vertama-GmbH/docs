# DIGT API Integration Guide

A practical guide for integration partners using the DIGT (Digitale Sterbefall-Meldung) API.

**Version:** 0.3.0
**Last Updated:** 2026-10-19

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

The DIGT API enables clinical information systems (KIS) and undertaker software (Bestatter-Software) to pre-fill a digital death notification (Sterbefall-Meldung) for the civil registry office (Standesamt) via xPersonenstand integration. This API allows integration partners to:

- **Create form mementos** to generate pre-filled form URLs from case data
- **Enable user review** by staff before official submission
- **Retrieve report results** and status after end users submit forms to the Standesamt

### Use Case

DIGT solves the digital transmission of a Sterbefall-Meldung:

1. **Source system (KIS / Bestatter-Software)** has case data but wants staff to review and complete the form before xPersonenstand submission
2. **System calls API** with report data as JSON, populating exactly one of the three report-type slots
3. **API returns** an encrypted memento string and a magic link
4. **System uses the `magicLink`** to open a pre-filled form
5. **User reviews, completes missing info, and submits** to the Standesamt
6. **System automatically polls** for the processing status and confirmation PDF

```
KIS / Bestatter-Software
    ↓
[1] POST /api/digt/v1/memento  (API user credentials)
    ↓
[2] Receives { "memento": "...", "magicLink": "/mtl/...?m=..." }
    ↓
[3] Constructs absolute URL: https://elim.vertamob.de + magicLink
    ↓
[4] Opens URL in browser — authenticated via MTL token
    ↓
End User
    ↓
[5] Reviews pre-filled data, completes form → submits to Standesamt
    ↓
KIS / Bestatter-Software (asynchronous)
    ↓
[6] GET /api/digt/v1/reports/{id}  → status (PENDING, SUCCESS, FAILURE) + receipt PDF
```

**Benefits:**

- No direct automated submission — users maintain control and can review/correct data
- Form validation happens in browser (immediate feedback)
- Secure, encrypted mementos protect sensitive personal data

### Prerequisites

Before using the API, you need:

- **API User Credentials**: Username and password provided by your administrator

### OpenAPI Specification

The complete OpenAPI specification is available at:
```
https://elim.vertamob.de/api/docs/swagger-ui/index.html?urls.primaryName=DIGT
```

---

## Authentication

The API uses **HTTP Basic Authentication** with your API user credentials (the service account provided by your administrator). End users accessing the form do not need separate credentials.

### Example

```bash
curl -u "api-username:api-password" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"id":"DIGT-2026-001","Einrichtung":{}}' \
  https://elim.vertamob.de/api/digt/v1/memento
```

---

## Core Concepts

### Sterbefall-Meldung and its three report types

DIGT covers three xPersonenstand message types. A single memento request wraps all three in **slots**, of which **exactly one must be populated**. The populated slot determines which HTML form variant the memento targets:

| Slot | Message type | Form / target | Reporter |
|------|--------------|---------------|----------|
| `Einrichtung` | **084020** | Sterbefallanzeige (Einrichtung) | Hospital / care facility |
| `Bestatter` | **084021** | Sterbefallanzeige (Bestatter) | Undertaker |
| `Todesbescheinigung` | **084040** | Leichenschau-Mitteilung | Death certificate / examination |

Populating zero or more than one slot is a validation error (400). The active slot determines which form the link opens after redemption (`/digt/{084020|084021|084040}`) — that target is encrypted inside the token, not part of the `magicLink` path itself.

### Memento Pattern

A **memento** is an encrypted, URL-safe string that contains form pre-fill data:

- Generated from JSON report data
- Tamper-proof and URL-safe
- Used as query parameter: `?m={memento}`

### Magic Token Link (MTL)

The `magicLink` field in the API response is a server-issued, time-limited URL that:
- Authenticates the end user automatically (no login page)
- Redirects to `/digt/{reportType}?m={memento}` on success
- Is a **relative path** — prepend your instance host to make it absolute

The link itself is `/mtl/{token}?m={memento}`. The redirect target (`/digt/{reportType}`) is encrypted inside the opaque token — it is **not** a readable path segment.

```
magicLink: "/mtl/eyJ...token...?m=eyJ...memento..."

Full URL: https://elim.vertamob.de/mtl/eyJ...token...?m=eyJ...memento..."
```

See [Magic Token Link (MTL)](../../Authentication/magic-token-link.md) for security details and token lifetime.

### Report ID

The `id` field must be unique per API user. It serves multiple purposes:

1. **Form pre-fill and correlation**: Correlates your case data to the form
2. **Status retrieval key**: After submission, used to retrieve delivery status via `GET /api/digt/v1/reports/{id}`

---

## Memento Endpoint

**Endpoint:** `POST /api/digt/v1/memento`

**Purpose:** Create an encrypted memento string and magic link to pre-fill a DIGT reporting form.

This endpoint does **not** submit the report — it only creates a pre-fill token for the interactive HTML form.

### Request Body

The body wraps all three report types (`Einrichtung`, `Bestatter`, `Todesbescheinigung`). You must populate **exactly one** slot — it selects the target form (and thus the redirect target `/digt/084020|084021|084040`, encrypted in the token). Supplying zero or more than one slot returns **400 Bad Request**.

Within the chosen slot, only the top-level `id` is mandatory; every other field is optional to allow partial pre-filling (see [Formal API Definition](#reference) for the complete schema).

**Minimal Example (084020 — Einrichtung):**
```json
{
  "id": "DIGT-2026-00001",
  "Einrichtung": {}
}
```

**Extended Example (084020 — Einrichtung):**
```json
{
  "id": "DIGT-2026-00123",
  "standortId": "770001",
  "Einrichtung": {
    "anzeigender": {
      "ansprechpartner": {
        "vornamen": "Anna",
        "familienname": "Schmidt"
      },
      "kontaktdaten": [
        { "kanal": "telefon", "kennung": "+49 30 123456" }
      ]
    },
    "verstorbener": {
      "vorname": "Hans Wilhelm",
      "familienname": "Mueller",
      "geburtsname": "Schmidt",
      "geburtstag": "1945-03-22",
      "geschlecht": "maennlich",
      "letzterWohnsitz": {
        "strasse": "Musterstrasse 1",
        "plz": "10115",
        "ort": "Berlin"
      }
    },
    "sterbefall": {
      "todeszeitpunkt": {
        "todestag": {
          "zeitpunkt": "2026-04-12T14:30:00+02:00",
          "uhrzeitExakt": true
        }
      },
      "sterbeort": {
        "strasse": "Klinikstraße",
        "hausnummer": "1",
        "ort": "Berlin"
      }
    },
    "leichenID": "L-2026-04-001"
  }
}
```

To pre-fill an undertaker form, populate `Bestatter` instead; for a death-certificate form, populate `Todesbescheinigung`. See the OpenAPI schema for the field structure of each slot.

### Reporting Institution (`standortId`)

For `Einrichtung` (084020) and `Todesbescheinigung` (084040), the reporting hospital is identified by its 6-digit InEK Standort-ID (`standortId`, top level of the request, next to `id`). Name and address are taken from the Krankenhausstandorte registry for that Standort and cannot be entered:

| Slot | Taken from the Standort |
|------|-------------------------|
| `Einrichtung` (084020) | Name and address of the reporting institution (`anzeigender`) |
| `Todesbescheinigung` (084040) | Address of the physician (`angabenLeichenschau.anschriftArzt`) |

Contact person and contact details (`ansprechpartner`, `kontaktdaten`, `namenArzt`, `kontaktArzt`) are still supplied by you or entered in the form.

- The Standort must be one of the Standorte of your account. A Standort that is not (or an unknown or malformed value) is **ignored**, as if none was given — the request is not rejected.
- Without a valid `standortId`, the user picks one of the account's Standorte in the form; with only one Standort, it is set automatically.
- For `Einrichtung` (084020), the receiving Standesamt is limited to the Standesämter assigned to the chosen Standort.
- `Bestatter` (084021) ignores `standortId`; the undertaker's name and address are still entered.

**Deprecated fields:** `Einrichtung.anzeigender.nameOrganisation`, `Einrichtung.anzeigender.anschrift` and `Todesbescheinigung.angabenLeichenschau.anschriftArzt` are deprecated. They are still accepted, but ignored — the values from the Standort always apply. Do not send them in new integrations.

### Specifying a State (`staat`)

For places (`sterbeort`, `geburtsort` and the other event locations such as the place of marriage) and for the structured foreign address (`anschriftAuslandStrukturiert`), `staat` is an object, as xPersonenstand defines it (`Code.Staat`):

- `code`: key from the state list (Staatenliste) of the Federal Statistical Office (Destatis), e.g. `"000"` (Germany), `"129"` (France), `"368"` (United States)
- `nichtGelisteterWert`: free text, only if the state is not on the list

If both are given, `code` takes precedence.

```json
"staat": { "code": "129" }
```

```json
"staat": { "nichtGelisteterWert": "Beispielstaat" }
```

For a foreign address given as free lines (`anschriftAusland`), `staat` is the bare key itself (e.g. `"staat": "368"`) — no free text, and not `"000"`. At least two address lines of at most 35 characters each are required.

For postal addresses (`letzterWohnsitz`, the undertaker's `anschrift` and similar), `staat` remains free text.

The valid keys are listed in the [state code list](../xoev/codelists/StaatCode.yml).

### Response

Returns a JSON object containing the encrypted memento and a ready-to-use magic link:

```json
{
  "memento": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..DGG5lQvJC8OpYrCt.Xm8YR...",
  "magicLink": "/mtl/eyJ...token...?m=eyJ...memento..."
}
```

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `memento` | string | No | Encrypted, URL-safe string containing report data. Use as `?m={memento}` query parameter. |
| `magicLink` | string | Yes | Relative URL for authenticated single-click access. Prepend your instance host: `https://elim.vertamob.de + magicLink` |

---

## Report Retrieval Endpoints

DIGT reports are delivered asynchronously via xPersonenstand/XTA2 transport.

### GET /reports — List pending report IDs

**Endpoint:** `GET /api/digt/v1/reports`

Returns an array of `id` strings for reports that have been submitted but not yet retrieved (unpolled). Reports disappear from this list once retrieved without `?peek=true`.

**Request:**
```bash
curl -u "api-user:api-pass" \
  https://elim.vertamob.de/api/digt/v1/reports
```

**Response (200):**
```json
["DIGT-2026-00123", "DIGT-2026-00124"]
```

An empty array `[]` means no submissions are pending retrieval.

---

### GET /reports/{id} — Retrieve report result

**Endpoint:** `GET /api/digt/v1/reports/{id}`

**Parameters:**

- `id` (path, required)
- `peek` (query, optional): `true` for non-destructive read. Default: `false`.

**Non-destructive peek:**
```bash
curl -u "api-user:api-pass" \
  "https://elim.vertamob.de/api/digt/v1/reports/DIGT-2026-00123?peek=true"
```

**Response (200 — SUCCESS):**
```json
{
  "id": "DIGT-2026-00123",
  "status": "SUCCESS",
  "module": "DIGT",
  "submittedAt": "2026-04-12T14:32:00Z",
  "portal": "GOVCONNECT",
  "receiptPdf": "JVBERi0xLjQK...",
  "failureReason": null
}
```

**Status semantics:**

- `PENDING`: Sent but delivery not yet confirmed. Not marked as polled.
- `SUCCESS`: Successfully delivered to receiver. Contains `receiptPdf` (base64).
- `FAILURE`: Transport failed. Contains `failureReason`.

**Note:** By default, reading a SUCCESS or FAILURE report is destructive (it is marked as polled and disappears from future calls unless `?peek=true` is used).

**Testing**

The following mock IDs are reserved for testing to simulate different delivery outcomes without triggering real backend lookups or network requests:

- `DIGT-TEST-SUCCESS`: Always returns a SUCCESS response with a mock PDF receipt.
- `DIGT-TEST-PENDING`: Always returns a PENDING response.
- `DIGT-TEST-FAILURE`: Always returns a FAILURE response with a simulated failure reason.

---

## Error Handling

### HTTP Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| 200 | OK | Request successful |
| 400 | Bad Request | Request validation failed (e.g. invalid JSON, missing `id`, zero / more than one report-type slot populated) |
| 401 | Unauthorized | Missing or invalid API credentials — empty body, `WWW-Authenticate` header |
| 404 | Not Found | No DIGT report under this id for your API user |
| 410 | Gone | Report already retrieved, or aged out of the retention window |

### Problem Details (RFC 9457)

Except for 401, errors are returned as [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) problem details with `Content-Type: application/problem+json`. **Branch on the `type` URI** — it is the stable machine-readable discriminator; `title` and `detail` are developer diagnostics and may be reworded.

| `type` URI | Status | Documentation |
|---|---|---|
| `…/problems/validation-error` | 400 | [validation-error](../../problems/validation-error.md) |
| `…/Products/DIGT/problems/report-not-found` | 404 | [report-not-found](problems/report-not-found.md) |
| `…/Products/DIGT/problems/report-already-retrieved` | 410 | [report-already-retrieved](problems/report-already-retrieved.md) |
| `…/Products/DIGT/problems/report-expired` | 410 | [report-expired](problems/report-expired.md) |

Note that **the two 410 cases share a status code but differ in `type`** — one means "someone already consumed this", the other "it aged out". Distinguish them by `type`, never by status alone.

### Validation Errors

A rejected memento request returns 400 with one `errors` entry per violated constraint, each carrying a JSON Pointer to the offending member of your request body:

```json
{
  "type": "https://docs.vertama.com/problems/validation-error",
  "title": "Request validation failed",
  "status": 400,
  "detail": "1 violation",
  "instance": "/api/digt/v1/memento",
  "errors": [
    { "detail": "must not be null", "pointer": "#/id" }
  ]
}
```

---

## Reference

### Formal API Definition

- [OpenAPI](./api.yml)
- [API Viewer (Swagger)](https://elim.vertamob.de/api/docs/swagger-ui/index.html?urls.primaryName=DIGT)

### API Endpoints Summary

| Method | Endpoint                   | Description                     |
|--------|----------------------------|---------------------------------|
| POST | `/api/digt/v1/memento`     | Create memento                  |
| GET | `/api/digt/v1/reports` | List pending report IDs         |
| GET | `/api/digt/v1/reports/{id}` | Retrieve report delivery status |

### Date & Time Format
- **Date**: ISO 8601 format (`YYYY-MM-DD`, e.g., `2026-03-22`)
- **Date-time**: ISO 8601 format (`YYYY-MM-DDThh:mm:ss±hh:mm`, e.g., `2026-04-12T14:30:00+02:00`)

---

**Document Version:** 0.2.0
**Last Updated:** 2026-10-16
**API Version:** v1
