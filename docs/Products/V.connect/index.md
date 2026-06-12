# V.connect

V.connect is the family of products that close the gap between
what a KIS can natively do and what V.ap (the Vertama application
platform) requires for safe integration. Each V.connect service
targets a specific limitation of the KIS-to-V.ap interaction, and
may involve components on the customer's side of the network, in
V.ap, or on user-owned devices, depending on where the gap sits.

The family contract: every V.connect service is **operated by the
customer**, but **shipped, signed, and documented by Vertama**. The
operational pattern, naming, and support model are consistent
across services.

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
administrators installing and operating the binary receive the
**Betriebshandbuch** shipped with the binary itself, reachable from
the component's admin dashboard once installed.
