# Problem types

V.ap answers an error of its REST APIs with an [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457)
problem details object (`Content-Type: application/problem+json`). Its `type` names the kind of
problem as a path:

| Path | Meaning | Example |
| --- | --- | --- |
| `/api/docs/problems/<slug>` | a problem that all APIs share | `/api/docs/problems/validation-error` |
| `/api/docs/problems/<product>/<slug>` | a problem of one product's API | `/api/docs/problems/digg/report-not-found` |

## Where the pages are

V.ap serves the page of each type itself, on the host you call, without a login. Resolved against
the URL you called, the `type` path opens the page that describes it.

The index lists every type V.ap answers with, by product, each with its HTTP status:

- Production: [https://elim.vertamob.de/api/docs/problems](https://elim.vertamob.de/api/docs/problems)
- Any other V.ap host: `https://<your V.ap host>/api/docs/problems`

## How to use it

Branch on `type`. For a rejected request (`validation-error`), also branch on `errors[].pointer`, the
JSON Pointer to the member of your request body that failed. Do not branch on `title` or `detail`:
they are texts for developers and can change.

Until November 2026, `type` was a URL on this site. V.ap no longer sends those names, and their
pages are gone.
