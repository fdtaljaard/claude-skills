<!-- source: DRAFT, written from author knowledge of the QuickBooks Desktop SDK qbXML spec and Intuit OSR (onscreen reference), developer.intuit.com; not yet checked against them. To confirm: every object's fields, OR members and introducing version in the OSR | version: qbXML through 16.0 | verified: not yet (draft written 2026-10-06) -->
# qbXML object catalogue

A working catalogue of the lists and transactions most integrations touch, with their key fields, the OR
aggregates to watch, and the identifiers. **This is a curated subset, not a field dump** — for the full
field list of any object, and for anything not here, open the object in the OSR and cite it.

> Grep this file by topic: `(?i)serial`, `(?i)site`, `(?i)class`, `(?i)link`, `(?i)purchase`.
> Verified against the stable qbXML spec (≤ 16.0); field *availability by version* comes from the OSR.

## How to read an entry

Each entry lists: the **verbs** available, the **identifier**, the **required-ish** fields to create one,
the **OR aggregate(s)**, and **gotchas**. "Required-ish" = what QuickBooks almost always needs; the OSR
marks true required vs optional per version.

---

## Lists

### Customer (`CustomerAdd/Mod/Query`)
- **ID**: `ListID` + `EditSequence`; `Name` (unique) / `FullName` (with `:Job`).
- **Key fields**: `Name`, `CompanyName`, `BillAddress`/`ShipAddress` (aggregates), `Phone`, `Email`,
  `TermsRef`, `SalesTaxCodeRef`, `ItemSalesTaxRef`, `PriceLevelRef`, `CurrencyRef` (multicurrency on).
- **Gotchas**: a *job* is a Customer with a `ParentRef`. `IsActive` toggles visibility (Mod, don't Del, to
  retire). Credit limits/balances are read-only derived fields.

### Vendor (`VendorAdd/Mod/Query`)
- **ID**: `ListID` + `EditSequence`; `Name`.
- **Key fields**: `CompanyName`, `VendorAddress`, `TermsRef`, `VendorTaxIdent`, `IsVendorEligibleFor1099`,
  `CurrencyRef`.

### Item — inventory (`ItemInventoryAdd/Mod/Query`)
- **ID**: `ListID` + `EditSequence`; `Name` / `FullName`.
- **Key fields**: `IncomeAccountRef`, `COGSAccountRef`, `AssetAccountRef` (all three required for a true
  inventory item), `SalesPrice`/`SalesPriceIsSet`, `PurchaseCost`, `ManufacturerPartNumber`,
  `UnitOfMeasureSetRef`, `QuantityOnHand`/`TotalValue`/`InventoryDate` (**opening balance only on Add** —
  never Mod quantity here; use `InventoryAdjustment`).
- **Gotchas**: other item types are *different objects* — `ItemNonInventoryAdd`, `ItemServiceAdd`,
  `ItemInventoryAssemblyAdd`, `ItemGroupAdd`, `ItemDiscountAdd`, `ItemSalesTaxAdd`. Don't try to set an
  item type field on one object.

### Account (`AccountAdd/Mod/Query`)
- **ID**: `ListID`; `Name` / `FullName`.
- **Key fields**: `AccountType` (fixed enum — `Bank`, `AccountsReceivable`, `Income`, `Expense`,
  `CostOfGoodsSold`, `OtherCurrentAsset`, … take from OSR), `ParentRef` for sub-accounts.

### Class, SalesRep, InventorySite, Terms, PaymentMethod, ShipMethod, PriceLevel, UnitOfMeasureSet
- All `Add/Mod/Query` lists keyed by `ListID` + `FullName`. **`InventorySite`** exists only with Advanced
  Inventory (Enterprise); `InventorySiteRef` on lines/transfers points at it. Confirm fields in the OSR.

---

## Transactions

### Invoice (`InvoiceAdd/Mod/Query`)
- **ID**: `TxnID` + `EditSequence`; lines by `TxnLineID`. User number = `RefNumber`.
- **Header**: `CustomerRef` (required), `TxnDate`, `RefNumber`, `TermsRef`, `ClassRef`, `TemplateRef`,
  `ItemSalesTaxRef`, `CustomerMsgRef`, `IsToBePrinted`/`IsToBeEmailed`.
- **Lines**: `ORInvoiceLineAdd` per line → **either** `InvoiceLineAdd` (with `ItemRef`, `Quantity`,
  `ORRate` → `Rate`/`RatePercent`, `Amount`, `ClassRef`, `InventorySiteRef`, `ORSerialLotNumber`,
  `LinkToTxn`) **or** `SubtotalLineAdd`.
- **Link to sales order**: set a line's `LinkToTxn` = the SO `TxnID` + the SO line `TxnLineID`; let
  QuickBooks pull quantity unless the version supports explicit fulfil fields. Marks the SO invoiced.
- **Gotchas**: set `Amount` *or* `Rate`×`Quantity`, not conflicting values; one OR member per line;
  serial/lot and site only when Advanced Inventory is on.

### Sales Order (`SalesOrderAdd/Mod/Query`) — Premier/Enterprise only
- **ID**: `TxnID`; lines by `TxnLineID`.
- **Header/lines** mirror Invoice (`ORSalesOrderLineAdd`). Lines carry fulfilment fields
  (`QuantityToInvoice`, `IsManuallyClosed`). Invoices/item-ship link back here.
- **Gotcha**: unavailable in Pro — if the user is on Pro, say so.

### Sales Receipt (`SalesReceiptAdd/Mod/Query`)
- Like an Invoice but paid at point of sale (`DepositToAccountRef`, `PaymentMethodRef`). `ORSalesReceiptLineAdd`.

### Estimate / Credit Memo
- `EstimateAdd` (non-posting; can be linked to an invoice), `CreditMemoAdd` (`ORCreditMemoLineAdd`). Same shape.

### Purchase Order (`PurchaseOrderAdd/Mod/Query`)
- **ID**: `TxnID`; lines by `TxnLineID`. `VendorRef` (required), `ShipToEntityRef`, `RefNumber`,
  `ExpectedDate`, `InventorySiteRef`. Lines: `ORPurchaseOrderLineAdd` → `PurchaseOrderLineAdd`
  (`ItemRef`, `Quantity`, `Rate`, `Amount`, `CustomerRef`, `ClassRef`).
- Item receipts / bills link to PO lines to mark them received.

### Item Receipt (`ItemReceiptAdd/Mod/Query`)
- **ID**: `TxnID`; lines by `TxnLineID`. `VendorRef`, `TxnDate`, `RefNumber`, `APAccountRef`.
- **Lines**: `ORItemLineAdd` → `ItemLineAdd` (`ItemRef`, `Quantity`, `Cost`, `Amount`, `InventorySiteRef`,
  `ORSerialLotNumber`, `LinkToTxn` → PO `TxnID`+`TxnLineID`). Receives inventory into stock.
- **Gotcha**: linking to a PO line pulls remaining qty; setting conflicting qty/cost is a common error.

### Bill / Bill Payment
- `BillAdd` (`VendorRef`, `APAccountRef`, `ExpenseLineAdd` and/or `ItemLineAdd`). `BillPaymentCheckAdd` /
  `BillPaymentCreditCardAdd` link to bills via `AppliedToTxnAdd` (an OR/aggregate — confirm in OSR).

### Receive Payment (`ReceivePaymentAdd`)
- `CustomerRef`, `TotalAmount`, `PaymentMethodRef`, `DepositToAccountRef`, and `ORApplyPayment` /
  `AppliedToTxnAdd` to apply against specific invoices (`TxnID`). Over/underpayment handling via fields.

### Inventory Adjustment (`InventoryAdjustmentAdd`)
- **The correct way to change stock quantity/value** (never Mod an item's `QuantityOnHand`).
  `AccountRef` (adjustment account), `InventorySiteRef`, and `InventoryAdjustmentLineAdd` per item with
  `ItemRef` and **either** `QuantityAdjustment` **or** `ValueAdjustment` (OR), plus `ORSerialLotNumber`.

### Transfer Inventory (`TransferInventoryAdd`) — Advanced Inventory
- **Request name is `TransferInventoryAdd` (NOT `InventoryTransferAdd`).** qbXML: `TransferInventoryAddRq`.
  QBFC: `AppendTransferInventoryAddRq()` → `ITransferInventoryAdd`; lines via
  `TransferInventoryLineAddList.Append()` → `ITransferInventoryLineAdd`; response `ITransferInventoryRet`.
- Moves stock **site to site** (and bin to bin where enabled). Header: `TxnDate`, `RefNumber`,
  `FromInventorySiteRef`, `ToInventorySiteRef`. Lines: `ItemRef`, `QuantityToTransfer`, `ORSerialLotNumber`
  (serial/lot items), optional `FromInventorySiteLocationRef`/`ToInventorySiteLocationRef` (bins).
- **One From/To site pair per request** — split multiple pairs into separate requests.
- **Gotcha**: fails unless the file is Enterprise with Advanced Inventory + Multiple Sites enabled and the
  sites exist as `InventorySite` list entities. Introduced around qbXML spec 12.0. (Field names above are
  verified against a working QBFC16 integration; confirm bin-level fields and the exact minimum version in
  the OSR.)

### Journal Entry (`JournalEntryAdd`)
- `TxnDate`, `RefNumber`, and `JournalDebitLine` / `JournalCreditLine` aggregates (`AccountRef`, `Amount`,
  `EntityRef`, `ClassRef`). Debits must equal credits.

### Build Assembly (`BuildAssemblyAdd`) — assemblies
- `ItemInventoryAssemblyRef`, `QuantityToBuild`, `InventorySiteRef`. Consumes components, adds assemblies.

---

## Host / company info

### Host (`HostQueryRq`)
- Returns `HostRet`: `ProductName`, `MajorVersion`/`MinorVersion`, `Country`, `IsAutomaticLogin`,
  `SupportedQBXMLVersion` (list), `HostEditionList`. **Call this first** when you need to know what the
  connected file supports before choosing a message-set version or a feature-gated object.

### Company (`CompanyQueryRq`)
- Company name, address, legal name, EIN, `IsSampleCompany`, enabled subscriptions/features. Useful to
  confirm multicurrency/Advanced-Inventory before using gated fields.

### PreferencesQueryRq
- Returns feature toggles (inventory on? multicurrency? sales orders? sites?) — check before using a
  feature-gated object rather than failing at `Add`.
