# Testing & Sandbox

How to submit a laboratory report (§7 Abs. 3 IfSG) against the DEMIS `LIVE_TEST`
environment rather than production. Test reports land in RKI's test
infrastructure and do **not** count as a statutory notification.

> **Not part of the API contract.** Test-mode is an attribute on the
> authenticated ApiUser, toggled by Vertama — it is not a flag in the memento
> payload. The same `POST /memento` request works in both modes; what changes
> is where the resulting submission lands.

Two supported paths, depending on which test credentials your organisation has.

## Path A — Shared Vertama test infrastructure

If you do not have gematik-issued test credentials, Vertama can route your test
reports through a shared test slot that Vertama operates. Setup is light
because the credentials are already in place.

**Setup:** Vertama enables test-mode on the ApiUser(s) that will submit test
reports. No cert exchange, no changes to your customer data.

**Usage:** sign in, use the form as usual with a real BSNR selected, submit. The
report goes to DEMIS `LIVE_TEST` under Vertama's shared test identity — the
bundle carries Vertama's test BSNR, not yours. This is deliberate: a test bundle
carrying a real-hospital BSNR would pollute DEMIS test data and cannot be
un-sent.

### Path A limitations

- **All-or-nothing.** Once test-mode is enabled for an ApiUser, *every* report
  that user submits goes to `LIVE_TEST` until test-mode is disabled. There is no
  per-report toggle today. For mixed real/test operation, use two ApiUsers — one
  flagged, one not.
- **Vertama-operated.** Turning test-mode on or off requires a Vertama operator.
  Customer-admin self-service is a future capability, not available today.

## Path B — Your own gematik-issued test account

If your organisation holds gematik-issued test credentials — a `test-hospNN` or
`test-labNNN` slot with its own IK, Standort, BSNR and P12 certificate — ELIM+
uses them directly.

**Setup** is a one-time collaboration with Vertama. Per slot:

**What your side provides** (exchanged via an agreed-upon secure channel):

- The slot's public registry data (IK, Standort-ID, BSNR, names, address)
- The P12 keystore and its password

**What Vertama configures on your behalf:**

- Links your test IK to your customer account
- Registers the credential for your test Standort; your test slot is overlaid
  onto the
  [Krankenhausstandorte registry](../../background-and-explanations/krankenhausstandorte.md)
  so your test BSNR resolves like any other registry entry
- Enables test-mode on the ApiUser(s) that will submit test reports

**Usage:** sign in, open the report form, pick your test BSNR from the picker
(it appears alongside any real BSNRs in your IK scope), submit. The report goes
to DEMIS `LIVE_TEST` under your own test identity.

## Telling a test report from a real one

- **Receipt** (post-submission screen and PDF) indicates the DEMIS environment
  was `LIVE_TEST` rather than `PRODUCTION`.
- **Journal entry** carries the `Test: true` marker plus the BSNR transmitted.

## Getting set up

Contact your Vertama representative. Path A can typically be enabled the same
day. Path B requires a short onboarding call to exchange credential material.

## Related Documentation

- [ELIM+ API Integration Guide](integration-guide.md) — the production flow;
  identical from the API's perspective
- [Krankenhausstandorte Registry](../../background-and-explanations/krankenhausstandorte.md) —
  how test BSNRs are made resolvable via overlay
