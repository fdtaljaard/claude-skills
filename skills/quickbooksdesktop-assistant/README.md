# QuickBooks Desktop Assistant

A reference-backed Claude skill for **QuickBooks Desktop** SDK consultants and integrators. Ask in plain
English and it answers from bundled qbXML/QBFC reference material, cites where it came from, and tells you
what it could not verify. It never guesses a request name, a field, an OR-aggregate member or a qbXML
version — and it points you at Intuit's OSR (onscreen reference) for anything the bundled references don't
cover.

> **Desktop, not Online.** This skill is the QuickBooks *Desktop* SDK (qbXML over QBFC / QBXMLRP2 / the
> Web Connector, Windows-only COM). QuickBooks *Online* is a different REST/JSON API — the skill will say
> so rather than answer a QBO question wrongly.

## What it does

| Ask about | What you get |
|---|---|
| **qbXML / QBFC development (C#)** | Correct C# against the QB SDK: `QBSessionManager` session lifecycle, building a message set at the right version, appending Add/Mod/Query requests, OR aggregates, linking an invoice to a sales order, walking the response and checking every `StatusCode`, Mod with `EditSequence`. |
| **Object / field reference** | Which qbXML object or field holds what, the `ListID` / `TxnID` / `TxnLineID` / `EditSequence` model, Add vs Mod vs Query vs Void, OR (choice) fields, feature/version gating, and a catalogue of the common lists and transactions. |
| **Setup & connectivity** | QBFC vs QBXMLRP2 vs the Web Connector (QBWC), connection and company-file open modes, first-connection authorization and code-signing certificates, unattended / hosted topologies, the 32-bit / STA / local-install constraints, and common connection error signatures. |

The skill switches itself on whenever your question is about QuickBooks Desktop or the QB SDK, even if you
only mention `qbXML`, `QBFC`, `TxnID`, or a request like `InvoiceAdd`. There is no command to run.

### Example prompts

- "Show me C# with QBFC to add an invoice with two line items against QuickBooks Desktop."
- "I have a sales order TxnID and need to create an invoice that fulfils it — how do I link them in QBFC?"
- "What's the difference between ListID, TxnID and EditSequence, and when do I need EditSequence?"
- "Our Windows service posts to QuickBooks with no one logged in and fails with 'could not start QuickBooks'. Why?"
- "We're a SaaS app syncing to clients' on-premise QuickBooks we don't control — what's the right approach?"

## Install

### Option 1: Claude Code (terminal, desktop app Code tab, VS Code or JetBrains)

```
/plugin marketplace add fdtaljaard/claude-skills
/plugin install quickbooksdesktop-assistant@fdtaljaard-skills
```

To update later: `/plugin marketplace update fdtaljaard-skills`. To remove:
`/plugin uninstall quickbooksdesktop-assistant@fdtaljaard-skills`.

### Option 2: Claude desktop app and claude.ai (uploaded skill)

1. Get `quickbooksdesktop-assistant.skill` from the Releases page, or build it yourself (see
   [`MAINTENANCE.md`](MAINTENANCE.md), "Packaging").
2. In Claude, open **Settings, Capabilities, Skills** and upload the file.
3. If an older version is already listed, remove it first so only one copy triggers.

## How it answers

Every material claim comes from a file in `references/` and is cited, or is flagged "confirm in the OSR":

```
references/qbxml/    object-model.md (ListID/TxnID/EditSequence, verbs, OR aggregates, LinkToTxn,
                     versions & formats) and objects.md (catalogue of common lists & transactions)
references/qbfc/     csharp.md (correct QBFC idioms end to end) and common-mistakes.md
references/setup/    connectivity.md (QBFC vs QBXMLRP2 vs QBWC, modes, auth, constraints, errors)
```

Each folder has an `INDEX.md` with the source and verified date of every file. Because QuickBooks Desktop
has **no SQL schema** (the `.QBW` is proprietary, reachable only through the SDK), the authoritative
"schema" is Intuit's qbXML spec, documented object-by-object in the **OSR** — the skill treats the OSR as
the source of truth and tells you when to check it.

## Keeping it current and contributing

- [`SKILL.md`](SKILL.md) is what Claude loads; it describes routing, ground rules and each workflow.
- [`MAINTENANCE.md`](MAINTENANCE.md) explains how to bundle a real OSR export for deeper verification, add
  a capability, and refresh for a new SDK version.
- [`evals/evals.json`](evals/evals.json) holds test prompts per capability.

## Privacy and data handling

Answers come from the bundled references. When a question goes beyond them, the skill tells Claude to look the
answer up in Intuit's public developer documentation (developer.intuit.com), using whatever web tools your Claude
environment provides; the request carries the page address, not your prompts or data. The skill has no MCP server,
hook, telemetry or backend, and it writes code and queries as text without connecting to or running anything
against your systems. The maintenance script in `scripts/` is never used to answer questions and works on local
files only. Your conversation with Claude is covered by Anthropic's terms and privacy policy. See
[PRIVACY.md](https://github.com/fdtaljaard/claude-skills/blob/main/PRIVACY.md) for the full policy.

## Disclaimer

QuickBooks is a trademark of Intuit Inc. This skill is independent and not affiliated with or endorsed by
Intuit. The bundled reference material is derived from the publicly documented QuickBooks Desktop SDK for
use as a lookup aid. Always verify against Intuit's official documentation (the OSR and
developer.intuit.com), and on the client's own QuickBooks install, before acting on it in production.
