# Privacy and data handling

This policy covers every plugin in this repository (`sage300-assistant`, `sage200-assistant`, `sapb1-assistant`,
`sagex3-assistant`, `acumatica-assistant`, `quickbooksdesktop-assistant`, `cin7-assistant` and
`sageintacct-assistant`). Last updated 2026-10-21.

## What the plugins are

Each plugin is one documentation-based [Agent Skill](https://agentskills.io/specification): a `SKILL.md` and a set
of bundled Markdown reference files. No plugin contains an MCP server, hook, command, agent, executable or hosted
backend, and none contains telemetry or analytics.

## What this project collects

Nothing. The project has no server and receives no data from the plugins: no prompts, files, usage statistics,
identifiers or error reports. There is nothing to retain, share or delete.

## What happens when you use a plugin

- **Your conversation.** Your prompts, conversation context and any files you give Claude are handled by
  Anthropic under the terms and [privacy policy](https://www.anthropic.com/legal/privacy) that apply to your
  Claude account, not by this project.
- **Bundled references.** Answers come from reading the plugin's own files on your machine (or in your Claude
  environment). Reading them sends nothing anywhere.
- **Generated code and SQL.** The plugins write SQL, C#, HTTP requests and similar as text. They don't connect
  to your ERP system, database or API, and don't run what they write. Anything you run against your own systems,
  you run yourself.
- **Public vendor documentation (three plugins).** When a question goes beyond the bundled references, these
  skills tell Claude to look the answer up in the vendor's public documentation, using whatever web tools your
  Claude environment provides (those tools' own terms apply). The request carries the page address, such as a
  table or object name, not your prompts or business data:
  - `sage300-assistant`: help.sage300.com and docs.sage.com
  - `sagex3-assistant`: online-help.sagex3.com. This skill can also run `scripts/diff_table_versions.py`, which
    downloads the public V11 and V12 help pages of one table from online-help.sagex3.com and compares them. It
    sends only the page address and a User-Agent naming this repository.
  - `quickbooksdesktop-assistant`: developer.intuit.com, home of Intuit's onscreen reference (OSR)

The other five plugins answer from their bundled references only.

## Maintenance scripts

Each skill's `scripts/` folder holds tooling that maintainers run by hand to rebuild the references. Claude
doesn't use these scripts to answer questions (apart from the `sagex3-assistant` script above). When a
maintainer runs them, some download public documentation: beacon.acumatica.com (`acumatica-assistant`),
developer.intacct.com (`sageintacct-assistant`), online-help.sagex3.com (`sagex3-assistant`) and erpref.com
(`sapb1-assistant`). One script, `sageintacct-assistant/scripts/dump_object_definitions.py`, signs in to the
Sage Intacct XML API (api.intacct.com by default) with credentials the maintainer supplies in environment
variables, to read object definitions from a clean developer company. It never writes credentials to its output.

## Using the plugins with confidential data

The plugins add no data flows of their own beyond those listed above. Before you use them with confidential
business information, check how your own Claude environment and any other tools, MCP servers or integrations you
have connected handle data.

## Contact

Questions about this policy: open an issue at
[github.com/fdtaljaard/claude-skills/issues](https://github.com/fdtaljaard/claude-skills/issues). For security
concerns, see [SECURITY.md](SECURITY.md).
