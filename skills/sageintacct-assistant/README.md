# Sage Intacct Assistant

A reference-backed Claude skill for **Sage Intacct** consultants and integrators. Ask in plain English, it looks the
answer up in bundled, attributed references, cites where it came from, and tells you what it could not verify.

The first capability covers the **XML Web Services API** (DTD 3.0, the `xmlgw.phtml` gateway), which the official
SDKs and most live integrations use. Sage labels it "(Legacy)" and ships new objects on the **REST API**, which has
no bundled reference yet; the skill says so when asked.

## What it does

| Ask about | What you get |
|---|---|
| **XML API integration development.** "Connect to Intacct and list the bills changed since yesterday", "create an AP bill with two lines", "create a sales order for customer X and convert it to an invoice", "receive stock against a purchase order", "post an inventory adjustment with lot numbers", "which fields does `create` of `ITEM` take and which are required", "what are the `STATE` codes of `SODOCUMENT`", "why do I get GW-0010", "review my Intacct sync code" | XML requests (and client code when asked) built from a bundled extraction of the Sage Intacct developer portal and Sage's 3.0 request schema: the request envelope, sessions and endpoints, the three status levels and error categories, recovery with `uniqueid`, the `query` grammar and `readByQuery` string syntax with paging, date and number formats, multi-entity rules, concurrency and timeout guidance, every documented object page (197 pages, 1,694 operations in 17 modules) with its parameter tables, examples and release history, the grammar of all 52 generic functions and the 243 legacy function names, an object-definition snapshot of a clean developer company on 2026 Release 3 (632 objects, 21,342 fields with data types, read-only flags and valid values, 2,039 relationships) for exact names, a guide to Order Entry, Purchasing and Inventory Control flows, and a 36-rule common-mistakes checklist for reviews. Every answer names the reference file it used and what still needs confirming on your company. |

More capabilities to follow (see `MAINTENANCE.md`): the REST API is the obvious next one.

## Install

Through the [Claude Code](https://www.claude.com/product/claude-code) plugin marketplace:

```
/plugin marketplace add fdtaljaard/claude-skills
/plugin install sageintacct-assistant@fdtaljaard-skills
```

Or package it for the Claude desktop app and claude.ai (Settings, Capabilities, Skills) with:

```bash
python skills/sageintacct-assistant/scripts/package_skill.py skills/sageintacct-assistant dist
```

## Keeping it current and contributing

- [`SKILL.md`](SKILL.md) is what Claude loads; it describes routing, ground rules, the workflow and the gotchas.
- [`references/xml-api/INDEX.md`](references/xml-api/INDEX.md) lists every reference file with its source,
  verified date and known limits. The section files, operation catalogue and function grammar are generated from
  a cache of the developer portal and from Sage's `api.xsd`, and the snapshot from a scrubbed `lookup` / `inspect`
  dump kept under `sources/`, by the scripts in `scripts/`.
- [`MAINTENANCE.md`](MAINTENANCE.md) explains the conventions, how to regenerate the references, how to run the
  object-definition dump against a developer company, and how to add a capability.
- [`evals/evals.json`](evals/evals.json) holds test prompts per capability.
- Corrections and additions are welcome. See the repository's [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Disclaimer

Sage and Sage Intacct are trademarks of The Sage Group plc or its affiliates. This skill is independent and not
affiliated with or endorsed by Sage. The references are an extraction of Sage's public developer portal (page
content CC BY 4.0, code samples Apache 2.0 per the portal) and of Sage's Apache 2.0 request schema as of the
verified date in each file; confirm against Sage Intacct's documentation, and on the client's company, before
relying on any of it.
