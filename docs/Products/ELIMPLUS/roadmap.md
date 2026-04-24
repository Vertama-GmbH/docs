# ELIM+ API Roadmap

This page tracks the direction of travel for the ELIM+ API. Items listed here are **not part of the current contract** ([v0.3.0](api.yml)) — the current generic-memento flow will keep working. We surface them so integration partners can plan against where things are headed.

Roadmap items are additive: when they ship, the contract gets a new version and migration notes are published alongside.

## Planned

### Disease-aware memento

The memento payload will gain a disease identifier plus disease-specific pre-fill fields (e.g. pathogen, test method, sample type). Today the memento is disease-agnostic and the user picks the disease on the index page.

### Deep-link magic token links

With a disease-aware memento, the magic link can land directly on `/elimplus/{disease}/` instead of the index, skipping the manual disease-selection step.

### Direct per-disease POST

JSON submission endpoints per disease will let fully validated payloads bypass the browser-review step — useful for integrators who want end-to-end automation once their data quality is trusted.

## Related Documentation

- [ELIM+ API Integration Guide](integration-guide.md)
- [v0.2 → v0.3 Migration Notes](migration-v0.2-to-v0.3.md)
