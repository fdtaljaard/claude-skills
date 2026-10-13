#!/usr/bin/env python3
"""Build references/xml-api/functions.md from the Sage Intacct 3.0 request schema (maintenance only).

    python -I scripts/build_functions_reference.py --xsd ../../sources/sageintacct-assistant/api.v3.0.xsd \
        --out references/xml-api/functions.md --verified YYYY-MM-DD [--xsd-note "commit 89275604db, 2024-05-07"]

The input is `v3.0/api.xsd` from Sage's public schema repository (https://github.com/Intacct/intacct_dtd, Apache
2.0), the schema the Web Services gateway validates DTD 3.0 requests against. The script walks the schema and
writes, for the request envelope and for every generic (3.0-style) function, a table of the elements the schema
accepts: name, occurrence, type or allowed values and defaults, nested local elements indented, choices marked.
Global elements and named types that several functions share (the `filter` grammar, `fields`, `entities`, ...) are
expanded once in a "Shared structures" section and linked from the tables. It also lists the legacy (2.1-style,
`verb_object`) function names the schema still accepts, so a reviewer can tell a documented legacy function from an
invented one. Nothing here describes responses: the schema covers requests only.
"""
import argparse
import re
import xml.etree.ElementTree as ET

NS = {"xs": "http://www.w3.org/2001/XMLSchema"}
XS = "{http://www.w3.org/2001/XMLSchema}"

ENVELOPE = ["request", "control", "operation", "authentication", "login", "content", "function"]

# Generic functions in the order they are presented: sessions and metadata, reads and queries, writes, document
# actions, dimensions and company, audit and approvals, reports and views, DDS, consolidation, platform.
GENERIC = [
    "getAPISession", "inspect", "lookup",
    "read", "readByName", "readRelated", "readByQuery", "query", "readMore",
    "create", "update", "delete", "validate",
    "post", "unpost", "approve", "decline", "hold", "resume", "cancel", "uncancel", "deliver", "promote", "renew",
    "reallocate", "clearallmea", "clearlastactivemea", "retrievepdf",
    "getDimensions", "getDimensionRelationships", "getDimensionRestrictions", "getDimensionAutofillDetails",
    "getDimensionAutofillData", "getDimensionRestrictedData", "getUserPermissions", "getFinancialSetup",
    "readEntityDetails", "readUserFormatting", "getAuditTrail", "getTransactionsToApprove", "getApprovalHistory",
    "approveVendor", "declineVendor", "getVendorsToApprove", "getVendorApprovalHistory",
    "readReport", "readView", "runDdsJob", "getDdsObjects", "getDdsDdl",
    "consolidate", "consolidatebytier", "installApp",
]
LEGACY_RE = re.compile(r"^[a-z]+_[a-z_]+$|^(get|describe|describeall|get_list|init_session)$")


def occurs(node):
    mn, mx = node.get("minOccurs", "1"), node.get("maxOccurs", "1")
    if mx == "unbounded":
        mx = "n"
    if (mn, mx) == ("1", "1"):
        return "required"
    if (mn, mx) == ("0", "1"):
        return "optional"
    return f"{mn}..{mx}"


def anchor(kind, name):
    return f"{kind}-{name.lower()}"


class Schema:
    def __init__(self, root):
        self.elements = {e.get("name"): e for e in root.findall("xs:element", NS)}
        self.types = {t.get("name"): t for t in root.findall("xs:complexType", NS)}
        self.simple = {t.get("name"): t for t in root.findall("xs:simpleType", NS)}
        self.groups = {g.get("name"): g for g in root.findall("xs:group", NS)}
        self.attr_groups = {g.get("name"): g for g in root.findall("xs:attributeGroup", NS)}
        self.shared = []  # ("element"|"type", name) in order of first reference
        self.own = set(ENVELOPE) | set(GENERIC)
        self.collect = True  # False while rendering the last level of shared structures

    @staticmethod
    def restriction(node):
        r = node.find("xs:restriction", NS) if node is not None else None
        if r is None:
            return ""
        parts = []
        base = (r.get("base") or "").replace("xs:", "")
        enums = [e.get("value") for e in r.findall("xs:enumeration", NS)]
        if enums:
            shown = ", ".join("`" + v + "`" for v in enums[:40])
            parts.append("one of " + shown + (f" (and {len(enums) - 40} more)" if len(enums) > 40 else ""))
        elif base:
            parts.append(base)
        for tag, label in (("minInclusive", "min"), ("maxInclusive", "max"), ("minLength", "min length"),
                           ("maxLength", "max length"), ("pattern", "pattern")):
            x = r.find(f"xs:{tag}", NS)
            if x is not None:
                parts.append(f"{label} {x.get('value')}")
        return ", ".join(parts)

    def content_of(self, el):
        """(type text, complexType node or None) for an element definition."""
        t = el.get("type")
        if t:
            if t.startswith("xs:"):
                return t[3:], None
            if t in self.simple:
                return self.restriction(self.simple[t]) or t, None
            if t in self.types:
                return "", self.types[t]
            return t, None
        st = el.find("xs:simpleType", NS)
        if st is not None:
            return self.restriction(st) or "string", None
        ct = el.find("xs:complexType", NS)
        if ct is not None:
            if len([c for c in ct if c.tag != XS + "attribute"]) == 0:
                return ("text" if ct.get("mixed") == "true" else "(empty element)"), ct
            return "", ct
        return "text", None

    def note_shared(self, kind, name):
        if self.collect and (kind, name) not in self.shared and name not in self.own:
            self.shared.append((kind, name))

    def walk(self, container, rows, depth, owner):
        """Append (depth, label, occurs, type, note) rows for the particles under `container`."""
        for child in container:
            tag = child.tag.replace(XS, "")
            if tag in ("sequence", "all"):
                self.walk(child, rows, depth, owner)
            elif tag == "choice":
                mn, mx = child.get("minOccurs", "1"), child.get("maxOccurs", "1")
                note = "one of the following" + ("" if (mn, mx) == ("1", "1") else f", {mn}..{'n' if mx == 'unbounded' else mx} times")
                rows.append((depth, "(choice)", "", "", note))
                self.walk(child, rows, depth + 1, owner)
            elif tag == "group":
                g = self.groups.get(child.get("ref"))
                if g is not None:
                    self.walk(g, rows, depth, owner)
            elif tag == "any":
                rows.append((depth, "(any elements)", occurs(child), "",
                             "the object's own XML, not validated by the schema; see the object's parameter tables in `objects/`"))
            elif tag == "attribute":
                st = child.find("xs:simpleType", NS)
                t = (child.get("type") or "").replace("xs:", "") or self.restriction(st) or "string"
                rows.append((depth, "@" + child.get("name", child.get("ref", "?")),
                             "required" if child.get("use") == "required" else "optional", t,
                             "attribute" + (f", default `{child.get('default')}`" if child.get("default") else "")))
            elif tag == "attributeGroup":
                g = self.attr_groups.get(child.get("ref"))
                if g is not None:
                    self.walk(g, rows, depth, owner)
            elif tag == "element":
                ref = child.get("ref")
                if ref:
                    el = self.elements.get(ref)
                    if el is None:
                        rows.append((depth, ref, occurs(child), "", "(not defined in the schema)"))
                        continue
                    ttext, ct = self.content_of(el)
                    note = f"default `{el.get('default')}`" if el.get("default") else ""
                    if ct is not None and len(ct):
                        if ref in self.own:
                            note = f"see [`{ref}`](#{anchor('fn' if ref in GENERIC else 'env', ref)})"
                        elif self.collect or ("element", ref) in self.shared:
                            self.note_shared("element", ref)
                            note = f"structure: see [`{ref}`](#{anchor('shared', ref)})"
                        else:
                            note = "nested structure not expanded here: see the schema"
                    rows.append((depth, ref, occurs(child), ttext, note))
                    continue
                name = child.get("name")
                ttext, ct = self.content_of(child)
                note = f"default `{child.get('default')}`" if child.get("default") else ""
                t = child.get("type") or ""
                if t in self.types:
                    if self.collect or ("type", t) in self.shared:
                        self.note_shared("type", t)
                        note = f"structure: see [type `{t}`](#{anchor('shared', t)})"
                    else:
                        note = f"type `{t}`, not expanded here: see the schema"
                    rows.append((depth, name, occurs(child), "", note))
                    continue
                rows.append((depth, name, occurs(child), ttext, note))
                if ct is not None and len(ct) and depth < 8:
                    self.walk(ct, rows, depth + 1, owner)

    def table_for(self, kind, name):
        if kind == "element" and name == "function":
            n_fn = len([e for e in self.elements["function"].iter(XS + "element") if e.get("ref")])
            return ["| Element | Occurs | Type / allowed values | Notes |", "|---|---|---|---|",
                    "| @controlid | required | string | attribute: unique per function for recovery and idempotence |",
                    f"| (choice) | required |  | exactly one function element: one of the {n_fn} names the schema lists, "
                    "i.e. a generic function below or a legacy function from the last section |", ""]
        if kind == "type":
            ct, el = self.types[name], None
        else:
            el = self.elements[name]
            _, ct = self.content_of(el)
        rows = []
        if ct is not None:
            self.walk(ct, rows, 0, name)
        out = []
        order = {"all": "Child elements may appear in **any order** (`xs:all`).",
                 "sequence": "Child elements must appear **in this order** (`xs:sequence`).",
                 "choice": "Exactly one of the child elements (`xs:choice`)."}
        top = next((c.tag.replace(XS, "") for c in ct if c.tag.replace(XS, "") in order), None) if ct is not None else None
        if top and rows:
            out.append(order[top])
            out.append("")
        if not rows:
            t = self.content_of(el)[0] if el is not None else ""
            out.append(f"No child elements: `<{name}/>`" + (f" ({t})" if t and t not in ("", "(empty element)") else "") + ".")
            out.append("")
            return out
        out.append("| Element | Occurs | Type / allowed values | Notes |")
        out.append("|---|---|---|---|")
        for depth, n, occ, t, note in rows:
            shown = ("· " * depth) + (n if n.startswith(("(", "@")) else f"`{n}`")
            out.append(f"| {shown} | {occ} | {t} | {note} |")
        out.append("")
        return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xsd", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--verified", required=True)
    ap.add_argument("--xsd-note", default="", help="schema commit or date to record in the provenance header")
    args = ap.parse_args()

    root = ET.parse(args.xsd).getroot()
    schema = Schema(root)

    fn = schema.elements["function"]
    allowed = [e.get("ref") for e in fn.iter(XS + "element") if e.get("ref")]
    legacy = sorted(n for n in allowed if LEGACY_RE.match(n))
    generic_in_schema = [n for n in allowed if not LEGACY_RE.match(n)]
    documented = [n for n in GENERIC if n in allowed]
    missing = [n for n in GENERIC if n not in allowed]
    extra = [n for n in generic_in_schema if n not in GENERIC]

    prov = (f"<!-- source: https://github.com/Intacct/intacct_dtd (v3.0/api.xsd, Apache 2.0{', ' + args.xsd_note if args.xsd_note else ''}), "
            f"generated by scripts/build_functions_reference.py | version: Sage Intacct XML Web Services request schema, DTD 3.0 | "
            f"verified: {args.verified} -->")
    body = []
    body.append("## Request envelope")
    body.append("")
    for n in ENVELOPE:
        body.append(f'<a id="{anchor("env", n)}"></a>')
        body.append(f"### `{n}`")
        body.append("")
        body.extend(schema.table_for("element", n))
    body.append("## Generic functions")
    body.append("")
    for n in documented:
        body.append(f'<a id="{anchor("fn", n)}"></a>')
        body.append(f"### `{n}`")
        body.append("")
        body.extend(schema.table_for("element", n))
    body.append("## Shared structures")
    body.append("")
    body.append("Global elements and named types referenced from more than one place above, each expanded once.")
    body.append("")
    level1 = list(schema.shared)
    tables = {}
    for kind, n in level1:  # expanding these may reference a second level, which is rendered without further collection
        tables[(kind, n)] = schema.table_for(kind, n)
    schema.collect = False
    for kind, n in schema.shared[len(level1):]:
        tables[(kind, n)] = schema.table_for(kind, n)
    for kind, n in schema.shared:
        body.append(f'<a id="{anchor("shared", n)}"></a>')
        body.append(f"### {'type ' if kind == 'type' else ''}`{n}`")
        body.append("")
        body.extend(tables[(kind, n)])

    head = [prov, "", "# Sage Intacct XML API: request envelope and generic functions (from the 3.0 schema)", "",
            "What the gateway's request schema accepts, element by element: the request envelope, then every generic "
            "function, then the structures they share. `Occurs` is the schema's minOccurs/maxOccurs (`required` = exactly "
            "one, `optional` = at most one, `0..n` = any number). Nested elements are indented with `·`; `(choice)` means "
            "exactly one of the indented alternatives; `(any elements)` means the schema does not validate the content "
            "(the object's own fields, documented per object in `objects/`). Each table says whether the schema fixes the "
            "element order (`xs:sequence`, as in every legacy function) or allows any order (`xs:all`, as in `query`, `read` and "
            "`readByQuery`). The schema says nothing about responses, "
            "meanings or limits beyond the ranges shown: those come from the developer portal (`api-basics.md`, `objects/`). "
            "Where the schema is more permissive than the portal (it marks `password` and `dtdversion` optional in `control`), "
            "the portal's rule applies.", "",
            "| Name | Kind |", "|---|---|"]
    for n in ENVELOPE:
        head.append(f"| [`{n}`](#{anchor('env', n)}) | envelope |")
    for n in documented:
        head.append(f"| [`{n}`](#{anchor('fn', n)}) | function |")
    for kind, n in schema.shared:
        head.append(f"| [`{n}`](#{anchor('shared', n)}) | shared {kind} |")
    head.append("")

    tail = ["## Legacy (2.1-style) functions the 3.0 schema still accepts", "",
            f"{len(legacy)} object-specific function names appear in the schema's `function` choice. The developer portal "
            "documents them per object as \"(Legacy)\" operations (`objects.md`, Legacy column): supported, not enhanced. "
            "A `verb_object` name that is not in this list is not a function.", "",
            ", ".join(f"`{n}`" for n in legacy), ""]
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(head + body + tail).rstrip("\n") + "\n")
    print(f"functions in schema: {len(allowed)} ({len(generic_in_schema)} generic, {len(legacy)} legacy); "
          f"documented here: {len(documented)}; shared structures: {len(schema.shared)}")
    if missing:
        print("not in schema (dropped): " + ", ".join(missing))
    if extra:
        print("generic in schema but not in the GENERIC list (add them): " + ", ".join(extra))


if __name__ == "__main__":
    main()
