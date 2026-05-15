# V.connect

V.connect is the family of local-side bridges that adapt KIS
capabilities to V.ap (the Vertama application platform). Each
V.connect service runs on the customer's side of the network —
either on the KIS workstation or inside the hospital network — and
translates between what the KIS can natively do and what V.ap
expects.

The family contract: every V.connect service is **operated by the
customer**, but **shipped, signed, and documented by Vertama**. The
operational pattern, naming, and support model are consistent across
services.

## Services

| Service                                          | Purpose                                                                                                              | Status |
|--------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|--------|
| [Fremdaufruf](Fremdaufruf/overview.md)           | Bridges KIS systems that can only emit GET URLs to V.ap's POST-based session-initialisation endpoints.               | V1     |

## Fremdaufruf at a glance

The Fremdaufruf Service is a small, signed binary that runs on each
KIS workstation. It accepts the GET URL the KIS knows how to emit,
translates it into the authenticated POST request V.ap expects, and
303-redirects the workstation's browser to the resulting
`magicLink` — so the user lands on a pre-filled V.ap form inside
the KIS's embedded browser, the same outcome a POST-capable KIS
would have reached on its own.

Start with the [Fremdaufruf overview](Fremdaufruf/overview.md). KIS
integrators looking to configure their first integration go straight
to the [Benutzerhandbuch](Fremdaufruf/user-manual.md); system
administrators installing and operating the binary go to the
[Installation Manual](Fremdaufruf/installation.md).
