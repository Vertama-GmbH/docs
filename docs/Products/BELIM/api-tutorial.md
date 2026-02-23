# BELIM API Integration Guide

A practical guide for integration partners using the BELIM API.

**Version:** 0.1.0
**Last Updated:** 2026-02-23

---

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [Core Concepts](#core-concepts)
4. [Memento Endpoint](#memento-endpoint)
5. [Direct Submission Endpoint](#direct-submission-endpoint)
6. [Report Retrieval Endpoints](#report-retrieval-endpoints)
7. [Error Handling](#error-handling)
8. [Reference](#reference)

---

## Introduction

The BELIM API enables hospital information systems (KIS) to digitally submit or pre-fill bed occupancy reports (Bettenbelegung) for DEMIS. This API allows integration partners to:

- **Create form mementos** to generate pre-filled form URLs for user review
- **Submit reports directly** to DEMIS without user interaction
- **Retrieve report results** and status after submission

### Use Case

BELIM offers two distinct integration patterns:

**1. Interactive Form Workflow (Memento)**
Best when hospital staff need to review or complete the data before submission.
1. **Hospital system (KIS)** calls the API with partial or complete occupancy data.
2. **API returns** an encrypted `memento` string.
3. **System constructs and opens URL**: `https://elim.vertamob.de/elim/pm/De/Bettenbelegung?m={memento}`
4. **User reviews**, adjusts if needed, and submits to DEMIS.

**2. Direct Submission Workflow**
Best when the external system has complete, verified data and wants to automate the process.
1. **Hospital system (KIS)** calls the API with complete, valid occupancy data.
2. **API validates and submits** directly to DEMIS.
3. **API returns** the outcome immediately.

```
KIS / Hospital System
    ↓
[1] POST /api/belim/v1/memento    OR    POST /api/belim/v1/report
    (Returns memento string)            (Submits directly to DEMIS)
    ↓
    (If memento) Open pre-filled URL
    → User submits
    ↓
[2] GET /api/belim/v1/status/{reportId}  → Status (SUCCESS, FAILURE) + receipt PDF
```

### OpenAPI Specification

The complete OpenAPI specification is available at:
```
https://elim.vertamob.de/api/docs/swagger-ui/index.html?urls.primaryName=BELIM
```

---

## Authentication

The API uses **HTTP Basic Authentication** with your API user credentials (the service account provided by your administrator).

### Example

```bash
curl -u "api-username:api-password" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"reportId":"BELIM-2026-001"}' \
  https://elim.vertamob.de/api/belim/v1/memento
```

---

## Core Concepts

### Bettenbelegsmeldung

The main data structure for bed occupancy reporting. Contains:
- **reportId** (required): Unique laboratory report identifier for correlation. Must be unique per user.
- **StandortId**: 6-digit InEK Standort-Id, identifying the unique hospital location.
- **IK_Nummer**: 9-digit Institutionskennzeichen (IK) number.
- **numbers**: Bed occupancy counts (occupied/operational beds for adults and children).

### Memento Pattern

A **memento** is an encrypted, URL-safe string that contains form pre-fill data. It allows you to securely pass patient/hospital data to the interactive form without persisting it prematurely.
- Generated via `/api/belim/v1/memento`
- Tamper-proof and URL-safe
- Passed via URL parameter: `?m={memento}`

### Report ID

The `reportId` must be unique per API user. It serves to:
1. **Correlate data**: Identifying the exact report across your systems.
2. **Retrieve Status**: Used in `GET /api/belim/v1/status/{reportId}` to poll the delivery status and retrieve the PDF receipt.

---

## Memento Endpoint

**Endpoint:** `POST /api/belim/v1/memento`

**Purpose:** Create an encrypted memento string for the interactive HTML form flow.

### Request Body

Only `reportId` is strictly required for generating a memento. Other fields can be sent to pre-fill the form.

**Complete Example:**
```json
{
  "reportId": "BELIM-2026-00123",
  "dateOfReport": "2026-02-23",
  "StandortId": "987654",
  "IK_Nummer": "987654321",
  "Standortname": "Universitätsklinikum Musterstadt",
  "Strasse": "Musterstraße",
  "Hausnummer": "123",
  "PLZ": "12345",
  "Ort": "Musterstadt",
  "Telefon": "+49 123 456789",
  "numbers": {
    "kinder_betten_belegt": 3,
    "kinder_betten_betrieben": 4,
    "erwachsenen_betten_belegt": 1,
    "erwachsenen_betten_betrieben": 2
  }
}
```

### Response

Returns a JSON object with the memento string.

```json
{
  "memento": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## Direct Submission Endpoint

**Endpoint:** `POST /api/belim/v1/report`

**Purpose:** Submit a complete BELIM bed occupancy report directly to DEMIS without user interaction.

### Request Body

This requires a strictly validated object. All hospital details and numbers must be provided. By default, `StandortId`, `IK_Nummer`, and `numbers` are mandatory for a valid DEMIS submission.

```json
{
  "reportId": "BELIM-2026-00124",
  "dateOfReport": "2026-02-23",
  "StandortId": "987654",
  "IK_Nummer": "987654321",
  "Standortname": "Universitätsklinikum Musterstadt",
  "Strasse": "Musterstraße",
  "Hausnummer": "123",
  "PLZ": "12345",
  "Ort": "Musterstadt",
  "Telefon": "+49 123 456789",
  "numbers": {
    "kinder_betten_belegt": 5,
    "kinder_betten_betrieben": 10,
    "erwachsenen_betten_belegt": 20,
    "erwachsenen_betten_betrieben": 50
  }
}
```

### Response

Returns a JSON status response immediately detailing success or failure.

```json
{
  "reportId": "BELIM-2026-00124",
  "succeeded": true,
  "errorMsg": null
}
```

---

## Report Retrieval Endpoints

### GET /reports — List pending report IDs

**Endpoint:** `GET /api/belim/v1/reports`

Returns an array of `reportId` strings for reports that have been submitted to DEMIS but not yet retrieved (unpolled). Reports disappear from this list once retrieved without `?peek=true`.

**Request:**
```bash
curl -u "api-user:api-pass" \
  https://elim.vertamob.de/api/belim/v1/reports
```

**Response (200):**
```json
["BELIM-2026-00123", "BELIM-2026-00124"]
```

An empty array `[]` means no submissions are pending retrieval.

---

### GET /reports/{reportId} — Retrieve report result

**Endpoint:** `GET /api/belim/v1/status/{reportId}`

**Purpose:** Retrieve the transmission status and payload receipt for any previously submitted report.

**Request:**
```bash
curl -u "api-user:api-pass" \
  "https://elim.vertamob.de/api/belim/v1/status/BELIM-2026-00123"
```

**Response (200 — SUCCESS):**
```json
{
  "reportId": "BELIM-2026-00123",
  "succeeded": true,
  "sendDate": "2026-02-23T14:32:00Z",
  "formName": "belim.direct",
  "errorMsg": null,
  "base64Pdf": "JVBERi0xLjQK..."
}
```

**Status semantics:**
- `succeeded`: `true` if DEMIS successfully accepted the payload.
- `base64Pdf`: Contains the PDF receipt provided by DEMIS (if available).
- `errorMsg`: Contains the failure reason if submission failed.

---

## Error Handling

### HTTP Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid JSON or validation error |
| 401 | Unauthorized | Missing or invalid API credentials |
| 404 | Not Found | Report ID does not exist |

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
| POST | `/api/belim/v1/memento` | Create memento for interactive form |
| POST | `/api/belim/v1/report` | Submit report directly via API |
| GET | `/api/belim/v1/status/{reportId}` | Retrieve report delivery status & receipt PDF |

### Date Structure
- **Date Format**: ISO 8601 string (`YYYY-MM-DD`, e.g., `2026-02-23`)

---

**Document Version:** 0.1.0
**Last Updated:** 2026-02-23
**API Version:** v1
