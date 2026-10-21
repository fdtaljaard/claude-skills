# Acumatica Assistant

A reference-backed Claude skill for **Acumatica ERP** consultants and integrators. Ask in plain English and it
looks the answer up in a bundled extraction of Acumatica's own Integration Development Guide, cites where it
came from, and tells you what it could not verify. It never guesses an endpoint URL, a query-parameter syntax,
a header, a status-code meaning or an OAuth scope.

## What it does

| Ask about | What you get |
|---|---|
| **REST integration development** | Generate and review HTTP requests and client code (any language) against the contract-based REST API: cookie sign-in and OAuth 2.0 / OIDC (all four flows, scopes, refresh, session rules), endpoint and contract versions (`Default/20.200.001` to `Default/26.200.001`, Contract Version 4 vs 5), the JSON record shape, `$filter` / `$expand` / `$select` / `$custom` / `$top` / `$skip` per contract version, create / update / PATCH / delete rules, actions and long-running operations, processing forms, generic inquiries, reports, custom and user-defined fields, attachments, license limits on sessions and requests, push notifications and webhooks. Backed by a catalogue of the 187 example requests the guide documents, with links to each page, and a 36-row common-mistakes checklist for code reviews. |
| **Exact entity, field and action names** | Which entity a form is exposed as, the fields of an entity and of its nested detail and linked entities, what `$expand` accepts, and the actions an entity has with their parameters. Looked up in a snapshot generated from the OpenAPI document (`swagger.json`) of the `Default/25.200.001` system endpoint (2025 R2, Contract Version 4): 119 top-level entities, 5,338 fields, 575 expand paths, 163 actions. Exact for that endpoint; for other `Default` versions the skill applies the documented differences and tells you what to confirm. |
| **OData data access** | Read Acumatica data for BI, reporting and delta syncs through the two read-only OData interfaces, DAC-based (`/t/<Tenant>/api/odata/dac`) and generic-inquiry-based (`/t/<Tenant>/api/odata/gi`): URLs and tenant names (and the pre-2026 `/OData` and `/ODatav4` shapes), basic auth versus OAuth and what each costs in licence terms, the `BI` and `OData4 User` roles, `$select` / `$expand` / `$filter` (navigation paths, `Any` / `All` / `$count` lambdas), paging, archived and deleted records (`PX-ApiArchive`, `PX-ApiDeleted`, `px.GetDeletedRecords()`), multilingual fields, exposing inquiries and calling them with parameters, the inquiry interface's unsupported options, CORS and `Web.config`, Excel and Power BI feeds, and when to prefer OData over the REST API. Exact DAC, field and navigation-property names come from a bundled `$metadata` snapshot of a clean 2026 R2 instance (2,265 DACs, 42,288 fields with their UI display names, 23,576 navigation properties with their joins, 5,108 entity-set names, the non-filterable fields of each DAC), plus a 22-row common-mistakes checklist for reviewing OData URLs and Power Query. |

The skill switches itself on whenever your question is about Acumatica, even if you only mention an endpoint
path, an entity like `SalesOrder`, a DAC like `SOOrder`, a form ID like `SO301000`, OData, or "connected
applications". There is no command to run. More capabilities (SOAP, customization development, versions and
upgrades) are planned.

### Example prompts

- "Write a request that creates a sales order with two lines for customer ABAKERY on Acumatica 2026 R2, then releases it from hold."
- "Our Acumatica instance is 2024 R2. Give me the `$filter` and `$expand` to list stock items changed since yesterday with their warehouse quantities."
- "Set up OAuth for a background service that syncs invoices nightly. Which flow and scopes, and how do we refresh?"
- "My PUT returns 200 but the field is unchanged. Why?"
- "Review this Python Acumatica client" (paste the code).
- "We poll the API every minute for new shipments. Is there a push option?"
- "We're on 2025 R2. Which fields does a sales order line have, and what can I `$expand` on a shipment?"
- "Power BI needs open sales orders with customer name and line items, read-only, refreshed hourly. Give me the OData URL."
- "Which DAC and fields hold the warehouse quantity on hand, and how do I join it to the stock item code?"
- "Our nightly OData sync filters on LastModifiedDateTime but deleted customers never disappear downstream. What are we missing?"

## Install

There are two ways to use the skill, depending on where you use Claude.

### Option 1: Claude Code (terminal, desktop app Code tab, VS Code or JetBrains)

Add this collection once, then install the skill. Type these in Claude Code:

```
/plugin marketplace add fdtaljaard/claude-skills
/plugin install acumatica-assistant@fdtaljaard-skills
```

To update later: `/plugin marketplace update fdtaljaard-skills`. To remove: `/plugin uninstall acumatica-assistant@fdtaljaard-skills`.

### Option 2: Claude desktop app and claude.ai (uploaded skill)

The Claude desktop app and claude.ai accept a packaged skill file under **Settings, Capabilities, Skills**.

1. Get `acumatica-assistant.skill` from the [Releases page](https://github.com/fdtaljaard/claude-skills/releases).
   To build it yourself from this repository instead (needs Python 3.10+ and PyYAML):

   ```bash
   python skills/acumatica-assistant/scripts/package_skill.py skills/acumatica-assistant dist
   ```

   This validates the skill and writes `dist/acumatica-assistant.skill`.
2. In Claude, open **Settings, Capabilities, Skills** and upload the file.
3. If an older version of this skill is already listed, remove it first so only one copy triggers.

To update, upload the newer `.skill` file and remove the old one.

<details>
<summary>Other ways (developers)</summary>

With the [skills CLI](https://agentskills.io):

```bash
npx -y skills add fdtaljaard/claude-skills --skill acumatica-assistant --agent claude-code
```

Manually, copy the folder into your Claude skills directory (`~/.claude/skills/` for every project, or
`<project>/.claude/skills/` for one):

```bash
git clone https://github.com/fdtaljaard/claude-skills.git
cp -r claude-skills/skills/acumatica-assistant ~/.claude/skills/
```

</details>

## How it answers

Every material claim comes from a file in `references/` and is cited:

```
references/rest/   the REST API guide, query parameters per contract version, authentication and license limits,
                   endpoint and contract versions, the generated examples catalogue, push notifications and
                   webhooks, and the common-mistakes checklist
references/endpoints/  the Default/25.200.001 contract generated from its swagger.json: entities with form IDs,
                   every field, the expand paths and the actions with their parameters
references/odata/  the OData guide (both interfaces, auth, query options, headers, inquiries, CORS, Excel / Power BI,
                   OData versus REST), its common-mistakes checklist, and metadata/ — the DAC $metadata snapshot
                   of a clean 2026 R2 instance (entity-set names, a type index, bundled per-DAC field and
                   navigation lists with display names and joins)
```

Each folder's `INDEX.md` lists the sources, the edition or build and the verified date of every file. The skill
states which release, endpoint or interface and contract version it assumed. For the REST API it names only
entities, fields and actions that are in the `Default/25.200.001` contract snapshot or in the guide's own
examples, says which, and asks you to confirm them on your instance's OpenAPI document (`swagger.json`) or the
Web Service Endpoints (SM207060) form when your endpoint is a different one. For OData it names only DACs, fields
and navigation properties found in the 2026 R2 metadata snapshot and asks you to confirm them on your instance's
`$metadata`. No custom endpoint, inquiry, customization or user-defined field is bundled.

## Keeping it current and contributing

- [`SKILL.md`](SKILL.md) is what Claude loads; it describes routing, ground rules, the workflow and the gotchas.
- [`MAINTENANCE.md`](MAINTENANCE.md) explains how to refresh the references when Acumatica publishes a new
  release of the guide, and how to add a capability.
- [`evals/evals.json`](evals/evals.json) holds test prompts per capability.
- Corrections and additions are welcome. See the repository's [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Privacy and data handling

Answers come from the bundled references only. The skill reads its own files, sends nothing anywhere, and has no
MCP server, hook, telemetry or backend. It writes code and queries as text and never connects to or runs anything
against your systems. The maintenance scripts in `scripts/` are never used to answer questions; when a maintainer
runs `fetch_beacon_guide.py` it downloads guide pages from beacon.acumatica.com. Your conversation with Claude is
covered by Anthropic's terms and privacy policy. See
[PRIVACY.md](https://github.com/fdtaljaard/claude-skills/blob/main/PRIVACY.md) for the full policy.

## Disclaimer

Acumatica is a trademark of Acumatica, Inc. This skill is independent and not affiliated with or endorsed by
Acumatica. Its references are a compact extraction of facts (URL patterns, parameters, headers, status codes,
JSON shapes, rules) from the **2026 R2** editions of Acumatica's publicly available Integration Development Guide
and Reporting Tools Guide on beacon.acumatica.com (plus one System Administration Guide topic and, for pre-2026
OData URLs, the I300 *Data Retrieval with OData* training course, 2024 R1), not a copy of those pages, and
Acumatica's own terms apply to that material. The entity, field and action names of one system endpoint
(`Default/25.200.001`, 2025 R2) are bundled as extracted from its OpenAPI document, and the DAC, field and
navigation names of a clean 2026 R2 instance as extracted from its DAC-based OData `$metadata` (no business data,
no customer customization); other endpoint versions and releases differ where the references say so and may
differ elsewhere. Confirm against Acumatica's documentation, and on the client's instance, before relying on any
of it.
