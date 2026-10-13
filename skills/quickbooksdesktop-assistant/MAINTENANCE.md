# Maintenance

How this skill is built and how to extend it. The skill is reference-backed: its trustworthiness comes
from the bundled files in `references/` and the discipline of citing them or the OSR. Keep that intact.

## Design constraints (do not break)

- **Generic product knowledge only.** This skill must contain **no client-specific or proprietary
  integration content** — no customer names, no bespoke schema, no internal project detail. Everything
  here is publicly documented QuickBooks Desktop SDK knowledge. If you draft new material from a real
  integration, strip it down to the general QuickBooks concept before it goes in.
- **Desktop, not Online.** Scope is the QBD SDK (qbXML / QBFC / QBXMLRP2 / QBWC). QBO is out of scope on
  purpose; the scope guard in `SKILL.md` § 1 keeps the skill from answering QBO questions.
- **Verify or flag.** Never add an object, field, OR member or version from memory as if confirmed. Either
  verify it against the OSR and cite it, or mark it "confirm in the OSR".

## Current state of the references

The bundled references are **drafts**: written on 2026-10-06 from author knowledge of the stable QuickBooks
Desktop SDK (qbXML spec through 16.0, the last major version) and **not yet checked** against Intuit's
documentation. Each file's provenance header says what still needs confirming; when a file has been checked,
replace its `DRAFT` header with the documents it was checked against and the date, and update its `INDEX.md` row.
They are a **curated, structural** reference — the object model, the common objects, correct QBFC idioms, and
connectivity — **not** a complete field dump. That is the main opportunity to raise rigor (below).

## Raising rigor: bundle real OSR data

The single biggest improvement is to bundle an export of Intuit's **OSR (onscreen reference)** so the
skill can verify every field and its introducing version against a local file, the way the Sage-family
skills use a data dictionary. Options, roughly in order of fidelity:

1. **SDK-shipped reference.** The QuickBooks SDK (from developer.intuit.com) installs local documentation,
   including the qbXML spec and a QBFC help `.chm`. Extract object/field tables per request into
   `references/qbxml/objects/<Object>.md` and add an `INDEX.md` row per file with the SDK version and date.
2. **OSR scrape.** The OSR is a JavaScript app; a full automated scrape is awkward but the underlying
   spec data (`qbxmlops*.xml` / the OSR's data files) can be parsed into per-object field tables.
3. **Per-object pages on demand.** Short of a bundle, keep citing the live OSR object pages — which the
   skill already does for anything not in `objects.md`.

When you add bundled OSR data, update `references/qbxml/INDEX.md` and soften the "curated subset, not a
field dump" caveats in `objects.md` / `object-model.md` to point at the fuller local data.

## Add a capability

The skill routes in `SKILL.md` § 1. To add a capability (e.g. report requests, payroll, a specific
inventory workflow):

1. Add a routing row in § 1 and a numbered workflow section.
2. Create `references/<capability>/` with an `INDEX.md` and the reference file(s).
3. Add 1–2 test prompts to `evals/evals.json` tagged with the new capability.
4. Update `SKILL.md` § 7 Layout and the `description` frontmatter if the new capability introduces
   trigger terms a user would type.

## Refresh for a new SDK version

The SDK is frozen at 16.0, so this is unlikely — but if Intuit ships a new qbXML version: update the
version guidance in `references/qbxml/object-model.md` (§ versions), re-extract any bundled OSR data, and
note the new `SupportedQBXMLVersion` expectations.

## Packaging and validation

Package the skill into a `.skill` file for upload to the Claude desktop app / claude.ai with the bundled
packaging script, run from the repository root (needs PyYAML):

```bash
python skills/quickbooksdesktop-assistant/scripts/package_skill.py skills/quickbooksdesktop-assistant dist
```

It validates the frontmatter (`name` matches the folder, `description` <= 1024 characters, `compatibility`
<= 500) and refuses to write the archive on any failure. `scripts/` is maintenance tooling only and is never
needed at runtime.

Before packaging, sanity-check that:
- `SKILL.md` frontmatter `name` is `quickbooksdesktop-assistant` and the `description` is trigger-rich.
- Every `references/` subfolder has an `INDEX.md`.
- No client-specific content has crept in (grep for customer/project names).
- The scope guard and ground rules are intact.

## Evals

`evals/evals.json` holds one or two prompts per capability plus must-pass guardrail prompts (the QBO scope
guard and the "no direct DB" rule). Run them through the skill-creator's eval loop when you change routing
or ground rules, and add a prompt whenever you add a capability or fix a recurring wrong answer.
