# SAP Business One Assistant

A reference-backed Claude skill for **SAP Business One (SAP B1)** consultants and integrators. Ask in plain English
and it looks the answer up in bundled SAP reference material, cites where it came from, and tells you what it
could not verify. It never guesses an object type number, a table or column, an enum value, a DI API member or a
Service Layer endpoint.

## What it does

| Ask about | What you get |
|---|---|
| **Object types** | The object type number for a table or document, the table and primary key behind a number, and objects by topic ("everything about bins"). From a reconciled list of all B1 object types, with SAP's own DI API enumeration marking the confirmed rows. |
| **SQL and the schema** | Verified SQL views and queries against a B1 company database, and "what table / field holds X". Backed by data dictionaries for **B1 10.0** (from SAP's own SDK reference, the default) and **9.3**: tables, columns, indexes, valid values and parent-table links. Read-only: it will not write SQL that modifies B1 tables. |
| **DI API development (C#)** | Generate and review C# against the DI API (`SAPbobsCOM`): connect, create and update documents and master data, services, transactions, error handling, user-defined fields, tables and objects. Backed by the DI API 10.0 class and enum reference, a how-to guide, a common-mistakes list and a review checklist. |
| **Service Layer (REST / OData v4)** | Login and session handling, `$metadata` verification, query options and their limits, paging, writes and actions, ETag concurrency, `$batch` and transactions, UDF/UDT/UDO entities, attachments, SQL views, `SQLQueries`, configuration and troubleshooting, and FP 2602 webhooks, from SAP's *Working with SAP Business One Service Layer* guide; exact entity set, property, enum and action names from a bundled snapshot of a **FP 2602** `$metadata` document (customer objects removed). |
| **DI API or Service Layer?** | Which API to build on and why: SAP's documented limitations of each (transactions, direct SQL, XML, UDO restarts), a decision table, the operations side by side, and the naming differences you hit when porting code between them. |

The skill switches itself on whenever your question is about SAP Business One, even if you only say "B1", a table
name like `OINV`, an object type number, or mention the DI API or UDOs. There is no command to run.

### Example prompts

- "What's the SAP B1 object type number for a sales order, and what table and primary key is it?"
- "I need a SQL view of open sales orders with the customer name and document total. The client is on SAP B1 10.0."
- "Write C# that connects to a SAP B1 company on SQL Server 2019 and creates an A/R invoice for customer BP234 with two item lines."
- "Review this DI API module" (paste the code) or "Add a user-defined field to the OITM table from C#."
- "Can we stop polling SAP B1 for newly created sales orders and get notified instead? The system is on 10.0 FP2602."
- "New integration from Linux containers into B1: DI API or Service Layer?" or "Port this DI API routine to Service Layer."

## Install

There are two ways to use the skill, depending on where you use Claude.

### Option 1: Claude Code (terminal, desktop app Code tab, VS Code or JetBrains)

Add this collection once, then install the skill. Type these in Claude Code:

```
/plugin marketplace add fdtaljaard/claude-skills
/plugin install sapb1-assistant@fdtaljaard-skills
```

To update later: `/plugin marketplace update fdtaljaard-skills`. To remove: `/plugin uninstall sapb1-assistant@fdtaljaard-skills`.

### Option 2: Claude desktop app and claude.ai (uploaded skill)

The Claude desktop app and claude.ai accept a packaged skill file under **Settings, Capabilities, Skills**.

1. Get `sapb1-assistant.skill` from the [Releases page](https://github.com/fdtaljaard/claude-skills/releases).
   To build it yourself from this repository instead (needs Python 3.10+ and PyYAML):

   ```bash
   python skills/sapb1-assistant/scripts/package_skill.py skills/sapb1-assistant dist
   ```

   This validates the skill and writes `dist/sapb1-assistant.skill`.
2. In Claude, open **Settings, Capabilities, Skills** and upload the file.
3. If an older version of this skill is already listed, remove it first so only one copy triggers.

To update, upload the newer `.skill` file and remove the old one.

<details>
<summary>Other ways (developers)</summary>

With the [skills CLI](https://agentskills.io):

```bash
npx -y skills add fdtaljaard/claude-skills --skill sapb1-assistant --agent claude-code
```

Manually, copy the folder into your Claude skills directory (`~/.claude/skills/` for every project, or
`<project>/.claude/skills/` for one):

```bash
git clone https://github.com/fdtaljaard/claude-skills.git
cp -r claude-skills/skills/sapb1-assistant ~/.claude/skills/
```

</details>

## How it answers

Every material claim comes from a file in `references/` and is cited:

```
references/objects/       the reconciled object type list, with sources and known issues
references/dictionary/    B1 10.0 and 9.3 schema dictionaries, bundled by module with a table index
references/diapi/         DI API how-to, common mistakes, review checklist, class and enum reference bundles
references/servicelayer/  Service Layer guide, DI API vs Service Layer decision guide, SQLQueries and webhook notes, FP 2602 $metadata snapshot (metadata/)
```

Each folder has an `INDEX.md` with the source and verified date of every file. The skill states which schema
version it used, decodes status values from the dictionary rather than memory, and asks you to confirm anything
that matters on the client's own database. Client-specific user-defined tables and fields are never bundled.

## Keeping it current and contributing

- [`SKILL.md`](SKILL.md) is what Claude loads; it describes routing, ground rules, each workflow and the gotchas.
- [`MAINTENANCE.md`](MAINTENANCE.md) explains how to refresh the object list, the schema dictionaries, the DI API
  reference and the Service Layer references, and how to add a capability.
- [`evals/evals.json`](evals/evals.json) holds test prompts per capability.
- Corrections and additions are welcome. See the repository's [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Privacy and data handling

Answers come from the bundled references only. The skill reads its own files, sends nothing anywhere, and has no
MCP server, hook, telemetry or backend. It writes code and queries as text and never connects to or runs anything
against your systems. The maintenance scripts in `scripts/` are never used to answer questions; when a maintainer
runs `fetch_erpref_schema.py` it downloads schema pages from erpref.com. Your conversation with Claude is covered
by Anthropic's terms and privacy policy. See
[PRIVACY.md](https://github.com/fdtaljaard/claude-skills/blob/main/PRIVACY.md) for the full policy.

## Disclaimer

SAP and SAP Business One are trademarks of SAP SE. This skill is independent and not affiliated with or endorsed
by SAP. Its object type list is compiled from community websites; its B1 10.0 schema dictionary and DI API
reference are compiled from SAP's own SDK help (`REFDB.chm`, `REFDI.chm`) and SAP's terms apply to them; its 9.3
schema dictionary comes from erpref.com, a third party, while the schema IP belongs to SAP; its hand-written
Service Layer references are prose summaries of SAP Help Portal pages; and its generated Service Layer metadata
reference is derived from SAP Business One Service Layer `$metadata`, to which SAP's terms also apply. The schema
dictionaries cover SAP Business One **10.0 and 9.3 only**; the generated Service Layer metadata reference states
the exact feature pack captured. Client-specific user-defined tables, fields and objects are excluded from bundled
references. Confirm against SAP's own documentation, and on the client's system, before relying on any of it.
