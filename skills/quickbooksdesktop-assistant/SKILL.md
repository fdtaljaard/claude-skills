---
name: quickbooksdesktop-assistant
description: "QuickBooks Desktop (QBD) SDK assistant for developers integrating with QuickBooks Desktop. Use whenever someone builds or debugs code against the QB SDK - even phrased casually or without naming it - signalled by qbXML, QBFC / Interop.QBFC, QBXMLRP2, Web Connector / QBWC, a request like InvoiceAdd / SalesOrderAdd / ItemReceiptAdd / TransferInventoryAdd, an identifier like ListID / TxnID / EditSequence, or an SDK error like status 3200 or 0x80040408. Capabilities: (1) qbXML / QBFC C# development - session lifecycle, message sets, Add/Mod/Query, OR aggregates, LinkToTxn, response / StatusCode handling; (2) object & field reference - which object or field holds X, the ListID / TxnID / EditSequence model, verbs, OR (choice) fields, spec versions; (3) setup & connectivity - QBFC vs QBXMLRP2 vs Web Connector, open modes, app authorization, 32-bit / STA, connection errors. NOT for QuickBooks Online (a different REST API), the QuickBooks Desktop UI (reconciling, reports, bank feeds), or edition / pricing questions."
compatibility: "Runtime needs file read + grep over the bundled references and, for anything a reference marks unverified or for an exact qbXML object/field/version, web access to the Intuit OSR (onscreen reference) and developer.intuit.com. No scripts are required at runtime."
metadata:
  author: Francois Taljaard
  version: "2026.10"
  domain: QuickBooks Desktop (qbXML / QBFC SDK)
---

# QuickBooks Desktop Assistant

Reference-backed assistant for QuickBooks **Desktop** SDK work — qbXML, QBFC, the Request Processor
(QBXMLRP2) and the Web Connector (QBWC). The rule that makes it trustworthy: **object names, field
names, request/response structure, spec versions and length/format limits are things a model guesses
plausibly and wrongly — so verify them against a bundled reference or a fresh fetch of Intuit's OSR, and
say which.** Never invent a request name, a field, an OR-aggregate member, or a qbXML version.

**Scope guard — Desktop, not Online.** This skill is the *Desktop* SDK (qbXML over QBFC/QBXMLRP2/QBWC,
Windows-only COM). QuickBooks **Online** is a completely different REST/JSON API (OAuth 2.0, `/v3/company`).
If the request is actually QBO, say so plainly and don't answer it from this skill.

## 1. Route the request

| Request looks like | Go to |
|---|---|
| generate or fix **C# against the QB SDK** — open a session, build a request, add/mod/query a transaction or list, link an invoice to an order, walk the response, read errors | § 4 Development |
| "which object/field holds X", "what's the request for Y", Add vs Mod vs Query, OR / choice fields, ListID vs TxnID vs EditSequence, "which qbXML version has Z" | § 3 Object model |
| "it won't connect", "access denied / not authorized", QBFC vs QBXMLRP2 vs Web Connector, which company-file / open mode, certificate, unattended / hosted, 32-bit, threading | § 5 Setup |
| a mix — "write C# to post an invoice against a sales order, running unattended" | § 5 (connection shape) then § 4 |

If it's really QuickBooks **Online**, say so (see scope guard). If it's QBD but outside these three
capabilities (reports via the report requests, payroll, point-of-sale, deep tax behaviour), answer from
the OSR / developer.intuit.com, cite it, and note the skill could be extended (`MAINTENANCE.md`).

## 2. Ground rules

- **Verify, then cite.** Every qbXML object, field, OR-aggregate member and spec version you name comes
  from a bundled reference (say which file) or a fresh fetch of the OSR. The bundled references are
  curated from a stable, long-frozen SDK (16.0 is the last major), but they are **not** a complete field
  dump — when a field isn't in them, fetch the OSR rather than guessing. Mark anything you couldn't
  confirm "confirm in the OSR".
- **The OSR is the schema.** QuickBooks Desktop has **no SQL schema and no supported direct DB access** —
  the company file (`.QBW`) is proprietary and reachable only through the SDK. The authoritative
  "schema" is the qbXML spec, documented object-by-object in Intuit's **OSR (onscreen reference)**. Treat
  it the way the Sage skills treat a data dictionary: it is the source of truth for names and structure.
- **Never guess a request name, field, OR member or version.** These are exactly what a plausible guess
  gets wrong (e.g. flipping `TransferInventoryAdd` to `InventoryTransferAdd`, or using a field that only exists in a
  newer spec than the connected QB supports). If unsure, say so and point at the OSR object.
- **Writes go through the SDK, never around it.** There is no "just UPDATE the table" path — all changes
  are Add/Mod/Void/Del requests so QuickBooks runs its own logic. If asked for direct DB writes, explain
  there is no supported way and that it would corrupt the file; use the matching request instead.
- **Match the edition and version.** Ask which QuickBooks (year/edition: Pro/Premier/Enterprise, US/CA/UK)
  and which qbXML spec version the integration targets when it changes the answer — the supported version
  set, available fields, and some limits differ. A request built at a version the connected QB doesn't
  support fails; confirm support with `HostQueryRq` (§ 3).
- **Don't hedge-guess behaviour.** When an inventory/accounting effect (what posts to which account, how
  average cost moves, when a sales order shows as fulfilled) isn't in a reference, fetch the Intuit doc
  and cite it or leave it out. A hedged guess still reads as advice.

## 3. Object model (qbXML — the "schema")

Read `references/qbxml/object-model.md` for the model that underlies every request, then
`references/qbxml/objects.md` for the catalogue of the common lists and transactions, their key fields,
and the OR aggregates. `references/qbxml/INDEX.md` lists what each file covers and its verified date.

The essentials, so you route and answer correctly:

1. **Two kinds of entity.** *List* entities (Customer, Vendor, Employee, Item*, Account, Class,
   SalesRep, InventorySite…) are identified by **`ListID`** (immutable) and a **`FullName`**; *transaction*
   entities (Invoice, SalesOrder, PurchaseOrder, ItemReceipt, Bill, SalesReceipt, InventoryAdjustment,
   TransferInventory…) by **`TxnID`**, with lines identified by **`TxnLineID`**. Both carry an
   **`EditSequence`** used for concurrency (see Mod below). `*Ref` fields (e.g. `CustomerRef`,
   `ItemRef`) point at a list entity by `ListID` **or** `FullName` — set one.
2. **Verb per request.** Each object offers some of `Add`, `Mod`, `Query`, `Del`/`Void`. Naming is
   `<Object><Verb>Rq` / `...Rs` (e.g. `InvoiceAddRq`, `InvoiceModRq`, `InvoiceQueryRq`). Use Query to get
   `ListID`/`TxnID`/`EditSequence` first; Add to create; Mod to change; Void to zero a transaction while
   keeping it; Del to remove (lists and some txns only).
3. **Mod needs a current `EditSequence`.** Query the object, keep its `EditSequence`, send it back in the
   Mod. If it changed since (someone edited it), QuickBooks rejects with status **3200** — re-query and retry.
   This is optimistic concurrency; never fabricate an `EditSequence`.
4. **OR aggregates are choices — set exactly one.** qbXML marks mutually-exclusive groups with an `OR`
   prefix: `ORInvoiceLineAdd` (an `InvoiceLineAdd` **or** a `SubtotalLineAdd`), `ORSerialLotNumber`
   (`SerialNumber` **or** `LotNumber`), `ORRate`, etc. In QBFC these are `IOR…` objects where setting one
   member clears the others. Setting two, or neither when one is required, is a common and silent error.
5. **Linking transactions.** `LinkToTxn` / `LinkToTxnID` ties one transaction to another — e.g. an
   invoice line linked to a sales order line so QuickBooks marks the order fulfilled, or an item receipt
   linked to a purchase order. Link by `TxnID` + `TxnLineID`; don't re-key the linked lines by hand.
6. **Versions.** The number pair in the message set request (country + major.minor) selects the qbXML spec
   version; a field only exists from the version that introduced it, and the connected QB must support
   that version. `HostQueryRq` returns `SupportedQBXMLVersion` for the connected file — use it when you're
   unsure what's safe. `references/qbxml/object-model.md` has the version-history notes and the format
   limits that bite (date format, amount/qty formatting, `RefNumber` length, string lengths).

To look something up: grep `references/qbxml/objects.md` by topic (e.g. `(?i)serial`, `(?i)site`,
`(?i)class`), and if it isn't there fetch the OSR object page and cite it.

## 4. Development (C# — QBFC or raw qbXML)

Generate or review C# against the QB SDK. Default to **QBFC** (the typed COM wrapper, `Interop.QBFC<ver>`)
because the type library enforces object and field names at compile time — which is most of what keeps an
integration correct. Use **raw qbXML via QBXMLRP2** only when asked, or for the Web Connector.

1. **Pin the request**: which object and verb (InvoiceAdd? SalesOrderQuery? ItemReceiptAdd linked to a
   PO?), read vs create/modify, QBFC vs raw qbXML, the qbXML version, and the connection shape (§ 5 — a
   desktop tool vs an unattended/hosted service changes the open sequence). Ask when any of these changes
   the code.
2. **Read** `references/qbfc/csharp.md` for the correct QBFC idioms end-to-end (session lifecycle, build a
   `IMsgSetRequest` with the right version and `OnError`, append the request, `DoRequests`, then *walk*
   the `IMsgSetResponse` → `IResponseList` → check `StatusCode` → cast `Detail` to the typed `*Ret`), and
   `references/qbfc/common-mistakes.md` **before** writing code so you produce the correct pattern, not
   the common wrong one.
3. **Verify every object and field** against § 3 (`references/qbxml/objects.md` / the OSR). Never emit a
   `SetValue` on a field you haven't confirmed exists at the target version, and never guess an OR member.
   Cite the reference (or "confirm in the OSR").
4. **Generate correct C#**: an `IDisposable`-style wrapper that **ends the session and closes the
   connection in `finally`** (a leaked session holds the company file / a seat); check **every** response
   `StatusCode` (0 = OK; 1 = query found nothing; ≥ 3000 = error; some 500-range = warning) and surface
   `StatusMessage`; handle **null** fields on the response (an optional field absent in the file is null);
   set amounts/quantities and dates in qbXML's expected format; respect `RefNumber`/string length limits;
   choose exactly one OR member; and handle detail-line order deliberately. For Mod, Query → keep
   `EditSequence` → Mod (handle 3200).
5. **Deliver**: one ```csharp block, a short note on the session/connection lifecycle and which
   objects/fields were verified vs still need confirming on the install, and the environment caveats
   (§ 5 — 32-bit, STA/single-threaded, QB must be installed/authorized). Offer the raw-qbXML equivalent
   or a Web Connector variant as a follow-up when relevant.

## 5. Setup & connectivity

Read `references/setup/connectivity.md` for the full picture; `references/setup/INDEX.md` indexes it.
Pin these before writing connection code or diagnosing a failure:

- **Which access layer.** **QBFC** (typed COM wrapper) and **QBXMLRP2** (the raw Request Processor) both
  talk to a QuickBooks running **on the same machine**. The **Web Connector (QBWC)** is for when your code
  runs **elsewhere or unattended**: you expose a SOAP service implementing the QBWC callbacks
  (`authenticate`, `sendRequestXML`, `receiveResponseXML`, `closeConnection`, …) plus a `.QWC` config, and
  the Web Connector installed next to QuickBooks polls you and relays qbXML. Pick by *where the code runs*.
- **Connection & session sequence.** `OpenConnection(appID, appName)` (or `OpenConnection2` with a
  connection type) **before** `BeginSession(companyFile, openMode)`; one message set at a time; then
  `EndSession` and `CloseConnection`. `companyFile = ""` means "use the file currently open in QuickBooks".
- **Open modes.** `omDontCare` (match however QB is currently open), `omSingleUser`, `omMultiUser`. For
  unattended posting, multi-user lets QuickBooks stay open for humans; single-user is required for some
  operations. Getting this wrong is a frequent "could not start QuickBooks" cause.
- **Authorization & certificate.** The first connection makes QuickBooks prompt a logged-in **admin** to
  authorize the app (Integrated Application preferences), including "allow access even when QuickBooks is
  not running" + an auto-login user for unattended use. An unsigned app triggers a security warning; a
  code-signing certificate avoids it. These are one-time, per-company-file, admin actions — the integration
  can't grant them to itself.
- **Hard constraints.** The SDK is **32-bit COM, Windows-only** — build the host **x86**, and it needs a
  QuickBooks (or the SDK's runtime) installed locally; it is **not** usable from a clean .NET Core/Linux
  process. Sessions are **single-threaded / STA** — serialise requests, don't share a session across threads.

`references/setup/connectivity.md` carries the common error signatures (e.g. 0x80040408 "Could not start
QuickBooks", 0x80040416 company file in wrong mode, authorization-denied, version-not-supported) with the
usual cause and fix.

## 6. Gotchas (things a careful engineer still gets wrong)

- **No SQL, no direct DB.** There is no supported schema or table access — everything is a request. Reject
  "just read/write the table" asks and use a Query/Add/Mod instead.
- **Version mismatch fails silently or hard.** Building a request at a qbXML version the connected QB
  doesn't support, or using a field newer than that version, errors. Check `HostQueryRq` →
  `SupportedQBXMLVersion`; set the message set version to the lowest that has the fields you need.
- **`EditSequence` is mandatory for Mod** and goes stale — status **3200** means re-query and retry; never
  hand-craft or cache it long-term.
- **OR aggregates**: set exactly one member. Setting both, or relying on a default, produces wrong or
  rejected data and the message is often unhelpful.
- **Check `StatusCode` on every response** in a message set (each appended request has its own). `OnError`
  = `roeStop` aborts the set on the first failure; `roeContinue` runs the rest — choose deliberately.
  Status **1** on a Query is "found nothing", not an error.
- **Null on responses**: an optional field that's empty in the file comes back as a null object, not an
  empty string — null-check before `GetValue()`.
- **Formats/limits**: dates are `YYYY-MM-DD`; amounts and quantities are formatted strings; `RefNumber` and
  many name fields have length caps (exceeding them truncates or errors). Confirm limits in the OSR.
- **Leaked session = locked file / held seat.** Always `EndSession`/`CloseConnection` in `finally`.
- **32-bit + STA + local install**: the single biggest deployment surprise — the service must be x86, on a
  machine with QuickBooks, authorized against *that* company file, and must not fan requests across threads.
- **Desktop ≠ Online.** qbXML concepts do not map to the QBO REST API; don't answer a QBO question from here.

## 7. Layout

```
references/qbxml/    INDEX.md, object-model.md (ListID/TxnID/EditSequence, verbs, OR aggregates,
                     LinkToTxn, versions & format limits), objects.md (catalogue of common lists &
                     transactions with key fields and OR members)
references/qbfc/     INDEX.md, csharp.md (correct QBFC idioms: session → msg set → walk response),
                     common-mistakes.md (the wrong patterns, and why)
references/setup/    INDEX.md, connectivity.md (QBFC vs QBXMLRP2 vs QBWC, connection/open modes,
                     authorization & certificate, 32-bit/STA constraints, error signatures)
evals/evals.json     test prompts per capability
scripts/             package_skill.py (maintenance packaging only, never needed at runtime)
MAINTENANCE.md       how to bundle real OSR data, add a capability, refresh for a new SDK version
```

Each `references/` folder has an `INDEX.md` naming the source and verified date per file — read it first,
open only what the request needs.
