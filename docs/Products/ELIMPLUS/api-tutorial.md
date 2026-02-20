# ELIM+ API Integration Guide

A practical guide for integration partners using the ELIM+ (Laboratory Reporting) API.

**Version:** 0.1.2
**Last Updated:** 2026-02-20

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

The ELIM+ API enables laboratory information systems (KIS) to pre-fill laboratory reporting forms for notifiable diseases in Germany (DEMIS integration). This API allows integration partners to:

- **Create form mementos** to generate pre-filled form URLs from laboratory data
- **Retrieve report results** after end users submit forms to DEMIS
- **Support 4 disease types**: Influenza, RSV, Norovirus, SARS-CoV-2
- **Enable user review** before submission to public health authorities

### Use Case

ELIM+ solves a common integration pattern:

1. **Laboratory system (KIS)** has complete test results but wants users to review before DEMIS submission
2. **System calls API** with laboratory report data as JSON
3. **API returns** an encrypted memento string **and a ready-to-use `magicLink` URL**
4. **System sends the `magicLink`** to the end user (email, portal, etc.)
5. **User clicks the link** — authenticated, lands on ELIM+ index with pre-filled data
6. **User selects disease form, reviews, and submits** to DEMIS

```
KIS / Laboratory System
    ↓
[1] POST /api/elimplus/v1/memento  (API user credentials)
    ↓
[2] Receives { "memento": "...", "magicLink": "/mtl/.../?m=..." }
    ↓
[3] Constructs absolute URL: https://your-instance + magicLink
    ↓
[4] Delivers URL to end user (email, portal link, SMS, etc.)
    ↓
End User
    ↓
[5] Clicks link → authenticated via MTL token
    → lands on /elimplus/?m={memento}
    ↓
[6] Selects disease form → reviews pre-filled data → submits to DEMIS
    ↓
KIS / Laboratory System (asynchronous)
    ↓
[7] GET /api/elimplus/v1/reports  → list of pending reportIds
[8] GET /api/elimplus/v1/reports/{reportId}  → full result + receipt PDF
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
- **Base URL**: Your ELIM instance URL (e.g., `https://elim.example.com`)

That's it. End users do **not** need separate credentials — the `magicLink` in the API response handles their authentication automatically.

### API Versioning

All endpoints are versioned under `/api/elimplus/v1/`.

### OpenAPI Specification

The complete OpenAPI specification is available at:
```
https://your-instance/api/docs/swagger-ui/index.html?urls.primaryName=ELIM+
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
  -d '{"reportId":"LAB-2026-001"}' \
  https://elim.example.com/api/elimplus/v1/memento
```

The response contains both the encrypted memento and a ready-to-use `magicLink` — no further credentials are needed for the end user.

See [Magic Token Link (MTL)](../../Authentication/magic-token-link.md) for details on how the server-issued token works.

---

## Core Concepts

### Laboratory Report (Labormeldung)

The main data structure for notifiable disease reporting. Contains:
- **reportId** (required): Unique laboratory report identifier
- **Patient**: Patient information (standard with full identification, or anonymous with limited data for privacy)
- **MeldendeEinrichtung**: Reporting facility (laboratory)
- **MeldendePerson**: Reporting person
- **EinsendendeEinrichtung**: Sending facility (e.g., hospital that ordered the test)
- **Krankheit**: Disease-specific data (Influenza, RSV, Norovirus, or SARS-CoV-2)
- **MeldungsDatum**: Report date
- **MeldungsVerweisId**: Reference ID for linking corrections or follow-up reports

### Memento Pattern

A **memento** is an encrypted, URL-safe string that contains form pre-fill data:
- Generated from JSON laboratory report data
- Encrypted with AES-256-GCM using your API user's KEK
- Tamper-proof and URL-safe
- Typical size: 500–2000 characters
- Used as query parameter: `?m={memento}`

**Important:** The memento contains generic pre-fill data (patient info, dates, report IDs) — not disease-specific data. The user selects the disease on the ELIM+ index page. The same memento applies to all disease forms.

### Magic Token Link (MTL)

The `magicLink` field in the API response is a server-issued, time-limited URL that:
- Authenticates the end user automatically (no login page)
- Redirects to `/elimplus/?m={memento}` on success
- Is a **relative path** — prepend your instance host to make it absolute

```
magicLink: "/mtl/eyJ...token.../elimplus/?m=eyJ...memento..."

Full URL: https://elim.example.com/mtl/eyJ...token.../elimplus/?m=eyJ...memento..."
```

See [Magic Token Link (MTL)](../../Authentication/magic-token-link.md) for security details and token lifetime.

### Patient Types

ELIM+ supports two patient types for privacy protection:

**Standard Patient** (`IsAnonym: false`):
- Full identification with name, complete birthdate, full address, and contact information
- Used for typical laboratory reporting where patient identity is available
- Structure: `Patient.Standard` contains Name, Geschlecht, Geburtsdatum (YYYY-MM-DD), Adresse, Kontakt

**Anonymous Patient** (`IsAnonym: true`):
- Limited data to protect patient privacy
- No name or contact information
- Birth month/year only (not full date): `GeburtsmonatJahr` in YYYY-MM format
- Limited address with only postal code and country (no street, city, or identifying details)
- Structure: `Patient.Anonym` contains Geschlecht, GeburtsmonatJahr, Adresse (PLZ and Land only)

**When to use:**
- Use **Standard** for normal reporting when patient identity is available
- Use **Anonymous** when patient wishes to remain anonymous or local regulations require privacy protection

### Disease Types

ELIM+ supports 4 notifiable diseases:

| Disease | Code | Description |
|---------|------|-------------|
| Influenza | `Influenza` | Influenza virus detection (PCR) |
| RSV | `Rsv` | Respiratory Syncytial Virus |
| Norovirus | `Norovirus` | Norovirus RNA detection |
| SARS-CoV-2 | `Sarscov2` | COVID-19 laboratory detection |

### Report ID

The `reportId` field in the Labormeldung serves a dual purpose:

1. **Form pre-fill**: It's embedded in the memento and displayed in the pre-filled form for the end user to review
2. **Report retrieval key**: After the end user submits to DEMIS, the same `reportId` is used to retrieve the submission result via `GET /reports/{reportId}`

**Important:** Use a stable, unique ID per laboratory report. The `reportId` must be unique per API user — submitting a second report with the same `reportId` will be rejected.

### Form Workflow

1. User opens the magic link → lands on ELIM+ index: `/elimplus/`
2. User selects a disease form (Influenza, RSV, Norovirus, SARS-CoV-2)
3. System routes to disease-specific form: `/elimplus/{Disease}/`
4. Form is pre-filled via memento parameter: `/elimplus/{Disease}/?m={memento}`
5. User reviews, corrects if needed, submits to DEMIS
6. After successful submission, the result is available via `GET /reports/{reportId}`

---

## Memento Endpoint

**Endpoint:** `POST /api/elimplus/v1/memento`

**Purpose:** Create encrypted memento string and magic link to pre-fill laboratory reporting forms.

### Request Body

The endpoint accepts laboratory report data as JSON. Only `reportId` is required; all other fields are optional.

**Minimal Example:**
```json
{
  "reportId": "LAB-2026-00001"
}
```

**Complete Example:**
```json
{
  "reportId": "LAB-2026-00123",
  "KrankheitsCode": "J09",
  "MeldungsDatum": "2026-02-20",
  "MeldungsVerweisId": "MELD-REF-2026-00001",
  "Krankheit": {
    "Influenza": {},
    "Rsv": null,
    "Norovirus": null,
    "Sarscov2": null
  },
  "Patient": {
    "IsAnonym": false,
    "Standard": {
      "Name": {
        "Vorname": "Max",
        "Nachname": "Mustermann"
      },
      "Geschlecht": "MAENNLICH",
      "Geburtsdatum": "1980-05-15",
      "Adresse": {
        "Strasse": "Musterstraße 123",
        "PLZ": "12345",
        "Stadt": "Musterstadt"
      },
      "Kontakt": {
        "Telefon": "+49 123 456789",
        "Email": "max.mustermann@example.com"
      }
    }
  },
  "MeldendeEinrichtung": {
    "EinrichtungsName": "Universitätsklinikum Musterstadt",
    "BSNR": "123456789",
    "Adresse": {
      "Strasse": "Klinikstraße 1",
      "PLZ": "12345",
      "Stadt": "Musterstadt"
    },
    "Kontakt": {
      "Telefon": "+49 123 456700",
      "Email": "labor@klinikum-musterstadt.de"
    }
  },
  "MeldendePerson": {
    "Name": {
      "Vorname": "Dr. Anna",
      "Nachname": "Schmidt"
    },
    "Kontakt": {
      "Telefon": "+49 123 456750",
      "Email": "anna.schmidt@klinikum-musterstadt.de"
    }
  },
  "EinsendendeEinrichtung": {
    "EinrichtungsName": "Labor für Medizinische Mikrobiologie",
    "Adresse": {
      "Strasse": "Laborweg 5",
      "PLZ": "12345",
      "Stadt": "Musterstadt"
    },
    "Kontakt": {
      "Telefon": "+49 123 456800",
      "Email": "kontakt@labor-mikrobiologie.de"
    }
  }
}
```

### Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reportId` | string | **Yes** | Unique laboratory report identifier |
| `KrankheitsCode` | string | No | Disease code (e.g., ICD-10) |
| `MeldungsDatum` | date (YYYY-MM-DD) | No | Report date |
| `MeldungsVerweisId` | string | No | Reference ID for linking corrections or follow-up reports |
| `Krankheit.*` | object | No | Disease-specific data (only one should be populated) |
| `Patient.IsAnonym` | boolean | No | Patient type: false = standard (default), true = anonymous |
| `Patient.Standard.*` | object | No | Standard patient with full identification (use when IsAnonym=false) |
| `Patient.Standard.Name.*` | object | No | Patient name (Vorname, Nachname) |
| `Patient.Standard.Geschlecht` | enum | No | Gender (see enum values below) |
| `Patient.Standard.Geburtsdatum` | date (YYYY-MM-DD) | No | Full date of birth |
| `Patient.Standard.Adresse.*` | object | No | Full address (Strasse, PLZ, Stadt, Land) |
| `Patient.Standard.Kontakt.*` | object | No | Contact information (Telefon, Email, Fax) |
| `Patient.Anonym.*` | object | No | Anonymous patient with limited data (use when IsAnonym=true) |
| `Patient.Anonym.Geschlecht` | enum | No | Gender (see enum values below) |
| `Patient.Anonym.GeburtsmonatJahr` | string (YYYY-MM) | No | Birth month/year only (not full date for privacy) |
| `Patient.Anonym.Adresse.PLZ` | string | No | Postal code only |
| `Patient.Anonym.Adresse.Land` | string | No | Country only |
| `MeldendeEinrichtung.*` | object | No | Reporting facility (laboratory) |
| `MeldendePerson.*` | object | No | Reporting person |
| `EinsendendeEinrichtung.*` | object | No | Sending facility |

**Note:** `Geschlecht` enum values:
- `NASK` — Not asked (nicht gefragt)
- `ASKU` — Asked but unknown (gefragt, aber unbekannt)
- `MAENNLICH` — Male
- `WEIBLICH` — Female
- `DIVERS` — Diverse
- `UNBESTIMMT` — Unspecified

### Response

Returns a JSON object containing the encrypted memento and a ready-to-use magic link:

```json
{
  "memento": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..DGG5lQvJC8OpYrCt.Xm8YR...",
  "magicLink": "/mtl/eyJ...token.../elimplus/?m=eyJ...memento..."
}
```

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `memento` | string | No | Encrypted, URL-safe string containing laboratory report data. Use as `?m={memento}` query parameter. |
| `magicLink` | string | Yes | Relative URL for authenticated single-click access. Prepend your instance host: `https://your-instance + magicLink` |

**Note:** `magicLink` is `null` if the API user has no authentication configuration that supports token generation. In practice this should not occur for properly configured API users.

### Quick Reference

**Get the magic link and construct the full URL:**

```bash
RESPONSE=$(curl -s -X POST \
  -u "api-user:api-pass" \
  -H "Content-Type: application/json" \
  -d '{"reportId":"LAB-2026-001"}' \
  https://elim.example.com/api/elimplus/v1/memento)

MAGIC_LINK=$(echo "$RESPONSE" | jq -r '.magicLink')

# Construct absolute URL
FORM_URL="https://elim.example.com$MAGIC_LINK"
echo "Send to user: $FORM_URL"
```

---

## Report Retrieval Endpoints

After an end user submits a laboratory report via the ELIM+ form, the submission result is stored and made available for retrieval by the API user that created the original memento.

### GET /reports — List pending report IDs

**Endpoint:** `GET /api/elimplus/v1/reports`

Returns an array of `reportId` strings for reports that have been submitted to DEMIS but not yet retrieved (unpolled). Reports disappear from this list once retrieved without `?peek=true`.

**Request:**
```bash
curl -u "api-user:api-pass" \
  https://elim.example.com/api/elimplus/v1/reports
```

**Response (200):**
```json
["LAB-2026-00123", "LAB-2026-00124"]
```

An empty array `[]` means no submissions are pending retrieval.

---

### GET /reports/{reportId} — Retrieve report result

**Endpoint:** `GET /api/elimplus/v1/reports/{reportId}`

Returns the full result for a submitted report, including the RKI receipt PDF for successful submissions.

**Parameters:**

| Parameter | In | Required | Description |
|-----------|-----|----------|-------------|
| `reportId` | path | Yes | The report ID from the original Labormeldung |
| `peek` | query | No | `true` = non-destructive read (report remains pending). Default: `false` |

**Default (destructive) read:**
```bash
curl -u "api-user:api-pass" \
  https://elim.example.com/api/elimplus/v1/reports/LAB-2026-00123
```

**Non-destructive peek:**
```bash
curl -u "api-user:api-pass" \
  "https://elim.example.com/api/elimplus/v1/reports/LAB-2026-00123?peek=true"
```

**Response (200 — SUCCESS):**
```json
{
  "reportId": "LAB-2026-00123",
  "status": "SUCCESS",
  "module": "ELIMPLUS",
  "diseaseCode": "Influenza",
  "description": "Labormeldung Influenza",
  "submittedAt": "2026-02-20T14:32:00Z",
  "receiptPdf": "JVBERi0xLjQK...",
  "failureReason": null
}
```

**Response (200 — FAILURE):**
```json
{
  "reportId": "LAB-2026-00456",
  "status": "FAILURE",
  "module": "ELIMPLUS",
  "diseaseCode": "Rsv",
  "description": "Labormeldung Rsv",
  "submittedAt": "2026-02-20T15:10:00Z",
  "receiptPdf": null,
  "failureReason": "RKI Response Code: 422"
}
```

**ReportResult fields:**

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `reportId` | string | No | The original report ID |
| `status` | enum | No | `SUCCESS` or `FAILURE` |
| `module` | string | No | Always `"ELIMPLUS"` |
| `diseaseCode` | string | Yes | Disease identifier (e.g., `"Influenza"`, `"Rsv"`) |
| `description` | string | Yes | Human-readable description (e.g., `"Labormeldung Influenza"`) |
| `submittedAt` | date-time | No | ISO 8601 timestamp of DEMIS submission |
| `receiptPdf` | string | Yes | Base64-encoded RKI receipt PDF (SUCCESS only) |
| `failureReason` | string | Yes | Error message (FAILURE only) |

**Status codes:**

| Code | Meaning |
|------|---------|
| 200 | Report found and returned |
| 401 | Unauthorized — check credentials |
| 404 | Report not found or belongs to a different user |
| 410 | Gone — report was already retrieved (use `?peek=true` to avoid) |

### Extracting the receipt PDF

The `receiptPdf` field is a base64-encoded PDF. To save it:

```bash
RESPONSE=$(curl -s -u "api-user:api-pass" \
  "https://elim.example.com/api/elimplus/v1/reports/LAB-2026-00123?peek=true")

# Check status first
STATUS=$(echo "$RESPONSE" | jq -r '.status')

if [ "$STATUS" = "SUCCESS" ]; then
  echo "$RESPONSE" | jq -r '.receiptPdf' | base64 --decode > receipt-LAB-2026-00123.pdf
  echo "Receipt saved"
else
  echo "Submission failed: $(echo "$RESPONSE" | jq -r '.failureReason')"
fi
```

Or use the provided script:
```bash
./scripts/elimplus-get-report.sh LAB-2026-00123 --save-pdf receipt.pdf
```

### Polling pattern

Reports become available asynchronously — the end user must complete and submit the form first. Poll periodically:

```bash
# Poll for new reports every 60 seconds
while true; do
  IDS=$(curl -s -u "api-user:api-pass" \
    "https://elim.example.com/api/elimplus/v1/reports" | jq -r '.[]')

  for ID in $IDS; do
    RESULT=$(curl -s -u "api-user:api-pass" \
      "https://elim.example.com/api/elimplus/v1/reports/$ID")
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
# Complete workflow for KIS/laboratory system integration with ELIM+

BASE_URL="https://elim.example.com"
API_USER="lab-api"
API_PASS="api-secret"

# Step 1: Create memento and get magic link
echo "Creating memento via API..."
RESPONSE=$(curl -s -X POST \
  -u "$API_USER:$API_PASS" \
  -H "Content-Type: application/json" \
  -d '{
    "reportId": "LAB-2026-00123",
    "KrankheitsCode": "J09",
    "MeldungsDatum": "2026-02-20",
    "Patient": {
      "IsAnonym": false,
      "Standard": {
        "Name": {"Vorname": "Max", "Nachname": "Mustermann"},
        "Geschlecht": "MAENNLICH",
        "Geburtsdatum": "1980-05-15"
      }
    },
    "MeldendeEinrichtung": {
      "EinrichtungsName": "Universitätsklinikum Musterstadt",
      "BSNR": "123456789"
    }
  }' \
  "$BASE_URL/api/elimplus/v1/memento")

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
echo "2. Redirects to /elimplus/?m={memento}"
echo "3. User selects disease form (e.g., Influenza)"
echo "4. Form is pre-filled, user reviews and submits to DEMIS"
```

---

### Workflow 2: Email with pre-filled form link

```bash
#!/bin/bash
# Create memento and email magic link to laboratory technician

BASE_URL="https://elim.example.com"
API_USER="kis-api-user"
API_PASS="api-password"

# Create memento for RSV report
MAGIC_LINK=$(curl -s -X POST -u "$API_USER:$API_PASS" \
  -H "Content-Type: application/json" \
  -d '{
    "reportId": "LAB-2026-00456",
    "Krankheit": {"Rsv": {}},
    "Patient": {
      "IsAnonym": false,
      "Standard": {
        "Name": {"Vorname": "Anna", "Nachname": "Schmidt"},
        "Geburtsdatum": "1990-03-20"
      }
    }
  }' \
  "$BASE_URL/api/elimplus/v1/memento" | jq -r '.magicLink')

# Construct absolute URL
FORM_URL="$BASE_URL$MAGIC_LINK"

# Email the link (example using mail command)
echo "Please review and submit the laboratory report: $FORM_URL" | \
  mail -s "Laboratory Report Ready for Review (LAB-2026-00456)" \
    technician@hospital.example.com

echo "Email sent with single-click authenticated link"
echo "Note: The link expires — generate close to the time of sending"
```

---

### Workflow 3: Batch form generation from CSV

```bash
#!/bin/bash
# Generate multiple pre-filled form links from laboratory results CSV

BASE_URL="https://elim.example.com"
API_USER="kis-batch-user"
API_PASS="api-password"

# CSV format: reportId,disease,patientFirstName,patientLastName,dob
# Example: LAB-2026-001,Influenza,Max,Mustermann,1980-05-15

while IFS=, read -r report_id disease first_name last_name dob; do
  # Skip header line
  if [ "$report_id" = "reportId" ]; then
    continue
  fi

  # Prepare JSON
  LAB_DATA=$(jq -n \
    --arg reportId "$report_id" \
    --arg disease "$disease" \
    --arg vorname "$first_name" \
    --arg nachname "$last_name" \
    --arg dob "$dob" \
    '{
      reportId: $reportId,
      Krankheit: {($disease): {}},
      Patient: {
        IsAnonym: false,
        Standard: {
          Name: {Vorname: $vorname, Nachname: $nachname},
          Geburtsdatum: $dob
        }
      }
    }')

  # Create memento and get magic link
  MAGIC_LINK=$(curl -s -X POST -u "$API_USER:$API_PASS" \
    -H "Content-Type: application/json" \
    -d "$LAB_DATA" \
    "$BASE_URL/api/elimplus/v1/memento" | jq -r '.magicLink')

  # Output report ID and absolute URL
  echo "$report_id,$BASE_URL$MAGIC_LINK"
done < lab_results.csv > form_urls.csv

echo "Generated form URLs saved to form_urls.csv"
echo "Each URL provides single-click authenticated access to ELIM+ index"
```

---

### Workflow 4: QR code for mobile access

```bash
#!/bin/bash
# Create memento and generate QR code for mobile scanning

BASE_URL="https://elim.example.com"
API_USER="kis-api"
API_PASS="api-password"

# Create memento and get magic link
MAGIC_LINK=$(curl -s -X POST -u "$API_USER:$API_PASS" \
  -H "Content-Type: application/json" \
  -d '{
    "reportId": "LAB-2026-00789",
    "Krankheit": {"Sarscov2": {}},
    "Patient": {
      "IsAnonym": false,
      "Standard": {
        "Name": {"Vorname": "Thomas", "Nachname": "Müller"},
        "Geburtsdatum": "1975-08-12"
      }
    }
  }' \
  "$BASE_URL/api/elimplus/v1/memento" | jq -r '.magicLink')

# Construct absolute URL
FORM_URL="$BASE_URL$MAGIC_LINK"

# Generate QR code (requires qrencode tool)
echo "$FORM_URL" | qrencode -o lab-report-qr.png

echo "QR code saved to lab-report-qr.png"
echo "Scan with mobile device for single-click authenticated access"
```

---

### Workflow 5: Anonymous patient reporting

```bash
#!/bin/bash
# Create memento for anonymous patient (privacy protection)

BASE_URL="https://elim.example.com"
API_USER="kis-api"
API_PASS="api-password"

# Create memento with anonymous patient data
MAGIC_LINK=$(curl -s -X POST -u "$API_USER:$API_PASS" \
  -H "Content-Type: application/json" \
  -d '{
    "reportId": "LAB-2026-00999",
    "KrankheitsCode": "J09",
    "MeldungsDatum": "2026-02-20",
    "Krankheit": {"Influenza": {}},
    "Patient": {
      "IsAnonym": true,
      "Anonym": {
        "Geschlecht": "MAENNLICH",
        "GeburtsmonatJahr": "1985-06",
        "Adresse": {
          "PLZ": "12345",
          "Land": "Deutschland"
        }
      }
    },
    "MeldendeEinrichtung": {
      "EinrichtungsName": "Universitätsklinikum Musterstadt",
      "BSNR": "123456789"
    }
  }' \
  "$BASE_URL/api/elimplus/v1/memento" | jq -r '.magicLink')

FORM_URL="$BASE_URL$MAGIC_LINK"

echo "Anonymous patient URL (single-click authenticated access):"
echo "$FORM_URL"
echo ""
echo "Note: Form contains no name, contact info, or full address"
echo "Only birth month/year, postal code, and country are included"
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

```bash
curl -X POST -u "api-user:api-pass" \
  -H "Content-Type: application/json" \
  -d '{"invalid":"data"}' \
  https://elim.example.com/api/elimplus/v1/memento
```

Response (400):
```json
{
  "errors": ["reportId must not be null"]
}
```

### Date Format Validation

Dates must be in ISO 8601 format (YYYY-MM-DD):

```bash
# Invalid date format
curl -X POST -u "api-user:api-pass" \
  -H "Content-Type: application/json" \
  -d '{"reportId":"LAB-001","MeldungsDatum":"08.12.2026"}' \
  https://elim.example.com/api/elimplus/v1/memento
```

Response (400):
```json
{
  "errors": ["MeldungsDatum must be a valid date in format YYYY-MM-DD"]
}
```

### Handle Errors in Scripts

```bash
#!/bin/bash
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  -u "$API_USER:$API_PASS" \
  -H "Content-Type: application/json" \
  -d "$LAB_DATA" \
  "$BASE_URL/api/elimplus/v1/memento")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -1)

if [ "$HTTP_CODE" -eq 200 ]; then
  MAGIC_LINK=$(echo "$BODY" | jq -r '.magicLink')
  FORM_URL="$BASE_URL$MAGIC_LINK"
  echo "Success: $FORM_URL"
elif [ "$HTTP_CODE" -eq 400 ]; then
  echo "Validation error:"
  echo "$BODY" | jq -r '.errors[]'
  exit 1
elif [ "$HTTP_CODE" -eq 401 ]; then
  echo "Authentication failed — check API credentials"
  exit 1
else
  echo "Error: HTTP $HTTP_CODE"
  echo "$BODY"
  exit 1
fi
```

---

## Reference

### API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/elimplus/v1/memento` | Create encrypted memento and magic link for form pre-fill |
| GET | `/api/elimplus/v1/reports` | List pending (unpolled) report IDs |
| GET | `/api/elimplus/v1/reports/{reportId}` | Retrieve full report result (status, receipt PDF) |

### OpenAPI Specification

Interactive API documentation (Swagger UI):
```
https://your-instance/api/docs/swagger-ui/index.html?urls.primaryName=ELIM+
```

### Disease Routes

| Disease | API Code | Form Route |
|---------|----------|------------|
| Influenza | `Influenza` | `/elimplus/Influenza/` |
| RSV | `Rsv` | `/elimplus/Rsv/` |
| Norovirus | `Norovirus` | `/elimplus/Norovirus/` |
| SARS-CoV-2 | `Sarscov2` | `/elimplus/Sarscov2/` |

**Entry point:** Always use `/elimplus/` — the index page where users select their disease form.

### Date Format

All dates use ISO 8601 format:
```
YYYY-MM-DD
Example: 2026-02-20
```

### Gender Enum Values

| Value | Description |
|-------|-------------|
| `NASK` | Not asked (nicht gefragt) |
| `ASKU` | Asked but unknown (gefragt, aber unbekannt) |
| `MAENNLICH` | Male (männlich) |
| `WEIBLICH` | Female (weiblich) |
| `DIVERS` | Diverse |
| `UNBESTIMMT` | Unspecified (unbestimmt) |

### Security Notes

**Memento Encryption:**
- Mementos are encrypted with AES-256-GCM using your API user's KEK (Key Encryption Key)
- Each memento is unique even for identical data (includes random IV)
- Mementos cannot be decrypted without the correct API user credentials
- Tampering is detected and rejected

**Magic Link Security:**
- Tokens are server-issued and signed — they cannot be forged
- Each token is single-use and time-limited
- The target URL (`/elimplus/`) is encoded inside the encrypted token

**Best Practices:**
- ✓ Generate the magic link close to the time of sending (token is time-limited)
- ✓ Mementos are safe to pass via URL parameters and can be logged or stored
- ✗ Do not expose mementos or magic links to unauthorized users (they contain sensitive patient data)
- ✗ Do not reuse magic links; generate a fresh one for each workflow run

**Data Minimization:**
- Only include data that's actually needed for the form
- Empty/null fields don't bloat the memento (they're omitted)
- Minimal mementos result in shorter, more manageable URLs

### Support

For technical support or questions about the ELIM+ API:
- Contact your system administrator
- Refer to the OpenAPI specification for detailed schema documentation
- Check integration test examples in `src/integration-test/kotlin/de/vertama/elimplus/`

### Related Documentation

- [Magic Token Link (MTL)](../../Authentication/magic-token-link.md) — How server-issued authentication tokens work

---

**Document Version:** 0.1.2
**Last Updated:** 2026-02-20
**API Version:** v1
