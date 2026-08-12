# report-not-found

| | |
| --- | --- |
| **Type URI** | `https://docs.vertama.com/Products/ELIMPLUS/problems/report-not-found` |
| **HTTP status** | 404 Not Found |
| **Endpoint** | `GET /api/elimplus/v1/reports/{reportId}` |

!!! info "Availability"
    Ships with the RFC 9457 error contract for the ELIM+ API. Until your
    instance runs that release, the endpoint returns a body-less 404.

No retrievable report exists under this `reportId` for your API user. This is
**usually not an error in your integration** — it covers four cases:

1. **Not yet submitted** — the memento was created, but the end user has not
   (yet) successfully submitted the form. This is the normal state between
   memento creation and user action; it can last hours or days.
2. **Unknown id** — no memento/report with this id was ever created.
3. **Different API user** — the report exists but belongs to another API user;
   reports are only visible to the user whose memento created them.
4. **Expired** — the report was never retrieved and fell out of the retention
   window (3 days, nightly cleanup).

```json
{
  "type": "https://docs.vertama.com/Products/ELIMPLUS/problems/report-not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "No report 'LAB-2024-00123' for this user — not yet submitted, unknown id, or expired",
  "instance": "/api/elimplus/v1/reports/LAB-2024-00123"
}
```

## What to do

If you are polling for a result: keep polling — a 404 before the user submits
is expected. If the id should exist and is older than the retention window,
the result is no longer retrievable. Verify you are calling with the same API
user that created the memento.
