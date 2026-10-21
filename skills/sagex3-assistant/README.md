# Sage X3 Assistant

A reference-backed Claude skill for **Sage X3** consultants and integrators. Ask in plain English and it looks the
answer up in bundled reference material, cites where it came from, and tells you what it could not verify. It
never guesses a table, column, local-menu value, release date or platform requirement.

## What it does

| Ask about | What you get |
|---|---|
| **Data dictionary and SQL** | Verified SQL views and queries against an X3 folder, and "what table / field holds X", "what does status 3 mean". Backed by a bundled **V11** table dictionary: every table with its abbreviation, keys and indexes, columns with data types and dimensions, local-menu enum values and the link expressions that define foreign-key joins. Read-only: it will not write SQL that modifies X3 tables. |
| **Versions and upgrades** | V12 release and patch naming, lifecycle stage and end of maintenance, platform prerequisites per release (Windows Server, SQL Server or Oracle, MongoDB, Java), upgrade paths and methods from V6, V7, U9, V11 and V12 to the current release, what changed per release from 2023 R2 to 2026 R1, and whether views and integrations break. |

The skill switches itself on whenever your question is about Sage X3, even if you only say "X3", a table or
abbreviation like `SORDER` or `SOH`, a local menu number, or a release like "2026 R1" or "patch 39". There is no
command to run.

### Example prompts

- "I need a SQL view of open sales orders in Sage X3 with the sold-to customer name and the order total. The folder is SEED."
- "What table and field holds the allocation status on an X3 sales order, and what do the values mean?"
- "My X3 query `WHERE SHIDAT IS NULL` returns no rows but I know many orders have no shipment date. Why?"
- "A client on Sage X3 V11 (SQL Server 2016, Windows Server 2016) wants to move to the current V12 release. What does it involve?"
- "Is Sage X3 2025 R1 still supported, and when does it end?"

## Install

There are two ways to use the skill, depending on where you use Claude.

### Option 1: Claude Code (terminal, desktop app Code tab, VS Code or JetBrains)

Add this collection once, then install the skill. Type these in Claude Code:

```
/plugin marketplace add fdtaljaard/claude-skills
/plugin install sagex3-assistant@fdtaljaard-skills
```

To update later: `/plugin marketplace update fdtaljaard-skills`. To remove: `/plugin uninstall sagex3-assistant@fdtaljaard-skills`.

### Option 2: Claude desktop app and claude.ai (uploaded skill)

The Claude desktop app and claude.ai accept a packaged skill file under **Settings, Capabilities, Skills**.

1. Get `sagex3-assistant.skill` from the [Releases page](https://github.com/fdtaljaard/claude-skills/releases).
   To build it yourself from this repository instead (needs Python 3.10+ and PyYAML):

   ```bash
   PYTHONUTF8=1 python skills/sagex3-assistant/scripts/package_skill.py skills/sagex3-assistant dist
   ```

   This validates the skill and writes `dist/sagex3-assistant.skill`.
2. In Claude, open **Settings, Capabilities, Skills** and upload the file.
3. If an older version of this skill is already listed, remove it first so only one copy triggers.

To update, upload the newer `.skill` file and remove the old one.

<details>
<summary>Other ways (developers)</summary>

With the [skills CLI](https://agentskills.io):

```bash
npx -y skills add fdtaljaard/claude-skills --skill sagex3-assistant --agent claude-code
```

Manually, copy the folder into your Claude skills directory (`~/.claude/skills/` for every project, or
`<project>/.claude/skills/` for one):

```bash
git clone https://github.com/fdtaljaard/claude-skills.git
cp -r claude-skills/skills/sagex3-assistant ~/.claude/skills/
```

</details>

## How it answers

Every material claim comes from a file in `references/` and is cited:

```
references/dictionary/     V11 table dictionary: table index, per-module table entries, local menus, data types, conventions
references/upgrades/       upgrade guide and platform matrix
references/release-notes/  one file per release, 2023 R2 (patch 34) to 2026 R1 (patch 39)
```

Each folder has an `INDEX.md` with the source, version and verified date of every file. The dictionary is V11, so
for a V12 folder the skill says so and tells you how to confirm a column on the client's folder. It knows the
platform details that trip people up, such as the `_0` column suffix for dimensioned columns and the empty-date
sentinel on SQL Server, and will not invent a release date it cannot cite.

## Keeping it current and contributing

- [`SKILL.md`](SKILL.md) is what Claude loads; it describes routing, ground rules, each workflow and the gotchas.
- [`MAINTENANCE.md`](MAINTENANCE.md) explains how to rebuild the dictionary and release notes from Sage's sites,
  add a version, add a capability and package the skill.
- [`evals/evals.json`](evals/evals.json) holds test prompts per capability.
- Corrections and additions are welcome. See the repository's [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Privacy and data handling

Answers come from the bundled references. When a question goes beyond them, the skill tells Claude to look the
answer up in Sage's public online help (online-help.sagex3.com), using whatever web tools your Claude environment
provides; the request carries the page address, not your prompts or data. The skill has no MCP server, hook,
telemetry or backend, and it writes code and queries as text without connecting to or running anything against your
systems. Claude may also run `scripts/diff_table_versions.py`, which downloads the public V11 and V12 help pages of
one table from online-help.sagex3.com and sends only the page address and a User-Agent naming this repository. The
other scripts in `scripts/` are maintenance only and download from the same site when a maintainer runs them. Your
conversation with Claude is covered by Anthropic's terms and privacy policy. See
[PRIVACY.md](https://github.com/fdtaljaard/claude-skills/blob/main/PRIVACY.md) for the full policy.

## Disclaimer

Sage X3 is a trademark of its respective owner. This skill is independent and not affiliated with or endorsed by
Sage. Its table dictionary is a compact extraction of facts (table and column names, types, keys, local-menu
values, link expressions) from the "Table dictionary" pages of Sage's public online help for **Sage X3 V11 only**,
not a copy of those pages, and Sage's own terms apply to that material. Other versions (V12 and later, V9 and V10
patches), folder-specific customisations, activity-code-dependent columns and local-menu changes are not
included. Confirm against Sage's own documentation, and on the client's folder, before relying on any of it.
