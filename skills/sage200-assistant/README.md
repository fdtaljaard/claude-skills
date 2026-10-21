# Sage 200 Evolution Assistant

A reference-backed Claude skill for **Sage 200 Evolution (Pastel Evolution)** consultants and integrators. Ask in
plain English and it looks the answer up in bundled reference material, cites where it came from, and tells you
what it could not verify. It never guesses a table, column, SDK class, method or enum value.

## What it does

| Ask about | What you get |
|---|---|
| **SQL and the data dictionary** | Verified read-only T-SQL views and queries against an Evolution company database, and "what table / field holds X". Backed by a bundled dictionary of 689 tables with every column, keys and Sage's own table descriptions, plus the conventions that make Evolution joins work (name prefixes, identity keys, posting tables, NULL and default behaviour). Read-only: it will not write SQL that modifies Evolution tables. |
| **SDK development (C#)** | Correct C# against the `Pastel.Evolution` .NET SDK: connecting through `DatabaseContext`, the record load, set and `Save()` pattern, posting documents and transactions. Backed by a class and enum reference extracted from the shipped SDK help (152 types, 94 enumerations, with enum members read from the SDK assembly where the help omits them), a how-to guide and a common-mistakes list. |

The skill switches itself on whenever your question is about Sage 200 Evolution or Pastel Evolution, even if you
only say "Evolution", a table name like `Client`, `StkItem` or `_btblInvoiceLines`, or an SDK type like
`InventoryTransaction`. There is no command to run.

### Example prompts

- "I need a view of open customer invoices with the customer name, invoice total and outstanding amount."
- "What table and field holds the warehouse on an Evolution inventory transaction?"
- "Show me C# that connects to an Evolution company and creates a customer."
- "Post an inventory adjustment through the SDK and roll back if any line fails."
- "Why does my join from `InvNum` to `Client` return the wrong names on some rows?"

## Install

There are two ways to use the skill, depending on where you use Claude.

### Option 1: Claude Code (terminal, desktop app Code tab, VS Code or JetBrains)

Add this collection once, then install the skill. Type these in Claude Code:

```
/plugin marketplace add fdtaljaard/claude-skills
/plugin install sage200-assistant@fdtaljaard-skills
```

To update later: `/plugin marketplace update fdtaljaard-skills`. To remove: `/plugin uninstall sage200-assistant@fdtaljaard-skills`.

### Option 2: Claude desktop app and claude.ai (uploaded skill)

The Claude desktop app and claude.ai accept a packaged skill file under **Settings, Capabilities, Skills**.

1. Get `sage200-assistant.skill` from the [Releases page](https://github.com/fdtaljaard/claude-skills/releases).
   To build it yourself from this repository instead (needs Python 3.10+ and PyYAML):

   ```bash
   python skills/sage200-assistant/scripts/package_skill.py skills/sage200-assistant dist
   ```

   This validates the skill and writes `dist/sage200-assistant.skill`.
2. In Claude, open **Settings, Capabilities, Skills** and upload the file.
3. If an older version of this skill is already listed, remove it first so only one copy triggers.

To update, upload the newer `.skill` file and remove the old one.

<details>
<summary>Other ways (developers)</summary>

With the [skills CLI](https://agentskills.io):

```bash
npx -y skills add fdtaljaard/claude-skills --skill sage200-assistant --agent claude-code
```

Manually, copy the folder into your Claude skills directory (`~/.claude/skills/` for every project, or
`<project>/.claude/skills/` for one):

```bash
git clone https://github.com/fdtaljaard/claude-skills.git
cp -r claude-skills/skills/sage200-assistant ~/.claude/skills/
```

</details>

## How it answers

Every material claim comes from a file in `references/` and is cited:

```
references/dictionary/  conventions and the 689-table dictionary, grouped by table-name prefix
references/sdk/         SDK how-to, common mistakes, class reference bundles and enumerations
```

Each folder has an `INDEX.md` that says what every file covers and where it came from. The SDK reference is for
`Pastel.Evolution` version 11.0.0.10, and the skill says so when a client's version may differ. It asks you to
confirm anything that matters on the client's own database or installed SDK.

## Keeping it current and contributing

- [`SKILL.md`](SKILL.md) is what Claude loads; it describes routing, ground rules and each workflow.
- [`MAINTENANCE.md`](MAINTENANCE.md) explains how the dictionary is maintained, how to rebuild the SDK reference
  from the shipped help, and how to add a capability.
- [`evals/evals.json`](evals/evals.json) holds test prompts per capability.
- Corrections and additions are welcome. See the repository's [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Privacy and data handling

Answers come from the bundled references only. The skill reads its own files, sends nothing anywhere, and has no
MCP server, hook, telemetry or backend. It writes code and queries as text and never connects to or runs anything
against your systems. The maintenance scripts in `scripts/` are never used to answer questions and work on local
files only. Your conversation with Claude is covered by Anthropic's terms and privacy policy. See
[PRIVACY.md](https://github.com/fdtaljaard/claude-skills/blob/main/PRIVACY.md) for the full policy.

## Disclaimer

Sage 200 Evolution and Pastel Evolution are trademarks of their respective owners. This skill is independent and
not affiliated with or endorsed by Sage. Its SDK reference is extracted from the shipped `Pastel.Evolution.chm`
and XML documentation for SDK version **11.0.0.10 only**; other versions are not included, and Sage's own terms
apply to that material. It documents the `Pastel.Evolution` object SDK, not the Evolution ODBC/SQL layer or the
Connector/API web service. Verify against Sage's own documentation, and on the client's installed SDK, before
relying on any of it. The SDK binds to a licensed Evolution install of a matching version.
