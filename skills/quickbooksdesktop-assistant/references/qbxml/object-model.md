<!-- source: DRAFT, written from author knowledge of the QuickBooks Desktop SDK qbXML spec and Intuit OSR (onscreen reference), developer.intuit.com; not yet checked against them. To confirm: verbs, ID and EditSequence rules, OR aggregates, spec versions and limits in the OSR | version: qbXML through 16.0 | verified: not yet (draft written 2026-10-06) -->
# qbXML object model

The model every QuickBooks Desktop request is built on. This is the part a model gets wrong by guessing,
so treat it as the contract. Exact object/field names and the version that introduced a field live in
Intuit's **OSR (onscreen reference)** — this file gives the structure; confirm specifics there.

> Verified from the stable QB SDK (qbXML spec through 16.0). The SDK has been frozen for years, so the
> model below is durable; individual field availability by version still comes from the OSR.

## Contents
- [Lists vs transactions](#lists-vs-transactions)
- [Identifiers: ListID, TxnID, TxnLineID, EditSequence](#identifiers)
- [Ref fields](#ref-fields)
- [Request verbs: Add / Mod / Query / Del / Void](#verbs)
- [OR aggregates (choices)](#or-aggregates)
- [Linking transactions (LinkToTxn)](#linking)
- [Custom fields (DataExt)](#custom-fields)
- [Message sets and spec versions](#versions)
- [Formats and limits](#formats)

<a name="lists-vs-transactions"></a>
## Lists vs transactions

Everything in a company file is either a **list** entity or a **transaction** entity, and they behave
differently.

**List entities** — the master data referenced by transactions:
`Customer`, `Vendor`, `Employee`, `OtherName`, `Account`, `Class`, `Item*` (ItemInventory,
ItemInventoryAssembly, ItemNonInventory, ItemService, ItemDiscount, ItemGroup, ItemSalesTax, …),
`PriceLevel`, `SalesRep`, `SalesTaxCode`, `PaymentMethod`, `ShipMethod`, `Terms`, `InventorySite`
(Enterprise, Advanced Inventory), `UnitOfMeasureSet`, `Currency`, `ToDo`, `Template`.

**Transaction entities** — the documents:
`Invoice`, `SalesReceipt`, `SalesOrder`, `Estimate`, `CreditMemo`, `ReceivePayment`, `PurchaseOrder`,
`ItemReceipt`, `Bill`, `BillPaymentCheck`, `BillPaymentCreditCard`, `Check`, `CreditCardCharge`,
`CreditCardCredit`, `Deposit`, `JournalEntry`, `InventoryAdjustment`, `TransferInventory` (site-to-site;
Advanced Inventory), `TimeTracking`, `VehicleMileage`, `BuildAssembly`, `Transfer`.

(Not every object supports every verb, and some are query-only. Confirm per object in the OSR.)

<a name="identifiers"></a>
## Identifiers

- **`ListID`** — the immutable, QuickBooks-assigned key of a *list* entity. Stable across renames. The
  thing to store on your side as the foreign key, not the name.
- **`FullName`** — the human path of a list entity, with `:` separating hierarchy levels
  (`Customer:Job`, `ParentItem:Child`). Unique but *mutable* (a rename changes it). Fine for lookups, bad
  as a stored key.
- **`TxnID`** — the immutable key of a *transaction*. Store this to find or link the document later.
- **`TxnLineID`** — the immutable key of a single *line* within a transaction. Needed to link or modify a
  specific line (e.g. link an invoice line to a specific sales-order line).
- **`TxnNumber`** — an internal sequential number QuickBooks assigns (read-only). Distinct from
  **`RefNumber`**, the user-visible document number (invoice no., PO no.) which you may set and which has a
  length limit.
- **`EditSequence`** — an opaque concurrency token on every list and transaction object. See Mod below.

<a name="ref-fields"></a>
## Ref fields (`*Ref`)

A field ending in `Ref` points at a list entity: `CustomerRef`, `VendorRef`, `ItemRef`, `AccountRef`,
`ClassRef`, `SalesRepRef`, `InventorySiteRef`, `TemplateRef`, `SalesTaxCodeRef`, etc. Each `*Ref` has a
`ListID` and a `FullName` — **set one** (prefer `ListID` when you have it, since it survives renames). On
responses, a `*Ref` returns both so you can cache the `ListID`.

<a name="verbs"></a>
## Request verbs

Requests are named `<Object><Verb>Rq` and responses `<Object><Verb>Rs`.

| Verb | Purpose | Notes |
|---|---|---|
| `Query` | Read existing objects | Returns `ListID`/`TxnID` + `EditSequence`. Filter by ID, ref, date range, status, modified-date, etc. Status **1** = nothing matched (not an error). Supports paging (`MaxReturned`, iterator attributes). |
| `Add` | Create a new object | Returns the created object (`…Ret`) with its new `ListID`/`TxnID`. |
| `Mod` | Change an existing object | Requires `ListID`/`TxnID` **and a current `EditSequence`**. |
| `Del` | Delete | Lists and some transactions. By `ListID`/`TxnID` + `EditSequence`. |
| `Void` | Void a transaction | Zeros amounts but keeps the record (audit trail). Transactions only. |

**Mod + `EditSequence` (optimistic concurrency).** Flow: `Query` the object → keep its `EditSequence` →
send `Mod` with the same `ListID`/`TxnID` and `EditSequence`. If anyone changed the object since the
query, the `EditSequence` is stale and QuickBooks rejects with **StatusCode 3200** ("the object has been
modified"). Re-query to get the new `EditSequence` and retry. Never cache an `EditSequence` across a long
gap and never fabricate one.

**Line edits in a Mod** (e.g. `InvoiceModRq`): to keep an existing line, send its `TxnLineID`; to add a
line, send `TxnLineID` = `-1` (or the documented "add" sentinel); omitting a line usually deletes it.
Confirm the exact line-mod semantics per transaction in the OSR — they differ and are easy to get wrong.

<a name="or-aggregates"></a>
## OR aggregates (choices)

qbXML represents a mutually-exclusive choice with an aggregate whose name starts with `OR`. You set
**exactly one** member; setting two is invalid, and omitting a required one is invalid.

Common examples (confirm members in the OSR):
- **`ORInvoiceLineAdd`** / `ORSalesOrderLineAdd` / … — a normal line (`InvoiceLineAdd`) **or** a subtotal
  line (`SubtotalLineAdd`). Line-item aggregates exist on most transactions.
- **`ORSerialLotNumber`** — `SerialNumber` **or** `LotNumber` (Advanced Inventory).
- **`ORRate`** — a flat `Rate` **or** a `RatePercent`.
- **`ORPrice`**, **`ORApplyCheck`**, **`ORTxnID`** (link by `TxnID` or by ref)… many requests have one.

In **QBFC** these surface as `IOR…` objects: calling `OrInvoiceLineAdd.InvoiceLineAdd` (vs
`.SubtotalLineAdd`) selects that member and clears the other. In **raw qbXML** you simply emit one child
element. Either way: one, and only one.

<a name="linking"></a>
## Linking transactions (`LinkToTxn` / `LinkToTxnID`)

A transaction can be linked to another so QuickBooks tracks fulfilment/receipt:
- **Invoice ↔ Sales Order**: link an invoice (or its lines) to a sales order so the order shows as
  invoiced/closed.
- **Item Receipt / Bill ↔ Purchase Order**: link to mark PO lines received.
- **Receive Payment ↔ Invoice**, **Bill Payment ↔ Bill**, etc.

Mechanics: at the **header** level some requests accept `LinkToTxnID` (link the whole document); at the
**line** level a line's `LinkToTxn` carries the target `TxnID` **and** `TxnLineID`. When you link a line,
let QuickBooks pull the quantity/amount from the linked source rather than re-keying it, unless the
request explicitly supports partial fulfilment fields. Exact link fields differ by transaction — confirm
in the OSR.

<a name="custom-fields"></a>
## Custom fields (`DataExt`)

User-defined/custom fields are **not** inline on the object — they're separate `DataExt` entities:
- Read them with the object's query (request the data-ext aggregate) or `DataExtQueryRq`.
- Write with `DataExtAddRq` / `DataExtModRq`, naming the `DataExtName`, the owner (`OwnerID`), and the
  target (`ListObjType`/`TxnID`). A custom field must already be *defined* in QuickBooks for the object
  type before you can set it. Confirm the aggregate shape in the OSR.

<a name="versions"></a>
## Message sets and spec versions

A request is wrapped in a **message set** stamped with a country and a qbXML spec version
(major.minor). In QBFC: `CreateMsgSetRequest(country, major, minor)` (e.g. `"US", 16, 0`). In raw qbXML
the `<?qbxml version="16.0"?>` processing instruction does the same.

- **A field exists only from the version that introduced it.** Using a newer field against an older
  message-set version — or against a QuickBooks that doesn't support that version — errors.
- **Find what the connected file supports** with **`HostQueryRq`**: the `HostRet` lists
  `SupportedQBXMLVersion` (and country, product, edition). Set your message-set version to the **lowest**
  version that still has every field you need, so you stay compatible with older installs.
- **16.0 is the last major qbXML version** (the SDK is frozen). Most fields you need exist well below it;
  don't reach for the top version reflexively.

Rough era guide (confirm specifics in the OSR):
- Inventory **sites / `TransferInventory` / serial & lot** are Enterprise *Advanced Inventory* features
  that arrived in the 12.0-era spec — they fail against editions/versions without Advanced Inventory on.
- Early specs (≤ 6.0) lack many later aggregates; integrations targeting old QuickBooks must drop to a
  version those files support.

<a name="formats"></a>
## Formats and limits (confirm exact caps in the OSR)

- **Dates**: `YYYY-MM-DD`. **Datetimes**: ISO-8601. No locale formatting.
- **Amounts**: decimal strings, 2 dp for money; **quantities**: decimal strings (QuickBooks stores up to 5
  dp). QBFC takes typed values and formats them; raw qbXML needs the string right.
- **`RefNumber`**: capped (historically 11 characters) — exceeding it truncates or errors.
- **Names / `FullName`** and many text fields have length caps; `:` is the hierarchy separator in
  `FullName`, so a literal `:` in a name is illegal.
- **Booleans**: `true`/`false` in raw qbXML.
- **Enumerated fields** (account types, item types, txn statuses) take a fixed set of string values —
  take them from the OSR, never guess.
