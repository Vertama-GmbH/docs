# report-not-found

| | |
| --- | --- |
| **Type URI** | `https://docs.vertama.com/Products/ELIM/problems/report-not-found` |
| **HTTP status** | 404 Not Found |
| **Endpoint** | `GET /api/elim/v1/reports/{reportId}` |

!!! info "Availability"
    Ships with the RFC 9457 error contract for the ELIM API. Until your
    instance runs that release, the endpoint returns a body-less 404.

No retrievable report exists under this `MeldeId` for your API user. This is
**usually not an error in your integration** — a retrievable report only
comes into existence with a *successful* submission by the end user. The
cases:

1. **Not yet successfully submitted** — the memento was created, but the end
   user has not (yet) successfully sent the form. This includes failed
   attempts the user has not yet retried, and is the normal state between
   memento creation and user action; it can last hours or days.
2. **Unknown id** — no memento/report with this id was ever created.
3. **Different API user** — reports are only visible to the API user whose
   memento created them.
4. **Expired** — the report was never retrieved and fell out of the retention
   window (3 days, nightly cleanup).

```json
{
  "type": "https://docs.vertama.com/Products/ELIM/problems/report-not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "No report 'ELIM-2024-00123' for this user — not yet submitted, unknown id, or expired",
  "instance": "/api/elim/v1/reports/ELIM-2024-00123"
}
```

## What to do

If you are polling for a result: keep polling — a 404 before the user
successfully submits is expected. Prefer the event-driven fetch after the
[success redirect](../api-tutorial.md#detecting-submission-success-from-an-embedding-client).
If the id should exist and is older than the retention window, the result is
no longer retrievable. Verify you are calling with the same API user that
created the memento.
