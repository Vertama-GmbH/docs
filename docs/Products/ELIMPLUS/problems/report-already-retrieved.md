# report-already-retrieved

| | |
| --- | --- |
| **Type URI** | `https://docs.vertama.com/Products/ELIMPLUS/problems/report-already-retrieved` |
| **HTTP status** | 410 Gone |
| **Endpoint** | `GET /api/elimplus/v1/reports/{reportId}` |

!!! info "Availability"
    Ships with the RFC 9457 error contract for the ELIM+ API. Until your
    instance runs that release, the endpoint returns a body-less 410.

The report existed and was already retrieved (consumed) by a previous
`GET /reports/{reportId}` call without `?peek=true`. A consumed report leaves
the pending list and its result is not delivered again.

```json
{
  "type": "https://docs.vertama.com/Products/ELIMPLUS/problems/report-already-retrieved",
  "title": "Gone",
  "status": 410,
  "detail": "Report 'LAB-2024-00123' was already retrieved; use ?peek=true to read without consuming",
  "instance": "/api/elimplus/v1/reports/LAB-2024-00123"
}
```

## What to do

If your system needs to read a result more than once, use `?peek=true` for
non-destructive reads and consume the report only once you have durably
stored the result. If you see this unexpectedly, another process under the
same API user has consumed the report — coordinate which component owns
report retrieval.
