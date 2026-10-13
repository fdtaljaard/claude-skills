<!-- source: https://developer.intacct.com/api/order-entry/, /api/purchasing/ and /api/inventory-control/ reference pages (Order Entry Transactions, Order Entry Transaction Definitions, Subtotal Templates, Purchasing Transactions, Purchasing Transaction Definitions, Inventory Transactions, Warehouse Transfers, Items, Warehouses, Bins, Available Inventory, Inventory Total Details, Item Warehouse Details, Inventory Work Queue Orders and Details, Stockable Kit Transactions, Cycle Counts), the XML Functions guide and the FAQ; page named per section | version: Sage Intacct XML Web Services, DTD 3.0 | verified: 2026-10-13 -->

# Order Entry, Purchasing and Inventory Control through the XML API

Curated rules for the supply-chain modules, the ones a warehouse, e-commerce or order integration touches.
Field-level detail (every parameter table and example) is in `objects/order-entry.md`, `objects/purchasing.md`
and `objects/inventory-control.md`; grep them by object or `Function:` line. Everything here is as documented on
the portal; transaction definition names, workflows and custom fields are company configuration and must be
confirmed on the client's company.

## 1. Transaction definitions drive everything

- A **transaction definition** is "the template for an Order Entry transaction" (`SODOCUMENTPARAMS`), a Purchasing
  transaction (`PODOCUMENTPARAMS`: "accounting rules, workflow settings, security settings, and other
  characteristics") or an inventory transaction (`INVDOCUMENTPARAMS`). Its **name is the `transactiontype`** you
  send when creating a document ("Transaction definition to use, such as a Purchase Order"), and the `docparid` you
  send when reading one.
- Names are company-specific (`Sales Order`, `Sales Invoice`, `Purchase Order`, `Vendor Invoice` appear in the
  portal's examples only as examples). Read the definitions with `query` on `SODOCUMENTPARAMS` /
  `PODOCUMENTPARAMS` / `INVDOCUMENTPARAMS` at setup rather than assuming them; the definition fixes the default
  `state`, numbering, whether a document can be converted from another, and whether it creates an AR invoice or an
  AP bill (§ 4).
- Definitions can be created and updated through the API when the company has **advanced workflows** enabled
  (Purchasing Transaction Definitions page: "If your company has enabled advanced workflows, you can add new
  transaction definitions or edit existing ones"; the page's examples are "for demonstration purposes only").
- **Subtotal templates** (`SOSUBTOTALTEMPLATE`, `POSUBTOTALTEMPLATE`) "can only be used at the top level of a multi
  entity company that is configured to use subtotal templates".

## 2. Documents, lines and keys

| Module | Header | Lines | Subtotals |
|---|---|---|---|
| Order Entry | `SODOCUMENT` | `SODOCUMENTENTRY` | `SODOCUMENTSUBTOTALS` |
| Purchasing | `PODOCUMENT` | `PODOCUMENTENTRY` | `PODOCUMENTSUBTOTALS` |
| Inventory Control | `INVDOCUMENT` | `INVDOCUMENTENTRY` | `INVDOCUMENTSUBTOTALS` |

- **`docparid`** on `lookup`, `query`, `read` and `readByQuery` of these objects names the transaction definition
  ("You must use this to take advantage of any custom fields on the specified document type"). Without it the
  definition's custom fields are absent.
- **Two keys.** Generic `read` and `delete` take `keys` = comma-separated `RECORDNO`. The legacy transaction
  functions take `key` = the document ID (`DOCID`, e.g. `Sales Order-SO1234`), "For draft transactions, specify the
  record number."
- **`STATE` database values** for `readByQuery` on `SODOCUMENT`: `S` Submitted, `A` Approved, `X` Partially Approved,
  `R` Declined, `I` Draft, `O` Pending, `D` Closed, `G` In Progress, `C` Converted, `P` Partially Converted (Order
  Entry Transactions, readByQuery query fields). `query` filters and `read` use the values `lookup` reports. The 2026
  Release 3 snapshot lists four more values (`Converted By Line`, `Partially Converted By Line`, `Exception`,
  `Analyzing`) with no documented database character: filter on them with `query` and the display value, or
  confirm the character on the company (`snapshot/`, `SODOCUMENT`). An In Progress, Converted or Partially
  Converted transaction cannot be updated with `update_sotransaction` (Order Entry Transactions, update note).
- Lines are **owned objects**: no standalone create, update or delete on `SODOCUMENTENTRY` / `PODOCUMENTENTRY` /
  `INVDOCUMENTENTRY` (their pages document `lookup`, `query`, `readByQuery` and `read` only); change them through
  the header (§ 3).
- `read` on these headers returns lines with a **zero-based `LINE_NO`**; the legacy update functions address lines
  one-based (`api-basics.md` § 6).
- `retrievepdf` returns base64-encoded PDF data for an Order Entry transaction (Order Entry Transactions, "Get
  Order Entry Transaction PDF Data").

## 3. Create, update, convert, delete, approve

Creating and updating OE, Purchasing and Inventory documents is documented **only with the legacy functions**
(`create_sotransaction`, `update_sotransaction`, `create_potransaction`, `update_potransaction`,
`partialupdate_potransaction`, `create_ictransaction`, `update_ictransaction`); the pages have no generic
`create`/`update` for them. Element order matters in legacy functions (`api-basics.md` § 1); copy it from the page's
example and parameter table.

### 3.1 `create_sotransaction` (Order Entry Transactions page)

- Required: `transactiontype`, `datecreated` (`year`/`month`/`day`), `customerid`, `sotransitems` with at least one
  `sotransitem` (`itemid`, `quantity` required; `warehouseid`, `unit`, `price`, `locationid` optional, but
  `locationid` is "Required if company is multi-entity enabled").
- `documentno`: not required for drafts; "For states other than draft, leave blank to use auto numbering if set in
  definition". `datedue` is required when `termname` is not used. `state`: `Draft`, `Pending` or `Closed`, "Default
  depends on transaction definition configuration".
- Conversion: `createdfrom` = the document number of the source transaction, and `sourcelinekey` = the `RECORDNO`
  of the source line on each converted line.
- `subtotals`, `customfields` (`customfieldname` / `customfieldvalue`, multi-pick-list values joined with `#~#`),
  change-order fields (Construction subscription) as documented.

### 3.2 `create_potransaction` (Purchasing Transactions page)

- Required: `transactiontype`, `datecreated`, `vendorid`, `returnto` and `payto` contact objects ("Set it to null to
  use vendor's default"), `potransitems` with at least one `potransitem` (`itemid`, `quantity`).
- Conversions: "Convert from a single document: use the `createdfrom` field ... and the `sourcelinekey` field in the
  `potransitem`"; "Convert from multiple documents: use the `sourcedocid` and `sourcedoclineid` fields for each
  `potransitem` ... The company must have a Construction subscription to do multi-document conversion."
- `partialupdate_potransaction`: `key` (document ID) plus the header fields to change (for example `dateposted`).
- Approvals (when the definition uses them): `getTransactionsToApprove`, then `approve` or `decline` with
  `PODOCUMENT`, `DOCID` and optional `COMMENT`, and `getApprovalHistory`.
- Delete: generic `delete` with `object` `PODOCUMENT` and `keys` (`RECORDNO`), or legacy `delete_potransaction key`.
  Order Entry documents are deleted with `delete_sotransaction key="<DOCID>"` only.

### 3.3 Updating lines: `update_sotransaction`, `update_potransaction`, `update_ictransaction`

- `key` = document ID (record number for drafts). `updatesotransitems` holds `updatesotransitem line_num="n"` to change
  an existing line ("To update an existing line use `updatesotransitem` otherwise to create a new line use
  `sotransitem`"). `line_num` is **one-based**; a `read` reports the same line as `LINE_NO` n-1. Same for the
  Purchasing and Inventory update functions. The portal's warning on all three pages: "Before doing any large scale
  update operations, perform a test to make sure you are modifying the correct lines."
- Header fields on update (`datecreated`, `documentno` for drafts without a number, `datedue`, `state`) are optional.

### 3.4 `create_ictransaction` (Inventory Transactions page)

- "An inventory transaction is usually a transfer or an adjustment." Required: `transactiontype`, `datecreated`,
  `ictransitems` with at least one `ictransitem` (`itemid`, `warehouseid`, `quantity` required; `unit`, `cost`,
  `sourcelinekey`, dimensions, `adjdocentrykey` optional).
- `adjdocentrykey`: "Record number of the source transaction line this inventory adjustment will affect. The item in
  the source transaction line must match the `itemid`".
- Tracking goes in `itemdetails/itemdetail`: `quantity`, `serialno`, `lotno`, `aisle`, `row`, `bin`,
  `itemexpiration` (year/month/day).
- Delete: generic `delete` on `INVDOCUMENT` by `RECORDNO`, or `delete_ictransaction`.

## 4. Links to Accounts Receivable and Accounts Payable

- Order Entry definitions such as Sales Invoice, Contract Invoice or Sales Credit Memo "are configured to create
  corresponding invoices in the Accounts Receivable application"; Purchasing definitions such as Vendor Invoice
  create AP bills. **When the OE/PO transaction is updated, the related AR/AP transaction is deleted and recreated
  with a new `RECORDNO`.**
- Look the related document up through **`PRRECORDKEY`** on `SODOCUMENT` / `PODOCUMENT` ("Related `RECORDNO` of
  the corresponding AR transaction"), never by a stored AR/AP record number. From the AP side, bills created by
  Purchasing carry `MODULEKEY` `9.PO` (bills entered in AP carry `3.AP`); the Bills page recommends a `MODULEKEY`
  filter for integrations.

## 5. Warehouse transfers (`ICTRANSFER`, generic `create`)

Warehouse Transfers page. A generic object, unlike the documents above.

- `TRANSACTIONDATE` required ("Date of `Immediate` transfers, creation date of `In transit` transfers").
  `TRANSFERTYPE` `Immediate` (default) or `In transit`. `ACTION` sets `TRANSFERSTATE`: for `Immediate` transfers
  `Draft` or `Post` (default `Post`); `In transit` has its own values (see the table). `OUTDATE` and `INDATE` are
  required for `In transit` and must not precede `TRANSACTIONDATE` / `OUTDATE`.
- `ICTRANSFERITEMS` "Must be one or more matched pairs" of `ICTRANSFERITEM`: `IN_OUT` `O` (outgoing warehouse) and
  `I` (incoming), `ITEMID`, `WAREHOUSEID`, `QUANTITY`, `UNIT` all required; dimensions optional (the portal table spells
  the vendor field `VENDDORID`; the 2026 Release 3 snapshot reports `VENDORID` on `ICTRANSFERITEM`, `snapshot/`).
- Exchange rate fields (`EXCH_RATE_TYPE_ID` or `EXCHANGE_RATE`, `EXCH_RATE_DATE`) for warehouses with different base
  currencies.

## 6. Items, warehouses, bins and stock

- **`ITEM`** (Items page, generic `create`/`update`/`delete`, legacy `create_item`/`update_item`/`delete_item`):
  required `ITEMID`, `NAME`, `ITEMTYPE` = `Inventory`, `Non-Inventory`, `Non-Inventory (Purchase only)`,
  `Non-Inventory (Sales only)`, `Kit` (needs Kits enabled in OE or IC), `Stockable Kit` (needs Stockable kits in IC).
  `STATUS` `active` (default) / `inactive`; `COST_METHOD` `Standard`, `Average`, `FIFO`, `LIFO`; `UOMGRP` (`Count`,
  `Weight`, ... or a custom group); `ENABLEFULFILLMENT` lets a non-inventory item appear in kits; `TAXGROUP` (GB, AU,
  ZA only); landed-cost (`METHOD` `Volume`/`Weight`/`Count`, `VALUE`) and per-warehouse replenishment entries
  (`WAREHOUSEID`, `VENDORID`) as nested tables. "Items are used in Inventory Control, Order Entry, and Purchasing."
- `readByQuery` with `fields` `*` on `ITEM` "can return different fields" per component type: name the fields.
- **`WAREHOUSE`** is a dimension; bins (`BIN`) carry the optional `ZONE`, `AISLE`, `ICROW` (rows) and `BINFACE`
  attributes and a `BINSIZE`; **`ITEMWAREHOUSEINFO`** (Item Warehouse Details) holds per-warehouse reorder data used by
  the Inventory Reorders report; **`ITEMCROSSREF`** maps customer, vendor or substitute item codes.
- **Stock on hand**: `AVAILABLEINVENTORY` ("available quantities for tracked items per serial number, lot number,
  bin number, and so forth") and `INVENTORYTOTALDETAIL` (onhand, onhold, onorder, damaged, requisitioned,
  scrap/spoilage or custom totals). Both are query objects: `lookup` them for the fields.
- **Cycle counts**: `ICCYCLECOUNT` generic `create` (`CYCLECOUNTDESC`, `WAREHOUSEID`, `EMPUSERKEY` required) with
  `ICCYCLECOUNTENTRY` lines (create, update, delete).
- **Stockable kits**: `create_stkittransaction` builds kits (required `transactiontype`, `datecreated`,
  `stkittransitems` with `itemid`, `warehouseid`, `quantity`; component tracking in `itemdetails`), and the page
  shows the disassembly request; **`COGSCLOSEDJE`** posts prior-period cost-of-goods-sold adjustments to an open
  period through the journal set in the Inventory Control configuration.

## 7. Fulfilment work queue

Inventory Work Queue Orders and Details pages (fulfilment must be enabled on the company).

- `INVENTORYWQORDER` is "the fulfillment-enhanced view of a Sales Order"; `INVENTORYWQDETAIL` "represents a
  'bundle' within fulfillment". Both support `lookup`, `query`, `readByQuery`, `read` (keys = object `ID`) and
  generic `update`; no create or delete.
- Update fields: `STATUS` (`open`, `ready to pick`, `picked`, `packed`, `ready to ship`, `shipped`, `ready to
  invoice`, `invoiced`; "No default value"), `PICKCONTAINER`, `PACKCONTAINER`, `SHIPTRACKING`; on the detail also
  `HOLDPROGRESS` (pause within the workflow, "no impact on either the customer or the order"), `QUANTITYPICKED`,
  `QUANTITYPACKED`, `ASSIGNED` (picker), `NOTES`.
- The pages' `lookup` examples write the object as `InventoryWQOrder` / `InventoryWQDetail`; the parameter tables
  and the 2026 Release 3 snapshot report `INVENTORYWQORDER` / `INVENTORYWQDETAIL`. The snapshot's `STATUS` valid
  values also include `ready to pack`, which the portal's table omits (`snapshot/`).

## 8. A warehouse integration, call by call

1. Session: `getAPISession` (entity-level `locationid` when the warehouse belongs to one entity; `api-basics.md` § 4).
2. Setup reads: `query` `SODOCUMENTPARAMS`, `PODOCUMENTPARAMS`, `INVDOCUMENTPARAMS` for the definition names and
   which ones convert into which; `lookup` with `docparid` for each definition's fields; `query` `WAREHOUSE`,
   `ITEM`, `UOM`.
3. Orders to pick: `query` `SODOCUMENT` with `docparid` and a `STATE` / date filter, `pagesize` up to 2000 with
   `offset` (or `readByQuery` + `readMore` by `resultId` for a stable set), then `read` each header for its lines
   (`LINE_NO` zero-based), or use the work queue objects when fulfilment is enabled (§ 7).
4. Shipments and invoices: either `update_sotransaction` on the order (`line_num` = `LINE_NO` + 1) or create the
   next document in the company's chain with `create_sotransaction` and `createdfrom` + `sourcelinekey`, whichever
   the definitions are configured for; the AR invoice's `RECORDNO` is read back through `PRRECORDKEY`, never stored
   from an earlier read (§ 4).
5. Receipts: `create_potransaction` for the receiving definition with `createdfrom` = the purchase order and
   `sourcelinekey` per line (multi-PO receipts need the Construction subscription).
6. Adjustments and transfers: `create_ictransaction` with the adjustment definition (`adjdocentrykey` for a
   line-level adjustment, `itemdetails` for lot, serial and bin), `ICTRANSFER` for warehouse moves.
7. Stock levels: `query` `AVAILABLEINVENTORY` / `INVENTORYTOTALDETAIL` rather than summing transactions.
8. Keep requests under 100 affected records, give every function a unique `controlid`, resubmit with
   `uniqueid` `true` after a lost response, and back off on `GW-0010` (`api-basics.md` § 5.3, § 10).
