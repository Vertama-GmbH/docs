# report-id-missing

| | |
| --- | --- |
| **Type URI** | `https://docs.vertama.com/Products/ELIMPLUS/problems/report-id-missing` |
| **HTTP status** | 400 Bad Request |
| **Context** | submitting a Labormeldung without a `reportId` |

!!! info "Availability"
    Ships with the RFC 9457 error contract for the ELIM+ API.

A report was submitted without a `reportId`. The `reportId` is your
correlation handle: without it, the submission outcome cannot be retrieved
via `GET /reports/{reportId}` later.

## What to do

Always assign your own `reportId` when creating the memento — an identifier
from your system that you can correlate later. Report ids are single-use:
after a successful submission, use a fresh id for the next report.
