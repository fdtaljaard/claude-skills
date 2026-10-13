
# ERP Skills for Real Integrators

[![License: MIT](https://img.shields.io/github/license/fdtaljaard/claude-skills)](LICENSE)
[![Latest release](https://img.shields.io/github/v/release/fdtaljaard/claude-skills)](https://github.com/fdtaljaard/claude-skills/releases)
[![Claude Code plugin marketplace](https://img.shields.io/badge/Claude%20Code-plugin%20marketplace-5A4FE5)](#installing-a-skill)

Reference-backed [Agent Skills](https://agentskills.io/specification) for real ERP work — built for consultants, developers, and integrators.

ERP systems are complicated. Their schemas, APIs, SDKs, versions, and configuration rules are even worse.

These skills give Claude the references it needs to work with real ERP systems — Sage 300, Sage 200 Evolution, Sage X3, SAP Business One, Acumatica, and more. No plausible guessing. No invented fields. No hallucinated APIs.

Small, composable skills built around vendor documentation, data dictionaries, release notes, SDK references, and other authoritative sources. Give your agent the knowledge. Keep control of the engineering.



## Skills

| Skill | What it does |
|---|---|
| [`sageintacct-assistant`](skills/sageintacct-assistant) | Sage Intacct cloud financial management / ERP assistant for consultants and integrators: **XML Web Services API** integration development from a bundled extraction of the Sage Intacct developer portal (verified 2026-10-13) and Sage's DTD 3.0 request schema: the request envelope and the two `controlid`s, sessions and endpoints, the three status levels and error categories (`XL03000006`, `GW-0010` / 429, `BL01001973`) with `uniqueid` recovery, the `query` grammar and `readByQuery` string syntax with paging, `mm/dd/yyyy` dates and number formats, multi-entity rules, concurrency and timeout guidance, every documented object page (197 pages, 1,694 operations in 17 modules) with its parameter tables, examples and release history, the grammar of all 52 generic functions and the 243 legacy function names, exact object, field, valid-value and relationship names from an object-definition snapshot of a clean developer company on **2026 Release 3** (632 objects, 21,342 fields, 2,039 relationships), a guide to Order Entry, Purchasing and Inventory Control flows (transaction definitions, `docparid`, conversions, line numbering, `PRRECORDKEY`), and a 36-rule common-mistakes checklist for code reviews. The REST API is not covered yet. More capabilities to follow. |
| [`cin7-assistant`](skills/cin7-assistant) | Cin7 inventory and order management assistant for consultants and integrators: **Cin7 Core** (formerly DEAR Systems) API v2 integration development from a bundled extraction of the Cin7 Core developer portal (verified 2026-10-07): the two authentication headers and per-application limits, pagination (`page` / `limit` / `Total`), status codes and the 60-calls-per-minute limit, UTC ISO 8601 dates, void vs undo, the overwrite semantics of sub-document POSTs, the stage preconditions of sales (quote, order, pick, pack, ship, invoice, credit note, payment) and purchases (the `/advanced-purchase` family), every documented endpoint (295 actions in 33 groups) with field tables, parameters, request and response bodies, the status and type value lists, webhook events and retry rules, and a 31-rule common-mistakes checklist for code reviews. Cin7 Omni is not covered yet. More capabilities to follow. |
| [`sage300-assistant`](skills/sage300-assistant) | Sage 300 (Accpac) ERP assistant for consultants and integrators: verified T-SQL views/queries from bundled AOM data dictionaries, version/upgrade guidance and release notes, and C# against the `ACCPAC.Advantage` .NET library. |
| [`sage200-assistant`](skills/sage200-assistant) | Sage 200 Evolution (Pastel Evolution) ERP assistant for consultants and integrators: C# development against the `Pastel.Evolution` .NET SDK — connecting via `DatabaseContext`, the record load/set/`Save()` pattern, posting transactions, and generating correct code from a bundled class and enum reference (152 types, 41 enums) extracted from the shipped SDK CHM. More capabilities to follow. |
| [`sagex3-assistant`](skills/sagex3-assistant) | Sage X3 ERP assistant for consultants and integrators: verified SQL views/queries and table/field lookup from a bundled Sage X3 **V11** table dictionary (every table with abbreviation, keys/indexes, columns, data types, dimensions, local-menu enum values and foreign-key link expressions) compiled from Sage's online help; versions and upgrades — V12 release/patch naming and lifecycle, platform prerequisites per release, upgrade paths and procedures, and per-release notes 2023 R2 → 2026 R1 with the tables whose definition changed. More capabilities to follow. |
| [`sapb1-assistant`](skills/sapb1-assistant) | SAP Business One ERP assistant for consultants and integrators: object type number, table and primary key lookup from a bundled list of all B1 object types, verified SQL views/queries from bundled B1 10.0 and 9.3 data dictionaries (tables, columns, indexes, valid values, parent-table links), C# development against the DI API (`SAPbobsCOM`) from a bundled DI API 10.0 class and enum reference, and Service Layer (REST / OData v4) integration guidance (session handling, query options, ETags, batch, SQLQueries, FP 2602 webhooks) summarised from SAP's documentation. More capabilities to follow. |
| [`acumatica-assistant`](skills/acumatica-assistant) | Acumatica ERP assistant for consultants and integrators: REST integration development against the contract-based REST API from a bundled extraction of Acumatica's Integration Development Guide (**2026 R2**): cookie sign-in and OAuth 2.0 / OIDC, endpoint and contract versions (Contract Version 4 vs 5), the JSON record shape, `$filter` / `$expand` / `$select` per contract version, CRUD rules, actions and long-running operations, processing forms, generic inquiries, reports, custom and user-defined fields, attachments, license limits, push notifications and webhooks, plus a catalogue of the 187 example requests the guide documents and a common-mistakes checklist for code reviews; exact entity, field and action names from a generated snapshot of the `Default/25.200.001` contract (**2025 R2**: 119 entities, 5,338 fields, 163 actions); OData data access (DAC-based and generic-inquiry-based OData v4 reads for BI, reporting and delta syncs: URLs, auth and licence, `$filter` / `$expand`, deleted-record tracking, CORS, Excel and Power BI) from the Reporting Tools Guide (**2026 R2**), with a generated DAC `$metadata` snapshot of a clean 2026 R2 instance (2,265 DACs, 42,288 fields, 23,576 navigation properties) for exact DAC, field and navigation names. More capabilities to follow. |
| [`quickbooksdesktop-assistant`](skills/quickbooksdesktop-assistant) | QuickBooks **Desktop** SDK assistant for consultants and integrators: qbXML / QBFC C# development (`QBSessionManager` session lifecycle, message sets, Add/Mod/Query requests, OR aggregates, `LinkToTxn`, response and `StatusCode` handling); object and field reference (the `ListID` / `TxnID` / `EditSequence` model, request verbs, OR choice fields, spec versions, and a catalogue of the common lists and transactions); and setup and connectivity (QBFC vs QBXMLRP2 vs the Web Connector, open modes, app authorization and certificates, the 32-bit / STA constraints and common connection error signatures). Targets QuickBooks Desktop (qbXML), not QuickBooks Online. More capabilities to follow. |

## Installing a skill

These skills run inside **[Claude Code](https://www.claude.com/product/claude-code)** — Anthropic's assistant that you use through the Claude desktop app or the `claude` command. You don't need to write any code to install or use them. You add this collection once, then install whichever skill you need.

**Step 1 — Add this collection (do this once).** In Claude Code, type:

```
/plugin marketplace add fdtaljaard/claude-skills
```

This just tells Claude where to find the skills. You only ever do it once.

**Step 2 — Install the skill you want.** Type one of:

```
/plugin install sage300-assistant@fdtaljaard-skills
/plugin install sage200-assistant@fdtaljaard-skills
/plugin install sapb1-assistant@fdtaljaard-skills
/plugin install sagex3-assistant@fdtaljaard-skills
/plugin install acumatica-assistant@fdtaljaard-skills
/plugin install quickbooksdesktop-assistant@fdtaljaard-skills
/plugin install sageintacct-assistant@fdtaljaard-skills
```

(Pick the one for the system you work with — Sage 300, Sage 200 Evolution, SAP Business One, Sage X3, Acumatica, QuickBooks Desktop, or Sage Intacct.)

**Step 3 — Just ask your question in plain English.** There's no special command to "turn it on" — the skill switches itself on whenever your question is about that product. For example: *"I need a Sage 300 view of open sales orders with the customer name and total."* Claude looks the answer up in the bundled reference and shows its working.

**Keeping it current.** To get the latest version later, type `/plugin marketplace update fdtaljaard-skills`. To remove a skill, type `/plugin uninstall <skill-name>@fdtaljaard-skills`.

<details>
<summary><b>Other ways to install (for developers)</b></summary>

**With the [skills CLI](https://agentskills.io):**

```bash
npx -y skills add fdtaljaard/claude-skills --skill sage300-assistant --agent claude-code
```

**Manually** — copy the skill folder into your Claude skills directory (`~/.claude/skills/` for all projects, or `<project>/.claude/skills/` for one):

```bash
git clone https://github.com/fdtaljaard/claude-skills.git
cp -r claude-skills/skills/sage300-assistant ~/.claude/skills/
```

Each skill's `SKILL.md` describes when it triggers and how it works; `MAINTENANCE.md` covers how it is built and kept up to date.

</details>

## Layout

```
skills/
  <skill-name>/
    SKILL.md        # entry point loaded on activation
    references/     # bulk reference material, read on demand
    scripts/        # maintenance tooling (not needed at runtime)
sources/
  <skill-name>/     # scrubbed machine-generated inputs a builder needs to regenerate a reference (never packaged)
```

## Contributing

Issues and pull requests are welcome — corrections to a reference, a new skill, or a new capability on an existing one. See [CONTRIBUTING.md](CONTRIBUTING.md) for how skills are structured and the bar a change should meet (every claim verifiable and cited), and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for how we work together. To report a problem with the data a skill returns, or a security concern, see [SECURITY.md](SECURITY.md).

## License

The code and original content in this repository are released under the [MIT License](LICENSE). Reference material derived from Sage's documentation and product metadata remains subject to Sage's own terms (see the disclaimer below).

## Disclaimer

Sage 300 and Accpac are trademarks of their respective owners. This project is independent and not affiliated with or endorsed by Sage. Reference material bundled with `sage300-assistant` is derived from Sage's published documentation and product metadata for use as a lookup aid; always verify against official Sage documentation before acting on it in a production system.

Sage 200 Evolution and Pastel Evolution are trademarks of their respective owners. `sage200-assistant` is independent and not affiliated with or endorsed by Sage. Its SDK reference is extracted from the shipped `Pastel.Evolution.chm` and XML documentation for SDK version **11.0.0.10 only** (other versions are not included), and Sage's own terms apply to that material. It documents the `Pastel.Evolution` object SDK, not the Evolution ODBC/SQL layer or the Connector/API web service. Verify against Sage's own documentation, and on the client's installed SDK, before relying on any of it — the SDK binds to a licensed Evolution install of a matching version.

Sage X3 is a trademark of its respective owner. `sagex3-assistant` is independent and not affiliated with or endorsed by Sage. Its table dictionary is a compact extraction of facts (table and column names, types, keys, local-menu values, link expressions) from the "Table dictionary" pages of Sage's public online help for **Sage X3 V11 only** (`online-help.sagex3.com/erp/11/`), not a copy of those pages; Sage's own terms apply to that material. Other versions (V12 and later, V9/V10 patches), folder-specific customizations, activity-code-dependent columns and local-menu changes are not included. Confirm against Sage's own documentation, and on the client's folder, before relying on any of it.

SAP and SAP Business One are trademarks of SAP SE. `sapb1-assistant` is independent and not affiliated with or endorsed by SAP. Its object type list is compiled from community websites, its B1 10.0 schema dictionary and DI API reference are compiled from SAP's own SDK help (`REFDB.chm`, `REFDI.chm`) and SAP's terms apply to them, its 9.3 schema dictionary comes from erpref.com (a third party; the schema IP belongs to SAP), and its Service Layer references are prose summaries of SAP Help Portal pages (sources and caveats are in `skills/sapb1-assistant/references/objects/INDEX.md`, `skills/sapb1-assistant/references/dictionary/INDEX.md`, `skills/sapb1-assistant/references/diapi/INDEX.md` and `skills/sapb1-assistant/references/servicelayer/INDEX.md`). The schema dictionaries cover SAP Business One **10.0 and 9.3 only**; other releases (including later feature packs) and client-specific user-defined tables and fields are not included. Confirm against SAP's own documentation, and on the client's database, before relying on any of it.

Acumatica is a trademark of Acumatica, Inc. `acumatica-assistant` is independent and not affiliated with or endorsed by Acumatica. Its references are a compact extraction of facts (URL patterns, parameters, headers, status codes, JSON shapes, rules) from the **2026 R2** editions of Acumatica's publicly available Integration Development Guide and Reporting Tools Guide on beacon.acumatica.com, not a copy of those pages, and Acumatica's own terms apply to that material (sources and caveats are in `skills/acumatica-assistant/references/rest/INDEX.md` and `references/odata/INDEX.md`). The entity, field and action names of one system endpoint (`Default/25.200.001`, 2025 R2) are extracted from its OpenAPI document (`skills/acumatica-assistant/references/endpoints/INDEX.md`), and the DAC, field and navigation names of a clean 2026 R2 instance from its DAC-based OData `$metadata` (`references/odata/metadata/INDEX.md`); other endpoint versions and releases can differ. Confirm against Acumatica's own documentation, and on the client's instance, before relying on any of it.

QuickBooks is a trademark of Intuit Inc. `quickbooksdesktop-assistant` is independent and not affiliated with or endorsed by Intuit. Its references describe the publicly documented QuickBooks **Desktop** SDK (qbXML / QBFC / QBXMLRP2 / Web Connector) as a lookup aid and are not a copy of Intuit's documentation; they are a curated, structural reference rather than a complete field dump, so object names, field names, length limits and the qbXML version a field was introduced in should be confirmed against Intuit's onscreen reference (OSR) and developer.intuit.com. It targets QuickBooks Desktop only — QuickBooks Online is a separate REST API and out of scope. Confirm against Intuit's own documentation, and on the client's QuickBooks install, before relying on any of it.

Sage Intacct is a trademark of The Sage Group plc or its affiliates. `sageintacct-assistant` is independent and not affiliated with or endorsed by Sage. Its references are an extraction of the XML API reference and guide pages of Sage's public developer portal (developer.intacct.com; page content CC BY 4.0, code samples Apache 2.0 per the portal) as of the verified date in each file, a rendering of Sage's Apache 2.0 `api.xsd` request schema, and the `lookup` / `inspect` object metadata of a clean developer company on 2026 Release 3 with custom fields removed (both under `sources/sageintacct-assistant/`); sources and caveats are in `skills/sageintacct-assistant/references/xml-api/INDEX.md`. It covers the XML Web Services API only; the REST API is out of scope for now. Confirm against Sage Intacct's own documentation, and on the client's company, before relying on any of it.
