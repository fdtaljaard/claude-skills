<!-- source: DRAFT, written from author knowledge of the QuickBooks Desktop SDK QBFC programmer's guide and QBFC type library (Interop.QBFC), developer.intuit.com; not yet checked against them. To confirm: every method signature and enum member (ENOpenMode, ENRqOnError, ENResponseType) against the installed type library | version: QBFC 16.0 | verified: not yet (draft written 2026-10-06) -->
# QBFC in C# — the correct idioms

QBFC (QuickBooks Foundation Classes) is the **typed COM wrapper** over qbXML. Prefer it for C# because the
type library enforces object and field names at compile time — most of what keeps an integration correct.
The assembly is `Interop.QBFC<ver>` (e.g. `Interop.QBFC16`); the core object is `QBSessionManager`.

> Idioms are version-independent. Confirm exact object/field names against the OSR (§ 3 of SKILL.md) and
> exact method signatures/enum members against the QBFC type library or the SDK's QBFC help (`.chm`).

## Contents
- [The lifecycle in one place](#lifecycle)
- [Building a message set request](#msgset)
- [Appending a request and setting fields](#append)
- [OR aggregates in QBFC](#or)
- [Sending and walking the response](#walk)
- [Reading a query result](#query)
- [Mod with EditSequence](#mod)
- [Linking an invoice to a sales order](#link)
- [Errors](#errors)

<a name="lifecycle"></a>
## The lifecycle in one place

Open connection → begin session → (build request → do request → walk response)\* → end session → close
connection. **End/close in `finally`** so a thrown exception never leaks a session (a leaked session locks
the company file and holds a seat). One message set at a time; single-threaded (STA).

```csharp
using Interop.QBFC16;

public sealed class QbSession : IDisposable
{
    private readonly QBSessionManager _mgr = new QBSessionManager();
    private bool _sessionOpen, _connectionOpen;

    public QbSession(string appName, string companyFile = "")
    {
        _mgr.OpenConnection("", appName);          // appID "" is normal; name shows in QB's app list
        _connectionOpen = true;
        _mgr.BeginSession(companyFile, ENOpenMode.omDontCare); // "" = file currently open in QB
        _sessionOpen = true;
    }

    public IMsgSetResponse Do(IMsgSetRequest request) => _mgr.DoRequests(request);

    // CreateMsgSetRequest lives on the manager, so expose it for callers:
    public IMsgSetRequest NewRequest(short major = 16, short minor = 0, string country = "US")
    {
        var set = _mgr.CreateMsgSetRequest(country, major, minor);
        set.Attributes.OnError = ENRqOnError.roeContinue; // or roeStop — choose deliberately
        return set;
    }

    public void Dispose()
    {
        try { if (_sessionOpen) _mgr.EndSession(); }
        finally { if (_connectionOpen) _mgr.CloseConnection(); }
    }
}
```

<a name="msgset"></a>
## Building a message set request

```csharp
IMsgSetRequest req = mgr.CreateMsgSetRequest("US", 16, 0);
req.Attributes.OnError = ENRqOnError.roeStop; // roeStop: abort set on first failure; roeContinue: run rest
```

- The `(major, minor)` pair is the **qbXML spec version** — pick the *lowest* that has every field you
  need (see version guidance in `references/qbxml/object-model.md`). If unsure what the connected file
  supports, send a `HostQueryRq` first and read `SupportedQBXMLVersion`.
- `OnError`: `roeStop` is safest when requests depend on each other; `roeContinue` when you batch
  independent requests and want partial success. Either way, **check each response's `StatusCode`**.

<a name="append"></a>
## Appending a request and setting fields

Each object has an `Append<Object><Verb>Rq()` on the message set. Fields are typed; set with
`.SetValue(...)`. `*Ref` fields take `ListID` or `FullName`.

```csharp
IInvoiceAdd add = req.AppendInvoiceAddRq();
add.CustomerRef.ListID.SetValue(customerListId);      // prefer ListID over FullName
add.TxnDate.SetValue(DateTime.Today);
add.RefNumber.SetValue(refNo);                         // mind the length cap

IORInvoiceLineAdd orLine = add.ORInvoiceLineAddList.Append();   // one OR line per item
IInvoiceLineAdd line = orLine.InvoiceLineAdd;                   // choose the InvoiceLineAdd member
line.ItemRef.ListID.SetValue(itemListId);
line.Quantity.SetValue(qty);
line.ORRate.Rate.SetValue(rate);                       // ORRate: Rate XOR RatePercent
```

Notes:
- Repeating aggregates expose a `…List` with `.Append()` returning the new element (as above).
- Set a typed value with the overload that matches (`SetValue(double)`, `SetValue(DateTime)`,
  `SetValue(string)`); QBFC formats it into qbXML for you.
- Only call the field(s) you mean to send — unset fields are simply omitted.

<a name="or"></a>
## OR aggregates in QBFC

An `IOR…` object exposes each choice as a property. **Touching one member selects it and clears the
others** — so reference exactly the member you want and set its fields:

```csharp
IORInvoiceLineAdd or = add.ORInvoiceLineAddList.Append();
// a normal line:
or.InvoiceLineAdd.ItemRef.FullName.SetValue("Widget");
// OR a subtotal line (do NOT also touch InvoiceLineAdd above):
// or.SubtotalLineAdd.ItemRef.FullName.SetValue("Subtotal");
```

Same for `ORSerialLotNumber` (`.SerialNumber` XOR `.LotNumber`), `ORRate` (`.Rate` XOR `.RatePercent`),
`ORApplyPayment`, etc. Setting two members, or none when one is required, is the classic silent bug.

<a name="walk"></a>
## Sending and walking the response

Every request in the set produces one response in the same order. **Walk, check status, then cast.**

```csharp
IMsgSetResponse resp = mgr.DoRequests(req);
IResponseList list = resp.ResponseList;
if (list == null) throw new InvalidOperationException("null response list");

for (int i = 0; i < list.Count; i++)
{
    IResponse r = list.GetAt(i);
    if (r.StatusCode != 0)
    {
        // 1 = query matched nothing (often fine); >=3000 = error; some 500s = warning
        if (r.StatusCode == 1) continue;
        throw new InvalidOperationException($"qbXML status {r.StatusCode} ({r.StatusSeverity}): {r.StatusMessage}");
    }
    if (r.Detail == null) continue;

    // Cast by the response type you expect:
    if (r.Detail is IInvoiceRet inv)
    {
        string txnId = inv.TxnID.GetValue();
        string refNo = inv.RefNumber?.GetValue(); // null-check: optional fields come back null
    }
}
```

- `StatusCode == 0` success; `1` = query found nothing; `>= 3000` = error; `500`-range = warning (data
  accepted with a caveat — still read `StatusMessage`).
- `r.Detail` is typed as the matching `*Ret` (or a `*RetList`). Prefer `is`-pattern casts; if you check
  `r.Type.GetValue()` against an `ENResponseType`, cast only after it matches.
- **Null-check every response field** before `GetValue()` — an absent optional field is a null object.

<a name="query"></a>
## Reading a query result

```csharp
ICustomerQuery q = req.AppendCustomerQueryRq();
q.ORCustomerListQuery.CustomerListFilter.MaxReturned.SetValue(50); // paging / filters live under an OR
// ... DoRequests, walk to the response ...
if (r.Detail is ICustomerRetList crl)
    for (int j = 0; j < crl.Count; j++)
    {
        ICustomerRet c = crl.GetAt(j);
        string listId = c.ListID.GetValue();
        string edit   = c.EditSequence.GetValue(); // keep this if you plan to Mod
    }
```

Large result sets: use the query's iterator attributes (`iterator` / `iteratorID` / `iteratorRemainingCount`)
or filters (`MaxReturned`, `FromModifiedDate`) to page — don't pull an entire file blind.

<a name="mod"></a>
## Mod with `EditSequence`

```csharp
// 1) Query to get TxnID + current EditSequence (see above).
// 2) Mod with both:
IInvoiceMod mod = req.AppendInvoiceModRq();
mod.TxnID.SetValue(txnId);
mod.EditSequence.SetValue(editSeq);              // MUST be current
mod.RefNumber.SetValue(newRef);
// line edits: keep a line by sending its TxnLineID; add with the "add" sentinel; omit to delete
```

If the object changed since the query, `DoRequests` returns **StatusCode 3200** ("object has been
modified"). Catch that specifically, re-query for a fresh `EditSequence`, and retry.

<a name="link"></a>
## Linking an invoice to a sales order

Set the invoice **line's** `LinkToTxn` to the sales-order `TxnID` + the SO line's `TxnLineID`. Let
QuickBooks pull the quantity from the linked line (don't also set a conflicting `Quantity` unless the
version supports partial-fulfil fields):

```csharp
IORInvoiceLineAdd or = add.ORInvoiceLineAddList.Append();
or.InvoiceLineAdd.LinkToTxn.TxnID.SetValue(salesOrderTxnId);
or.InvoiceLineAdd.LinkToTxn.TxnLineID.SetValue(salesOrderTxnLineId);
```

The same pattern links an `ItemReceiptAdd`/`BillAdd` line to a purchase-order line. Store the source
`TxnID`/`TxnLineID` when you create the order so you can link later.

<a name="errors"></a>
## Errors

- The **primary** signal is each response's `StatusCode`/`StatusSeverity`/`StatusMessage` — read them even
  when no exception is thrown.
- Connection/session problems surface as **COM exceptions** with HRESULTs (e.g. `0x80040408`
  "could not start QuickBooks", `0x80040416` wrong open mode, `0x80040410`/authorization). See
  `references/setup/connectivity.md` for the signatures and fixes.
- Wrap COM calls so you can distinguish "QuickBooks rejected the data" (status code) from "couldn't reach
  QuickBooks" (HRESULT) — they need different responses.
