<!-- source: https://developer.intacct.com/ (Sage Intacct developer portal: XML Web Services Overview, XML Requests, XML Responses, Error Handling, XML Functions, Queries, Parameter Formats, Synchronous or Asynchronous Response Types, Your First XML API Calls, FAQ, the API Reference index and the API Sessions, Objects, Attachments, Audit Trails, Bills, Order Entry Transactions and Purchasing Transactions reference pages; page named per section) | version: Sage Intacct XML Web Services, DTD 3.0 (the portal states no release number; "verified" is the fetch date) | verified: 2026-10-13 -->

# Sage Intacct XML Web Services API: the basics

Protocol facts that apply to every call, extracted from the guide pages of the developer portal. Object-specific
facts (fields, required flags, examples, release history) are in `objects/` (generated per API Reference
section); the exact request grammar the gateway validates is in `functions.md` (generated from Sage's 3.0 schema).
Each section names the portal page it was taken from.

## 1. Product, API surfaces and versions

| Fact | Value | Page |
|---|---|---|
| Surface described here | The **XML Web Services API** (the "XML API"): HTTP POST of an XML document to the Web Services gateway | XML Web Services Overview |
| Status | Sage labels the XML API reference **"(Legacy)"**. The portal's home page says: "We continue to release new objects and features using the REST API"; the API Reference index says: "If an object or function is not included in the API documentation, it is likely not supported. We recommend using the REST API for your client applications." | developer.intacct.com home; XML API Reference |
| REST API | A separate surface at https://developer.sage.com/intacct/docs/ (OAuth 2.0, JSON). Sage's schema repository states the REST API is **generally available since 2025 Release 1 (February 2025)** and that the XML DTD/XSD schemas are no longer enhanced. Not reference-backed in this skill yet (`MAINTENANCE.md`). | github.com/Intacct/intacct_dtd README |
| `dtdversion` | **`3.0`** on every request (current; gives both the generic and the object-specific functions). `2.1` is still supported but "will likely not receive new product enhancements". | XML Web Services Overview, Current version |
| Releases | Quarterly: "2026 Release 1" (went live early 2026), "2026 Release 2" (live 8 May 2026), "2026 Release 3" (live 7 August 2026). Reference pages carry per-field **release history** tables (`objects/`, "Release history:"). The portal itself carries no edition stamp. | developer.intacct.com home; per-object History tables |
| Generic vs legacy functions | *Generic* functions (`create`, `read`, `update`, `delete`, `query`, `lookup`, ...) take one or more objects in any element order. *Object-specific* functions (`create_customer`, `update_sotransaction`, ...) have a unique body with ordered sub-elements, one object per call, and are labelled **Legacy**: "will not be enhanced", "no plans to deprecate", and "there are cases in which they are the only functions available". Both kinds may be mixed in one client. Convention: upper-case object elements with generic functions, lower-case with legacy ones. | XML Functions; FAQ "Are legacy functions going away?" |
| Undocumented functions | "likely not yet supported and subject to change" | FAQ |

## 2. Prerequisites and transport

| Fact | Value | Page |
|---|---|---|
| Licence | A Web Services developer licence provides a **sender ID and password** (Web Services credentials). A sender ID can be authorised for more than one company; its use is tracked in an audit history report. | Overview, Requirements |
| Company side | The company administrator must enable the Web Services subscription (Company > Admin > Subscriptions), **authorise the sender ID** for the company (Company Configuration, Security tab, Web Services authorizations list), and create a user, normally a **Web Services user** (no UI access). | Overview, Requirements; FAQ "invalid Web Services authorization" |
| Endpoint | `https://api.intacct.com/ia/xml/xmlgw.phtml` initially; `getAPISession` returns the endpoint to use afterwards (§ 4). | Overview, Endpoint |
| Method | **HTTP POST only**; GET is blocked since 15 January 2023. | Overview, Endpoint |
| Content type | `Content-Type: application/xml`; "Sage Intacct currently does not support receiving JSON through Web Services". | Overview, Content-Type |
| Response mode | Synchronous by default (response in the same HTTP connection); asynchronous via a transport policy (§ 10). | Overview, The XML response |
| TLS | Sage uses CloudFlare; integrations must not pin or hard-code certificate authority files, or they break at certificate rotations. | FAQ, SSL issues |
| Characters | "Sage Intacct does not support special characters in the XML API." `<` and `&` are illegal in XML content; use `&lt;`, `&gt;`, `&amp;`. | Your First XML API Calls; Queries, Illegal characters |
| Tooling | Official SDKs for .NET, Node.js and PHP (Apache 2.0) and a Postman collection (`Intacct_API_Postman_Collection.zip`) wrap the same XML. | Overview; Tools |

## 3. The request envelope

`<request>` holds one `<control>` and one `<operation>` (XML Requests). The exact grammar is in `functions.md`
("Request envelope"); the meanings below are the portal's.

### 3.1 `control`

| Element | Required | Meaning |
|---|---|---|
| `senderid`, `password` | yes | Web Services credentials, both **case sensitive**; the sender ID must be authorised for the target company. |
| `controlid` | yes | Client identifier to match a request to its response. **Not checked for uniqueness**; a timestamp or GUID is suggested. |
| `uniqueid` | no, default `true` | `true`: the request cannot be repeated; the gateway checks each function's `controlid` attribute against completed operations. `false`: functions may run any number of times. Portal guidance: `false` for read-only operations and while testing, `true` for creates and updates. |
| `dtdversion` | yes | `3.0` (§ 1). |
| `includewhitespace` | no, default `true` | `false` drops formatting from the response (smaller, faster to parse). |
| `policyid` | no | Names an existing asynchronous transport policy (§ 10); absent means synchronous. |
| `showadditionalerrorinfo` | no, default `false` | `true` adds an `<additionalinfo>` block to each error: `errorid` (e.g. `GL-0493`), `category`, `target` (object, field, module...), `description`, `cdescription`, `correction` (each with `messageid`, `target`, `placeholders`). Empty elements are returned when nothing is available. |

### 3.2 `operation`

- Attribute `transaction` (optional, default `false`): `true` makes every function in the operation one
  transaction; a failure rolls back the functions already executed and the response says "The entire transaction
  in this operation has been rolled back due to an error." `false`: functions execute independently; one failure
  does not stop the others. (XML Requests; Overview, Transactions.)
- `authentication` (§ 3.3), then `content` with one or more `function` elements (§ 3.4).

### 3.3 `authentication`: login or session

Either a `login` or a `sessionid` (XML Requests, authentication element):

| Scenario | `login` content |
|---|---|
| Standalone company | `userid`, `companyid`, `password` (the UI sign-in values) |
| Multi-entity shared company, entity-level access | add `locationid` = the entity's location ID |
| Console "slide in" to a distributed child company | `userid` and `password` of the **console** user, `companyid` = the console ID, `clientid` = the client company ID, optionally `locationid`; or `companyid` = `consoleId|clientId|entityId` |
| Repeated requests (preferred) | `sessionid` from `getAPISession` (§ 4) |

Login authentication on every request "is not recommended": get a session and reuse it (Overview, Company
credentials). A `login` block carries the user's password, so the Web Services user should be a dedicated account.

### 3.4 `content` and `function`

- Each `<function controlid="...">` carries exactly one function element (`create`, `query`, `create_sotransaction`,
  ...). The `controlid` **attribute** should be unique (GUID or sequence number): the gateway logs it per processed
  function and uses it for recovery and idempotence when `uniqueid` is `true` (§ 5.5). It is distinct from the
  request-level `<controlid>` element, which only matches responses to requests. (XML Requests; Error Handling.)
- A generic function may carry several objects: the portal's example creates a `LOCATION`, a `VENDOR` and a custom
  `COUNTER` object in one `create`. (XML Requests, function element.)
- Several functions in one operation can raise throughput (the portal's example: one operation creating 20 vendors
  can be quicker than 20 operations), but keep `transaction="true"` operations small (§ 10). (Sync vs Async, Best practices.)

## 4. Sessions (`getAPISession`)

From the API Sessions reference page unless stated.

- A session is "a temporary unique identifier tied to a company ID, user ID, possibly an entity (via location ID),
  and an endpoint URL". Send `getAPISession` **alone in its own request**, never mixed with other functions.
- Response: `<api><sessionid>...</sessionid><endpoint>https://<cluster>.intacct.com/ia/xml/xmlgw.phtml</endpoint><locationid/></api>`.
  Use **both** the session ID and the returned endpoint for subsequent requests. `locationid` is empty at the top
  level of a company.
- Entity-level sessions: `<getAPISession><locationid>California</locationid></getAPISession>` (added 2018 Release 4).
  From an entity-level session, an **empty** `locationid` returns a new top-level session, if the user is not
  restricted to entity-level access (2019 Release 2).
- Lifespan: every response's `authentication` element carries `sessiontimestamp` and `sessiontimeout`. The timeout
  is the user's or company's session duration added to the current time, and it is **reset by each call**; the
  session expires when no call arrives before the projected timeout.
- Session IDs can also arrive from Smart Events, triggers and UI events: "Do not blindly trust session IDs that your
  server receives over the internet": call `getAPISession` with the received session to validate it and get the
  endpoint, and check that endpoints are `*.intacct.com`. (Overview, Session authentication.)

## 5. Responses and errors

### 5.1 Shape (XML Responses)

`<response>` mirrors the request: `control` (status of the Web Services authentication) and `operation` with
`authentication` (status of the company access, plus `userid`, `companyid`, `locationid`, `sessiontimestamp`,
`sessiontimeout`) and one `result` per function: `status`, `function`, `controlid` (the function's attribute),
`data` and, on failure, `errormessage`. There are **three status levels**: control, authentication, result.
Individual functions succeed or fail independently unless `transaction="true"`. A `create` returns `<data
listtype="objects" count="n">` with one child per created object; `delete` returns only a status.

### 5.2 Error categories (Error Handling)

| Category | Where it shows | Example `errorno` | Notes |
|---|---|---|---|
| XML validation | `control` status `failure`, `errormessage` at response level; nothing executes | `XL03000003` "XML Parse schema error" | Validate the XML client-side first (the schema is `functions.md`'s source). |
| Gateway | `GW-nnnn` | `GW-0011` "Invalid Request"; `GW-0010` = **HTTP 429 rate limit** | 429: the client exceeded its assigned rate limit (polling loops, concurrent loops, or an inadequate contracted level of service). Portal advice: back off and retry until success, ask Sage for alternatives to polling, or upgrade the level of service. No numeric limit is published. |
| Web Services credentials | `control` status `failure` | `XL03000006` "Incorrect Intacct XML Partner ID or password" | sender ID or password wrong |
| Sender not authorised | `control` success, `authentication` **failure** | `XL03000006` "Invalid Web Services Authorization ... sender ID '...' is not authorized to make Web Services requests to company ID '...'" | administrator must add the sender ID to the company's authorisation list |
| Company credentials | `authentication` failure | `XL03000006` "Sign-in information is incorrect" | |
| Function level | `result` status `failure` | `BL01001973` e.g. "Cannot find vendor with key '12345' to delete", "Duplicate account number" | business-logic and business-rule errors; `description2` carries the text and a Support ID; `correction` may be filled |

Control-level errors execute nothing; authentication-level errors execute no function; content-level errors fail
only that function (others can succeed, unless the operation is a transaction).

### 5.3 Mid-process failures

No XML response at all (for example HTTP 500, or a connection dropped) means the gateway stopped part-way: some
functions may have run. Recovery (Error Handling, Mid-process failures): give every function a unique `controlid`
attribute, then **resubmit the same request with `<uniqueid>true</uniqueid>`**; the gateway compares the function
control IDs against its cache and activity logs and executes each function only once. A timeout on a very long
request (§ 10) looks the same but the processing may still complete.

### 5.4 Reading results

- Query results carry `data` attributes: `listtype`, `totalcount`, `count`, `offset` and `numremaining` (`query`), or
  `count`, `totalcount`, `numremaining` and `resultId` (`readByQuery`). Only the XML return format carries them;
  the FAQ recommends XML "for all API calls" and notes JSON lacks `resultId`.
- `read` returns owned objects nested (an `APBILL` with its `APBILLITEMS/apbillitem` lines).

## 6. Functions

The gateway accepts 52 generic (3.0-style) functions and 243 legacy function names (`functions.md`, generated
from the schema). The portal documents them per object; the ones that apply to every object are:

| Function | Purpose (portal page) |
|---|---|
| `getAPISession` | session ID and endpoint (§ 4) |
| `inspect` | `<object>*</object>` lists every object the company exposes; `<inspect detail="1"><object>APBILL</object></inspect>` lists a standard object's fields with attributes (Objects; Your First XML API Calls) |
| `lookup` | an object's queryable fields (`ID`, `LABEL`, `DESCRIPTION`, `REQUIRED`, `READONLY`, `DATATYPE`, `ISCUSTOM`, `VALIDVALUES` for enumerations) and `Relationships` (`OBJECTPATH`, `OBJECTNAME`, `RELATIONSHIPTYPE` such as `MANY2ONE`, `RELATEDBY`); standard and custom objects; takes `object` or `name`, and `docparid` for a transaction definition. "Information about owned objects is not provided." (Queries; Objects) |
| `read` | one or more records by key: `object`, `keys` (comma-separated `RECORDNO`), optional `fields`, `returnFormat` (`xml` default, `json`, `csv`), `docparid` |
| `readByName` | by name instead of record number (e.g. Units of Measure "Get Unit of Measure by ID") |
| `query` | filtered, sorted, paged list with fields of related objects (§ 7.1) |
| `readByQuery`, `readMore` | legacy string query and its pagination (§ 7.2) |
| `create`, `update`, `delete` | generic writes; `delete` takes `object` and `keys`. Owned objects (transaction lines) are written through their owner: an `update` of a line is an `update` of the header carrying the line (Overview, Manipulating owned objects; FAQ). A statistical journal entry `update` (`GLBATCH`, used for every journal entry type) **replaces all entries**: send every entry to keep (FAQ) |
| document actions | `approve`, `decline`, `getTransactionsToApprove`, `getApprovalHistory` (Purchasing transactions, when approvals are enabled), `retrievepdf` (base64 PDF of a transaction), `post`, `unpost`, `hold`, `resume`, `cancel`, `deliver`, `renew`... as documented per object |
| `getDimensions`, `getDimensionRelationships`, `getDimensionRestrictions`, `getDimensionAutofillDetails`, `getDimensionRestrictedData` | standard and user-defined dimensions and their relationships (Platform Services, Dimensions) |
| `getAuditTrail` | audit trail of a record; needs **View** permission on custom reports (Platform Services subscription) (Audit Trails) |
| `readReport`, `readView` | custom reports and views (Customization Services, Custom Reports) |
| `runDdsJob`, `getDdsObjects`, `getDdsDdl` | Data Delivery Service exports (Data Delivery Service) |

Line numbering differs between the two function families (XML Functions, Working with transaction lines):
`read` on `SODOCUMENT` returns entries with a **zero-based** `LINE_NO`, while `update_sotransaction` (and
`update_potransaction`, `update_ictransaction`) address lines with a **one-based** `line_num`: add one. Other
transactions' `read` responses are one-based. The portal's own warning: test before any large-scale update.

## 7. Queries and paging

### 7.1 `query` (current)

Source: Queries page. Grammar: `functions.md` (`query`, type `filteroption`).

- Elements: `object` (standard or custom), `select` (one or more `field`; aggregates `count`, `avg`, `min`, `max`,
  `sum`, in which case the selected fields group the results; "Returning all fields is not supported"), `filter`
  (optional), `orderby` (`order` with `field` and `ascending` or `descending`; **no default order**), `options`,
  `pagesize`, `offset`, `docparid`.
- Comparison operators: `equalto`, `notequalto`, `lessthan`, `lessthanorequalto`, `greaterthan`,
  `greaterthanorequalto`, `isnull`, `isnotnull`. Logical: `between` (two `value`s), `in` and `notin` (1 to 1000
  values per the schema), `like` and `notlike` (`%` any run, `_` one character). Conditions: `and`, `or`, nestable.
- **Fields of related objects**: `RELATED.FIELD` with the `OBJECTPATH` from `lookup` (many-to-one only), in
  `select` and `filter`; several dots are allowed (`PAYTOCONTACT.MAILADDRESS.ZIP`); hierarchical self-relations one
  level only (`CUSTOMER.PARENT.NAME` works, `CUSTOMER.PARENT.PARENT.NAME` errors). Custom relationships: between two
  custom objects, or a custom and a standard object; **not** between two standard objects.
- `options`: `returnformat` `xml` (default), `csv`, `json` (CSV and JSON return only the data, no envelope);
  `caseinsensitive` `true` (queries are case sensitive by default); `showprivate` `true` to include private entities
  when querying from the top level of a multi-entity company.
- Paging: `pagesize` default **100**, maximum **2000**; `offset` to page beyond it. **Each offset call is a new
  query**, not a cursor: records inserted between calls can shift the result set and be missed.
- `docparid`: the transaction definition name (`Sales Order`, `Purchase Order`...) for `SODOCUMENT`, `PODOCUMENT`
  and `INVDOCUMENT`; required to see the definition's custom fields.
- Custom fields are not indexed: filter on standard fields first and use custom fields as supplemental filters.
- Tip: with aggregates, do not also select `RECORDNO`, or every record becomes its own group with a count of 1.
- Response: `<data listtype="APBILL" totalcount="2" offset="0" count="2" numremaining="0">`.

### 7.2 `readByQuery` and `readMore` (legacy)

- `object`, `fields` (comma-separated; omit or `*` for all, but the portal recommends naming fields: `RECORD_URL` is
  only returned when named, and `*` "can lead to inconsistent results", e.g. `ITEM` rows of different component
  types return different fields), `query` (string; empty returns everything up to `pagesize`), `pagesize` **1 to
  1000, default 100**, optional `returnFormat`, `docparid`.
- Query string: `<`, `>`, `>=`, `<=`, `=`, `like`, `not like`, `in`, `not in`, `IS NULL`, `IS NOT NULL`, `AND`, `OR`,
  `NOT (...)`; string operands are **case sensitive**; escape `'` as `\'`; encode `<` `>` `&` as entities; "Joins are
  not supported" and "You cannot query on a field that is a join by foreign key" (a field shown with a dot, such as
  `PERSONALINFO.FIRSTNAME`: use `query` for those, FAQ). `rownum = 1`, `rownum < 5` limit rows. Dates are
  compared as `MM/DD/YYYY` strings (`ACCESSTIME='03/31/2018 16:24:51'` for audit timestamps).
- Relationships: "you cannot perform queries involving many-to-many or one-to-many relationships" nor return
  several owned objects: `readByQuery` for the keys, then `read` for the owned and related objects. Many-to-one works
  from the *many* side. (FAQ.)
- Paging: `readMore` with `<object>` or, better, `<resultId>` from the `readByQuery` response (keeps the same result
  set); the last page has `numremaining="0"`.
- A newly added boolean field is NULL on existing records: `read` shows `false`, but `readByQuery` must test NULL.
  Validated lists store single characters (`usertype = 'B'`, `STATE='A'`): use the database value, listed in the
  object page's `query` fields table (`objects/`).

## 8. Parameter formats

| Topic | Rule | Page |
|---|---|---|
| Dates, generic functions | strings `mm/dd/yyyy` (`<WHENCREATED>12/22/2018</WHENCREATED>`) | Parameter Formats |
| Dates, legacy functions | objects: `<datecreated><year>2018</year><month>06</month><day>30</day></datecreated>` | Parameter Formats |
| Timestamps (audit) | `MM/DD/YYYY HH:MM:SS` | Parameter Formats |
| Time zones | "Dates in Sage Intacct do not have associated timezones"; the integrator converts. **ISO 8601 is not supported.** | FAQ, dates |
| Decimals | no thousands separators (`1000.00`, never `1,000.00`) | Parameter Formats |
| Currency amounts | more than 2 decimals are rounded to 2; round client-side first | Bills page note |
| Custom fields | generic functions: the field's integration name as an element; legacy functions: `customfields/customfield` with `customfieldname` and `customfieldvalue`; multi-pick-list values joined with `#~#`. Name/value integration codes for picklists work only on custom objects, not on custom picklists of standard objects. | Bills; Inventory Transactions; FAQ |
| Attachments | the field is `SUPDOCID` (the UI says "Attachments"); attachment and folder management is legacy-only (`create_supdoc`...) | FAQ; Attachments page |
| Keys | standard objects are addressed by `RECORDNO` in `read`/`delete`/generic `update`; legacy transaction functions take the document ID (`key="Sales Order-SO1234"`), or the record number for drafts | Your First XML API Calls; Order Entry Transactions |

## 9. Multi-entity shared companies

- Sign in at the **top level** (no `locationid`) or at an **entity** (`locationid` in `login` or in `getAPISession`,
  § 3.3, § 4). To update a record "at the entity level", add the location ID to the login (FAQ).
- When multi-entity is enabled, transaction lines need a `LOCATIONID` / `locationid` ("Required if company is
  multi-entity enabled" on OE, Purchasing and AP line tables; `objects/`).
- Top-level queries skip private entities unless `showprivate` is `true` (§ 7.1).
- Some objects exist only at the top level (Order Entry and Purchasing subtotal templates: "You can only use these
  functions at the top level of a multi entity company"). A Smart Rule can forbid creating a record at the top
  level (FAQ, Customization Services).
- Console (distributed) companies use the slide-in login (§ 3.3).

## 10. Limits, throughput, timeouts and asynchronous processing

| Topic | Portal statement | Page |
|---|---|---|
| Concurrency | Concurrent connections are limited **per tenant (company ID)**. Example given: of 100 concurrent requests 5 are processed and 95 held about 5 seconds or until earlier ones complete, then served first-in first-out. "For more throughput, use quick requests." | Overview, Concurrent requests |
| Rate limit | `GW-0010` / HTTP 429 when the client exceeds its assigned rate limit; back off and retry (§ 5.2). No figure published. | Error Handling |
| Timeout | A large request can time out the sender after **15 minutes** while Sage is still processing it. | Overview, Timeouts; Sync vs Async |
| Request sizing | Keep queries under **1000 records** and paginate (also `get_list`); keep writes under **100 affected records** per request; log elapsed time and alert above **5 minutes**; set `uniqueid` `true` for idempotence. | Overview, Timeouts |
| Offline jobs | Standard level of service: one API transaction job (online or offline: asynchronous requests, triggers, Smart Events, CSV imports) and one offline report job per company at a time; a third concurrent request is held 30 seconds, then "There are too many operations running for this company". Queue administration (API or UI) lists queued jobs; a premium level of service can prioritise and cancel them. | FAQ, throughput |
| Asynchronous requests | Need a **transport policy** set up through a support case: policy ID, HTTPS response URL, optional basic-auth user and password, `Serialize`. Send `policyid` in `control`; the gateway answers at once with `<acknowledgement><status>success</status></acknowledgement>` and later POSTs the full response to the URL. Maximum asynchronous request size **500K characters**. FIFO is not guaranteed unless the company's requests are serialised. | Sync vs Async |
| Transactions | Avoid large multi-function operations with `transaction="true"`: rollback is expensive. | Sync vs Async, Best practices |
| Polling | Named by Sage as a cause of 429s; ask Sage about change notifications (Smart Events and triggers can call out, § 11). | Error Handling |

## 11. Beyond the XML API (pointers only)

- **Platform Services** extends Sage Intacct from inside: custom objects, fields, pages, applications, and
  *triggers* (HTTP triggers can GET or POST to an external application, and triggers can call the API from inside).
  Custom objects are queried with the same generic functions; `inspect` and `lookup` describe them
  (Overview, Web Services versus Platform Services; Objects page).
- **Customization Services**: Smart Events (including API Smart Events that run XML functions on an event, with
  `{!OBJECT.FIELD!}` injections; detail-line events use the zero-based `LINE_NO`) and Smart Rules (validation,
  e.g. prevent creating at the top level). Examples and walkthroughs are on the portal; nothing of them is
  bundled here beyond the API reference pages in `objects/customization-services.md`.
- **Data Delivery Service** (`runDdsJob`): bulk export of objects to cloud storage; `objects/data-delivery-service.md`.
- **Dimensions**: standard dimensions (location, department, class, project, customer, vendor, employee, item,
  warehouse...) and user-defined dimensions; `objects/platform-services.md`.
