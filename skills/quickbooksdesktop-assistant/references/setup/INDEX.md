# references/setup — index

How a program reaches a QuickBooks Desktop company file, and why connections fail.

| File | Covers | Source | Verified |
|---|---|---|---|
| `connectivity.md` | Choosing QBFC vs QBXMLRP2 vs the Web Connector (QBWC) by where the code runs; connection/session sequence; open modes (`omDontCare`/`omSingleUser`/`omMultiUser`); first-connection authorization & code-signing certificate; unattended (auto-login) and hosted (QBWC `.QWC` + SOAP callbacks) topologies; 32-bit/STA/local-install constraints; HRESULT & qbXML status error signatures with fixes | **Draft**: from author knowledge of the SDK and Web Connector programmer's guides; not yet checked (header says what to confirm) | not yet |

HRESULTs listed are the long-standing ones; confirm an unfamiliar code against developer.intuit.com.
