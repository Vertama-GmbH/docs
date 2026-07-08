# Documentation sources

This file documents how the docs.vertama.com site is sourced — where each
document is authored canonically, where mirror copies live, and how content
moves between repositories.

It is not part of the published documentation site (it lives at the repo
root, outside the `docs/` tree). It serves two audiences: contributors who
need to know where to make edits, and the eventual sync automation that
will replace today's manual mirroring.

## The model

Documentation lives in the repo that owns the subject it describes:

- This repo (`Vertama-GmbH/docs`) is the **publishing layer**. It only
  authors content that is purely product positioning — narrative about
  products that doesn't trace to a specific codebase.
- Other repos own engineering content (specs, architecture rationale,
  wire contracts) and customer-facing manuals tightly coupled to a
  product's UI or operations.
- Content that originates in another repo and surfaces here is **mirrored**
  — manually for now, automatically later. The mirror is never the
  authoritative copy.
- Some content does **not** mirror here at all because it travels with its
  own delivery vehicle (e.g. an operations manual shipped with a binary).

Multi-language convention: files without a language suffix are the default
language (English). Files with a `.<lang>.md` suffix are localized versions.
The `mkdocs-static-i18n` plugin renders a language switcher in the header
and falls back to the default language when a translation is missing.

## Provenance table

| Document | Path here | Canonical source | Mirror? | Sync mechanism |
|---|---|---|---|---|
| V.connect intro | `Products/V.connect/index.md` | this repo | canonical | n/a |
| Fremdaufruf Overview (EN) | `Products/V.connect/Fremdaufruf/overview.md` | this repo | canonical | n/a |
| Fremdaufruf Übersicht (DE) | `Products/V.connect/Fremdaufruf/overview.de.md` | this repo | canonical | n/a |
| Fremdaufruf Architecture | `Products/V.connect/Fremdaufruf/solution-outline.md` | `mcp-health/V.connect` → `fremdaufruf/solution-outline.md` | yes | manual copy |
| Fremdaufruf URL-Builder (DE) | `Products/V.connect/Fremdaufruf/url-builder.de.md` | `Vertama-GmbH/elim` (historical name; the V.ap repo) → `docs/external/v.connect/fremdaufruf/url-builder.md` | yes | manual copy |
| Fremdaufruf Betriebshandbuch | — | `mcp-health/V.connect` → `fremdaufruf/betriebshandbuch.html` | **no** — ships with binary; admin dashboard serves at `/admin/help` | n/a |
| Fremdaufruf Präsentation (DE) | `Products/V.connect/Fremdaufruf/presentation/` | `mcp-health/V.connect` → `fremdaufruf/presentation/` | yes | `make sync-fremdaufruf-deck` — pulls the self-contained reveal.js deck from V.c, strips `<aside class="notes">` speaker-note blocks (presenter guidance not intended for the public site) via `scripts/strip-notes.py`, copies brand assets and images unchanged |

## Internal mirror points

Not published here, but tracked because the cross-repo dependency is real
and the next sync needs to know what to preserve:

| Artifact | Path | Canonical source | Sync mechanism |
|---|---|---|---|
| Fremdaufruf Presentationsfolien — URL-Builder Screenshots | `mcp-health/V.connect` → `fremdaufruf/presentation/images/{04-platzhalter-edit, 05-aktuelle-vorlage}.png` | `Vertama-GmbH/elim` → `docs/external/v.connect/fremdaufruf/images/` | manual copy; refresh when V.ap URL-Builder UI changes |

## Transition state

The current mirror-by-manual-copy state is intentional V1 behavior, not the
long-term target. The end state varies per document:

- **The URL-Builder doc** is the first candidate for a transition to **live
  link**. Once V.ap serves its own documentation directly (the V.ap
  application already serves OpenAPI; documentation can follow), this
  site's URL-Builder page becomes a thin pointer to the V.ap-hosted
  authoritative version. No mirror, no drift, ownership = publication.
- **The Architecture doc** is a candidate for **automated mirror** (e.g.
  `mkdocs-multirepo-plugin` pulling at build time, or a CI sync). Both
  ends remain markdown; only the sync mechanism upgrades.
- **The Betriebshandbuch** is a different model entirely: it travels with
  its delivery vehicle (the binary). Not mirrored here; Vertama supplies
  it on request prior to deployment for IT-security review.

## When to update this file

- Adding a new doc to the site: add a row.
- Renaming or moving a doc: update the row.
- Moving canonical source between repos: update the canonical column.
- Removing a doc: remove the row.
- Designing sync automation: this file is the spec.
