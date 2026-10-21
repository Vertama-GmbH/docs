# DIGT API Integration Guide

A practical guide for integration partners using the DIGT (Digitale Sterbefall-Meldung) API.

**Version:** 0.4.0
**Last Updated:** 2026-10-21

---

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [Core Concepts](#core-concepts)
4. [Memento Endpoint](#memento-endpoint)
5. [Detecting submission success from an embedding client](#detecting-submission-success-from-an-embedding-client)
6. [Report Retrieval Endpoints](#report-retrieval-endpoints)
7. [Complete Workflow Example](#complete-workflow-example)
8. [Error Handling](#error-handling)
9. [Reference](#reference)

---

## Introduction

The DIGT API enables clinical information systems (KIS) and undertaker software (Bestatter-Software) to pre-fill a digital death notification (Sterbefall-Meldung) for the civil registry office (Standesamt) via xPersonenstand integration. This API allows integration partners to:

- **Create form mementos** to generate pre-filled form URLs from case data
- **Enable user review** by staff before official submission
- **Retrieve report results** and status after end users submit forms to the Standesamt

### Use Case

DIGT solves the digital transmission of a Sterbefall-Meldung:

1. **Source system (KIS / Bestatter-Software)** has case data but wants staff to review and complete the form before xPersonenstand submission
2. **System calls API** with report data as JSON, populating exactly one of the three report-type slots
3. **API returns** an encrypted memento string and a magic link
4. **System uses the `magicLink`** to open a pre-filled form
5. **User reviews, completes missing info, and submits** to the Standesamt
6. **System polls** for the delivery status and the report PDF

```
KIS / Bestatter-Software
    ↓
[1] POST /api/digt/v1/memento  (API user credentials)
    ↓
[2] Receives { "memento": "...", "magicLink": "/mtl/...?m=..." }
    ↓
[3] Constructs absolute URL: https://elim.vertamob.de + magicLink
    ↓
[4] Opens URL in browser — authenticated via MTL token
    ↓
End User
    ↓
[5] Reviews pre-filled data, completes form → submits to Standesamt
    ↓
KIS / Bestatter-Software (asynchronous)
    ↓
[6] GET /api/digt/v1/reports/{id}  → status (PENDING, SUCCESS, FAILURE) + report PDF
```

**Benefits:**

- No direct automated submission — users maintain control and can review/correct data
- Form validation happens in browser (immediate feedback)
- Secure, encrypted mementos protect sensitive personal data

### Prerequisites

Before using the API, you need:

- **API User Credentials**: Username and password provided by your administrator
- **Standorte on your account**: for `Einrichtung` (084020) and `Todesbescheinigung` (084040), the reporting hospital is one of the InEK Standorte assigned to your account (see [Reporting Institution](#reporting-institution-standortid))
- **Receiving Standesämter**: the Standesämter your users can send to are the ones assigned to your account's Standorte. Vertama sets up this assignment; a Standesamt that is not assigned cannot be chosen in the form
- **Test or production mode**: each account runs in one of the two modes, switched by Vertama. In test mode, submissions only go to test Standesämter — no report reaches a real civil registry office. Start in test mode and ask for production once your integration works end to end

### OpenAPI Specification

The complete OpenAPI specification is available at:
```
https://elim.vertamob.de/api/docs/swagger-ui/index.html?urls.primaryName=DIGT
```

---

## Authentication

The API uses **HTTP Basic Authentication** with your API user credentials (the service account provided by your administrator). End users accessing the form do not need separate credentials.

### Example

```bash
curl -u "api-username:api-password" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"id":"DIGT-2026-001","Einrichtung":{}}' \
  https://elim.vertamob.de/api/digt/v1/memento
```

---

## Core Concepts

### Sterbefall-Meldung and its three report types

DIGT covers three xPersonenstand message types. A single memento request wraps all three in **slots**, of which **exactly one must be populated**. The populated slot determines which HTML form variant the memento targets:

| Slot | Message type | Form / target | Reporter |
|------|--------------|---------------|----------|
| `Einrichtung` | **084020** | Sterbefallanzeige (Einrichtung) | Hospital / care facility |
| `Bestatter` | **084021** | Sterbefallanzeige (Bestatter) | Undertaker |
| `Todesbescheinigung` | **084040** | Leichenschau-Mitteilung | Physician performing the post-mortem examination |

Populating zero or more than one slot is a validation error (400). The active slot determines which form the link opens after redemption (`/digt/{084020|084021|084040}`) — that target is encrypted inside the token, not part of the `magicLink` path itself.

### Memento Pattern

A **memento** is an encrypted, URL-safe string that contains form pre-fill data:

- Generated from JSON report data
- Tamper-proof and URL-safe
- Used as query parameter: `?m={memento}`

### Magic Token Link (MTL)

The `magicLink` field in the API response is a server-issued, time-limited URL that:
- Authenticates the end user automatically (no login page)
- Redirects to `/digt/{reportType}?m={memento}` on success
- Is a **relative path** — prepend your instance host to make it absolute

The link itself is `/mtl/{token}?m={memento}`. The redirect target (`/digt/{reportType}`) is encrypted inside the opaque token — it is **not** a readable path segment.

```
magicLink: "/mtl/eyJ...token...?m=eyJ...memento..."

Full URL: https://elim.vertamob.de/mtl/eyJ...token...?m=eyJ...memento..."
```

See [Magic Token Link (MTL)](../../Authentication/magic-token-link.md) for security details and token lifetime.

### Report ID

The `id` field identifies one Sterbefall-Meldung of your API user. It serves multiple purposes:

1. **Form pre-fill and correlation**: Correlates your case data to the form
2. **Status retrieval key**: After submission, used to retrieve delivery status via `GET /api/digt/v1/reports/{id}`

Use a **new `id` for every report**. The memento endpoint does not check whether an `id` was used before — but sending the form is refused if a report with this `id` was already submitted ("Diese Meldung wurde bereits übermittelt"), since the same id twice would be a second filing of the same death.

### Corrections and follow-up reports

DIGT has no correction or follow-up message: a submitted Sterbefall-Meldung cannot be amended or resent through the API. If facts change after submission, clarify this directly with the receiving Standesamt.

### Choice fields ("either/or")

Several types are *choices* — populate exactly one branch and leave the other absent:

| Type | Branch A | Branch B |
|------|----------|----------|
| `Todeszeitpunkt` (`sterbefall.todeszeitpunkt`) | `todestag` — exact time of death (`zeitpunkt`, `uhrzeitExakt`) | `sterbezeitraum` — period: last day alive (`letzterTagLebend`, optional `letzterTagLebendUhrzeit`) until death was certain (`mitSicherheitTotZeitpunkt`) |
| `AnschriftInlandAusland` (084040 `verstorbener.letzterWohnort`) | `anschriftInland` — German address | `anschriftAusland` — foreign address as free lines, **or** `anschriftAuslandStrukturiert` — structured foreign address |
| `Uhrzeit` (084040 `angabenLeichenschau.uhrzeit`) | `uhrzeit` — `{ "wert": "HH:mm", "exakt": true/false }` | `unbekannt: true` — time unknown |
| `Staat` | `code` — key from the Destatis state list | `nichtGelisteterWert` — free text for an unlisted state (see [Specifying a State](#specifying-a-state-staat)) |
| `Bestattungsart`, `CodeIdentifizierungsart` | `code` — value from the list (see [Enumerations](#enumerations)) | `nichtGelisteterWert` — free text |

`TeilbekanntesDatum` (084040 `verstorbener.tagDerGeburt`) takes either the full `datum`, or `jahr` with an optional `monat` when the exact date of birth is not known.

---

## Memento Endpoint

**Endpoint:** `POST /api/digt/v1/memento`

**Purpose:** Create an encrypted memento string and magic link to pre-fill a DIGT reporting form.

This endpoint does **not** submit the report — it only creates a pre-fill token for the interactive HTML form.

### Request Body

The body wraps all three report types (`Einrichtung`, `Bestatter`, `Todesbescheinigung`). You must populate **exactly one** slot — it selects the target form (and thus the redirect target `/digt/084020|084021|084040`, encrypted in the token). Supplying zero or more than one slot returns **400 Bad Request**.

The only mandatory field is the top-level `id`. Everything else — including every field inside the chosen slot — is optional to allow partial pre-filling; the form validates completeness when the user sends it (see [Formal API Definition](#reference) for the complete schema).

**Minimal Example (084020 — Einrichtung):**
```json
{
  "id": "DIGT-2026-00001",
  "Einrichtung": {}
}
```

**Extended Example (084020 — Einrichtung):**
```json
{
  "id": "DIGT-2026-00123",
  "standortId": "770001",
  "Einrichtung": {
    "anzeigender": {
      "ansprechpartner": {
        "vornamen": "Anna",
        "familienname": "Schmidt"
      },
      "kontaktdaten": [
        { "kanal": "telefon", "kennung": "+49 30 123456" }
      ]
    },
    "verstorbener": {
      "vorname": "Hans Wilhelm",
      "familienname": "Mueller",
      "geburtsname": "Schmidt",
      "geburtstag": "1945-03-22",
      "geschlecht": "maennlich",
      "letzterWohnsitz": {
        "strasse": "Musterstrasse 1",
        "plz": "10115",
        "ort": "Berlin"
      }
    },
    "sterbefall": {
      "todeszeitpunkt": {
        "todestag": {
          "zeitpunkt": "2026-04-12T14:30:00+02:00",
          "uhrzeitExakt": true
        }
      },
      "sterbeort": {
        "strasse": "Klinikstraße",
        "hausnummer": "1",
        "ort": "Berlin"
      }
    },
    "leichenID": "L-2026-04-001"
  }
}
```

**Example (084021 — Bestatter):**

The undertaker form carries the most data: next of kin, marriage history and the certificates to be issued. The undertaker (`anzeigender`) gives their own name and address — `standortId` is not used here.

```json
{
  "id": "DIGT-2026-00124",
  "Bestatter": {
    "anzeigender": {
      "nameOrganisation": "Bestattungshaus Muster GmbH",
      "ansprechpartner": { "vornamen": "Peter", "familienname": "Muster" },
      "anschrift": { "strasse": "Friedhofsweg 5", "plz": "10117", "ort": "Berlin" },
      "kontaktdaten": [
        { "kanal": "email", "kennung": "info@bestattung-muster.de" }
      ]
    },
    "verstorbener": {
      "vorname": "Hans Wilhelm",
      "familienname": "Mueller",
      "geburtstag": "1945-03-22",
      "geburtsort": { "ort": "Hamburg", "staat": { "code": "000" } },
      "geschlecht": "maennlich",
      "familienstand": "verheiratet",
      "letzterWohnsitz": { "strasse": "Musterstrasse 1", "plz": "10115", "ort": "Berlin" }
    },
    "sterbefall": {
      "todeszeitpunkt": {
        "sterbezeitraum": {
          "letzterTagLebend": "2026-04-10",
          "letzterTagLebendUhrzeit": "22:00",
          "mitSicherheitTotZeitpunkt": "2026-04-12T08:15:00+02:00"
        }
      },
      "sterbeort": { "strasse": "Musterstrasse", "hausnummer": "1", "ort": "Berlin" }
    },
    "partnerVerstorbener": {
      "vorname": "Maria",
      "familienname": "Mueller",
      "geburtsname": "Schneider",
      "istAuskunftsgeber": true
    },
    "letzteEheVerstorbener": {
      "tagEheLpVerstorbener": "1970-06-12",
      "ortEheLpVerstorbener": { "ort": "Hamburg", "staat": { "code": "000" } }
    },
    "artDerBestattung": { "code": "Feuerbestattung" },
    "urkundenAnforderung": {
      "anzahlStandardformat": 3,
      "anzahlSozialversicherung": 1
    }
  }
}
```

**Example (084040 — Todesbescheinigung):**

Filled in by the physician who performed the post-mortem examination. As with 084020, the physician's address comes from the Standort (`standortId`); you supply name and contact details.

```json
{
  "id": "DIGT-2026-00125",
  "standortId": "770001",
  "Todesbescheinigung": {
    "verstorbener": {
      "vorname": "Hans Wilhelm",
      "familienname": "Mueller",
      "tagDerGeburt": { "datum": "1945-03-22" },
      "ortDerGeburt": "Hamburg",
      "geschlecht": "maennlich",
      "letzterWohnort": {
        "anschriftInland": {
          "strasse": "Musterstrasse",
          "hausnummer": "1",
          "postleitzahl": "10115",
          "wohnort": "Berlin"
        }
      },
      "identifizierung": { "code": "Nach Einsicht in den Personalausweis/Reisepass" }
    },
    "sterbefall": {
      "sterbeort": true,
      "ereignisort": { "strasse": "Klinikstraße", "hausnummer": "1", "ort": "Berlin", "staat": { "code": "000" } },
      "todeszeitpunkt": {
        "todestag": { "zeitpunkt": "2026-04-12T14:30:00+02:00", "uhrzeitExakt": true }
      },
      "natuerlicherTod": true,
      "totgeburt": false
    },
    "angabenLeichenschau": {
      "namenArzt": { "vornamen": "Julia", "familienname": "Becker" },
      "kontaktArzt": [
        { "kanal": "telefon", "kennung": "+49 30 123457" }
      ],
      "datum": "2026-04-12",
      "uhrzeit": { "uhrzeit": { "wert": "15:10", "exakt": true } },
      "ort": "Berlin"
    }
  }
}
```

**Attachments (`anhaenge`):** `Einrichtung.anhaenge` and `Bestatter.anhaenge` are accepted but currently **ignored**. Documents cannot be attached through the API; the report PDF V.ap generates from the form is attached automatically (084020/084021).

### Reporting Institution (`standortId`)

For `Einrichtung` (084020) and `Todesbescheinigung` (084040), the reporting hospital is identified by its 6-digit InEK Standort-ID (`standortId`, top level of the request, next to `id`). Name and address are taken from the [Krankenhausstandorte registry](../../background-and-explanations/krankenhausstandorte.md) for that Standort and cannot be entered:

| Slot | Taken from the Standort |
|------|-------------------------|
| `Einrichtung` (084020) | Name and address of the reporting institution (`anzeigender`) |
| `Todesbescheinigung` (084040) | Address of the physician (`angabenLeichenschau.anschriftArzt`) |

Contact person and contact details (`ansprechpartner`, `kontaktdaten`, `namenArzt`, `kontaktArzt`) are still supplied by you or entered in the form.

- The Standort must be one of the Standorte of your account. A Standort that is not (or an unknown or malformed value) is **ignored**, as if none was given — the request is not rejected.
- Without a valid `standortId`, the user picks one of the account's Standorte in the form; with only one Standort, it is set automatically.
- For `Einrichtung` (084020), the receiving Standesamt is limited to the Standesämter assigned to the chosen Standort.
- `Bestatter` (084021) ignores `standortId`; the undertaker's name and address are still entered.

**Deprecated fields:** `Einrichtung.anzeigender.nameOrganisation`, `Einrichtung.anzeigender.anschrift` and `Todesbescheinigung.angabenLeichenschau.anschriftArzt` are deprecated. They are still accepted, but ignored — the values from the Standort always apply. Do not send them in new integrations.

### Specifying a State (`staat`)

For places (`sterbeort`, `geburtsort` and the other event locations such as the place of marriage) and for the structured foreign address (`anschriftAuslandStrukturiert`), `staat` is an object, as xPersonenstand defines it (`Code.Staat`):

- `code`: key from the state list (Staatenliste) of the Federal Statistical Office (Destatis), e.g. `"000"` (Germany), `"129"` (France), `"368"` (United States)
- `nichtGelisteterWert`: free text, only if the state is not on the list

If both are given, `code` takes precedence.

```json
"staat": { "code": "129" }
```

```json
"staat": { "nichtGelisteterWert": "Beispielstaat" }
```

For a foreign address given as free lines (`anschriftAusland`), `staat` is the bare key itself (e.g. `"staat": "368"`) — no free text, and not `"000"`. At least two address lines of at most 35 characters each are required.

For postal addresses (`letzterWohnsitz`, the undertaker's `anschrift` and similar), `staat` remains free text.

The valid keys are listed in the [state code list](../xoev/codelists/StaatCode.yml).

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

## Detecting submission success from an embedding client

If you embed the DIGT form in a browser component (KIS container, modal plugin, iframe wrapper), you can detect the outcome from the URL alone:

- **Success**: after a successful submission, the server responds with an **HTTP 302 redirect** to `/digt/success/{id}?reportType={084020|084021|084040}` — `{id}` is the `id` of your memento request.
- **Failure**: no redirect happens. The review page is shown again with an error message; the URL stays the form URL (`/digt/{reportType}`). Nothing was sent to the Standesamt, and no report is recorded — the user can correct the problem and send again.

After seeing the success redirect, fetch `GET /api/digt/v1/reports/{id}`. It returns `PENDING` at first: delivery to the Standesamt is confirmed asynchronously.

---

## Report Retrieval Endpoints

DIGT reports are delivered asynchronously via xPersonenstand/XTA2 transport: once the user has sent the form, the report shows up as `PENDING` and resolves to `SUCCESS` or `FAILURE` when the transport confirms or rejects the delivery.

**Retention**: report results are kept for **3 days** after submission; a nightly cleanup removes the payload including the report PDF after that. Retrieve results within this window.

### GET /reports — List pending report IDs

**Endpoint:** `GET /api/digt/v1/reports`

Returns an array of `id` strings for reports that have been submitted but not yet retrieved (unpolled). Reports disappear from this list once retrieved without `?peek=true`.

**Request:**
```bash
curl -u "api-user:api-pass" \
  https://elim.vertamob.de/api/digt/v1/reports
```

**Response (200):**
```json
["DIGT-2026-00123", "DIGT-2026-00124"]
```

An empty array `[]` means no submissions are pending retrieval.

---

### GET /reports/{id} — Retrieve report result

**Endpoint:** `GET /api/digt/v1/reports/{id}`

**Parameters:**

- `id` (path, required)
- `peek` (query, optional): `true` for non-destructive read. Default: `false`.

**Non-destructive peek:**
```bash
curl -u "api-user:api-pass" \
  "https://elim.vertamob.de/api/digt/v1/reports/DIGT-2026-00123?peek=true"
```

**Response (200 — SUCCESS):**
```json
{
  "id": "DIGT-2026-00123",
  "status": "SUCCESS",
  "module": "DIGT",
  "submittedAt": "2026-04-12T14:32:00Z",
  "portal": "GOVCONNECT",
  "receiptPdf": "JVBERi0xLjQK...",
  "failureReason": null
}
```

**Status semantics:**

- `PENDING`: Sent, but delivery not yet confirmed. Never marked as polled.
- `SUCCESS`: Successfully delivered to the Standesamt.
- `FAILURE`: The transport reported a failed delivery. Contains `failureReason`.

**Fields:**

- `receiptPdf`: base64-encoded **report PDF** — the Sterbefallanzeige V.ap generated from the submitted form (for 084020/084021 also attached to the message sent to the Standesamt). It is **not** a confirmation issued by the Standesamt and carries no signature. It is included for every status — `PENDING`, `SUCCESS` and `FAILURE` — until the report is consumed or the retention window ends.
- `portal`: the Standesamt portal the report was sent through, e.g. `GOVCONNECT`, `GOVCONNECT_TEST` (test mode) or `AKDB`.
- `submittedAt`: when the user sent the form.

**Note:** By default, reading a SUCCESS or FAILURE report is destructive — it is marked as polled, the report PDF is deleted, and the report is not delivered again ([report-already-retrieved](problems/report-already-retrieved.md)). Use `?peek=true` and consume the report only once you have durably stored the result.

### Recommended polling loop

1. `GET /reports` to learn which of your submissions have results waiting.
2. For each id, `GET /reports/{id}?peek=true`.
3. On `PENDING`, do nothing — it stays in the list and resolves later.
4. On `SUCCESS` / `FAILURE`, store the result (and decode `receiptPdf`), then re-read **without** `peek` to consume it.

If your client detects the [success redirect](#detecting-submission-success-from-an-embedding-client), start watching that `id` right after it. As a cyclic safety net, once per minute against `GET /reports` is more than sufficient — keep the cadence moderate. The result carries the report PDF base64-encoded and can be a few hundred kilobytes.

Poll well inside the 3-day retention window: results that are never fetched are removed by the retention cleanup and return 410 ([report-expired](problems/report-expired.md)).

### Testing

The following IDs are reserved for testing. They return canned responses without a real report lookup, for every account, and are never consumed:

- `DIGT-TEST-SUCCESS`: Always returns a SUCCESS response with a mock report PDF.
- `DIGT-TEST-PENDING`: Always returns a PENDING response.
- `DIGT-TEST-FAILURE`: Always returns a FAILURE response with a simulated failure reason.

Their `portal` is `TEST-PORTAL`.

---

## Complete Workflow Example

```bash
#!/bin/bash
# Complete workflow: create a memento, hand the link to the user, fetch the result

BASE_URL="https://elim.vertamob.de"
API_USER="kis-api"
API_PASS="api-secret"
REPORT_ID="DIGT-2026-00123"

# Step 1: Create memento and get magic link
RESPONSE=$(curl -s -X POST \
  -u "$API_USER:$API_PASS" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "'"$REPORT_ID"'",
    "standortId": "770001",
    "Einrichtung": {
      "verstorbener": {
        "vorname": "Hans Wilhelm",
        "familienname": "Mueller",
        "geburtstag": "1945-03-22",
        "geschlecht": "maennlich"
      }
    }
  }' \
  "$BASE_URL/api/digt/v1/memento")

MAGIC_LINK=$(echo "$RESPONSE" | jq -r '.magicLink')
if [ -z "$MAGIC_LINK" ] || [ "$MAGIC_LINK" = "null" ]; then
  echo "Error: no magic link in response"
  echo "$RESPONSE" | jq .
  exit 1
fi

# Step 2: Open the form for the user — the link is short-lived, use it right away
echo "Form URL: $BASE_URL$MAGIC_LINK"

# Step 3: After the user has sent the form, wait for the delivery result
while true; do
  RESULT=$(curl -s -u "$API_USER:$API_PASS" \
    "$BASE_URL/api/digt/v1/reports/$REPORT_ID?peek=true")
  STATUS=$(echo "$RESULT" | jq -r '.status // empty')

  case "$STATUS" in
    SUCCESS|FAILURE)
      echo "$RESULT" | jq -r '.receiptPdf' | base64 --decode > "$REPORT_ID.pdf"
      echo "$REPORT_ID: $STATUS $(echo "$RESULT" | jq -r '.failureReason // ""')"
      # Step 4: Result stored — consume it
      curl -s -o /dev/null -u "$API_USER:$API_PASS" \
        "$BASE_URL/api/digt/v1/reports/$REPORT_ID"
      break
      ;;
    *)
      # PENDING, or 404 while the user has not sent the form yet
      sleep 60
      ;;
  esac
done
```

---

## Error Handling

### HTTP Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| 200 | OK | Request successful |
| 400 | Bad Request | Request validation failed (e.g. invalid JSON, missing `id`, zero / more than one report-type slot populated) |
| 401 | Unauthorized | Missing or invalid API credentials — empty body, `WWW-Authenticate` header |
| 404 | Not Found | No DIGT report under this id for your API user |
| 410 | Gone | Report already retrieved, or aged out of the retention window |

### Problem Details (RFC 9457)

Except for 401, errors are returned as [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) problem details with `Content-Type: application/problem+json`. **Branch on the `type` URI** — it is the stable machine-readable discriminator; `title` and `detail` are developer diagnostics and may be reworded.

| `type` URI | Status | Documentation |
|---|---|---|
| `…/problems/validation-error` | 400 | [validation-error](../../problems/validation-error.md) |
| `…/Products/DIGT/problems/report-not-found` | 404 | [report-not-found](problems/report-not-found.md) |
| `…/Products/DIGT/problems/report-already-retrieved` | 410 | [report-already-retrieved](problems/report-already-retrieved.md) |
| `…/Products/DIGT/problems/report-expired` | 410 | [report-expired](problems/report-expired.md) |

Note that **the two 410 cases share a status code but differ in `type`** — one means "someone already consumed this", the other "it aged out". Distinguish them by `type`, never by status alone.

### Validation Errors

A rejected memento request returns 400 with one `errors` entry per violated constraint, each carrying a JSON Pointer to the offending member of your request body:

```json
{
  "type": "https://docs.vertama.com/problems/validation-error",
  "title": "Request validation failed",
  "status": 400,
  "detail": "1 violation",
  "instance": "/api/digt/v1/memento",
  "errors": [
    { "detail": "must not be null", "pointer": "#/id" }
  ]
}
```

`pointer` is absent for violations of the request as a whole, such as an unparseable body or a wrong number of populated slots.

### Not-found is normal

A 404 between memento creation and the user sending the form is the **expected** state, not a fault in your integration — keep polling. If sending fails in the form, nothing is recorded either, so the id stays 404 until the user sends successfully. See [report-not-found](problems/report-not-found.md) for the full case list.

---

## Reference

### Formal API Definition

- [OpenAPI](./api.yml)
- [API Viewer (Swagger)](https://elim.vertamob.de/api/docs/swagger-ui/index.html?urls.primaryName=DIGT)

### API Endpoints Summary

| Method | Endpoint                   | Description                     |
|--------|----------------------------|---------------------------------|
| POST | `/api/digt/v1/memento`     | Create memento                  |
| GET | `/api/digt/v1/reports` | List pending report IDs         |
| GET | `/api/digt/v1/reports/{id}` | Retrieve report delivery status |

### Date & Time Format

- **Date**: ISO 8601 format (`YYYY-MM-DD`, e.g., `2026-03-22`)
- **Date-time**: ISO 8601 format (`YYYY-MM-DDThh:mm:ss±hh:mm`, e.g., `2026-04-12T14:30:00+02:00`)
- **Time of day** (`letzterTagLebendUhrzeit`, `uhrzeit.wert`): `HH:mm` or `HH:mm:ss`, e.g. `22:00`

### Enumerations

| Field | Values |
|-------|--------|
| `geschlecht` | `maennlich`, `weiblich`, `divers`, `unbestimmt` |
| `familienstand` (084021) | `ledig`, `verheiratet`, `geschieden`, `verwitwet`, `lebenspartnerschaft`, `lebenspartnerschaftAufgehoben`, `lebenspartnerschaftDurchTodAufgeloest`, `nichtBekannt` |
| `artDerBestattung.code` (084021) | `Erdbestattung`, `Feuerbestattung`, `unbekannte Bestattungsart` — otherwise `nichtGelisteterWert` |
| `identifizierung.code` (084040) | `Nach Angaben von Angehörigen/Dritten`, `Aufgrund eigener Kenntnis`, `Nach Einsicht in den Personalausweis/Reisepass`, `Nach Einsicht in sonstiges Identifikationsdokument`, `Nicht möglich` — otherwise `nichtGelisteterWert` |
| `kontaktdaten[].kanal`, `kontaktArzt[].kanal` | `telefon`, `fax`, `email`, `internet`, `sonstiges` |
| `staat.code` | Key from the Destatis state list — **not** ISO 3166 (see [state code list](../xoev/codelists/StaatCode.yml)) |
| `status` (report result) | `PENDING`, `SUCCESS`, `FAILURE` |

### Security Notes

**Memento Encryption:**
- Mementos are encrypted with AES-256-GCM using your API user's key
- Each memento is unique even for identical data
- Tampering is detected and rejected

**Magic Link Security:**
- Tokens are server-issued, short-lived and can be used only a limited number of times — see [Magic Token Link (MTL)](../../Authentication/magic-token-link.md)

**Data protection:**
- Consuming a result (a read without `?peek=true` of a `SUCCESS` / `FAILURE` report) deletes the report PDF on the server
- Unretrieved results are removed after the 3-day retention window

**Best Practices:**
- ✓ Generate the magic link close to the time the user opens it
- ✓ Use a new `id` for every Sterbefall-Meldung
- ✗ Do not expose mementos or magic links to unauthorized users
- ✗ Do not reuse magic links; generate a fresh one for each workflow run

---

**Document Version:** 0.4.0
**Last Updated:** 2026-10-21
**API Version:** v1
