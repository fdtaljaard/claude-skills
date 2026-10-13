<!-- source: DRAFT, written from author knowledge of the QuickBooks Desktop SDK programmer's guide (connection, session, authorization) and Web Connector programmer's guide, developer.intuit.com; not yet checked against them. To confirm: open modes, the QBWC callback sequence and every HRESULT against those guides | version: SDK 16.0 / Web Connector 2.x | verified: not yet (draft written 2026-10-06) -->
# Setup & connectivity

How a program actually reaches a QuickBooks Desktop company file, and why connections fail. Pin the
*shape* of the integration first — it decides which access layer and open mode you use.

> Verified against the stable QB SDK (QBFC/QBXMLRP2) and Web Connector model. HRESULT values are the
> long-standing ones; confirm an unfamiliar code against developer.intuit.com.

## Contents
- [Pick the access layer](#layer)
- [Connection & session sequence](#sequence)
- [Open modes](#modes)
- [Authorization & certificate](#auth)
- [Unattended / hosted](#unattended)
- [Hard constraints](#constraints)
- [Error signatures](#errors)

<a name="layer"></a>
## Pick the access layer — by *where the code runs*

| Your code runs… | Use | Notes |
|---|---|---|
| On the **same machine** as QuickBooks, typed in C#/.NET | **QBFC** (`Interop.QBFC<ver>`) | Typed COM wrapper over qbXML. Default for .NET — compile-time field names. |
| On the **same machine**, you want to send raw qbXML strings | **QBXMLRP2** (`QBXMLRP2Lib.RequestProcessor2`) | The raw Request Processor. You build/parse qbXML yourself. QBFC sits on top of this. |
| On a **different machine**, or **unattended / hosted**, pushing to a client's QuickBooks | **Web Connector (QBWC)** | You host a SOAP web service; the Web Connector (installed next to QB) polls it and relays qbXML. |

QBFC and QBXMLRP2 are two ways to drive a **local** QuickBooks. The Web Connector is a fundamentally
different topology for **remote/unattended** delivery.

<a name="sequence"></a>
## Connection & session sequence (local: QBFC / QBXMLRP2)

```
OpenConnection(appID, appName)            // appID usually "", appName shows in QB's integrated-app list
  BeginSession(companyFile, openMode)     // companyFile "" = file currently open in QB
    DoRequests(msgSetRequest)             // one message set at a time; repeat as needed
  EndSession()
CloseConnection()
```

- `OpenConnection2(appID, appName, connectionType)` lets you state the connection type
  (`ctLocalQBD`, `ctLocalQBDLaunchUI`, `ctRemoteQBD` / `ctRemoteQBOE` on the raw processor). For a normal
  local service `OpenConnection` is enough.
- **End/close in `finally`.** A leaked session locks the file and holds a seat.

<a name="modes"></a>
## Open modes (`ENOpenMode`)

- **`omDontCare`** — connect to whatever mode QuickBooks is already in. Most tolerant; the usual choice
  when a human may have QB open.
- **`omSingleUser`** — require single-user. Some operations (and some older files) need it; it blocks other
  users while you hold it.
- **`omMultiUser`** — require multi-user, so people keep working while your service posts.

Mismatch between the mode you ask for and how the file is open is a common failure (HRESULT `0x80040416`).
For unattended posting against a shared file, multi-user is usually right; confirm the operation supports it.

<a name="auth"></a>
## Authorization & certificate (one-time, admin, per company file)

The **first** time your app connects to a given company file, QuickBooks shows the **Application
Certificate** dialog to a logged-in **admin** user, asking whether to allow access. The admin chooses:
- allow / deny, and the access level;
- **"allow access even when QuickBooks is not running"** — required for unattended use;
- the **auto-login user** whose permissions the app runs as when QB isn't open.

Key points that trip people up:
- This is granted in **QuickBooks**, by an **admin**, on **that machine**, for **that company file**. Your
  integration cannot authorize itself, and the grant doesn't travel to another file or machine.
- An **unsigned** app triggers a security warning each time / looks untrusted. Ship with an Authenticode
  **code-signing certificate** so the certificate dialog shows your verified publisher and the grant
  sticks cleanly.
- Authorization is managed afterward under **Edit → Preferences → Integrated Applications → Company
  Preferences** — that's where a client revokes or re-grants access.

<a name="unattended"></a>
## Unattended / hosted

- **Local unattended service**: authorize with "allow when QB not running" + an auto-login user, pass the
  explicit `.QBW` path to `BeginSession`, and run the host as a 32-bit process on the QB machine. If QB
  isn't running, the SDK launches it headless under the auto-login user.
- **Remote / SaaS → client site**: use the **Web Connector**. You provide:
  - a SOAP web service implementing the QBWC callbacks — `serverVersion`, `clientVersion`,
    `authenticate`, `sendRequestXML`, `receiveResponseXML`, `getLastError`, `closeConnection`
    (names per the QBWC spec);
  - a **`.QWC`** config file the client imports into their Web Connector (your service URL, app name,
    owner/ file IDs, scheduling);
  The Web Connector, installed beside QuickBooks, periodically calls `authenticate` then pulls qbXML from
  `sendRequestXML`, applies it locally, and returns results to `receiveResponseXML`. Your service never
  touches the file directly — it just supplies/consumes qbXML. Good for pushing to many client sites you
  don't control.

<a name="constraints"></a>
## Hard constraints (design around these up front)

- **32-bit, Windows-only COM.** Build the host **x86**; QuickBooks or the SDK runtime must be installed on
  the machine. Not .NET Core/Linux, not a clean container.
- **Single-threaded / STA.** Don't share a session across threads or overlap `DoRequests`.
- **Local presence.** QBFC/QBXMLRP2 require QuickBooks on the same box. If your code can't live there, that
  forces the Web Connector topology — decide this before anything else.
- **One authorized app per company file identity.** Changing your app's name/identity re-triggers the
  certificate prompt.

<a name="errors"></a>
## Error signatures (HRESULT / status) — cause → fix

| Signature | Usual meaning | Fix |
|---|---|---|
| `0x80040408` "Could not start QuickBooks" | QB can't be launched / no auto-login for unattended, or wrong bitness | Authorize "allow when not running" + auto-login user; run host x86; QB installed. |
| `0x80040416` | Company file open in a mode incompatible with the one requested | Use `omDontCare`, or match single/multi-user to the operation. |
| `0x80040410` / authorization denied | App not authorized, or admin denied / revoked it | Have an admin re-grant under Integrated Applications; check access level. |
| `0x80040400`-range | General request-processor errors (bad qbXML, version) | Validate qbXML; check message-set version vs `HostQueryRq`. |
| qbXML **StatusCode 3200** | `EditSequence` out of date (object changed) | Re-query for a fresh `EditSequence`, retry the Mod. |
| qbXML **StatusCode ≥ 3000** | Request-specific data error | Read `StatusMessage`; fix the field it names. |
| "version not supported" on `DoRequests` | Message-set version > what the file supports | Drop to a supported version (`SupportedQBXMLVersion`). |

When diagnosing: separate **COM/HRESULT** failures (couldn't reach/launch QuickBooks — environment, auth,
bitness) from **qbXML StatusCode** failures (QuickBooks ran but rejected the data). They have different fixes.
