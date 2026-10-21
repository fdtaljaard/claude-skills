# Sage 300 Assistant

A reference-backed Claude skill for **Sage 300 (Accpac)** consultants and integrators. Ask in plain English and it
looks the answer up in bundled Sage reference material, cites where it came from, and tells you what it could not
verify. It never guesses a table, field, enum value, version requirement or .NET signature.

## What it does

| Ask about | What you get |
|---|---|
| **SQL and the data dictionary** | Verified T-SQL views and queries against a Sage 300 company database, and "what table / field holds X". Backed by Sage's AOM data dictionaries for Sage 300 2023, 2024, 2025 and 2026 (7.0A to 7.3A), plus 6.0A for legacy 6.x clients. Read-only: it will not write SQL that modifies Sage tables. |
| **Upgrades and versions** | What a move between versions involves, what a version requires (SQL Server, Windows, Office), what changed, whether views and integrations break, checklists and release notes for 2023 to 2026. |
| **.NET / C# development** | Correct code against the `ACCPAC.Advantage` .NET library: session lifecycle, opening and composing views, reading and posting documents, error handling. Backed by the shipped class and enum reference and verified compose graphs for core OE, PO, IC, AR, AP and GL documents. |

The skill switches itself on whenever your question is about Sage 300 or Accpac, even if you only mention a table
name like `OEORDH` or a module like OE or AR. There is no command to run.

### Example prompts

- "I need a SQL view of open sales orders with the customer name and order total. The client is on Sage 300 2026."
- "What table and field holds the salesperson on a Sage 300 order?"
- "A client on Sage 300 2023 wants to move to 2026. What does the jump involve and will our SQL views break?"
- "We're on SQL Server 2016 and Windows 10. Can we run Sage 300 2026?"
- "Generate C# to create and post an OE order."

## Install

There are two ways to use the skill, depending on where you use Claude.

### Option 1: Claude Code (terminal, desktop app Code tab, VS Code or JetBrains)

Add this collection once, then install the skill. Type these in Claude Code:

```
/plugin marketplace add fdtaljaard/claude-skills
/plugin install sage300-assistant@fdtaljaard-skills
```

To update later: `/plugin marketplace update fdtaljaard-skills`. To remove: `/plugin uninstall sage300-assistant@fdtaljaard-skills`.

### Option 2: Claude desktop app and claude.ai (uploaded skill)

The Claude desktop app and claude.ai accept a packaged skill file under **Settings, Capabilities, Skills**.

1. Get `sage300-assistant.skill` from the
   [Releases page](https://github.com/fdtaljaard/claude-skills/releases). To build it yourself from this
   repository instead, follow "Packaging and validation" in [`MAINTENANCE.md`](MAINTENANCE.md).
2. In Claude, open **Settings, Capabilities, Skills** and upload the file.
3. If an older version of this skill is already listed, remove it first so only one copy triggers.

To update, upload the newer `.skill` file and remove the old one.

<details>
<summary>Other ways (developers)</summary>

With the [skills CLI](https://agentskills.io):

```bash
npx -y skills add fdtaljaard/claude-skills --skill sage300-assistant --agent claude-code
```

Manually, copy the folder into your Claude skills directory (`~/.claude/skills/` for every project, or
`<project>/.claude/skills/` for one):

```bash
git clone https://github.com/fdtaljaard/claude-skills.git
cp -r claude-skills/skills/sage300-assistant ~/.claude/skills/
```

</details>

## How it answers

Every material claim comes from a file in `references/` and is cited:

```
references/dictionary/     AOM data dictionaries per version (7.3A, 7.2A, 7.1A, 7.0A, 6.0A) and SQL conventions
references/upgrades/       upgrade guide and platform compatibility matrix 2023 to 2026
references/release-notes/  per-year release notes 2023 to 2026
references/dotnet/         ACCPAC.Advantage how-to, common mistakes, compose graphs, class and enum reference
```

Each folder has an `INDEX.md` with the source, Sage 300 version and verified date of every file. The skill states
which dictionary version it used and asks you to confirm anything that matters on the client's own database.
For anything newer than a reference's verified date it checks Sage's online documentation.

## Keeping it current and contributing

- [`SKILL.md`](SKILL.md) is what Claude loads; it describes routing, ground rules and each workflow.
- [`MAINTENANCE.md`](MAINTENANCE.md) explains how the references are built and refreshed and how to add a
  dictionary version, a release-note year, a compatibility guide or a capability.
- [`evals/evals.json`](evals/evals.json) holds test prompts per capability.
- Corrections and additions are welcome. See the repository's [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Privacy and data handling

Answers come from the bundled references. When a question goes beyond them, the skill tells Claude to look the
answer up in Sage's public documentation (help.sage300.com, docs.sage.com), using whatever web tools your Claude
environment provides; the request carries the page address, not your prompts or data. The skill has no MCP server,
hook, telemetry or backend, and it writes code and queries as text without connecting to or running anything
against your systems. The maintenance scripts in `scripts/` are never used to answer questions and work on local
files only. Your conversation with Claude is covered by Anthropic's terms and privacy policy. See
[PRIVACY.md](https://github.com/fdtaljaard/claude-skills/blob/main/PRIVACY.md) for the full policy.

## Disclaimer

Sage 300 and Accpac are trademarks of their respective owners. This skill is independent and not affiliated with
or endorsed by Sage. The bundled reference material is derived from Sage's published documentation and product
metadata for use as a lookup aid. Always verify against official Sage documentation, and on the client's own
system, before acting on it in production.
