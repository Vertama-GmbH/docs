# ELIM+ API Integration Guide

A practical guide for integration partners using the ELIM+ (Laboratory Reporting) API.

**Version:** 0.1.0
**Last Updated:** 2026-01-29

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
- **Patient**: Patient information (standard with full identification, or anonymous with limited data for privacy)
- **MeldendeEinrichtung**: Reporting facility (laboratory)
- **MeldendePerson**: Reporting person
- **EinsendendeEinrichtung**: Sending facility (e.g., hospital that ordered the test)
- **Krankheit**: Disease-specific data (Influenza, RSV, Norovirus, or SARS-CoV-2)
- **MeldungsDatum**: Report date
- **MeldungsVerweisId**: Reference ID for linking corrections or follow-up reports

### Memento Pattern

A **memento** is an encrypted, URL-safe string that contains form data:
- Generated from JSON laboratory report data
- Encrypted with AES-256-GCM using your API user's KEK
- Tamper-proof and URL-safe
- Typical size: 500-2000 characters
- Used as query parameter: `?m={memento}`

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
  "MeldungsVerweisId": "MELD-REF-2024-00001",
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
    "MeldungsVerweisId": "MELD-REF-2024-00001",
    "Krankheit": {
      "Influenza": {}
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

### Constructing URLs for End Users

Once you have a memento, construct a URL for end users to access pre-filled forms.

#### Recommended: Basic Auth Login (BAL) Pattern

For external integrations, use the BAL endpoint for single-click authenticated access:

**URL Pattern:**
```
https://username:password@your-instance/bal/elimplus/?m={memento}
```

**Components:**
- `username:password` - End user's credentials (not API credentials)
- `/bal/` - Basic Auth Login endpoint (converts credentials to session)
- `/elimplus/` - ELIM+ product index page
- `?m={memento}` - Pre-fill data parameter

**Example:**
```bash
https://lab-tech:secret@elim.example.com/bal/elimplus/?m=eyJhbGciOiJkaXIi...
```

**User Flow:**
1. User clicks link
2. BAL authenticates with provided credentials
3. Creates secure session (no more credentials needed)
4. Redirects to `/elimplus/?m={memento}`
5. User sees ELIM+ index with pre-filled data
6. User selects disease form and submits

**Benefits:**
- ✅ Single-click access (no login page)
- ✅ Proper session with logout support
- ✅ Credentials only sent once

See [Basic Auth Login Guide](../../Authentication/basic-auth-login.md) for details.

#### Alternative: Manual Login

If users prefer manual login, construct a simple URL without credentials:

**URL Pattern:**
```
https://your-instance/elimplus/?m={memento}
```

Users must login manually before accessing the form.

#### Legacy: Direct Disease Form URLs

Disease-specific forms can be accessed directly (requires login):

| Disease | Route |
|---------|-------|
| Influenza | `/elim/r/Influenza/?m={memento}` |
| RSV | `/elim/r/Rsv/?m={memento}` |
| Norovirus | `/elim/r/Norovirus/?m={memento}` |
| SARS-CoV-2 | `/elim/r/Sarscov2/?m={memento}` |

**Note:** The index page (`/elimplus/`) is recommended as the entry point for better user experience.

---

## Complete Workflow Examples

### Overview: End-to-End External Integration

For external systems integrating with ELIM+, the complete workflow involves:

**1. API Step (System-to-System):**
- Your system calls the Memento API with laboratory data
- Receives encrypted memento string

**2. User Access Step (User-Facing):**
- Your system constructs an authenticated URL for end users
- Users click the link to access ELIM+ with pre-filled data
- **Recommended:** Use Basic Auth Login (BAL) for single-click authenticated access

**Complete Integration Pattern: API + BAL**

```
External System (Laboratory/KIS)
    ↓
[1] POST /api/elimplus/v1/memento
    with API user credentials
    receives memento string
    ↓
[2] Construct authenticated URL:
    https://enduser:password@host/bal/elimplus/?m={memento}
    ↓
[3] Send URL to end user
    (via email, portal link, SMS, etc.)
    ↓
End User
    ↓
[4] Click link → BAL authenticates
    → redirects to /elimplus/?m={memento}
    ↓
[5] ELIM+ index page with pre-filled data
    → User selects disease form
    ↓
[6] Review pre-filled form and submit to DEMIS
```

**Key Concepts:**

- **Two Sets of Credentials:**
  - **API user:** System credentials for calling the memento API (service account)
  - **End user:** Individual user credentials for accessing ELIM+ (their login account)

- **Basic Auth Login (BAL):**
  - Endpoint: `GET /bal/{target-path}`
  - Converts Basic Auth credentials into secure session
  - Users get proper session-based authentication with logout support
  - See [Basic Auth Login Guide](../../Authentication/basic-auth-login.md) for details

- **ELIM+ Index Page:**
  - Entry point: `/elimplus/` or `/elimplus/index`
  - Users select which disease form to work with
  - Memento data is available across all forms

**Why use BAL?**
✅ Single-click access (no separate login page)
✅ Proper session management with logout
✅ Secure credential handling
✅ Compatible with existing Basic Auth patterns

---

### Workflow 1: Complete external integration (API + BAL)

```bash
#!/bin/bash
# Complete workflow for external laboratory system integration

BASE_URL="https://elim.example.com"
API_USER="lab-api"          # System credentials for API
API_PASS="api-secret"
END_USER="lab-tech"         # End user credentials for form access
END_USER_PASS="tech-secret"

# Step 1: Create memento via API (system-to-system)
echo "Creating memento via API..."
MEMENTO=$(curl -s -X POST \
  -u "$API_USER:$API_PASS" \
  -H "Content-Type: application/json" \
  -d '{
    "reportId": "LAB-2024-00123",
    "KrankheitsCode": "J09",
    "MeldungsDatum": "2024-12-08",
    "Krankheit": {"Influenza": {}},
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
  "$BASE_URL/api/elimplus/v1/memento" | jq -r '.memento')

echo "Memento created: ${MEMENTO:0:50}..."

# Step 2: Construct BAL URL for end user (ELIM+ index page)
FORM_URL="https://$END_USER:$END_USER_PASS@$BASE_URL/bal/elimplus/?m=$MEMENTO"

# Step 3: Deliver to end user (example: email)
echo ""
echo "Sending link to end user..."
echo "To: lab-tech@hospital.com"
echo "Subject: Laboratory Report Ready for Review (LAB-2024-00123)"
echo ""
echo "Form URL (user clicks → auto-login → ELIM+ index):"
echo "$FORM_URL"
echo ""
echo "What happens when user clicks:"
echo "1. BAL authenticates with end user credentials"
echo "2. Creates secure session for end user"
echo "3. Redirects to /elimplus/?m={memento}"
echo "4. User sees ELIM+ index page with pre-filled data"
echo "5. User selects disease form (e.g., Influenza)"
echo "6. Form is pre-filled, user reviews and submits"
```

**Note:** The memento parameter (`?m={memento}`) is preserved when navigating from the index page to disease-specific forms.

---

### Workflow 2: Direct to disease form (alternative)

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
    "IsAnonym": false,
    "Standard": {
      "Name": {"Vorname": "Max", "Nachname": "Mustermann"},
      "Geschlecht": "MAENNLICH",
      "Geburtsdatum": "1980-05-15",
      "Adresse": {
        "Strasse": "Musterstraße 123",
        "PLZ": "12345",
        "Stadt": "Musterstadt"
      }
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

# Step 4: Construct ELIM+ index URL (without BAL - requires manual login)
FORM_URL="$BASE_URL/elimplus/?m=$MEMENTO"

echo "Success! ELIM+ URL:"
echo "$FORM_URL"
echo ""
echo "Send this URL to users who will login manually."
echo "Note: For single-click access, use Workflow 1 with BAL instead."
```

### Workflow 3: Email with pre-filled form link (BAL)

```bash
#!/bin/bash
# Create memento and email link to laboratory technician

BASE_URL="https://elim.example.com"
API_USER="kis-api-user"
API_PASS="api-password"
END_USER="lab-tech"
END_USER_PASS="tech-password"

# Create memento for RSV report (using API credentials)
MEMENTO=$(curl -s -X POST -u "$API_USER:$API_PASS" \
  -H "Content-Type: application/json" \
  -d '{
    "reportId": "LAB-2024-00456",
    "Krankheit": {"Rsv": {}},
    "Patient": {
      "IsAnonym": false,
      "Standard": {
        "Name": {"Vorname": "Anna", "Nachname": "Schmidt"},
        "Geburtsdatum": "1990-03-20"
      }
    }
  }' \
  "$BASE_URL/api/elimplus/v1/memento" | jq -r '.memento')

# Construct BAL URL for end user (ELIM+ index page)
FORM_URL="https://$END_USER:$END_USER_PASS@$BASE_URL/bal/elimplus/?m=$MEMENTO"

# Email the link (example using mail command)
echo "Please review and submit the laboratory report: $FORM_URL" | \
  mail -s "Laboratory Report Ready for Review (LAB-2024-00456)" \
    technician@hospital.example.com

echo "Email sent with single-click authenticated link"
```

### Workflow 4: Batch form generation from CSV

```bash
#!/bin/bash
# Generate multiple pre-filled forms from laboratory results CSV

BASE_URL="https://elim.example.com"
API_USER="kis-batch-user"
API_PASS="api-password"
END_USER="lab-tech"
END_USER_PASS="tech-password"

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
        IsAnonym: false,
        Standard: {
          Name: {Vorname: $vorname, Nachname: $nachname},
          Geburtsdatum: $dob
        }
      }
    }')

  # Create memento (using API credentials)
  MEMENTO=$(curl -s -X POST -u "$API_USER:$API_PASS" \
    -H "Content-Type: application/json" \
    -d "$LAB_DATA" \
    "$BASE_URL/api/elimplus/v1/memento" | jq -r '.memento')

  # Output report ID and BAL URL for end user (ELIM+ index)
  echo "$report_id,https://$END_USER:$END_USER_PASS@$BASE_URL/bal/elimplus/?m=$MEMENTO"
done < lab_results.csv > form_urls.csv

echo "Generated form URLs saved to form_urls.csv"
echo "Each URL provides single-click authenticated access to ELIM+ index"
```

### Workflow 5: Generate QR code for mobile access

```bash
#!/bin/bash
# Create memento and generate QR code for mobile scanning

BASE_URL="https://elim.example.com"
API_USER="kis-api"
API_PASS="api-password"
END_USER="mobile-user"
END_USER_PASS="mobile-password"

# Create memento (using API credentials)
MEMENTO=$(curl -s -X POST -u "$API_USER:$API_PASS" \
  -H "Content-Type: application/json" \
  -d '{
    "reportId": "LAB-2024-00789",
    "Krankheit": {"Sarscov2": {}},
    "Patient": {
      "IsAnonym": false,
      "Standard": {
        "Name": {"Vorname": "Thomas", "Nachname": "Müller"},
        "Geburtsdatum": "1975-08-12"
      }
    }
  }' \
  "$BASE_URL/api/elimplus/v1/memento" | jq -r '.memento')

# Construct BAL URL for end user (ELIM+ index)
FORM_URL="https://$END_USER:$END_USER_PASS@$BASE_URL/bal/elimplus/?m=$MEMENTO"

# Generate QR code (requires qrencode tool)
echo "$FORM_URL" | qrencode -o lab-report-qr.png

echo "QR code saved to lab-report-qr.png"
echo "Scan with mobile device for single-click authenticated access"
```

### Workflow 6: Anonymous patient reporting

```bash
#!/bin/bash
# Create memento for anonymous patient (privacy protection)

BASE_URL="https://elim.example.com"
API_USER="kis-api"
API_PASS="api-password"
END_USER="privacy-user"
END_USER_PASS="user-password"

# Create memento with anonymous patient data (using API credentials)
MEMENTO=$(curl -s -X POST -u "$API_USER:$API_PASS" \
  -H "Content-Type: application/json" \
  -d '{
    "reportId": "LAB-2024-00999",
    "KrankheitsCode": "J09",
    "MeldungsDatum": "2024-12-08",
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
  "$BASE_URL/api/elimplus/v1/memento" | jq -r '.memento')

# Construct BAL URL for end user (ELIM+ index)
FORM_URL="https://$END_USER:$END_USER_PASS@$BASE_URL/bal/elimplus/?m=$MEMENTO"

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
