# DUBA API Integration Guide

A practical guide for integration partners using the DUBA (Digital Court Guardianship) API.

**Version:** 0.2.0
**Last Updated:** 2025-11-28

---

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [Core Concepts](#core-concepts)
4. [List Messages Endpoint](#list-messages-endpoint)
5. [Understanding MessageInfo](#understanding-messageinfo)
6. [Download Message Endpoint](#download-message-endpoint)
7. [Acknowledge Messages Endpoint](#acknowledge-messages-endpoint)
8. [Complete Workflow Examples](#complete-workflow-examples)
9. [Filtering Best Practices](#filtering-best-practices)
10. [Error Codes](#error-codes)
11. [Reference](#reference)

---

## Introduction

The DUBA API provides programmatic access to court messages exchanged via EGVP (Elektronisches Gerichts- und Verwaltungspostfach). This API allows integration partners to:

- **List available messages** with filtering by job ID, Safe-ID, or timestamp
- **Download messages** as ZIP files containing XJustiz XML and attachments
- **Acknowledge messages** to trigger cleanup of sensitive data (GDPR compliance)

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
**Last Updated:** 2025-11-27
**API Version:** v1
