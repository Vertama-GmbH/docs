# report-already-retrieved

| | |
| --- | --- |
| **Type URI** | `https://docs.vertama.com/Products/ZEAG/problems/report-already-retrieved` |
| **HTTP status** | 410 Gone |
| **Endpoint** | `GET /api/zeag/v1/reports/{id}` |

!!! info "Availability"
    ZEAG ships with the RFC 9457 error contract from the start (the module
    is not yet in production).

The report existed and was already retrieved (consumed) by a previous
`GET /reports/{id}` call without `?peek=true`. A consumed report leaves the
pending list and its result is not delivered again. Note: `PENDING` reports
are never consumed — only terminal results are.

```json
{
  "type": "https://docs.vertama.com/Products/ZEAG/problems/report-already-retrieved",
  "title": "Gone",
  "status": 410,
  "detail": "Report 'ZEAG-2024-00123' was already retrieved; use ?peek=true to read without consuming",
  "instance": "/api/zeag/v1/reports/ZEAG-2024-00123"
}
```

## What to do

Use `?peek=true` for non-destructive reads and consume the report only once
you have durably stored the result. If you see this unexpectedly, another
process under the same API user has consumed the report.
