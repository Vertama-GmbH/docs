# Magic Token Link (MTL)

A link that V.ap issues: one click logs the user in and opens the prefilled form. The URL carries
no credentials and no form data.

**Version:** 2.0.0
**Last Updated:** 2026-11-14

---

## How it works

1. Your system calls a product's memento endpoint with basic auth, for example
   `POST /api/digg/v1/memento`, and sends the form data.
2. The answer carries `magicLink`, a relative path: `/mtl/{token}`.
3. Your system puts its V.ap host in front and opens the link in the browser the user works in.
4. V.ap logs the user in as the API account and opens the prefilled form.

From there on, the session works like any login: the user reviews, completes and sends the form,
and logging out ends the session.

## The link

- **No data in the URL.** The token carries no credentials and no form data. The form data and
  the target stay on the server, sealed, until the link is opened. A URL in a log file or a browser
  history opens nothing once the link is no longer valid.
- **Valid only briefly.** A link is valid for a short time and for few uses, both depending on the
  configuration. Count on one use: create the link right before the user opens it, and open it at
  once. A link sent ahead of time, for example by email, has most likely expired.
- **Relative.** Put your V.ap host in front: `https://<your V.ap host>` + `magicLink`.

## A refused link

A link that is malformed, unknown, used up, expired or revoked leads to the login page with a short
note. V.ap creates no session for it. Ask your system for a new link.

## Example

```bash
HOST="https://elim.vertamob.de"
LINK=$(curl -s -u "$API_USER:$API_PASS" \
  -H "Content-Type: application/json" \
  -d '{"id": "DIGG-2026-00123"}' \
  "$HOST/api/digg/v1/memento" | jq -r '.magicLink')

open "$HOST$LINK"   # or hand the URL to the browser the user works in
```

Runnable Java examples, from the command line or the IDE:
[vap-examples](https://github.com/Vertama-GmbH/vap-examples).

## The `memento` field (deprecated)

The answer also carries `memento`, the encrypted form data. It serves only the old entry, where a
form URL with `?m={memento}` is opened in a session the user already has. New integrations open the
magic link.

## Related documentation

- The API tutorials of each product, under Products
- [Basic Auth Login (BAL)](basic-auth-login.md): the old door, retired
