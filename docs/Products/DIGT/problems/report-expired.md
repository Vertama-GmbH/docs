# report-expired

| | |
| --- | --- |
| **Type URI** | `https://docs.vertama.com/Products/DIGT/problems/report-expired` |
| **HTTP status** | 410 Gone |
| **Endpoint** | `GET /api/digt/v1/reports/{id}` |

The report existed, but its payload (including the report PDF) was removed
by the retention cleanup before it was retrieved. The result is no longer
available. Distinct from
[report-already-retrieved](report-already-retrieved.md): nothing consumed
this report — it aged out.

Results are kept for 3 days after submission. This type is returned only
once: the expired report then counts as retrieved, and later calls return
[report-already-retrieved](report-already-retrieved.md).

```json
{
  "type": "https://docs.vertama.com/Products/DIGT/problems/report-expired",
  "title": "Gone",
  "status": 410,
  "detail": "Report 'DIGT-2026-00123' fell out of the retention window; its payload is no longer available",
  "instance": "/api/digt/v1/reports/DIGT-2026-00123"
}
```

## What to do

Retrieve results within the retention window — ideally promptly after
dispatch, cyclically while `PENDING`. If you see this regularly, your
polling cadence is slower than the retention window.
