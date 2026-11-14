# Basic Auth Login (BAL): retired

The `/bal/` door no longer exists. It turned basic-auth credentials in a URL
(`https://user:password@host/bal/…`) into a browser session. V.ap removed it in September 2026, and
links of that form no longer work.

Use the magic link instead. A product's memento endpoint answers with `magicLink`: a link that logs
the user in and opens the prefilled form, with no credentials in the URL. See
[Magic Token Link (MTL)](magic-token-link.md).

Basic auth for the API calls themselves (`/api/…`) stays as it is.
