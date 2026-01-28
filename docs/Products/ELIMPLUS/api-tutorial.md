# ELIM+ API Integration Guide

A practical guide for integration partners using the ELIM+ (Laboratory Reporting) API.

**Version:** 0.1.0
**Last Updated:** 2026-01-28

---

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [Core Concepts](#core-concepts)
4. [Memento Endpoint](#memento-endpoint)
5. [Complete Workflow Examples](#complete-workflow-examples)
6. [Error Handling](#error-handling)
7. [Reference](#reference)

---

## Introduction

The ELIM+ API enables laboratory information systems (KIS) to pre-fill laboratory reporting forms for notifiable diseases in Germany (DEMIS integration). This API allows integration partners to:

- **Create form mementos** to generate pre-filled form URLs from laboratory data
- **Support 4 disease types**: Influenza, RSV, Norovirus, SARS-CoV-2
- **Enable user review** before submission to public health authorities

### Use Case

ELIM+ solves a common integration pattern:

1. **Laboratory system (KIS)** has complete test results but wants users to review before DEMIS submission
2. **System calls API** with laboratory report data as JSON
3. **API returns** encrypted, URL-safe string (the "memento")
4. **System constructs URL** with memento parameter
5. **Users open URL** and see pre-filled form ready to review and submit

**Benefits:**
- No direct submission required - users maintain control
- Form validation happens in browser (immediate feedback)
- Users can correct or supplement data before sending
- Encrypted mementos are tamper-proof

### Prerequisites

Before using the API, you need:
- **API User Credentials**: Username and password provided by your administrator
- **Base URL**: Your ELIM instance URL (e.g., `https://elim.example.com`)
- **Disease type**: One of Influenza, RSV, Norovirus, SARS-CoV-2

### API Versioning

All endpoints are versioned under `/api/elimplus/v1/`.

### OpenAPI Specification

The complete OpenAPI specification is available at:
```
https://your-instance/api/docs/swagger-ui/index.html?urls.primaryName=ELIM+
```

---

## Authentication

The API uses **HTTP Basic Authentication** with your API user credentials.

### How It Works

1. Your administrator creates an API user account with username and password
2. For each API request, provide credentials in the `Authorization` header
3. Internally, the system derives a KEK (Key Encryption Key) from your password for cryptographic operations

### Example

```bash
curl -u "username:password" \
  https://elim.example.com/api/elimplus/v1/memento
```

Or explicitly with Authorization header:

```bash
# Encode credentials (username:password in base64)
echo -n "username:password" | base64
# Result: dXNlcm5hbWU6cGFzc3dvcmQ=

curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"reportId":"LAB-2024-001"}' \
  https://elim.example.com/api/elimplus/v1/memento
```

---

## Core Concepts

### Laboratory Report (Labormeldung)

The main data structure for notifiable disease reporting. Contains:
- **reportId** (required): Unique laboratory report identifier
- **Patient**: Name, gender, birthdate, address, contact
- **MeldendeEinrichtung**: Reporting facility (laboratory)
- **MeldendePerson**: Reporting person
- **EinsendendeEinrichtung**: Sending facility (e.g., hospital that ordered the test)
- **Krankheit**: Disease-specific data (Influenza, RSV, Norovirus, or SARS-CoV-2)
- **MeldungsDatum**: Report date

### Memento Pattern

A **memento** is an encrypted, URL-safe string that contains form data:
- Generated from JSON laboratory report data
- Encrypted with AES-256-GCM using your API user's KEK
- Tamper-proof and URL-safe
- Typical size: 500-2000 characters
- Used as query parameter: `?m={memento}`

### Disease Types

ELIM+ supports 4 notifiable diseases:

| Disease | Code | Description |
|---------|------|-------------|
| Influenza | `Influenza` | Influenza virus detection (PCR) |
| RSV | `Rsv` | Respiratory Syncytial Virus |
| Norovirus | `Norovirus` | Norovirus RNA detection |
| SARS-CoV-2 | `Sarscov2` | COVID-19 laboratory detection |

### Form Workflow

1. User selects disease from index page: `/elimplus/index`
2. System routes to disease-specific form: `/elim/r/{Disease}/`
3. Form can be pre-filled via memento parameter: `/elim/r/{Disease}/?m={memento}`
4. User reviews, corrects if needed, submits to DEMIS

**Note:** Form controllers currently use legacy `/elim/r/` routes during transition to `/elimplus/` structure.

---

## Memento Endpoint

**Endpoint:** `POST /api/elimplus/v1/memento`

**Purpose:** Create encrypted memento string to pre-fill laboratory reporting forms.

### Request Body

The endpoint accepts laboratory report data as JSON. Only `reportId` is required; all other fields are optional.

**Minimal Example:**
```json
{
  "reportId": "LAB-2024-00001"
}
```

**Complete Example:**
```json
{
  "reportId": "LAB-2024-00123",
  "KrankheitsCode": "J09",
  "MeldungsDatum": "2024-12-08",
  "Krankheit": {
    "Influenza": {},
    "Rsv": null,
    "Norovirus": null,
    "Sarscov2": null
  },
  "Patient": {
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
| `Krankheit.*` | object | No | Disease-specific data (only one should be populated) |
| `Patient.Name.*` | object | No | Patient name (Vorname, Nachname) |
| `Patient.Geschlecht` | enum | No | Gender: NASK, ASKU, MAENNLICH, WEIBLICH, DIVERS, UNBESTIMMT |
| `Patient.Geburtsdatum` | date (YYYY-MM-DD) | No | Date of birth |
| `Patient.Adresse.*` | object | No | Patient address (Strasse, PLZ, Stadt) |
| `Patient.Kontakt.*` | object | No | Patient contact (Telefon, Email, Fax) |
| `MeldendeEinrichtung.*` | object | No | Reporting facility (laboratory) |
| `MeldendePerson.*` | object | No | Reporting person |
| `EinsendendeEinrichtung.*` | object | No | Sending facility |

**Note:** `Geschlecht` enum values:
- `NASK` - Not asked (nicht gefragt)
- `ASKU` - Asked but unknown (gefragt, aber unbekannt)
- `MAENNLICH` - Male
- `WEIBLICH` - Female
- `DIVERS` - Diverse
- `UNBESTIMMT` - Unspecified

### Response

Returns a JSON object containing the encrypted memento string:

```json
{
  "memento": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..DGG5lQvJC8OpYrCt.Xm8YR..."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `memento` | string | Encrypted, URL-safe string containing laboratory report data |

### Examples

#### Minimal request (reportId only)

```bash
curl -X POST \
  -u "user:pass" \
  -H "Content-Type: application/json" \
  -d '{"reportId":"LAB-2024-001"}' \
  https://elim.example.com/api/elimplus/v1/memento
```

Response:
```json
{
  "memento": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..abc123..."
}
```

#### Complete laboratory report

```bash
curl -X POST \
  -u "user:pass" \
  -H "Content-Type: application/json" \
  -d '{
    "reportId": "LAB-2024-00123",
    "KrankheitsCode": "J09",
    "MeldungsDatum": "2024-12-08",
    "Krankheit": {
      "Influenza": {}
    },
    "Patient": {
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
    },
    "MeldendeEinrichtung": {
      "EinrichtungsName": "Universitätsklinikum Musterstadt",
      "BSNR": "123456789"
    }
  }' \
  https://elim.example.com/api/elimplus/v1/memento
```

#### Extract memento with jq

```bash
MEMENTO=$(curl -s -X POST \
  -u "user:pass" \
  -H "Content-Type: application/json" \
  -d '{"reportId":"LAB-2024-001"}' \
  https://elim.example.com/api/elimplus/v1/memento | jq -r '.memento')

echo "Memento: $MEMENTO"
```

### Constructing Form URLs

Once you have a memento, construct a URL to pre-fill a laboratory reporting form:

**URL Pattern:**
```
https://your-instance/elim/r/{Disease}/?m={memento}
```

**Disease Routes:**

| Disease | Route |
|---------|-------|
| Influenza | `/elim/r/Influenza/` |
| RSV | `/elim/r/Rsv/` |
| Norovirus | `/elim/r/Norovirus/` |
| SARS-CoV-2 | `/elim/r/Sarscov2/` |

**Example URLs:**

```bash
# Influenza form
https://elim.example.com/elim/r/Influenza/?m=eyJhbGciOiJkaXIi...

# RSV form
https://elim.example.com/elim/r/Rsv/?m=eyJhbGciOiJkaXIi...

# Norovirus form
https://elim.example.com/elim/r/Norovirus/?m=eyJhbGciOiJkaXIi...

# SARS-CoV-2 form
https://elim.example.com/elim/r/Sarscov2/?m=eyJhbGciOiJkaXIi...
```

---

## Complete Workflow Examples

### Workflow 1: Create memento and construct form URL

```bash
#!/bin/bash
# Complete workflow: Create memento for Influenza report

BASE_URL="https://elim.example.com"
USER="your-username"
PASS="your-password"
DISEASE="Influenza"

# Step 1: Prepare laboratory report data
LAB_DATA='{
  "reportId": "LAB-2024-00123",
  "KrankheitsCode": "J09",
  "MeldungsDatum": "2024-12-08",
  "Krankheit": {
    "Influenza": {}
  },
  "Patient": {
    "Name": {"Vorname": "Max", "Nachname": "Mustermann"},
    "Geschlecht": "MAENNLICH",
    "Geburtsdatum": "1980-05-15",
    "Adresse": {
      "Strasse": "Musterstraße 123",
      "PLZ": "12345",
      "Stadt": "Musterstadt"
    }
  },
  "MeldendeEinrichtung": {
    "EinrichtungsName": "Universitätsklinikum Musterstadt",
    "BSNR": "123456789"
  }
}'

# Step 2: Create memento
echo "Creating memento..."
RESPONSE=$(curl -s -X POST \
  -u "$USER:$PASS" \
  -H "Content-Type: application/json" \
  -d "$LAB_DATA" \
  "$BASE_URL/api/elimplus/v1/memento")

# Step 3: Extract memento from response
MEMENTO=$(echo "$RESPONSE" | jq -r '.memento')

if [ -z "$MEMENTO" ] || [ "$MEMENTO" = "null" ]; then
  echo "Error: Failed to create memento"
  echo "$RESPONSE" | jq .
  exit 1
fi

# Step 4: Construct form URL
FORM_URL="$BASE_URL/elim/r/$DISEASE/?m=$MEMENTO"

echo "Success! Form URL:"
echo "$FORM_URL"
echo ""
echo "Send this URL to the authorized user to open the pre-filled form."
```

### Workflow 2: Email with pre-filled form link

```bash
#!/bin/bash
# Create memento and email link to laboratory technician

BASE_URL="https://elim.example.com"
USER="kis-api-user"
PASS="your-password"

# Create memento for RSV report
MEMENTO=$(curl -s -X POST -u "$USER:$PASS" \
  -H "Content-Type: application/json" \
  -d '{
    "reportId": "LAB-2024-00456",
    "Krankheit": {"Rsv": {}},
    "Patient": {
      "Name": {"Vorname": "Anna", "Nachname": "Schmidt"},
      "Geburtsdatum": "1990-03-20"
    }
  }' \
  "$BASE_URL/api/elimplus/v1/memento" | jq -r '.memento')

FORM_URL="$BASE_URL/elim/r/Rsv/?m=$MEMENTO"

# Email the link (example using mail command)
echo "Please review and submit the RSV laboratory report: $FORM_URL" | \
  mail -s "Laboratory Report Ready for Review (LAB-2024-00456)" \
    technician@hospital.example.com

echo "Email sent to technician@hospital.example.com"
```

### Workflow 3: Batch form generation from CSV

```bash
#!/bin/bash
# Generate multiple pre-filled forms from laboratory results CSV

BASE_URL="https://elim.example.com"
USER="kis-batch-user"
PASS="your-password"

# CSV format: reportId,disease,patientFirstName,patientLastName,dob
# Example: LAB-2024-001,Influenza,Max,Mustermann,1980-05-15

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
      Krankheit: {
        ($disease): {}
      },
      Patient: {
        Name: {vorname: $vorname, nachname: $nachname},
        Geburtsdatum: $dob
      }
    }')

  # Create memento
  MEMENTO=$(curl -s -X POST -u "$USER:$PASS" \
    -H "Content-Type: application/json" \
    -d "$LAB_DATA" \
    "$BASE_URL/api/elimplus/v1/memento" | jq -r '.memento')

  # Output report ID and form URL
  echo "$report_id,$BASE_URL/elim/r/$disease/?m=$MEMENTO"
done < lab_results.csv > form_urls.csv

echo "Generated form URLs saved to form_urls.csv"
```

### Workflow 4: Generate QR code for mobile access

```bash
#!/bin/bash
# Create memento and generate QR code for mobile scanning

BASE_URL="https://elim.example.com"
USER="your-username"
PASS="your-password"

# Create memento
MEMENTO=$(curl -s -X POST -u "$USER:$PASS" \
  -H "Content-Type: application/json" \
  -d '{
    "reportId": "LAB-2024-00789",
    "Krankheit": {"Sarscov2": {}},
    "Patient": {
      "Name": {"Vorname": "Thomas", "Nachname": "Müller"},
      "Geburtsdatum": "1975-08-12"
    }
  }' \
  "$BASE_URL/api/elimplus/v1/memento" | jq -r '.memento')

FORM_URL="$BASE_URL/elim/r/Sarscov2/?m=$MEMENTO"

# Generate QR code (requires qrencode tool)
echo "$FORM_URL" | qrencode -o lab-report-qr.png

echo "QR code saved to lab-report-qr.png"
echo "Scan with mobile device to open pre-filled form"
```

---

## Error Handling

### HTTP Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| 200 | OK | Memento created successfully |
| 400 | Bad Request | Invalid JSON or validation error |
| 401 | Unauthorized | Missing or invalid credentials |
| 500 | Internal Server Error | Server error (contact support) |

### Validation Errors

If the request data is invalid, you'll receive a 400 Bad Request with details:

```bash
curl -X POST -u "user:pass" \
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
curl -X POST -u "user:pass" \
  -H "Content-Type: application/json" \
  -d '{"reportId":"LAB-001","MeldungsDatum":"08.12.2024"}' \
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
RESPONSE=$(curl -s -X POST -u "$USER:$PASS" \
  -H "Content-Type: application/json" \
  -d "$LAB_DATA" \
  "$BASE_URL/api/elimplus/v1/memento")

# Check HTTP status
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -u "$USER:$PASS" \
  -H "Content-Type: application/json" \
  -d "$LAB_DATA" \
  "$BASE_URL/api/elimplus/v1/memento")

if [ "$HTTP_CODE" -eq 200 ]; then
  MEMENTO=$(echo "$RESPONSE" | jq -r '.memento')
  echo "Success: $MEMENTO"
elif [ "$HTTP_CODE" -eq 400 ]; then
  echo "Validation error:"
  echo "$RESPONSE" | jq -r '.errors[]'
  exit 1
elif [ "$HTTP_CODE" -eq 401 ]; then
  echo "Authentication failed - check credentials"
  exit 1
else
  echo "Error: HTTP $HTTP_CODE"
  echo "$RESPONSE"
  exit 1
fi
```

---

## Reference

### API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/elimplus/v1/memento` | Create encrypted memento for form pre-fill |

### OpenAPI Specification

Interactive API documentation (Swagger UI):
```
https://your-instance/api/docs/swagger-ui/index.html?urls.primaryName=ELIM+
```

### Disease Routes

| Disease | API Code | Form Route |
|---------|----------|------------|
| Influenza | `Influenza` | `/elim/r/Influenza/` |
| RSV | `Rsv` | `/elim/r/Rsv/` |
| Norovirus | `Norovirus` | `/elim/r/Norovirus/` |
| SARS-CoV-2 | `Sarscov2` | `/elim/r/Sarscov2/` |

### Date Format

All dates use ISO 8601 format:
```
YYYY-MM-DD
Example: 2024-12-08
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

**Best Practices:**
- ✓ Mementos are safe to pass via URL parameters
- ✓ Mementos can be safely logged or stored
- ✓ Mementos expire after a reasonable time (check instance configuration)
- ✗ Don't expose mementos to unauthorized users (they contain sensitive patient data)
- ✗ Don't reuse mementos across different diseases or reports

**Data Minimization:**
- Only include data that's actually needed for the form
- Empty/null fields don't bloat the memento (they're omitted)
- Minimal mementos result in shorter, more manageable URLs

### Support

For technical support or questions about the ELIM+ API:
- Contact your system administrator
- Refer to the OpenAPI specification for detailed schema documentation
- Check integration test examples: `src/integration-test/kotlin/de/vertama/elimplus/`

---

**Document Version:** 0.1.0
**Last Updated:** 2026-01-28
**API Version:** v1
