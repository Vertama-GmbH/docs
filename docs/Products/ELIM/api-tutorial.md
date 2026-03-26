# ELIM API Integration Guide

A practical guide for integration partners using the ELIM (Hospitalisierungsmeldung) API.

**Version:** 0.1.0
**Last Updated:** 2026-03-25

---

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [Core Concepts](#core-concepts)
4. [Memento Endpoint](#memento-endpoint)
5. [Report Retrieval Endpoints](#report-retrieval-endpoints)
6. [Complete Workflow Examples](#complete-workflow-examples)
7. [Error Handling](#error-handling)
8. [Reference](#reference)

---

## Introduction

The ELIM API enables hospital information systems (KIS) to pre-fill disease notification forms (Hospitalisierungsmeldung) in Germany (DEMIS integration). This API allows integration partners to:

- **Create form mementos** to generate pre-filled form URLs from hospital data
- **Retrieve report results** after end users submit forms to DEMIS
- **Enable user review** before submission to public health authorities

### Use Case

ELIM solves a common integration pattern:

1. **Hospital system (KIS)** has patient and reporting data but wants users to review before DEMIS submission
2. **System calls API** with hospital report data as JSON
3. **API returns** an encrypted memento string **and a ready-to-use `magicLink` URL**
4. **System sends the `magicLink`** to the end user (email, portal, etc.)
5. **User clicks the link** — authenticated, lands on ELIM index with pre-filled data
6. **User selects disease form, reviews, and submits** to DEMIS

```
KIS / Hospital System
    ↓
[1] POST /api/elim/v1/memento  (API user credentials)
    ↓
[2] Receives { "memento": "...", "magicLink": "/mtl/.../elim/?m=..." }
    ↓
[3] Constructs absolute URL: https://your-instance + magicLink
    ↓
[4] Delivers URL to end user (email, portal link, SMS, etc.)
    ↓
End User
    ↓
[5] Clicks link → authenticated via MTL token
    → lands on pre-filled form
    ↓
[6] Reviews pre-filled data → submits to DEMIS
    ↓
KIS / Hospital System (asynchronous)
    ↓
[7] GET /api/elim/v1/reports  → list of pending reportIds
[8] GET /api/elim/v1/reports/{reportId}  → full result + receipt PDF
```

**Benefits:**
- No direct submission required — users maintain control
- No separate end-user login credentials needed — `magicLink` handles authentication
- Form validation happens in browser (immediate feedback)
- Users can correct or supplement data before sending
- Encrypted mementos are tamper-proof

### Prerequisites

Before using the API, you need:
- **API User Credentials**: Username and password provided by your administrator
- **Base URL**: Your ELIM instance URL (e.g., `https://elim.vertamob.de`)

That's it. End users do **not** need separate credentials — the `magicLink` in the API response handles their authentication automatically.

### API Versioning

All endpoints are versioned under `/api/elim/v1/`.

### OpenAPI Specification

The complete OpenAPI specification is available at:
```
https://your-instance/api/docs/swagger-ui/index.html?urls.primaryName=ELIM
```

---

## Authentication

The API uses **HTTP Basic Authentication** with your API user credentials (the service account provided by your administrator). End users do not need separate credentials.

### How It Works

1. Your administrator creates an API user account with username and password
2. For each API request, provide credentials in the `Authorization` header
3. The API returns a `magicLink` in the response — a server-issued token that grants end users one-time authenticated access to the pre-filled form

### Example

```bash
curl -u "api-username:api-password" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"MeldeId":"ELIM-2026-001"}' \
  https://elim.example.com/api/elim/v1/memento
```

The response contains both the encrypted memento and a ready-to-use `magicLink` — no further credentials are needed for the end user.

See [Magic Token Link (MTL)](../../Authentication/magic-token-link.md) for details on how the server-issued token works.

---

## Core Concepts

### Disease Notification (Hospitalisierungsmeldung)

The main data structure for hospital disease reporting. Contains:
- **MeldeId**: Unique hospital report identifier
- **Patient**: Patient information
- **MedizinischeInformationen**: Medical details (onset, diagnosis date)
- **KlinischeAngaben**: Clinical information (hospitalization, death, intensive care)
- **MeldendeEinrichtung**: Reporting facility
- **Arzt**: Reporting doctor

### Memento Pattern

A **memento** is an encrypted, URL-safe string that contains form pre-fill data:
- Generated from JSON disease notification data
- Encrypted with AES-256-GCM using your API user's KEK
- Tamper-proof and URL-safe
- Typical size: 500–2000 characters
- Used as query parameter: `?m={memento}`

### Magic Token Link (MTL)

The `magicLink` field in the API response is a server-issued, time-limited URL that:
- Authenticates the end user automatically (no login page)
- Redirects to `/elim/forms/{memento}` on success or specifically configured form routes
- Is a **relative path** — prepend your instance host to make it absolute

```
magicLink: "/mtl/eyJ...token.../elim/forms/eyJ...memento..."

Full URL: https://elim.example.com/mtl/eyJ...token.../elim/forms/eyJ...memento..."
```

See [Magic Token Link (MTL)](../../Authentication/magic-token-link.md) for security details and token lifetime.

### Report ID

The `MeldeId` field in the Hospitalisierungsmeldung serves to correlate the report later. For checking the report status via `/reports`, the unique identifier string tracking the submission outcome is referred to as `reportId` in the API endpoints.

---

## Memento Endpoint

**Endpoint:** `POST /api/elim/v1/memento`

**Purpose:** Create encrypted memento string and magic link to pre-fill disease notification forms.

### Request Body

The endpoint accepts Hospitalisierungsmeldung data as JSON. All fields are optional for partial pre-filling.

**Minimal Example:**
```json
{}
```

**Complete Example:**
```json
{
  "MeldeId": "ELIM-2026-00123",
  "MeldeDatum": "2026-03-20",
  "Patient": {
    "Vorname": "Max",
    "Name": "Mustermann",
    "Geburtsdatum": "1980-05-15",
    "Geschlecht": "MAENNLICH",
    "Adresse": {
      "Strasse": "Musterstraße",
      "Hausnummer": "123",
      "PLZ": "12345",
      "Stadt": "Musterstadt",
      "inDeutschland": true
    },
    "Kontakt": {
      "Telefon": "+49 123 456789",
      "Email": "max.mustermann@example.com"
    }
  },
  "KlinischeAngaben": {
    "Hospitalisiert": "YES",
    "Hospitalisierung": {
      "AufnahmeAm": "2026-03-18",
      "EntlassungAm": null,
      "IntensivBehandlung": false
    }
  },
  "MeldendeEinrichtung": {
    "Name": "Universitätsklinikum Musterstadt",
    "BSNR": "123456789",
    "IK_Nummer": "987654321",
    "Adresse": {
      "Strasse": "Klinikstraße 1",
      "PLZ": "12345",
      "Stadt": "Musterstadt",
      "Land": "DE"
    }
  },
  "Arzt": {
    "Titel": "Dr.",
    "Vorname": "Anna",
    "Nachname": "Schmidt",
    "LANR": "123456789",
    "Kontakt": {
      "Telefon": "+49 123 456750"
    }
  }
}
```

### Response

Returns a JSON object containing the encrypted memento and a ready-to-use magic link:

```json
{
  "memento": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..DGG5lQvJC8OpYrCt.Xm8YR...",
  "magicLink": "/mtl/eyJ...token.../elim/forms/eyJ...memento..."
}
```

**Note:** `magicLink` is `null` if the API user has no authentication configuration that supports token generation.

---

## Report Retrieval Endpoints

After an end user submits the report via the ELIM form, the submission result is stored and made available for retrieval by the API user that created the original memento.

### GET /reports — List pending report IDs

**Endpoint:** `GET /api/elim/v1/reports`

Returns an array of `reportId` strings for reports that have been submitted to DEMIS but not yet retrieved. Reports disappear from this list once retrieved without `?peek=true`.

**Request:**
```bash
curl -u "api-user:api-pass" \
  https://elim.example.com/api/elim/v1/reports
```

**Response (200):**
```json
["ELIM-2026-00123", "ELIM-2026-00124"]
```

---

### GET /reports/{reportId} — Retrieve report result

**Endpoint:** `GET /api/elim/v1/reports/{reportId}`

Returns the full result for a submitted report, including the RKI receipt PDF for successful submissions.

**Parameters:**

| Parameter | In | Required | Description |
|-----------|-----|----------|-------------|
| `reportId` | path | Yes | The report ID from the submission |
| `peek` | query | No | `true` = non-destructive read. Default: `false` |

**Non-destructive peek:**
```bash
curl -u "api-user:api-pass" \
  "https://elim.example.com/api/elim/v1/reports/ELIM-2026-00123?peek=true"
```

**Response (200 — SUCCESS):**
```json
{
  "reportId": "ELIM-2026-00123",
  "status": "SUCCESS",
  "module": "ELIM",
  "diseaseCode": "Influenza",
  "description": "Hospitalisierungsmeldung Influenza",
  "submittedAt": "2026-03-20T14:32:00Z",
  "receiptPdf": "JVBERi0xLjQK...",
  "failureReason": null
}
```

**Response (200 — FAILURE):**
```json
{
  "reportId": "ELIM-2026-00456",
  "status": "FAILURE",
  "module": "ELIM",
  "diseaseCode": "Influenza",
  "description": "Hospitalisierungsmeldung Influenza",
  "submittedAt": "2026-03-20T15:10:00Z",
  "receiptPdf": null,
  "failureReason": "RKI Response Code: 422"
}
```

### Polling pattern

Reports become available asynchronously — the end user must complete and submit the form first. Poll periodically:

```bash
# Poll for new reports every 60 seconds
while true; do
  IDS=$(curl -s -u "api-user:api-pass" \
    "https://elim.example.com/api/elim/v1/reports" | jq -r '.[]')

  for ID in $IDS; do
    RESULT=$(curl -s -u "api-user:api-pass" \
      "https://elim.example.com/api/elim/v1/reports/$ID")
    STATUS=$(echo "$RESULT" | jq -r '.status')
    echo "$ID: $STATUS"

    if [ "$STATUS" = "SUCCESS" ]; then
      echo "$RESULT" | jq -r '.receiptPdf' | base64 --decode > "${ID}.pdf"
    fi
  done

  sleep 60
done
```

---

## Complete Workflow Examples

### Workflow 1: Complete external integration

```bash
#!/bin/bash
# Complete workflow for KIS/hospital system integration with ELIM

BASE_URL="https://elim.example.com"
API_USER="kis-api"
API_PASS="api-secret"

# Step 1: Create memento and get magic link
echo "Creating memento via API..."
RESPONSE=$(curl -s -X POST \
  -u "$API_USER:$API_PASS" \
  -H "Content-Type: application/json" \
  -d '{
    "MeldeId": "ELIM-2026-00123",
    "MeldeDatum": "2026-03-20",
    "Patient": {
      "Vorname": "Max",
      "Name": "Mustermann",
      "Geburtsdatum": "1980-05-15",
      "Geschlecht": "MAENNLICH"
    },
    "MeldendeEinrichtung": {
      "Name": "Universitätsklinikum Musterstadt",
      "BSNR": "123456789"
    }
  }' \
  "$BASE_URL/api/elim/v1/memento")

MAGIC_LINK=$(echo "$RESPONSE" | jq -r '.magicLink')

if [ -z "$MAGIC_LINK" ] || [ "$MAGIC_LINK" = "null" ]; then
  echo "Error: No magic link in response"
  echo "$RESPONSE" | jq .
  exit 1
fi

# Step 2: Construct absolute URL
FORM_URL="$BASE_URL$MAGIC_LINK"

# Step 3: Deliver to end user
echo ""
echo "Form URL for end user (single-click, no login required):"
echo "$FORM_URL"
echo ""
echo "What happens when user clicks:"
echo "1. MTL token authenticates the user automatically"
echo "2. Redirects to pre-filled ELIM form"
echo "3. User reviews and submits to DEMIS"
```

---

## Error Handling

### HTTP Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid JSON or validation error (memento endpoint) |
| 401 | Unauthorized | Missing or invalid API credentials |
| 404 | Not Found | Report ID does not exist or belongs to a different user |
| 410 | Gone | Report was already retrieved (use `?peek=true` to avoid) |
| 500 | Internal Server Error | Server error (contact support) |

### Validation Errors

If the request data is invalid, you'll receive a 400 Bad Request with details:

Response (400):
```json
{
  "errors": ["MeldeDatum must be a valid date"]
}
```

---

## Reference

### API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/elim/v1/memento` | Create encrypted memento and magic link for form pre-fill |
| GET | `/api/elim/v1/reports` | List pending (unpolled) report IDs |
| GET | `/api/elim/v1/reports/{reportId}` | Retrieve full report result (status, receipt PDF) |

### OpenAPI Specification

Interactive API documentation (Swagger UI):
```
https://your-instance/api/docs/swagger-ui/index.html?urls.primaryName=ELIM
```

### Date Format

All dates use ISO 8601 format:
```
YYYY-MM-DD
Example: 2026-03-20
```

### Security Notes

**Memento Encryption:**
- Mementos are encrypted with AES-256-GCM using your API user's KEK
- Each memento is unique even for identical data
- Tampering is detected and rejected

**Magic Link Security:**
- Tokens are server-issued and signed
- Each token is single-use and time-limited

**Best Practices:**
- ✓ Generate the magic link close to the time of sending
- ✗ Do not expose mementos or magic links to unauthorized users
- ✗ Do not reuse magic links; generate a fresh one for each workflow run

---

**Document Version:** 0.1.0
**Last Updated:** 2026-03-25
**API Version:** v1
