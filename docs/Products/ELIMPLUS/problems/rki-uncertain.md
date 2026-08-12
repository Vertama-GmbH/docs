# rki-uncertain

| | |
| --- | --- |
| **Type URI** | `https://docs.vertama.com/Products/ELIMPLUS/problems/rki-uncertain` |
| **HTTP status** | 502 Bad Gateway |
| **Context** | submitting a Labormeldung to DEMIS |

!!! info "Availability"
    Ships with the RFC 9457 error contract for the ELIM+ API.

The submission to the RKI's DEMIS infrastructure ended in an **uncertain
state**: a server error or timeout on the RKI side made it impossible to tell
whether the report was processed or not.

To rule out a double report — DEMIS does not detect duplicates itself — the
`reportId` used in the uncertain attempt is locked.

## What to do

Do not retry under the same `reportId`. Restart the reporting workflow from
your system with a **new** `reportId`. If the uncertainty persists across
attempts, the DEMIS infrastructure is likely degraded — try again later.
