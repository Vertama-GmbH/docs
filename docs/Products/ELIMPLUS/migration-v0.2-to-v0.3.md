# Migration: ELIM+ API v0.2 → v0.3

This document summarises what changes for existing integrators moving from ELIM+ API **v0.2.0** to **v0.3.0**. The previous contract is preserved alongside the current one at [`api-v0.2.0.yml`](api-v0.2.0.yml); the current contract is [`api.yml`](api.yml).

## TL;DR

1. `MeldendeEinrichtung` is **flat** now: only `BSNR`, `Telefon`, `Email`. Drop `EinrichtungsName`, `Adresse`, and the nested `Kontakt` wrapper.
2. The API remains **disease-agnostic**. The memento carries generic pre-fill data; disease is selected by the human in the browser on the ELIM+ index page. Disease-specific memento pre-fill and direct per-disease POST endpoints are on the roadmap but not yet part of the API.
3. No endpoint paths changed. `POST /memento`, `GET /reports`, `GET /reports/{reportId}` are stable.

## 1. `MeldendeEinrichtung` flattened

### Before (v0.2)

```json
"MeldendeEinrichtung": {
  "EinrichtungsName": "Universitätsklinikum Musterstadt",
  "BSNR": "123456789",
  "Adresse": {
    "Strasse": "Hauptstr. 1",
    "PLZ": "12345",
    "Stadt": "Musterstadt"
  },
  "Kontakt": {
    "Telefon": "+49 123 456700",
    "Email": "meldungen@example-klinik.de"
  }
}
```

### After (v0.3)

```json
"MeldendeEinrichtung": {
  "BSNR": "123456789",
  "Telefon": "+49 123 456700",
  "Email": "meldungen@example-klinik.de"
}
```

### Why

`BSNR` is now the routing key. Name and postal address are resolved server-side at form-open time from the [Krankenhausstandorte registry](../../background-and-explanations/krankenhausstandorte.md) against the authenticated ApiUser's IK scope. Telephone is not carried in the registry, so it stays in the payload (nullable at memento creation, required at form submit). Email remains optional.

### What integrators need to do

- Remove `EinrichtungsName` and `Adresse` from `MeldendeEinrichtung`.
- Lift `Telefon` and `Email` out of the nested `Kontakt` to the top level.
- Make sure the `BSNR` you send resolves to an active Einrichtung under an IK that's in scope for your ApiUser. If it doesn't, you'll get a `400` with an `errors[]` entry naming the field.
- `EinsendendeEinrichtung` (the submitting institution) keeps its nested shape — only `MeldendeEinrichtung` changed.

## 2. Disease routing: API vs. browser

v0.2 documentation framed `/elimplus/{Disease}/` as if it were part of the API surface. **It isn't.** Those are **browser pages** the human navigates to after the magic link lands on the index. The API itself has no notion of disease; the memento carries no disease field.

### Current flow (v0.3)

```
[1] POST /api/elimplus/v1/memento         (generic pre-fill)
       ↓
[2] response.magicLink                     (/mtl/…/elimplus/?m=…)
       ↓
[3] user opens link → ELIM+ index page
       ↓
[4] user picks disease on index
       ↓
[5] /elimplus/{disease}/?m=…               (browser navigation, not API)
       ↓
[6] user reviews, submits → DEMIS bundle sent
```

The per-disease GET/POST routes in the server exist to serve the human's in-browser review. They're not integrator-facing endpoints.

## 3. Already-landed cleanups (recap for version-skippers)

If you're moving from an older pre-0.2 tutorial, these changes are already in effect:

- `KrankheitsCode` / `Krankheit` envelope removed — the memento never carried disease-specific data.
- `Fax` removed from contact fields — not emitted into the DEMIS bundle.

## 4. What's coming after v0.3

The direction of travel — disease-aware memento, deep-link MTL, direct per-disease POST — is tracked on its own page: [ELIM+ Roadmap](roadmap.md). All additive to the v0.3 flow.

## Links

- [Integration Guide](integration-guide.md) — full walkthrough of v0.3
- [`api.yml`](api.yml) — current OpenAPI contract (v0.3.0)
- [`api-v0.2.0.yml`](api-v0.2.0.yml) — previous contract for reference
