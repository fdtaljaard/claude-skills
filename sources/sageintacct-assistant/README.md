# sageintacct-assistant: builder inputs

Machine-readable inputs that `skills/sageintacct-assistant/scripts/` needs to regenerate a bundled reference. They
are kept here, outside the skill folder, so they are never packaged or loaded at runtime, and so that anyone can
rebuild the generated files and review a builder change by diffing its output.

| File | What it is | Licence and scrubbing | Regenerates |
|---|---|---|---|
| `api.v3.0.xsd` | `v3.0/api.xsd` from Sage's public schema repository https://github.com/Intacct/intacct_dtd, the XML Schema the Web Services gateway validates DTD 3.0 requests against; commit `89275604db` of 2024-05-07 (the repository's README states the schemas are no longer enhanced since the REST API went GA in 2025 Release 1). SHA-256 `f6265062d4fa0554bfbf2e2a789a31fe7bcf018a8cd8e3f69f18cf051561fa49`. | Apache License 2.0 (the repository's `LICENSE`); redistributed unchanged. Nothing to scrub: it holds element definitions only. | `skills/sageintacct-assistant/references/xml-api/functions.md` |
| `object-definitions-2026-Release-3.zip` | The scrubbed output of `scripts/dump_object_definitions.py` run on 2026-10-13 against a clean developer company on **2026 Release 3**, packed with its `--pack` mode: `inspect.xml` (632 objects), `lookup/<OBJECT>.xml` (632 files, the `<data>` of each `lookup` result), `manifest.json`. 0.8 MB, SHA-256 `b962c0f6e2e7d19d01e898c91784722f29e5e14c07fb98cf449a40e8ffb4a1ba`. | The content is Sage's object metadata, not company data: 13 custom (`ISCUSTOM`) fields on 3 objects were removed, the per-transaction-definition `inspect` entries of the document objects were collapsed to the generic entry (definition names are company configuration), the `<control>` block (sender ID), session ID, endpoint, company ID and user ID were never written, and the output was grepped for the company's identifiers before committing (`MAINTENANCE.md`, "Object-definition snapshot"). | `skills/sageintacct-assistant/references/xml-api/snapshot/` |

The developer portal cache (developer.intacct.com, about 275 HTML pages) is **not** kept here: it is re-fetched by
`scripts/fetch_developer_portal.py` into a scratch folder, and the generated files cite the page URLs.

To regenerate the function grammar, run from the repository root:

```
python -I skills/sageintacct-assistant/scripts/build_functions_reference.py --xsd sources/sageintacct-assistant/api.v3.0.xsd --out skills/sageintacct-assistant/references/xml-api/functions.md --verified YYYY-MM-DD --xsd-note "commit 89275604db of 2024-05-07"
```

To regenerate the snapshot:

```
python -I skills/sageintacct-assistant/scripts/build_object_snapshot.py --dump sources/sageintacct-assistant/object-definitions-2026-Release-3.zip --out skills/sageintacct-assistant/references/xml-api/snapshot --release "2026 Release 3" --verified YYYY-MM-DD
```

The full procedures are "Refreshing `references/xml-api/`" and "Object-definition snapshot" in
`skills/sageintacct-assistant/MAINTENANCE.md`.
