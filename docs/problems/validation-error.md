# validation-error

| | |
| --- | --- |
| **Type URI** | `https://docs.vertama.com/problems/validation-error` |
| **HTTP status** | 400 Bad Request |
| **Scope** | all Vertama REST APIs using the RFC 9457 error contract |

The request was understood but rejected as invalid input: a required field is
missing, a value is malformed, a domain rule on the request body is violated,
or the body itself is not parseable JSON.

The response is an [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) problem
details object (`Content-Type: application/problem+json`) extended with an
`errors` array carrying one entry per violated constraint:

```json
{
  "type": "https://docs.vertama.com/problems/validation-error",
  "title": "Request validation failed",
  "status": 400,
  "detail": "1 violation",
  "instance": "/api/elimplus/v1/memento",
  "errors": [
    { "detail": "must not be null", "pointer": "#/id" }
  ]
}
```

- `errors[].detail` — what is wrong with the value (English).
- `errors[].pointer` — JSON Pointer to the offending member of your request
  body. Absent for violations of the request as a whole (e.g. a rule across
  several fields, or an unparseable body).

## What to do

Fix the request. Every violation is listed, so one round trip shows all
problems at once. The `detail` texts are diagnostics for developers, not
display strings — do not show them to end users and do not parse them; they
may be reworded. Branch on the `type` URI and the `pointer`, which are stable.
