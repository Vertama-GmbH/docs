# DIVI API Integration Guide

A practical guide for integration partners using the DIVI (Intensivregister) API.

**Version:** 0.1.0
**Last Updated:** 2026-02-23

---

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [Core Concepts](#core-concepts)
4. [Direct Submission Endpoint](#direct-submission-endpoint)
5. [Memento Endpoint](#memento-endpoint)
6. [Status & Receipt Endpoint](#status--receipt-endpoint)
7. [Complete Workflow Examples](#complete-workflow-examples)
8. [Error Handling](#error-handling)
9. [Reference](#reference)

---

## Introduction

The DIVI API enables hospital information systems (KIS) to automate capacity reporting to the **DIVI Intensivregister**. This API allows integration partners to:

- **Submit reports directly** (machine-to-machine) without user interaction.
- **Create form mementos** to pre-fill the interactive browser form for manual review.
- **Retrieve report results**, tracking status, and RKI receipt PDFs for confirmation.

### Use Cases

The DIVI module supports two distinct workflows:

**Workflow A: Fully Automated (Direct Submission)**
1. **Hospital system (KIS)** gathers bed occupancy (Kapazitäten) and situation data.
2. **System calls API** `POST /api/divi/v1/report` with the full data payload.
3. **API submits immediately** to the DIVI Intensivregister and returns success/failure.
4. **System calls API** `GET /api/divi/v1/status/{reportId}` to download the official PDF receipt.

**Workflow B: Staff Review (Memento & Pre-fill)**
1. **Hospital system (KIS)** gathers partial or complete data.
2. **System calls API** `POST /api/divi/v1/memento` to get an encrypted `memento` string.
3. **System constructs URL** to the interactive DIVI form: `https://elim.vertamob.de/divi/?m={memento}`.
4. **User** opens the link, reviews the pre-filled data, completes missing fields, and clicks submit.

### Prerequisites

Before using the API, you need:
- **API User Credentials**: Basic Auth username and password provided by your administrator.
- **Meldebereich ID**: The identifier of your intensive care unit (ICU) provided by DIVI.

### OpenAPI Specification

The complete OpenAPI specification is available at:
```
https://elim.vertamob.de/api/docs/swagger-ui/index.html?urls.primaryName=DIVI
```

---

## Authentication

The API uses **HTTP Basic Authentication** with your API user credentials.

### Example

```bash
curl -u "api-username:api-password" \
  https://elim.vertamob.de/api/divi/v1/status/divi-2026-001
```

---

## Core Concepts

### Intensivregister Meldung

The main data structure for reporting. Key components include:
- **reportId** (required): Your unique identifier for tracking this specific submission.
- **meldebereich** (required): The specific ICU taking the report.
- **auspraegung** (required): Report format version (always `"V2"`).
- **kapazitaeten** (required): ICU capacity counts (total beds, occupied, ECMO, etc.).
- **betriebssituation**: Operational status of the hospital.
- **faelleCovidAktuell**, **altersstrata**, **neuaufnahmen**, **influenzaStatus**, **rsvStatus**: Optional extended metric blocks for patient populations.

### Direct vs. Memento

- The **Direct Submission** endpoint requires all mandatory fields to perform the transmission.
- The **Memento** endpoint requires only `reportId` (others are optional), as it merely encrypts the data to assist the human user in filling out the UI form.

### Report ID

The `reportId` field must be unique per API user. It is used to retrieve the result and PDF receipt later via `GET /api/divi/v1/status/{reportId}`.

---

## Direct Submission Endpoint

**Endpoint:** `POST /api/divi/v1/report`

**Purpose:** Submits complete DIVI report data directly to the DIVI Intensivregister API.

### Request Body

**Minimal Example:**
```json
{
  "reportId": "divi-2026-00001",
  "meldebereich": {
    "id": "MB-12345"
  },
  "auspraegung": "V2",
  "betriebssituation": "REGULAERER_BETRIEB",
  "kapazitaeten": {
    "intensivBetten": 20,
    "intensivBettenBelegt": 15
  }
}
```

### Response

Returns a JSON object indicating immediate submission success or the DIVI API failure reason.

```json
{
  "reportId": "divi-2026-00001",
  "succeeded": true,
  "errorMsg": null
}
```

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `reportId` | string | No | The report identifier you provided |
| `succeeded`| boolean| No | `true` if accepted by DIVI Intesivregister |
| `errorMsg` | string | Yes | Error text from the upstream API if `succeeded` is `false` |

---

## Memento Endpoint

**Endpoint:** `POST /api/divi/v1/memento`

**Purpose:** Create encrypted memento string to pre-fill the interactive HTML form.

### Request Body

Same structure as Direct Submission, but only `reportId` is strictly required.

```json
{
  "reportId": "divi-2026-00002",
  "kapazitaeten": {
    "intensivBetten": 20,
    "intensivBettenBelegt": 16
  }
}
```

### Response

Returns the encrypted memento string.

```json
{
  "memento": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..DGG5lQvJC8OpYrCt.Xm8YR..."
}
```

You can then pass this string to your users:
`https://elim.vertamob.de/divi/?m=eyJhb...`

---

## Status & Receipt Endpoint

After a report is submitted (either directly via `api/divi/v1/report` or interactively by a user who used a memento link), you can download the status and PDF receipt.

**Endpoint:** `GET /api/divi/v1/status/{reportId}`

Returns the full report result including the PDF receipt for successful submissions.

**Parameters:**

| Parameter | In | Required | Description |
|-----------|-----|----------|-------------|
| `reportId` | path | Yes | The report ID from your original submission |

**Request Example:**
```bash
curl -u "api-user:api-pass" \
  https://elim.vertamob.de/api/divi/v1/status/divi-2026-00001
```

**Response (200 — SUCCESS):**
```json
{
  "reportId": "divi-2026-00001",
  "succeeded": true,
  "sendDate": "2026-02-23T14:32:00Z",
  "formName": "DIVI",
  "errorMsg": null,
  "base64Pdf": "JVBERi0xLjQK..."
}
```

By default, reading this status marks it as polled. If polled a second time, the endpoint will return `410 Gone`.

### Extracting the Receipt PDF

The `base64Pdf` field contains the base64-encoded PDF. To save it:

```bash
RESPONSE=$(curl -s -u "api-user:api-pass" \
  "https://elim.vertamob.de/api/divi/v1/status/divi-2026-00001")

if [ "$(echo "$RESPONSE" | jq -r '.succeeded')" = "true" ]; then
  echo "$RESPONSE" | jq -r '.base64Pdf' | base64 --decode > divi-receipt.pdf
  echo "Receipt saved."
else
  echo "Submission failed."
fi
```

---

## Error Handling

### HTTP Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| 200 | OK | Request successful (Check `succeeded` / `errorMsg` inside body) |
| 400 | Bad Request | Invalid JSON structure or required fields missing |
| 401 | Unauthorized | Missing or invalid API credentials |
| 404 | Not Found | Report ID does not exist |
| 410 | Gone | Status for this report was already retrieved (polled) |

### Validation Errors

If the request lacks mandatory fields, a 400 Bad Request is returned:
```json
{
  "errors": ["kapazitaeten.intensivBetten must be greater than or equal to 0"]
}
```

---

## Reference

### API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/divi/v1/report` | Submit report directly |
| POST | `/api/divi/v1/memento` | Create memento string for pre-fill |
| GET | `/api/divi/v1/status/{reportId}` | Retrieve submission result and PDF |

**Document Version:** 0.1.0
**Last Updated:** 2026-02-23
**API Version:** v1
