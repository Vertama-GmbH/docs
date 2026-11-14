# DIGG API Integration Guide

A practical guide for integration partners using the DIGG (Digitale Geburtsanzeige) API.

**Version:** 0.5.1
**Last Updated:** 2026-07-21

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

The DIGG API enables hospital information systems (KIS) to pre-fill digital birth registration forms (Geburtsanzeige) for the civil registry office (Standesamt) via xPersonenstand integration. This API allows integration partners to:

- **Create form mementos** to generate pre-filled form URLs from hospital birth data
- **Enable user review** by hospital staff or midwives before official submission
- **Retrieve report results** and status after end users submit forms to the Standesamt

### Use Case

DIGG solves the digital transmission of a Geburtsanzeige:

1. **Hospital system (KIS)** has birth data but wants staff to review and complete the form before xPersonenstand submission
2. **System calls API** with birth report data as JSON
3. **API returns** an encrypted memento string
4. **System uses the `memento`** to open a prefilled form
5. **User reviews, completes missing info, applies digital signature/seal, and submits** to the Standesamt
6. **System automatically polls** for the processing status and signed confirmation PDF

```
KIS / Hospital System
    ↓
[1] POST /api/digg/v1/memento  (API user credentials)
    ↓
[2] Receives { "memento": "...", "magicLink": "/mtl/...?m=..." }
    ↓
[3] Constructs absolute URL: https://elim.vertamob.de + magicLink
    ↓
[4] Opens URL in browser — authenticated via MTL token
    ↓
End User
    ↓
[6] Reviews pre-filled data, completes form, applies signature/seal → submits to Standesamt
    ↓
KIS / Hospital System (asynchronous)
    ↓
[7] GET /api/digg/v1/reports/{id}  → status (PENDING, SUCCESS, FAILURE) + receipt PDF
```

**Benefits:**

- No direct automated submission — users maintain control and can review/correct data
- Form validation happens in browser (immediate feedback)
- Secure, encrypted mementos protect sensitive parent/child data

### Prerequisites

Before using the API, you need:

- **API User Credentials**: Username and password provided by your administrator
- **Seal or Signature**: You have to create a seal or signature and deposit it at https://elim.vertamob.de/home/signaturen

### OpenAPI Specification

The complete OpenAPI specification is available at:
```
https://elim.vertamob.de/api/docs/swagger-ui/index.html?urls.primaryName=DIGG
```

---

## Authentication

The API uses **HTTP Basic Authentication** with your API user credentials (the service account provided by your administrator). End users accessing the form do not need separate credentials.

### Example

```bash
curl -u "api-username:api-password" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"id":"DIGG-2026-001"}' \
  https://elim.vertamob.de/api/digg/v1/memento
```

---

## Core Concepts

### Geburtsanzeige

The main data structure for birth registration reporting. Key fields include:

- **id** (required): Unique report identifier for tracking
- **standortId**: ID of the reporting hospital
- **nameEinrichtung**: Name of the hospital
- **ansprechpartner**: Contact name
- **anschriftAutor**: Hospital Address
- **geburtsangaben**: Details about time and place of birth
- **kind**: Child's gender and names
- **mehrlingsgeburt**: In case of a multiple birth
- **mutter**: Mother's standard or confidential data (vertrauliche Geburt)
- **elternteil2**: Optional secondary parent data
- **standesamtKennung**: Optional Standesamtkennung if multiple Standesämter are applicable (and configured)
- **zuordnungGeburtsanzeige**: Identifier for further official references
- **clientReference**: Optional opaque reference string that is echoed back verbatim in the report result — useful for correlating a report to a KIS case (see [Client Reference](#client-reference))

### Digital Signature (Siegel / Signatur)

Submitting a birth registration to the Standesamt via xPersonenstand legally requires a valid digital signature or seal.
If a seal is available it will be applied automatically, otherwise the end user will be prompted to apply this signature directly within the DIGG form interface prior to final submission. This step is mandatory; a report cannot be sent without it.

### Memento Pattern

A **memento** is an encrypted, URL-safe string that contains form pre-fill data:

- Generated from JSON hospital report data
- Tamper-proof and URL-safe
- Used as query parameter: `?m={memento}`

### Magic Token Link (MTL)

The `magicLink` field in the API response is a server-issued, time-limited URL that:
- Authenticates the end user automatically (no login page)
- Redirects to `/digg/Geburtsbescheinigung?m={memento}` on success
- Is a **relative path** — prepend your instance host to make it absolute

The link itself is `/mtl/{token}?m={memento}`. The redirect target (`/digg/Geburtsbescheinigung`) is encrypted inside the opaque token — it is **not** a readable path segment.

```
magicLink: "/mtl/eyJ...token...?m=eyJ...memento..."

Full URL: https://elim.vertamob.de/mtl/eyJ...token...?m=eyJ...memento..."
```

See [Magic Token Link (MTL)](../../Authentication/magic-token-link.md) for security details and token lifetime.

### Report ID

The `id` field must be unique per API user. It serves multiple purposes:

1. **Form pre-fill and correlation**: Correlates the hospital data to the form
2. **Status retrieval key**: After submission, used to retrieve delivery status via `GET /api/digg/v1/reports/{id}`

### Client Reference

The optional `clientReference` field is an arbitrary, opaque string of your choosing. DIGG stores it verbatim and echoes it back unchanged in the report result (`ReportResult.clientReference`), letting you map a retrieved report back to its originating case in your system.

Unlike `id`, `clientReference` carries no uniqueness or format requirements and is not interpreted by DIGG by default. A common convention — when HL7 is used to receive reports — is to combine the KIS PatientenID and Fallnummer as `{PatientenID}|{Fallnummer}`:

```json
{
  "id": "DIGG-2026-00123",
  "clientReference": "12345|67890"
}
```

---

## Memento Endpoint

**Endpoint:** `POST /api/digg/v1/memento`

**Purpose:** Create encrypted memento string and magic link to pre-fill DIGG reporting forms.

### Request Body

Only `id` is required; all other fields are optional to allow partial pre-filling (see [Formal API Definition](#reference) for the complete schema).

**Minimal Example:**
```json
{
  "id": "DIGG-2026-00001"
}
```

**Extended Example:**
```json
{
  "id": "DIGG-2026-00123",
  "clientReference": "12345|67890",
  "standortId": "770001",
  "nameEinrichtung": "Universitätsklinikum Musterstadt",
  "anschriftAutor": {
    "gebaeude": {
      "postleitzahl": "10117",
      "strasse": "Musterstraße",
      "hausnummer": "1",
      "wohnort": "Berlin"
    }
  },
  "totgeburt": false,
  "vertraulicheGeburt": false,
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
    "geschlecht": "WEIBLICH",
    "name": {
      "vornamen": "Emma Sophie",
      "familienname": "Mustermann"
    }
  },
  "mutter": {
    "standard": {
      "name": {
        "vornamen": "Anna",
        "familienname": "Mustermann",
        "geburtsname": "Schmidt"
      },
      "geburtsdatum": "1990-05-15",
      "anschrift": {
        "strasse": "Musterweg",
        "hausnummer": "12",
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
  "magicLink": "/mtl/eyJ...token...?m=eyJ...memento..."
}
```

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `memento` | string | No | Encrypted, URL-safe string containing report data. Use as `?m={memento}` query parameter. |
| `magicLink` | string | Yes | Relative URL for authenticated single-click access. Prepend your instance host: `https://elim.vertamob.de + magicLink` |

---

## Report Retrieval Endpoints

DIGG reports are delivered asynchronously via xPersonenstand/XTA2 transport.

### GET /reports — List pending report IDs

**Endpoint:** `GET /api/digg/v1/reports`

Returns an array of `id` strings for reports that have been submitted to DEMIS but not yet retrieved (unpolled). Reports disappear from this list once retrieved without `?peek=true`.

**Request:**
```bash
curl -u "api-user:api-pass" \
  https://elim.vertamob.de/api/digg/v1/reports
```

**Response (200):**
```json
["DIGG-2026-00123", "DIGG-2026-00124"]
```

An empty array `[]` means no submissions are pending retrieval.

---

### GET /reports/{id} — Retrieve report result

**Endpoint:** `GET /api/digg/v1/reports/{id}`

**Parameters:**

- `id` (path, required)
- `peek` (query, optional): `true` for non-destructive read. Default: `false`.

**Non-destructive peek:**
```bash
curl -u "api-user:api-pass" \
  "https://elim.example.com/api/digg/v1/reports/DIGG-2026-00123?peek=true"
```

**Response (200 — SUCCESS):**
```json
{
  "id": "DIGG-2026-00123",
  "status": "SUCCESS",
  "module": "DIGG",
  "submittedAt": "2026-02-23T14:32:00Z",
  "portal": "StandesamtPortal",
  "clientReference": "12345|67890",
  "receiptPdf": "JVBERi0xLjQK...",
  "failureReason": null
}
```

The `clientReference` field echoes back verbatim whatever was supplied on submission (or `null` if none was supplied), letting you correlate the result to its originating case. See [Client Reference](#client-reference).

**Status semantics:**

- `PENDING`: Sent but delivery not yet confirmed. Not marked as polled.
- `SUCCESS`: Successfully delivered to receiver. Contains `receiptPdf` (base64).
- `FAILURE`: Transport failed. Contains `failureReason`.

**Note:** By default, reading a SUCCESS or FAILURE report is destructive (it is marked as polled and disappears from future calls unless `?peek=true` is used).

**Testing**

The following mock IDs are reserved for testing to simulate different delivery outcomes without triggering real backend lookups or network requests:

- `DIGG-TEST-SUCCESS`: Always returns a SUCCESS response with a mock PDF receipt.
- `DIGG-TEST-PENDING`: Always returns a PENDING response.
- `DIGG-TEST-FAILURE`: Always returns a FAILURE response with a simulated failure reason.

---

## Error Handling

### HTTP Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| 200 | OK | Request successful |
| 400 | Bad Request | Request validation failed (e.g. invalid JSON, missing `id`, a date not in ISO 8601) |
| 401 | Unauthorized | Missing or invalid API credentials — empty body, `WWW-Authenticate` header |
| 404 | Not Found | No DIGG report under this id for your API user |
| 410 | Gone | Report already retrieved, or aged out of the retention window |

### Problem Details (RFC 9457)

Except for 401, errors are returned as [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) problem details with `Content-Type: application/problem+json`. **Branch on the `type`** — it is the stable machine-readable discriminator; `title` and `detail` are developer diagnostics and may be reworded. Each `type` is a path: resolved against your V.ap host, it opens the type's page, and `/api/docs/problems` lists all types (see [Problem types](../../problems/index.md)).

| `type` | Status |
|---|---|
| `/api/docs/problems/validation-error` | 400 |
| `/api/docs/problems/digg/report-not-found` | 404 |
| `/api/docs/problems/digg/report-already-retrieved` | 410 |
| `/api/docs/problems/digg/report-expired` | 410 |

Note that **the two 410 cases share a status code but differ in `type`** — one means "someone already consumed this", the other "it aged out". Distinguish them by `type`, never by status alone.

### Validation Errors

A rejected memento request returns 400 with one `errors` entry per violation, each carrying a JSON Pointer to the offending member of your request body. A missing `id` answers `"pointer": "#/id"` with `"detail": "must not be null"`. A value that does not read has its pointer too, here a date in German notation:

```json
{
  "type": "/api/docs/problems/validation-error",
  "title": "Request validation failed",
  "status": 400,
  "detail": "1 violation",
  "instance": "/api/digg/v1/memento",
  "errors": [
    { "detail": "not a valid value: expected a date, YYYY-MM-DD", "pointer": "#/geburtsangaben/tag" }
  ]
}
```

`pointer` is absent only for a violation of the request as a whole, such as JSON that is broken; `detail` then names its line and column.

### Not-found is normal

A 404 between memento creation and the user sending the form is the **expected** state, not a fault in your integration — keep polling. If sending fails in the form, nothing is recorded either, so the id stays 404 until the user sends successfully. Poll well inside the 3-day retention window: a result that is never fetched is removed by the retention cleanup and answers 410 (`report-expired`).

---

## Reference

### Formal API Definition

- [OpenAPI](./api.yml) 
- [API Viewer (Swagger)](https://elim.vertamob.de/api/docs/swagger-ui/index.html?urls.primaryName=DIGG)

### Runnable Examples

[vap-examples](https://github.com/Vertama-GmbH/vap-examples) holds small Java programs that call the memento endpoint with basic auth and open the prefilled form: the `id` alone, a rich prefill (built in code, and the same as literal JSON), and two refused requests with V.ap's answer as sent. Run them from the command line with `make`, or in your IDE.

### API Endpoints Summary

| Method | Endpoint                   | Description                     |
|--------|----------------------------|---------------------------------|
| POST | `/api/digg/v1/memento`     | Create memento                  |
| GET | `/api/digg/v1/reports` | List pending report IDs         |
| GET | `/api/digg/v1/reports/{id}` | Retrieve report delivery status |

### Date & Time Format
- **Date**: ISO 8601 format (`YYYY-MM-DD`, e.g., `2026-02-23`)
- **Time**: ISO 8601 format (`HH:mm`, e.g., `14:30`)

---

**Document Version:** 0.5.1
**Last Updated:** 2026-07-21
**API Version:** v1
