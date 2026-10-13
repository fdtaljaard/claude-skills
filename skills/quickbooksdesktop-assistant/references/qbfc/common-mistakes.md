<!-- source: DRAFT, written from author knowledge of the QuickBooks Desktop SDK QBFC programmer's guide and qbXML spec, developer.intuit.com; not yet checked against them. To confirm: each pattern and its stated failure against the SDK documentation | version: QBFC / qbXML 16.0 | verified: not yet (draft written 2026-10-06) -->
# QBFC / qbXML — common mistakes (and why)

Read before writing code. Each is a real pattern that passes on a developer's machine and fails at a
customer site, or corrupts data quietly. The *why* matters more than the rule — it tells you when the rule
bends.

## Session & connection

- **Leaking the session.** Not calling `EndSession`/`CloseConnection` in a `finally`. A thrown exception
  then leaves the company file locked and a seat/connection held until the process dies. *Always* release
  in `finally` (or an `IDisposable` wrapper). One leaked session can block every other user.
- **Wrong order.** Calling `BeginSession` before `OpenConnection`, or `DoRequests` before `BeginSession`.
  The sequence is fixed: open connection → begin session → do requests → end session → close connection.
- **Assuming a company file.** Passing `""` to `BeginSession` means "whatever file is open in QuickBooks"
  — great for an attended desktop tool, wrong for an unattended service that must target a specific file.
  Pass the explicit `.QBW` path for unattended, and make sure the app is authorized for *that* file with
  an auto-login user.
- **Building for AnyCPU / .NET Core.** QBFC is 32-bit COM, Windows-only. An AnyCPU build that happens to
  run 64-bit can't load it; a .NET Core/Linux host can't either. Target **x86** on Windows with the SDK/QB
  installed. This is the single most common "works for me, not in prod" cause.
- **Threading a single session.** QBFC is STA/single-threaded. Sharing one `QBSessionManager` across
  threads, or firing overlapping `DoRequests`, corrupts state. Serialise; one message set at a time.

## Versions & features

- **Reaching for the newest version reflexively.** `CreateMsgSetRequest("US", 16, 0)` against a
  QuickBooks that only supports up to 13.0 fails. Pick the **lowest** version that has the fields you need,
  and confirm with `HostQueryRq` → `SupportedQBXMLVersion` when targeting unknown installs.
- **Using a field newer than your message-set version** (or newer than the connected QB). The field is
  silently unavailable or the request errors. Check the field's "introduced in" in the OSR.
- **Using a feature-gated object without checking the feature is on.** `SalesOrderAdd` on Pro (no sales
  orders), `TransferInventoryAdd` / `InventorySiteRef` / serial-lot without Advanced Inventory, multicurrency
  fields with multicurrency off — all fail. Query `PreferencesQueryRq` / `CompanyQueryRq` first when it's
  in doubt.

## Object model

- **Guessing a request or field name.** Flipped word order (`InventoryTransferAdd` — the real object is
  `TransferInventoryAdd`), custom-field inlining, "the
  status field" — invented names are the #1 failure. Verify in `references/qbxml/objects.md` or the OSR.
- **Setting both members of an OR aggregate** (or neither when one is required). One, and only one.
- **Storing `FullName` as the key.** `FullName` changes on rename; store `ListID`/`TxnID`. Keying your
  side by name breaks the first time a user renames a customer or item.
- **Mod without a current `EditSequence`.** Caching an old one, or omitting it, gives status 3200.
  Query → keep `EditSequence` → Mod → on 3200 re-query and retry.
- **Editing stock the wrong way.** Modding `ItemInventory.QuantityOnHand` (opening-balance only) instead
  of posting an `InventoryAdjustmentAdd`. The item Mod path won't move inventory correctly.
- **Re-keying linked quantities.** When linking an invoice line to a sales-order line (or an item receipt
  to a PO line), setting a conflicting `Quantity`/`Amount` instead of letting QuickBooks pull from the
  link produces double counts or rejects. Link by `TxnID`+`TxnLineID`; add explicit qty only where the
  version documents partial-fulfil fields.
- **Detail-line order / sequence.** Lines can come back or post in an order you didn't intend if you rely
  on defaults. Be explicit about line sequence where order matters.

## Responses & errors

- **Not checking `StatusCode` per response.** A message set with `roeContinue` can have request 1 succeed
  and request 2 fail; `DoRequests` doesn't throw for a data rejection. Walk every response and read
  `StatusCode`/`StatusMessage`. Status **1** on a query = "no match", not a failure.
- **`GetValue()` on a null field.** Optional fields absent in the file return a null object, not "". Null-
  check first or you get a `NullReferenceException` on perfectly valid data.
- **Confusing warnings with success.** 500-range statuses mean "accepted with a caveat" — still surface
  the message; the data may not be what the user expected.
- **Treating COM HRESULT failures and qbXML status codes the same.** "Couldn't reach QuickBooks"
  (HRESULT exception) and "QuickBooks rejected your data" (status code) need different handling — retry/
  alert vs fix-the-data. Separate them.

## Formats

- **Locale-formatted dates/amounts in raw qbXML.** Dates must be `YYYY-MM-DD`; amounts plain decimal
  strings. (QBFC formats typed values for you — this bites on hand-built qbXML.)
- **Overlong `RefNumber` / names.** Exceeding the cap truncates or errors. Validate before sending.
