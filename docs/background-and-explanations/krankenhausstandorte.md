# Krankenhausstandorte Registry

The **Krankenhausstandorte** registry is the authoritative directory of German hospitals, their locations, facilities, and reporting identifiers. V.ap uses it as reference data to resolve partner-supplied identifiers — BSNR, Standort-ID, IK — into the name and postal context needed for downstream processing.

## Authoritative source

The registry is published by the hospital associations and is publicly available at:

[https://krankenhausstandorte.de](https://krankenhausstandorte.de)

The official site covers Krankenhäuser, Standorte, Einrichtungen, and BSNRs, with validity date ranges per record.

## Identifier model

The registry exposes three identifier layers that appear across V.ap integrations:

| Identifier | What it is |
|------------|------------|
| **IK** (Institutionskennzeichen) | 9-digit identifier for a *Krankenhaus* — the legal institution, often a corporate entity that may operate multiple sites. |
| **Standort-ID** | The 6-digit InEK code identifying a physical *Standort* (a location belonging to a Krankenhaus). Also used for reimbursement. |
| **BSNR** (Betriebsstättennummer) | 9-digit KBV facility number identifying an *Einrichtung* at a Standort — a ward, department, or functional unit that can report. |

## Test scenarios and missing entries

Not every integration scenario can reference a currently-valid registry entry — test environments, pre-production data, newly-commissioned facilities, or sandbox ApiUsers often need to submit requests where the BSNR (or other mandatory data) is not yet in the authoritative registry.

V.ap supports test scenarios for these cases. If you need to work with an ApiUser or with requests whose BSNRs or other mandatory fields won't resolve against the public registry, coordinate with us — we'll arrange the overlay needed for your use case.

For the ELIM+ product specifically, the concrete setup paths are documented in [ELIM+ Testing & Sandbox](../Products/ELIMPLUS/testing-and-sandbox.md).

## Related Documentation

- [ELIM+ API Integration Guide](../Products/ELIMPLUS/integration-guide.md)
- [ELIM+ Testing & Sandbox](../Products/ELIMPLUS/testing-and-sandbox.md)
