# report-not-found

| | |
| --- | --- |
| **Type URI** | `https://docs.vertama.com/Products/ZEAG/problems/report-not-found` |
| **HTTP status** | 404 Not Found |
| **Endpoint** | `GET /api/zeag/v1/reports/{id}` |

!!! info "Availability"
    ZEAG ships with the RFC 9457 error contract from the start (the module
    is not yet in production).

No retrievable ZEAG report exists under this id for your API user. The cases:

1. **Not yet submitted** — the memento was created, but the end user has not
   (yet) dispatched the form. This is the normal state between memento
   creation and user action.
2. **Unknown id** — no memento/report with this id was ever created.
3. **Different API user** — reports are only visible to the API user whose
   memento created them.
4. **Not a ZEAG report** — the id belongs to a report of a different module.

```json
{
  "type": "https://docs.vertama.com/Products/ZEAG/problems/report-not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "No ZEAG report 'ZEAG-2024-00123' for this user — not yet submitted, unknown id, or not a ZEAG report",
  "instance": "/api/zeag/v1/reports/ZEAG-2024-00123"
}
```

## What to do

If you are polling for a result: keep polling — a 404 before the user
dispatches the form is expected. Note that ZEAG delivery is asynchronous
(xPersonenstand/XTA2 to the Standesamt): once dispatched, the report appears
with status `PENDING` and resolves to `SUCCESS` or `FAILURE` later.
