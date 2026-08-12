# ELIM API — FAQ

Frequently asked integration questions, collected from real KIS integrations.
Short answers here; the [API Integration Guide](api-tutorial.md) is the
canonical reference.

## Identity & attribution

**With which identity does ELIM submit to DEMIS? Does the facility need its own registration or an SMC-B?**

The facility needs its own DEMIS registration and receives a certificate
(PKCS12 + passphrase) from DEMIS, deposited per site and environment. No
SMC-B is needed. The report is cryptographically attributed to the facility;
the reporting doctor is carried as report content (name, LANR, contact).
→ [DEMIS registration and certificate](api-tutorial.md#demis-registration-and-certificate-per-facility)

## Correlation

**Is the `reportId` identical to the `MeldeId` I passed in?**

Yes — identical value, no re-keying. Always pass your own `MeldeId` (a
missing one is replaced by an uncorrelatable random UUID), and note that a
`MeldeId` is single-use after successful submission.
→ [Report ID](api-tutorial.md#report-id)

**When does a retrievable report come into existence?**

Only with the end user's successful submission. Before that,
`GET /reports/{reportId}` returns 404 — expected, not an error.
→ [404 semantics](api-tutorial.md#404-semantics)

## Retrieval

**Does `GET /reports` itself consume entries?**

No — the list is purely read-only. Only the detail call
`GET /reports/{reportId}` **without** `?peek=true` consumes a report. With
`?peek=true` you can read as often as you like. A `peek` parameter on the
list call is ignored (harmless, no effect).

**How long do unretrieved reports stay available? Can I re-fetch after a 410?**

Unretrieved results are kept for 3 days, then a nightly cleanup removes the
payload including the RKI receipt (after that: 404). A consumed report (410)
is not delivered again — use `?peek=true` if you need repeated reads.
→ [Report Retrieval](api-tutorial.md#report-retrieval-endpoints)

## Embedding & timing

**Can my embedding client (browser plugin / KIS container) detect a successful submission?**

Yes — success responds with an HTTP 302 redirect to the static, parameterless
`/elim/hospitalisierungsmeldung/success`; failure re-renders the form with
HTTP 400 and an unchanged URL. Outcome is reliably distinguishable from the
URL alone.
→ [Detecting submission success](api-tutorial.md#detecting-submission-success-from-an-embedding-client)

**What polling cadence is acceptable? How long until the result is retrievable?**

Submission to DEMIS is synchronous — the result is retrievable as soon as
the user sees the success page. Prefer an event-driven fetch right after the
success redirect; as a safety net, once per minute against `GET /reports` is
more than enough. No rate limits currently; timeouts of 10–30 s suffice.
→ [Polling pattern](api-tutorial.md#polling-pattern)

## Corrections & follow-ups

**How do I report discharge, transfer, death, intensive care — or correct a submitted report?**

Discharge, death and intensive care are fields within the report itself; a
transfer field does not exist. There is no correction report with a
machine-readable link to the original — a changed situation after submission
means a new report with a new `MeldeId`.
→ [Follow-up and correction reports](api-tutorial.md#follow-up-and-correction-reports)

## Errors

**Is there a catalog of `failureReason` values?**

Not today — `failureReason` is free text. A structured, documented error
catalog is coming as part of the migration of all Vertama REST APIs to
[RFC 9457 problem details](https://www.rfc-editor.org/rfc/rfc9457)
(`application/problem+json` with stable, machine-readable problem type URIs
that resolve to pages in this documentation). The
[ELIM+ API](../ELIMPLUS/integration-guide.md) migrates first; ELIM follows.
