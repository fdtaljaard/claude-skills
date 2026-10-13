# references/qbxml — index

The qbXML "schema": the object model and a catalogue of the common objects. QuickBooks Desktop has no SQL
schema — this, and Intuit's **OSR (onscreen reference)**, are the source of truth for object/field names.

| File | Covers | Source | Verified |
|---|---|---|---|
| `object-model.md` | Lists vs transactions; `ListID`/`TxnID`/`TxnLineID`/`EditSequence`; `*Ref` fields; Add/Mod/Query/Del/Void verbs; OR aggregates; `LinkToTxn`; `DataExt` custom fields; message sets & spec versions; formats/limits | **Draft**: from author knowledge of the qbXML spec (≤ 16.0) and OSR; not yet checked (header says what to confirm) | not yet |
| `objects.md` | Curated catalogue of common lists (Customer, Vendor, Item*, Account, …) and transactions (Invoice, SalesOrder, PurchaseOrder, ItemReceipt, InventoryAdjustment, TransferInventory, …) with key fields, OR members, gotchas; plus Host/Company/Preferences queries | **Draft**: from author knowledge of the qbXML spec (≤ 16.0) and OSR; not yet checked (header says what to confirm) | not yet |

**Not a complete field dump.** For the full field list of any object, the exact version a field was
introduced, or anything not catalogued, open the object in the OSR and cite it:
`https://developer.intuit.com/app/developer/qbdesktop/docs/api-reference/qbdesktop` (and the OSR itself).
See `MAINTENANCE.md` for bundling a real OSR export to raise verification rigor to the Sage-family level.
