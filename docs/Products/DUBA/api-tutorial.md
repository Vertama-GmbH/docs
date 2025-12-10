# DUBA API Integration Guide

A practical guide for integration partners using the DUBA (Digital Court Guardianship) API.

**Version:** 0.2.0
**Last Updated:** 2025-12-10

---

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [Core Concepts](#core-concepts)
4. [List Messages Endpoint](#list-messages-endpoint)
5. [Understanding MessageInfo](#understanding-messageinfo)
6. [Download Message Endpoint](#download-message-endpoint)
7. [Acknowledge Messages Endpoint](#acknowledge-messages-endpoint)
8. [Form Pre-fill with Memento Endpoint](#form-pre-fill-with-memento-endpoint)
9. [Complete Workflow Examples](#complete-workflow-examples)
10. [Filtering Best Practices](#filtering-best-practices)
11. [Error Codes](#error-codes)
12. [Reference](#reference)

---

## Introduction

The DUBA API provides programmatic access to court messages exchanged via EGVP (Elektronisches Gerichts- und Verwaltungspostfach). This API allows integration partners to:

- **List available messages** with filtering by job ID, Safe-ID, or timestamp
- **Download messages** as ZIP files containing XJustiz XML and attachments
- **Acknowledge messages** to trigger cleanup of sensitive data (GDPR compliance)
- **Create form mementos** to generate pre-filled form URLs from your system data

### Prerequisites

Before using the API, you need:
- **API User Credentials**: Username and password provided by your administrator
- **Base URL**: Your DUBA instance URL (e.g., `https://elim.example.com`)
- **Safe-ID**: EGVP Safe-ID(s) you have access to

### API Versioning

All endpoints are versioned under `/api/duba/v1/`.

### OpenAPI Specification

The complete OpenAPI specification is available at:
```
https://your-instance/api/docs/swagger-ui/index.html?urls.primaryName=DUBA
```

---

## Authentication

The API uses **HTTP Basic Authentication** with your API user credentials.

### How It Works

1. Your administrator creates an API user account with username and password
2. For each API request, provide credentials in the `Authorization` header
3. Internally, the system derives a KEK (Key Encryption Key) from your password for cryptographic operations, but you only need to provide your username and password

### Example

```bash
curl -u "username:password" \
  https://elim.example.com/api/duba/v1/messages
```

Or explicitly with Authorization header:

```bash
# Encode credentials (username:password in base64)
echo -n "username:password" | base64
# Result: dXNlcm5hbWU6cGFzc3dvcmQ=

curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
  https://elim.example.com/api/duba/v1/messages
```

---

## Core Concepts

### Message States

Messages go through different states in the system:

1. **Indexed**: Message metadata discovered from EGVP (lightweight, fast)
2. **Hydrated**: Full message downloaded and XJustiz parsed (aktenzeichen extracted)
3. **Available**: Message can be downloaded via API

**Important**: Only **hydrated** messages have complete metadata (aktenzeichen, sender info).

### Job IDs vs Aktenzeichen

Two different identifiers are used:

- **jobId**: Your internal work tracking ID (e.g., `"job-2024-001"`)
  - Arbitrary string meaningful to your system
  - Used to correlate messages with your cases
  - Set when sending messages via DUBA

- **aktenzeichen**: German legal case reference number (e.g., `"AZ-12345-2024"`)
  - Formal XJustiz identifier required in court communications
  - Extracted from message content after hydration
  - Used by courts and legal systems

**Mapping**: The system maintains a mapping between your jobIds and aktenzeichen values.

### Message Direction

Messages have a direction:

- **INCOMING**: Received from external courts or systems
- **OUTGOING**: Sent by you to external recipients

### ProcessCard Timestamps

Messages include timestamps from the EGVP ProcessCard:

- **createdAt** (`tspCreation`): When message arrived at EGVP server (always present)
- **receivedAt** (`tspReception`): When first retrieved by anyone
  - For INCOMING: When you or another system downloaded it
  - For OUTGOING: When the recipient downloaded it
  - `null` if not yet retrieved
- **hydratedAt**: When the system fully processed the message (downloaded + parsed)
  - `null` if not yet hydrated

---

## List Messages Endpoint

**Endpoint:** `GET /api/duba/v1/messages`

**Purpose:** Query available messages with optional filtering.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `jobId` | array[string] | No | Filter by your job IDs. Can specify multiple times. |
| `safeId` | array[string] | No | Filter by EGVP Safe-IDs. Can specify multiple times. |
| `since` | string (ISO 8601) | No | Only messages created after this timestamp. |

### Response

Returns an array of `MessageInfo` objects (see [Understanding MessageInfo](#understanding-messageinfo)).

### Examples

#### Get all available messages

```bash
curl -u "user:pass" \
  https://elim.example.com/api/duba/v1/messages
```

#### Filter by single job ID

```bash
curl -u "user:pass" \
  "https://elim.example.com/api/duba/v1/messages?jobId=job-2024-001"
```

#### Filter by multiple job IDs

```bash
curl -u "user:pass" \
  "https://elim.example.com/api/duba/v1/messages?jobId=job-123&jobId=job-456"
```

#### Get recent messages (since timestamp)

```bash
curl -u "user:pass" \
  "https://elim.example.com/api/duba/v1/messages?since=2025-11-25T10:00:00Z"
```

#### Combine multiple filters

```bash
curl -u "user:pass" \
  "https://elim.example.com/api/duba/v1/messages?jobId=job-123&safeId=safe-abc&since=2025-11-25T10:00:00Z"
```

### Filtering Behavior

**Important semantic note:**

- **Without `jobId` filter**: Returns ALL messages (hydrated + non-hydrated)
- **With `jobId` filter**: Returns only messages for those jobs
  - Naturally returns only **hydrated** messages (because jobId mapping requires aktenzeichen)
  - Non-hydrated messages cannot be matched to jobs yet (no aktenzeichen extracted)

This is **intentional and correct** behavior, not a bug.

---

## Understanding MessageInfo

The API returns `MessageInfo` objects with complete message metadata.

### Field Reference

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | integer | No | Message index ID - **use this for download** |
| `messageId` | string | No | EGVP/Vibilia transport message ID |
| `jobId` | string | **Yes** | Your job ID (null for external messages) |
| `aktenzeichen` | string | **Yes** | Legal case number (null if not hydrated) |
| `direction` | enum | No | `INCOMING` or `OUTGOING` |
| `createdAt` | datetime | No | When message arrived at EGVP server |
| `receivedAt` | datetime | **Yes** | When first retrieved (null if not yet retrieved) |
| `hydratedAt` | datetime | **Yes** | When processed by system (null if not hydrated) |
| `url` | string (uri) | No | Relative URL for download endpoint |

### Example Response

```json
[
  {
    "id": 214,
    "messageId": "gov2test_17623381049230a53d2f5-5015-4d9b-9afb-e86b1d0b6872",
    "jobId": "job-2024-001",
    "aktenzeichen": "AZ-12345-2024",
    "direction": "INCOMING",
    "createdAt": "2025-11-26T14:30:00Z",
    "receivedAt": "2025-11-26T15:00:00Z",
    "hydratedAt": "2025-11-26T15:01:00Z",
    "url": "/api/duba/v1/download/214"
  },
  {
    "id": 215,
    "messageId": "msg-def-456",
    "jobId": null,
    "aktenzeichen": "AZ-67890-2024",
    "direction": "INCOMING",
    "createdAt": "2025-11-26T14:35:00Z",
    "receivedAt": "2025-11-26T14:40:00Z",
    "hydratedAt": "2025-11-26T14:41:00Z",
    "url": "/api/duba/v1/download/215"
  }
]
```

### Understanding Nullable Fields

#### `jobId == null`

The message was not sent via your DUBA API integration. Possible reasons:
- External court sent you an unsolicited message
- Another system sharing your EGVP account sent the message
- Message predates your API integration

#### `aktenzeichen == null`

The message is **not yet hydrated** (still processing). This means:
- Metadata is available (indexed)
- Full content not yet downloaded/parsed
- Cannot be matched to jobs yet
- Wait for `hydratedAt != null` before relying on aktenzeichen

#### `receivedAt == null`

The message has not been retrieved yet:
- **For INCOMING messages**: Neither you nor any other system has downloaded it yet
- **For OUTGOING messages**: The recipient hasn't downloaded it yet

---

## Download Message Endpoint

**Endpoint:** `GET /api/duba/v1/download/{id}`

**Purpose:** Download a specific message as a ZIP file.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | integer | Yes | Message index ID from `MessageInfo.id` |

### Response

Returns a ZIP file containing:
- XJustiz XML message file
- Any attachments included with the message
- Metadata files

**Content-Type:** `application/zip`

### Examples

#### Download single message

```bash
curl -u "user:pass" \
  https://elim.example.com/api/duba/v1/download/214 \
  -o message-214.zip
```

#### Download with verbose output

```bash
curl -v -u "user:pass" \
  https://elim.example.com/api/duba/v1/download/214 \
  -o message-214.zip
```

#### Check download headers without downloading

```bash
curl -I -u "user:pass" \
  https://elim.example.com/api/duba/v1/download/214
```

---

## Acknowledge Messages Endpoint

**Endpoint:** `POST /api/duba/v1/messages/ack`

**Purpose:** Acknowledge receipt of one or more messages and trigger cleanup.

### What This Does

When you acknowledge a message:
1. **Deletes on-disk files** - Sensitive message content is removed (data protection)
2. **Soft-deletes index entry** - Metadata is preserved for audit trail
3. **Returns detailed status** - Know exactly what happened to each message

**Use case:** After successfully downloading and processing messages, acknowledge them to trigger cleanup and comply with data protection requirements.

### Request Body

```json
{
  "messageIds": [42, 43, 44]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `messageIds` | integer[] | Yes | Array of message index IDs to acknowledge (1-100 items) |

### Response

Returns status for each message ID:

```json
{
  "results": [
    {
      "id": 42,
      "status": "DELETED",
      "message": "Message acknowledged and deleted"
    },
    {
      "id": 43,
      "status": "ALREADY_DELETED",
      "message": "Message was already deleted"
    },
    {
      "id": 44,
      "status": "FORBIDDEN",
      "message": "User does not have access to this message"
    }
  ]
}
```

#### Status Values

| Status | Meaning | Is Error? |
|--------|---------|-----------|
| `DELETED` | Successfully acknowledged and cleaned up | No |
| `ALREADY_DELETED` | Message was already deleted (idempotent) | No |
| `NOT_FOUND` | Message index entry does not exist | Yes |
| `FORBIDDEN` | User does not have access to this message | Yes |
| `ERROR` | An error occurred during processing | Yes |

**Important:** Partial success is allowed. Some messages may succeed while others fail. Always check the status for each ID.

### Examples

#### Acknowledge single message

```bash
curl -X POST \
  -u "user:pass" \
  -H "Content-Type: application/json" \
  -d '{"messageIds": [214]}' \
  https://elim.example.com/api/duba/v1/messages/ack
```

#### Acknowledge multiple messages

```bash
curl -X POST \
  -u "user:pass" \
  -H "Content-Type: application/json" \
  -d '{"messageIds": [214, 215, 216]}' \
  https://elim.example.com/api/duba/v1/messages/ack
```

#### Parse response with jq

```bash
curl -X POST \
  -u "user:pass" \
  -H "Content-Type: application/json" \
  -d '{"messageIds": [214, 215, 216]}' \
  https://elim.example.com/api/duba/v1/messages/ack | jq .
```

#### Count successful deletions

```bash
curl -X POST \
  -u "user:pass" \
  -H "Content-Type: application/json" \
  -d '{"messageIds": [214, 215, 216]}' \
  https://elim.example.com/api/duba/v1/messages/ack | \
  jq '[.results[] | select(.status == "DELETED")] | length'
```

#### Download and acknowledge workflow

```bash
#!/bin/bash
# List messages, download each, then acknowledge all at once
MESSAGE_IDS=$(curl -u "user:pass" \
  "https://elim.example.com/api/duba/v1/messages?jobId=job-123" | \
  jq -r '.[].id')

# Download each message
for id in $MESSAGE_IDS; do
  echo "Downloading message $id..."
  curl -u "user:pass" \
    "https://elim.example.com/api/duba/v1/download/$id" \
    -o "message-$id.zip"
done

# Acknowledge all messages at once (bulk operation)
curl -X POST \
  -u "user:pass" \
  -H "Content-Type: application/json" \
  -d "{\"messageIds\": [$(echo $MESSAGE_IDS | tr '\n' ',' | sed 's/,$//' )]}" \
  https://elim.example.com/api/duba/v1/messages/ack
```

### Data Protection Notes

Acknowledging messages is one of three cleanup triggers in the system:

1. **ACK endpoint (this)** - Client-driven, explicit confirmation
2. **Sync-based cleanup** - Automatic when message confirmed gone from server
3. **Retention policy** - Time-based backstop (e.g., 30 days)

**Best practice:** Acknowledge messages as soon as you've successfully downloaded and processed them. This ensures:
- Sensitive data is deleted promptly (GDPR compliance)
- Your message list stays clean
- Audit trail is preserved for compliance

**Idempotent operation:** Safe to acknowledge the same message multiple times. Already-deleted messages return `ALREADY_DELETED` status (not an error).

---

## Form Pre-fill with Memento Endpoint

**Endpoint:** `POST /api/duba/v1/memento`

**Purpose:** Create encrypted memento strings to pre-fill DUBA web forms with data from your system.

### What This Does

The memento endpoint solves a common integration pattern:

1. **Your system (e.g., KIS)** has complete case data but wants users to review/approve before submission
2. **You call this endpoint** with the form data as JSON
3. **You receive back** an encrypted, URL-safe string (the "memento")
4. **You construct a URL** with the memento parameter
5. **Users open the URL** and see a pre-filled form ready to review and submit

**Benefits:**
- No direct submission required - users maintain control
- Form validation happens in the browser (immediate feedback)
- Users can correct or supplement data before sending
- Encrypted mementos are tamper-proof

### Use Case Example

```
Hospital KIS → Knows patient details for court guardianship request
           → Calls /memento with patient/case data as JSON
           → Receives encrypted memento string
           → Constructs URL: /duba/BetreuungAnregung?m={memento}
           → Emails/displays URL to authorized user
User       → Clicks URL
           → Sees pre-filled form with all case details
           → Reviews, corrects if needed, submits to court
```

### Request Body

The endpoint accepts DUBA form data as JSON. All fields except `jobId` are optional.

**Required Fields:**
- `jobId` - Your internal tracking ID (string)
- `absender.egvp_account_id` - EGVP/beBPo account ID for submission (integer)

**Common Structure:**

```json
{
  "jobId": "job-2024-12345",
  "meldeZeitpunkt": "2025-12-10T14:30:00+01:00",
  "absender": {
    "name": "Klinikum Musterstadt",
    "aktenzeichen": "KH-2024-001",
    "egvp_account_id": 42
  },
  "empfaenger": {
    "name": "Amtsgericht Musterstadt",
    "type": "Gericht",
    "safeId": "gov2test",
    "aktenzeichen": "AZ-2024-67890",
    "adresse": {
      "strasse": "Gerichtsplatz 1",
      "plz": "12345",
      "stadt": "Musterstadt"
    }
  },
  "betroffener": {
    "name": {
      "vorname": "Max",
      "nachname": "Mustermann"
    },
    "geburtsdatum": "1950-01-15",
    "familienstand": "Verheiratet",
    "anschrift": {
      "strasse": "Musterstraße 42",
      "plz": "12345",
      "stadt": "Musterstadt"
    },
    "anschriftTelefon": "+49 123 456789",
    "derzeitigerWohnort": {
      "strasse": "Klinikstraße 1",
      "plz": "12345",
      "stadt": "Musterstadt"
    },
    "derzeitigerWohnortTelefon": "+49 123 999888"
  }
}
```

### Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `jobId` | string | Yes | Your internal job/case tracking ID |
| `meldeZeitpunkt` | datetime (ISO 8601) | No | Timestamp of report/registration |
| `absender.name` | string | No | Sender organization name |
| `absender.aktenzeichen` | string | No | Your internal case reference |
| `absender.egvp_account_id` | integer | Yes* | EGVP beBPo account ID for submission |
| `empfaenger.name` | string | No | Recipient organization name |
| `empfaenger.type` | enum | No | `Gericht` or `Sonstige` |
| `empfaenger.safeId` | string | No | EGVP Safe-ID for recipient |
| `empfaenger.aktenzeichen` | string | No | Court case reference number |
| `empfaenger.adresse.*` | object | No | Recipient address (strasse, plz, stadt) |
| `betroffener.name.*` | object | No | Affected person's name (vorname, nachname) |
| `betroffener.geburtsdatum` | date (YYYY-MM-DD) | No | Date of birth |
| `betroffener.familienstand` | enum | No | `Ledig`, `Verheiratet`, `Geschieden`, `Verwitwet` |
| `betroffener.anschrift.*` | object | No | Home address |
| `betroffener.anschriftTelefon` | string | No | Home phone number |
| `betroffener.derzeitigerWohnort.*` | object | No | Current location (e.g., hospital) |
| `betroffener.derzeitigerWohnortTelefon` | string | No | Current location phone |

\* Required for actual form submission, but optional for memento creation

### Response

Returns a JSON object containing the encrypted memento string:

```json
{
  "memento": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..DGG5lQvJC8OpYrCt.Xm8YR..."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `memento` | string | Encrypted, URL-safe string containing your form data |

**Note:** Memento strings are typically 500-2000 characters depending on data size. They are encrypted with AES-256-GCM and safe to pass via URL parameters.

### Examples

#### Minimal example (jobId only)

```bash
curl -X POST \
  -u "user:pass" \
  -H "Content-Type: application/json" \
  -d '{"jobId":"job-2024-001","absender":{"egvp_account_id":42}}' \
  https://elim.example.com/api/duba/v1/memento
```

Response:
```json
{
  "memento": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..abc123..."
}
```

#### Complete guardianship request example

```bash
curl -X POST \
  -u "user:pass" \
  -H "Content-Type: application/json" \
  -d '{
    "jobId": "job-2024-12345",
    "meldeZeitpunkt": "2025-12-10T14:30:00+01:00",
    "absender": {
      "name": "Klinikum Musterstadt",
      "aktenzeichen": "KH-2024-001",
      "egvp_account_id": 42
    },
    "empfaenger": {
      "name": "Amtsgericht Musterstadt",
      "type": "Gericht",
      "safeId": "gov2test",
      "aktenzeichen": "AZ-2024-67890"
    },
    "betroffener": {
      "name": {
        "vorname": "Max",
        "nachname": "Mustermann"
      },
      "geburtsdatum": "1950-01-15",
      "familienstand": "Verheiratet",
      "anschrift": {
        "strasse": "Musterstraße 42",
        "plz": "12345",
        "stadt": "Musterstadt"
      },
      "anschriftTelefon": "+49 123 456789",
      "derzeitigerWohnort": {
        "strasse": "Klinikstraße 1",
        "plz": "12345",
        "stadt": "Musterstadt"
      }
    }
  }' \
  https://elim.example.com/api/duba/v1/memento
```

#### Extract memento with jq

```bash
MEMENTO=$(curl -s -X POST \
  -u "user:pass" \
  -H "Content-Type: application/json" \
  -d '{"jobId":"job-123","absender":{"egvp_account_id":42}}' \
  https://elim.example.com/api/duba/v1/memento | jq -r '.memento')

echo "Memento: $MEMENTO"
```

### Constructing Form URLs

Once you have a memento, construct a URL to pre-fill a DUBA form:

**URL Pattern:**
```
https://your-instance/duba/{FormName}?m={memento}
```

**Available Form Types:**

| Form Name | Purpose |
|-----------|---------|
| `BetreuungAnregung` | Guardianship suggestion/request |
| `UnterbringungAntrag` | Involuntary commitment application |
| `FreiheitsentzugAntrag` | Deprivation of liberty application |

**Example URLs:**

```bash
# Guardianship form
https://elim.example.com/duba/BetreuungAnregung?m=eyJhbGciOiJkaXIi...

# Commitment form
https://elim.example.com/duba/UnterbringungAntrag?m=eyJhbGciOiJkaXIi...
```

### Complete End-to-End Example

```bash
#!/bin/bash
# Complete workflow: Create memento and construct form URL

BASE_URL="https://elim.example.com"
USER="your-username"
PASS="your-password"
FORM_TYPE="BetreuungAnregung"

# Step 1: Prepare form data
FORM_DATA='{
  "jobId": "job-2024-12345",
  "meldeZeitpunkt": "2025-12-10T14:30:00+01:00",
  "absender": {
    "name": "Klinikum Musterstadt",
    "aktenzeichen": "KH-2024-001",
    "egvp_account_id": 42
  },
  "betroffener": {
    "name": {"vorname": "Max", "nachname": "Mustermann"},
    "geburtsdatum": "1950-01-15",
    "anschrift": {
      "strasse": "Musterstraße 42",
      "plz": "12345",
      "stadt": "Musterstadt"
    }
  }
}'

# Step 2: Create memento
echo "Creating memento..."
RESPONSE=$(curl -s -X POST \
  -u "$USER:$PASS" \
  -H "Content-Type: application/json" \
  -d "$FORM_DATA" \
  "$BASE_URL/api/duba/v1/memento")

# Step 3: Extract memento from response
MEMENTO=$(echo "$RESPONSE" | jq -r '.memento')

if [ -z "$MEMENTO" ] || [ "$MEMENTO" = "null" ]; then
  echo "Error: Failed to create memento"
  echo "$RESPONSE" | jq .
  exit 1
fi

# Step 4: Construct form URL
FORM_URL="$BASE_URL/duba/$FORM_TYPE?m=$MEMENTO"

echo "Success! Form URL:"
echo "$FORM_URL"
echo ""
echo "Send this URL to the authorized user to open the pre-filled form."
```

### Integration Patterns

#### Pattern 1: Email with pre-filled form link

```bash
# Create memento and email link to user
MEMENTO=$(curl -s -X POST -u "$USER:$PASS" \
  -H "Content-Type: application/json" \
  -d "$FORM_DATA" \
  "$BASE_URL/api/duba/v1/memento" | jq -r '.memento')

FORM_URL="$BASE_URL/duba/BetreuungAnregung?m=$MEMENTO"

# Email the link (example using mail command)
echo "Please review and submit the guardianship form: $FORM_URL" | \
  mail -s "Court Form Ready for Review" user@hospital.example.com
```

#### Pattern 2: Generate QR code for mobile access

```bash
# Create memento
MEMENTO=$(curl -s -X POST -u "$USER:$PASS" \
  -H "Content-Type: application/json" \
  -d "$FORM_DATA" \
  "$BASE_URL/api/duba/v1/memento" | jq -r '.memento')

FORM_URL="$BASE_URL/duba/BetreuungAnregung?m=$MEMENTO"

# Generate QR code (requires qrencode tool)
echo "$FORM_URL" | qrencode -o form-qr.png
echo "QR code saved to form-qr.png"
```

#### Pattern 3: Batch form generation

```bash
# Generate multiple pre-filled forms from case list
while IFS=, read -r case_id patient_name dob; do
  FORM_DATA=$(jq -n \
    --arg jobId "$case_id" \
    --arg vorname "$(echo $patient_name | cut -d' ' -f1)" \
    --arg nachname "$(echo $patient_name | cut -d' ' -f2)" \
    --arg dob "$dob" \
    '{
      jobId: $jobId,
      absender: {egvp_account_id: 42},
      betroffener: {
        name: {vorname: $vorname, nachname: $nachname},
        geburtsdatum: $dob
      }
    }')

  MEMENTO=$(curl -s -X POST -u "$USER:$PASS" \
    -H "Content-Type: application/json" \
    -d "$FORM_DATA" \
    "$BASE_URL/api/duba/v1/memento" | jq -r '.memento')

  echo "$case_id,$BASE_URL/duba/BetreuungAnregung?m=$MEMENTO"
done < cases.csv > form_urls.csv

echo "Generated form URLs saved to form_urls.csv"
```

### Error Handling

#### Validation Errors

If the request data is invalid, you'll receive a 400 Bad Request with details:

```bash
curl -X POST -u "user:pass" \
  -H "Content-Type: application/json" \
  -d '{"invalid":"data"}' \
  https://elim.example.com/api/duba/v1/memento
```

Response:
```json
{
  "error": "Validation failed",
  "errors": [
    "Field 'jobId' is required"
  ]
}
```

#### Handle Errors in Scripts

```bash
RESPONSE=$(curl -s -X POST -u "$USER:$PASS" \
  -H "Content-Type: application/json" \
  -d "$FORM_DATA" \
  "$BASE_URL/api/duba/v1/memento")

# Check for error field
if echo "$RESPONSE" | jq -e '.error' > /dev/null; then
  echo "Error creating memento:"
  echo "$RESPONSE" | jq -r '.error'
  if echo "$RESPONSE" | jq -e '.errors' > /dev/null; then
    echo "Details:"
    echo "$RESPONSE" | jq -r '.errors[]'
  fi
  exit 1
fi

# Extract memento
MEMENTO=$(echo "$RESPONSE" | jq -r '.memento')
echo "Success: $MEMENTO"
```

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
- ✗ Don't reuse mementos across different forms or cases

**Data Minimization:**
- Only include data that's actually needed for the form
- Empty/null fields don't bloat the memento (they're omitted)
- Minimal mementos result in shorter, more manageable URLs

---

## Complete Workflow Examples

### Workflow 1: Poll for new messages and download them

```bash
#!/bin/bash
# Configuration
BASE_URL="https://elim.example.com"
USER="your-username"
PASS="your-password"
SINCE="2025-11-25T10:00:00Z"

# Fetch messages since last check
echo "Fetching messages since $SINCE..."
MESSAGES=$(curl -s -u "$USER:$PASS" \
  "$BASE_URL/api/duba/v1/messages?since=$SINCE")

# Check if we got any messages
COUNT=$(echo "$MESSAGES" | jq '. | length')
echo "Found $COUNT messages"

# Download each message
echo "$MESSAGES" | jq -r '.[].id' | while read ID; do
  echo "Downloading message $ID..."
  curl -s -u "$USER:$PASS" \
    "$BASE_URL/api/duba/v1/download/$ID" \
    -o "message-$ID.zip"

  if [ $? -eq 0 ]; then
    echo "  ✓ Downloaded message-$ID.zip"
  else
    echo "  ✗ Failed to download message $ID"
  fi
done

echo "Done!"
```

### Workflow 2: Download all messages for a specific job

```bash
#!/bin/bash
# Configuration
BASE_URL="https://elim.example.com"
USER="your-username"
PASS="your-password"
JOB_ID="job-2024-001"

# Create output directory
mkdir -p "downloads/$JOB_ID"

# List messages for job
echo "Fetching messages for job $JOB_ID..."
MESSAGES=$(curl -s -u "$USER:$PASS" \
  "$BASE_URL/api/duba/v1/messages?jobId=$JOB_ID")

# Download each
echo "$MESSAGES" | jq -r '.[].id' | while read ID; do
  echo "Downloading message $ID..."
  curl -s -u "$USER:$PASS" \
    "$BASE_URL/api/duba/v1/download/$ID" \
    -o "downloads/$JOB_ID/message-$ID.zip"
done

echo "All messages for $JOB_ID downloaded to downloads/$JOB_ID/"
```

### Workflow 3: Check for INCOMING court responses

```bash
#!/bin/bash
# Configuration
BASE_URL="https://elim.example.com"
USER="your-username"
PASS="your-password"

# Fetch all messages
echo "Checking for incoming court responses..."
MESSAGES=$(curl -s -u "$USER:$PASS" \
  "$BASE_URL/api/duba/v1/messages")

# Filter INCOMING messages and download
echo "$MESSAGES" | jq -r '.[] | select(.direction == "INCOMING") | .id' | while read ID; do
  # Get message details
  MSG=$(echo "$MESSAGES" | jq -r ".[] | select(.id == $ID)")
  AKTENZEICHEN=$(echo "$MSG" | jq -r '.aktenzeichen // "unknown"')

  echo "Downloading incoming message $ID (AZ: $AKTENZEICHEN)..."
  curl -s -u "$USER:$PASS" \
    "$BASE_URL/api/duba/v1/download/$ID" \
    -o "incoming-$AKTENZEICHEN-$ID.zip"
done

echo "Done!"
```

### Workflow 4: Incremental polling with state tracking

```bash
#!/bin/bash
# Configuration
BASE_URL="https://elim.example.com"
USER="your-username"
PASS="your-password"
STATE_FILE=".last_poll_timestamp"

# Read last poll timestamp (or use default)
if [ -f "$STATE_FILE" ]; then
  SINCE=$(cat "$STATE_FILE")
  echo "Polling since last check: $SINCE"
else
  SINCE="2025-11-01T00:00:00Z"
  echo "First poll, using: $SINCE"
fi

# Fetch new messages
MESSAGES=$(curl -s -u "$USER:$PASS" \
  "$BASE_URL/api/duba/v1/messages?since=$SINCE")

# Process messages
echo "$MESSAGES" | jq -r '.[].id' | while read ID; do
  echo "Processing message $ID..."
  curl -s -u "$USER:$PASS" \
    "$BASE_URL/api/duba/v1/download/$ID" \
    -o "message-$ID.zip"
done

# Update timestamp for next poll
date -u +"%Y-%m-%dT%H:%M:%SZ" > "$STATE_FILE"
echo "Updated last poll timestamp"
```

---

## Filtering Best Practices

### Use jobId filtering for targeted queries

When you know which cases you're interested in, filter by jobId to reduce response size and processing:

```bash
curl -u "$USER:$PASS" \
  "$BASE_URL/api/duba/v1/messages?jobId=job-123&jobId=job-456"
```

### Use since parameter for incremental polling

Avoid re-fetching all messages by using the `since` parameter:

```bash
# First poll: get everything
curl -u "$USER:$PASS" "$BASE_URL/api/duba/v1/messages"

# Subsequent polls: only new messages
LAST_POLL="2025-11-26T10:00:00Z"
curl -u "$USER:$PASS" "$BASE_URL/api/duba/v1/messages?since=$LAST_POLL"
```

### Combine filters for precise queries

Combine multiple filters to narrow results:

```bash
# Only messages for specific jobs in a specific Safe-ID since yesterday
curl -u "$USER:$PASS" \
  "$BASE_URL/api/duba/v1/messages?jobId=job-123&safeId=safe-abc&since=2025-11-26T00:00:00Z"
```

### Handle nullable fields gracefully

Always check for `null` values before using fields:

```bash
# Using jq to safely handle nulls
curl -s -u "$USER:$PASS" "$BASE_URL/api/duba/v1/messages" | \
  jq -r '.[] | "\(.id): jobId=\(.jobId // "none"), aktenzeichen=\(.aktenzeichen // "not-hydrated")"'
```

### Filter by direction in client code

Since the API doesn't have a `direction` parameter, filter client-side:

```bash
# Get only INCOMING messages
curl -s -u "$USER:$PASS" "$BASE_URL/api/duba/v1/messages" | \
  jq '.[] | select(.direction == "INCOMING")'
```

---

## Error Codes

The API uses standard HTTP status codes:

| Code | Status | Meaning |
|------|--------|---------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid parameters (e.g., malformed timestamp) |
| 401 | Unauthorized | Missing or invalid credentials |
| 403 | Forbidden | No access to this message or account |
| 404 | Not Found | Message does not exist |
| 500 | Internal Server Error | Server error (contact support) |

### Example Error Response

```bash
# Invalid timestamp format
curl -u "$USER:$PASS" \
  "$BASE_URL/api/duba/v1/messages?since=invalid-date"

# Response: 400 Bad Request
```

### Handling Errors in Scripts

```bash
# Check HTTP status code
HTTP_CODE=$(curl -s -o response.json -w "%{http_code}" -u "$USER:$PASS" \
  "$BASE_URL/api/duba/v1/messages")

if [ "$HTTP_CODE" -eq 200 ]; then
  echo "Success!"
  cat response.json | jq .
elif [ "$HTTP_CODE" -eq 401 ]; then
  echo "Authentication failed - check credentials"
elif [ "$HTTP_CODE" -eq 403 ]; then
  echo "Access denied - check permissions"
else
  echo "Error: HTTP $HTTP_CODE"
fi
```

---

## Reference

### API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/duba/v1/messages` | List available messages |
| GET | `/api/duba/v1/download/{id}` | Download message as ZIP |
| POST | `/api/duba/v1/messages/ack` | Acknowledge messages (trigger cleanup) |
| POST | `/api/duba/v1/memento` | Create encrypted memento for form pre-fill |

### OpenAPI Specification

Interactive API documentation (Swagger UI):
```
https://your-instance/api/docs/swagger-ui/index.html?urls.primaryName=DUBA
```

### Timestamp Format

All timestamps use ISO 8601 format with UTC timezone:
```
YYYY-MM-DDTHH:MM:SSZ
Example: 2025-11-26T15:34:10Z
```

### Support

For technical support or questions about the DUBA API:
- Contact your system administrator
- Refer to the OpenAPI specification for detailed schema documentation

---

**Document Version:** 0.2.0
**Last Updated:** 2025-12-10
**API Version:** v1
