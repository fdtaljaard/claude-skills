# Cin7 Assistant

A reference-backed Claude skill for **Cin7** consultants and integrators. Ask in plain English, it looks the
answer up in bundled, attributed references, cites where it came from, and tells you what it could not verify.

The first capability covers **Cin7 Core** (formerly DEAR Systems / DEAR Inventory) and its API v2. **Cin7
Omni** is a different product with its own API; nothing is bundled for it yet, and the skill says so when asked.

## What it does

| Ask about | What you get |
|---|---|
| **Cin7 Core API integration development.** "Connect to Cin7 Core and list the sales changed since yesterday", "create a sale order for customer X with two lines and authorise it", "receive stock on an advanced purchase", "void this stock transfer", "which fields does the sale invoice take, and which are required", "what does `BACKORDERED` mean", "set up a webhook for authorised invoices", "review my Cin7 sync code" | HTTP requests or client code built from a bundled extraction of the Cin7 Core developer portal: the two authentication headers, pagination (`page` / `limit` / `Total`), status codes and the 60-calls-per-minute limit, UTC ISO 8601 dates, void versus undo, the overwrite semantics of sub-document POSTs, the stage preconditions of sales and purchases, every documented endpoint (295 actions in 33 groups) with its field tables, parameters, request and response bodies, the status and type value lists, webhook events and retry rules, and a 31-rule common-mistakes checklist for reviews. Every answer names the reference file it used and what still needs confirming on your account. |

More capabilities to follow (see `MAINTENANCE.md`).

## Install

Through the [Claude Code](https://www.claude.com/product/claude-code) plugin marketplace:

```
/plugin marketplace add fdtaljaard/claude-skills
/plugin install cin7-assistant@fdtaljaard-skills
```

Or package it for the Claude desktop app and claude.ai (Settings, Capabilities, Skills) with:

```bash
python skills/cin7-assistant/scripts/package_skill.py skills/cin7-assistant dist
```

## Keeping it current and contributing

- [`SKILL.md`](SKILL.md) is what Claude loads; it describes routing, ground rules, the workflow and the gotchas.
- [`references/core-api/INDEX.md`](references/core-api/INDEX.md) lists every reference file with its source,
  verified date and known limits. The group files, endpoint catalogue and value lists are generated from the
  portal's API Blueprint export by `scripts/build_core_api_reference.py`.
- [`MAINTENANCE.md`](MAINTENANCE.md) explains the conventions, how to regenerate the references and how to add
  a capability.
- [`evals/evals.json`](evals/evals.json) holds test prompts per capability.
- Corrections and additions are welcome. See the repository's [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Privacy and data handling

Answers come from the bundled references only. The skill reads its own files, sends nothing anywhere, and has no
MCP server, hook, telemetry or backend. It writes code and queries as text and never connects to or runs anything
against your systems. The maintenance scripts in `scripts/` are never used to answer questions and work on local
files only. Your conversation with Claude is covered by Anthropic's terms and privacy policy. See
[PRIVACY.md](https://github.com/fdtaljaard/claude-skills/blob/main/PRIVACY.md) for the full policy.

## Disclaimer

Cin7, Cin7 Core, Cin7 Omni and DEAR Systems are trademarks of their respective owners. This skill is independent
and not affiliated with or endorsed by Cin7. The references are an extraction of Cin7's public developer portal
as of the verified date in each file; confirm against Cin7's documentation, and on the client's account, before
relying on any of it.
