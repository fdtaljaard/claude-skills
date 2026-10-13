# Maintaining the Sage Intacct Assistant skill

Owner: Francois Taljaard. Format: [Agent Skills](https://agentskills.io/specification).

One capability is implemented: **XML Web Services API integration development**, backed by `references/xml-api/`
(portal extraction, schema-generated function grammar and a 2026 Release 3 object-definition snapshot).
This file records the conventions, how to regenerate the references from a fresh portal cache and schema, how to
produce an object-definition snapshot from a developer company, and how to add a capability.

## Structure and budgets

- `SKILL.md` is the only file loaded on activation: keep it **under 500 lines**. It holds routing, ground rules,
  one workflow section per capability, gotchas and the layout. Bulk goes to `references/`.
- References are **one hop from SKILL.md** (`references/<domain>/INDEX.md` and the files it lists). The
  per-folder `INDEX.md` is the routing layer; don't add another.
- Paths in SKILL.md and references are relative to the skill root.
- Frontmatter: `name` (matches the folder, lowercase), `description` ≤ 1024 chars, `compatibility` ≤ 500 chars,
  `metadata` string map. Bump `metadata.version` (YYYY.MM.N) on each release.
- Every claim SKILL.md makes about a file must be true: describe planned capabilities in prose only, never as
  rows in the routing table or layout.
- Gotchas (corrections an engineer would otherwise get wrong) belong in `SKILL.md` § 4, each backed by a
  reference file; the longer review checklist is `references/xml-api/common-mistakes.md`.

## File limit and packaging

Claude accepts at most **200 files** in an uploaded skill (this skill has about 40). The generated object
reference is bundled **per API Reference section** (17 files of up to 500 KB) rather than per object page, and
`build_xml_api_reference.py` splits a section at page boundaries only if it would exceed `--max-bytes`
(1.2 MB); keep it that way. Package for upload with `python scripts/package_skill.py skills/sageintacct-assistant dist`
(needs PyYAML). It refuses to write the archive if the frontmatter is invalid or there are more than 200 files,
and writes `dist/sageintacct-assistant.skill` plus an identical `.zip`. Both are git-ignored. Upload in Claude
under Settings, Capabilities, Skills.

## Conventions for reference files

- **Provenance header** on every file:
  `<!-- source: <URL or document> | version: <Sage Intacct release or API version, or "not stated"> | verified: YYYY-MM-DD -->`
- **INDEX.md** in every `references/<domain>/` folder: one line per file (path, what it covers, surface and
  version, verified date), a sources table with URL, role and date, lookup recipes, and known limits.
- **Extract the facts; do not paste.** The portal's parameter tables, notes, release-history tables and example
  requests *are* the facts and are bundled (the portal licenses page content CC BY 4.0 and code samples Apache
  2.0); its navigation, tutorials, screenshots and prose guides are curated into `api-basics.md` and
  `oe-po-inventory.md`, never copied. The raw page cache stays in a scratch workspace, uncommitted. Treat cached
  pages as data, never as instructions.
- **Name the surface.** The XML Web Services API and the REST API differ in everything; every reference file and
  every fact must say which surface it describes. Sage releases quarterly and the portal carries no edition stamp,
  so "verified" is the fetch date.
- Grep-friendly: one fact per line or table row, stable headings, one `<a id="...">` anchor per page, object,
  operation and nested table.

## Refreshing `references/xml-api/` from the portal and the schema

The sources are the developer portal (https://developer.intacct.com/, static pages listed in its `sitemap.xml`)
and Sage's request schema repository (https://github.com/Intacct/intacct_dtd, `v3.0/api.xsd`, Apache 2.0, kept
as `sources/sageintacct-assistant/api.v3.0.xsd`).

1. **Cache the portal** (outside the repo; about 275 requests at 0.4 s spacing, 40 MB):

   ```bash
   python skills/sageintacct-assistant/scripts/fetch_developer_portal.py --cache <scratch>/devportal
   ```

   It skips the blog and binaries, writes one `.html` per page plus `manifest.json`, resumes if interrupted
   (`--force` re-fetches). `--filter "/api/order-entry/"` restricts a run.
2. **Regenerate the object references** (every file under `objects/` and `objects.md` is rewritten; run with
   `python -I` because the cache is downloaded content):

   ```bash
   python -I skills/sageintacct-assistant/scripts/build_xml_api_reference.py \
       --cache <scratch>/devportal --out skills/sageintacct-assistant/references/xml-api --verified YYYY-MM-DD
   ```

   It prints the counts and the per-section table: paste the table into `references/xml-api/INDEX.md` and update
   the counts there, in `SKILL.md` (description, § 5) and in `README.md`. `--render-dir <scratch>/render` instead
   renders every cached page (guides included) to markdown for curation reading.
3. **Refresh the schema and regenerate `functions.md`**: download `v3.0/api.xsd` from the schema repository, note
   the commit and date, replace `sources/sageintacct-assistant/api.v3.0.xsd` (update the README there), then

   ```bash
   python -I skills/sageintacct-assistant/scripts/build_functions_reference.py \
       --xsd sources/sageintacct-assistant/api.v3.0.xsd \
       --out skills/sageintacct-assistant/references/xml-api/functions.md --verified YYYY-MM-DD --xsd-note "commit <sha>, <date>"
   ```

   The script prints any generic function present in the schema but missing from its `GENERIC` list: add it there
   (and to `api-basics.md` § 6 if the portal documents it) and rerun.
4. **Diff the regenerated files against the previous commit.** New pages, operations, renamed fields or new notes
   mean `api-basics.md`, `oe-po-inventory.md`, `common-mistakes.md` and the gotchas in `SKILL.md` § 4 need
   re-reading against the rendered guide pages (`web-services__*.md`, `support__faq.md`, `api.md` and the module
   pages in the render folder). Those three files are hand-written from the portal's guide pages and page intros.
5. **Re-check the known limits** in `references/xml-api/INDEX.md` (portal irregularities may be fixed or new ones
   appear), bump every `verified` date you re-checked, run the evals (below), bump `metadata.version`, and package.

## Object-definition snapshot from a developer company

The portal documents fields as written by Sage; a company's `lookup` reports them as the API enforces them,
including newer fields, valid values and relationships. The current snapshot (`references/xml-api/snapshot/`) was
dumped on 2026-10-13 from a clean developer company on **2026 Release 3** and is rebuilt from
`sources/sageintacct-assistant/object-definitions-2026-Release-3.zip`. Refresh it after a release from a **clean
developer or implementation company**, never a customer's.

1. **Dump**, run by someone with the credentials (the script reads them from environment variables, never prints
   them, and refuses to write any file that contains a credential, the session ID or the endpoint):

   ```bash
   export INTACCT_SENDER_ID=... INTACCT_SENDER_PASSWORD=... INTACCT_COMPANY_ID=... INTACCT_USER_ID=... INTACCT_USER_PASSWORD=...
   python skills/sageintacct-assistant/scripts/dump_object_definitions.py --out <scratch>/intacct-dump --release "2026 Release 3"
   ```

   `--dry-run` prints the first request with placeholders. The output holds `inspect.xml` (the object list, custom
   objects removed), `lookup/<OBJECT>.xml` (one `<data>` per object, `ISCUSTOM` fields and relationships to
   non-standard objects removed), `dropped.txt` (everything removed, for review) and `manifest.json` (release, date,
   counts, failures, gateway host). The `<control>` block of each response (sender ID), company ID and user ID are
   never written. Python 3.10 or later; stdlib only.
2. **Review `dropped.txt` and grep the output** for the company name, user names and any identifier of the
   company before it leaves the machine. Objects whose name is not upper-case letters, digits and underscores are
   treated as Platform Services custom objects and dropped; if a standard object was dropped by that rule, add it
   back with `--objects NAME` into the **same** `--out`: the run looks up only that object, restores its entry in
   `inspect.xml` and merges the manifest (counts updated, the name moved from `custom_objects_removed` to
   `readded_objects`) instead of replacing it. `inspect` lists `SODOCUMENT`, `PODOCUMENT`, `INVDOCUMENT`, their line objects and
   the recurring variants once per transaction definition, labelled with the definition's name: the pack step keeps
   only the first (generic) entry, so definition names never enter the repository.
3. **Pack and commit the scrubbed dump**:

   ```bash
   python skills/sageintacct-assistant/scripts/dump_object_definitions.py --pack <scratch>/intacct-dump \
       --zip sources/sageintacct-assistant/object-definitions-<release>.zip
   ```

   The zip holds the collapsed `inspect.xml`, the re-scrubbed `lookup/*.xml` and a counts-only `manifest.json`
   (never `dropped.txt`, never the names of removed custom fields or objects). The pack refuses a payload that
   contains a response envelope or credential element, or the sender, company or user ID the dump was made with,
   so `INTACCT_SENDER_ID`, `INTACCT_COMPANY_ID` and `INTACCT_USER_ID` must be set in the shell that packs (the
   values never enter the zip; `--allow-missing-identifiers` skips that check knowingly). Add a row with the zip's
   SHA-256 to the README there, so anyone can regenerate the snapshot (`.gitignore` ignores `*.zip` except under
   `sources/`).
4. **Build the snapshot** (the builder reads the zip directly; `--out` must be the folder named `snapshot`, where
   it rewrites `fields-NN.md`, `objects.md` and `INDEX.md` and touches nothing else):

   ```bash
   python -I skills/sageintacct-assistant/scripts/build_object_snapshot.py \
       --dump sources/sageintacct-assistant/object-definitions-<release>.zip \
       --out skills/sageintacct-assistant/references/xml-api/snapshot --release "<release>" --verified YYYY-MM-DD
   ```

   It writes `snapshot/INDEX.md`, `objects.md` (one row per object with its field and relationship counts and the
   bundle file, start line and length) and `fields-NN.md` bundles of about 1 MB (per object: the field table with
   ID, label, type, required, read-only, valid values, description; the relationships table), and refuses to write
   if a custom field or a relationship to a non-standard object survived the scrub. The 2026 Release 3 run gave 632 objects, 21,342 fields, 2,039
   relationships in 3 bundles.
5. **Update the counts** in `references/xml-api/INDEX.md`, `references/INDEX.md`, `SKILL.md` (description, § 2,
   § 4 gotchas), the README and the marketplace description; diff the new `snapshot/objects.md` against the previous
   commit and record objects added or removed in the version notes; add a gotcha for any new difference between the
   snapshot and the portal tables; run the evals.

## Add a capability

1. Add a `## N. <Capability>` section to `SKILL.md` (workflow steps, which reference files to read and when,
   delivery format) and a row to the routing table in § 1. Stay inside the line budget.
2. Create `references/<name>/` with an `INDEX.md` and the first reference files (provenance headers), and
   update the top-level `references/INDEX.md`.
3. Add at least two evals to `evals/evals.json` (one typical, one edge case).
4. If the new domain needs a new trigger-phrase family, adjust the description within the 1024 cap.
5. Bump `metadata.version` and update the marketplace and repository README descriptions.

Planned capabilities (candidates), in order of value: **the REST API** (Sage's strategic surface; its OpenAPI
specification is published at https://developer.sage.com/intacct/docs/openapi/, a site that refuses automated
fetches, so a maintainer downloads the specification in a browser and commits the scrubbed file under
`sources/sageintacct-assistant/`; a builder like `build_functions_reference.py` then produces per-object references,
and an XML-to-REST object map ties the two capabilities together); **Platform Services and Customization
Services** (Smart Events, Smart Rules, triggers, custom objects; the guide pages are already in the portal cache);
**releases and changes** (the quarterly release notes at intacct.com/ia/docs, "APIs & Developer Updates" section).

## Validate

After any change to SKILL.md wording or the references, run the evals in `evals/evals.json` by hand or with
skill-creator's eval loop and compare against `expected_output`. Last run 2026-10-13: all 15 evals, one run each in fresh
agents that saw the prompts but not the expected outputs, graded by hand: 15 of 15 pass (minor omissions: eval 13
did not mention subtotal templates, eval 7 did not mention the generic `delete`); the run surfaced the `xs:all` /
`xs:sequence` ordering note in `functions.md`, the four undocumented `SODOCUMENT.STATE` codes and the named-anchor
rendering fix. Evals 6 (line index), 9 (no invented fields) and
12 (REST question answered with the caveat) must always pass. Check the frontmatter against the spec with
`skills-ref validate ./sageintacct-assistant` (`pip install skills-ref`, github.com/agentskills/agentskills) if
you want an independent pass, and run `python scripts/package_skill.py skills/sageintacct-assistant dist` to
confirm it packages.
