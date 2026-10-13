# References index

One folder per domain; each has its own `INDEX.md` with sources, verified dates and known limits per file. Read
that index first, then open only what the request needs.

| Folder | Surface | Covers | Verified |
|---|---|---|---|
| `xml-api/` | **Sage Intacct XML Web Services API** (DTD 3.0, `xmlgw.phtml`) | Extraction of the developer portal and Sage's request schema: protocol basics (`api-basics.md`), a review checklist (`common-mistakes.md`), the Order Entry / Purchasing / Inventory guide (`oe-po-inventory.md`), the generic-function grammar (`functions.md`, 52 functions), the operation catalogue (`objects.md`, 1,694 operations), one generated file per API Reference section (`objects/`, 17 files, 197 pages, 2,653 parameter tables) and an object-definition snapshot of a clean developer company on 2026 Release 3 (`snapshot/`, 632 objects, 21,342 fields, 2,039 relationships) | 2026-10-13 |

Nothing is bundled for the **REST API**, Platform Services scripting, Smart Events and Smart Rules beyond their
API reference pages, or the Interactive Custom Report Writer.

Every file carries a provenance header:

```
<!-- source: <URL or document> | version: <Sage Intacct release or API version, or "not stated"> | verified: YYYY-MM-DD -->
```

See `MAINTENANCE.md` for the conventions and how to regenerate `xml-api/`.
