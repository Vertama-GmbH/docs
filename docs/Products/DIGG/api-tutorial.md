# DIGG API Integration Guide

A practical guide for integration partners using the DIGG (Digitale Geburtsanzeige) API.

**Version:** 0.1.0
**Last Updated:** 2026-02-23

---

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [Core Concepts](#core-concepts)
4. [Memento Endpoint](#memento-endpoint)
5. [Report Retrieval Endpoint](#report-retrieval-endpoint)
6. [Complete Workflow Examples](#complete-workflow-examples)
7. [Error Handling](#error-handling)
8. [Reference](#reference)

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
[2] Receives { "memento": "..." }
    ↓
[3] Constructs absolute URL: https://elim.vertamob.de/digg/Geburtsbescheinigung?m={memento}
    ↓
[4] Opens URL in browser
    ↓
End User
    ↓
[6] Reviews pre-filled data, completes form, applies signature/seal → submits to Standesamt
    ↓
KIS / Hospital System (asynchronous)
    ↓
[7] GET /api/digg/v1/reports/{reportId}  → status (PENDING, SUCCESS, FAILURE) + receipt PDF
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
  -d '{"reportId":"DIGG-2026-001"}' \
  https://elim.vertamob.de/api/digg/v1/memento
```

---

## Core Concepts

### Geburtsanzeige

The main data structure for birth registration reporting. Key fields include:
- **reportId** (required): Unique report identifier for tracking
- **StandortId**: ID of the reporting hospital
- **geburtsangaben**: Details about time and place of birth
- **kind**: Child's gender and names
- **mutter**: Mother's standard or confidential data (vertrauliche Geburt)
- **elternteil2**: Optional secondary parent data

### Digital Signature (Siegel / Signatur)

Submitting a birth registration to the Standesamt via xPersonenstand legally requires a valid digital signature or seal.
If a seal is available it will be applied automatically, otherwise the end user will be prompted to apply this signature directly within the DIGG form interface prior to final submission. This step is mandatory; a report cannot be sent without it.

### Memento Pattern

A **memento** is an encrypted, URL-safe string that contains form pre-fill data:
- Generated from JSON hospital report data
- Tamper-proof and URL-safe
- Used as query parameter: `?m={memento}`

### Report ID

The `reportId` field must be unique per API user. It serves a dual purpose:
1. **Form pre-fill and correlation**: Correlates the hospital data to the form
2. **Status retrieval key**: After submission, used to retrieve delivery status via `GET /api/digg/v1/status/{reportId}`

---

## Memento Endpoint

**Endpoint:** `POST /api/digg/v1/memento`

**Purpose:** Create encrypted memento string and magic link to pre-fill DIGG reporting forms.

### Request Body

Only `reportId` is required; all other fields are optional to allow partial pre-filling.

**Minimal Example:**
```json
{
  "reportId": "DIGG-2026-00001"
}
```

**Complete Example:**
```json
{
  "reportId": "DIGG-2026-00123",
  "standortId": "770001",
  "nameEinrichtung": "Universitätsklinikum Musterstadt",
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

```json
{
  "memento": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..DGG5lQvJC8OpYrCt.Xm8YR..."
}
```

---

## Report Retrieval Endpoint

DIGG reports are delivered asynchronously via xPersonenstand/XTA2 transport.

**Endpoint:** `GET /api/digg/v1/reports/{reportId}`

**Parameters:**
- `reportId` (path, required)
- `peek` (query, optional): `true` for non-destructive read. Default: `false`.

**Non-destructive peek:**
```bash
curl -u "api-user:api-pass" \
  "https://elim.example.com/api/digg/v1/reports/DIGG-2026-00123?peek=true"
```

**Response (200 — SUCCESS):**
```json
{
  "reportId": "DIGG-2026-00123",
  "status": "SUCCESS",
  "module": "DIGG",
  "submittedAt": "2026-02-23T14:32:00Z",
  "portal": "StandesamtPortal",
  "receiptPdf": "JVBERi0xLjQK...",
  "failureReason": null
}
```

**Status semantics:**
- `PENDING`: Sent but delivery not yet confirmed. Not marked as polled.
- `SUCCESS`: Successfully delivered to receiver. Contains `receiptPdf` (base64).
- `FAILURE`: Transport failed. Contains `failureReason`.

**Note:** By default, reading a SUCCESS or FAILURE report is destructive (it is marked as polled and disappears from future calls unless `?peek=true` is used).

---

## Error Handling

### HTTP Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid JSON or validation error |
| 401 | Unauthorized | Missing or invalid API credentials |
| 404 | Not Found | Report ID does not exist |
| 410 | Gone | Report was already retrieved (use `?peek=true` to avoid) |

### Validation Errors

If the request data is invalid (e.g. missing `reportId`), a 400 Bad Request is returned:
```json
{
  "errors": ["reportId must not be null"]
}
```

---

## Reference

### API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/digg/v1/memento` | Create memento |
| GET | `/api/digg/v1/reports/{reportId}` | Retrieve report delivery status |

### Date & Time Format
- **Date**: ISO 8601 format (`YYYY-MM-DD`, e.g., `2026-02-23`)
- **Time**: ISO 8601 format (`HH:mm`, e.g., `14:30`)

### Gender Enum Values
| Value | Description |
|-------|-------------|
| `MAENNLICH` | Male |
| `WEIBLICH` | Female |
| `UNBESTIMMT` | Unspecified |

---

**Document Version:** 0.1.0
**Last Updated:** 2026-02-23
**API Version:** v1
