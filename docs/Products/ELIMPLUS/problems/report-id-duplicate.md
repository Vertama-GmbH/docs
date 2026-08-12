# report-id-duplicate

| | |
| --- | --- |
| **Type URI** | `https://docs.vertama.com/Products/ELIMPLUS/problems/report-id-duplicate` |
| **HTTP status** | 409 Conflict |
| **Context** | submitting a Labormeldung under a `reportId` that was already used |

!!! info "Availability"
    Ships with the RFC 9457 error contract for the ELIM+ API.

A report under this `reportId` was already successfully submitted. Report ids
are **single-use** — this protects against accidental double reporting, since
DEMIS does not detect duplicates itself.

## What to do

If this is a genuinely new report, assign a fresh `reportId`. If you are
retrying after an unclear outcome, first retrieve the existing result via
`GET /reports/{reportId}?peek=true` to see whether the original submission
succeeded — do not blindly resubmit under a new id.
