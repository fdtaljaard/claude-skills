#!/usr/bin/env python3
"""Dump the object definitions of a Sage Intacct company through the XML API, scrubbed (maintenance only).

    python scripts/dump_object_definitions.py --out <folder outside the repo> --release "2026 Release 3" [--objects APBILL,VENDOR]
                                              [--batch 10] [--delay 0.5] [--dry-run]
    python scripts/dump_object_definitions.py --pack <dump folder> --zip sources/sageintacct-assistant/object-definitions-<release>.zip
                                              [--allow-missing-identifiers]

Run this yourself against a **clean developer or implementation company**; never against a customer's. Credentials
are read from environment variables only, are never printed, and never reach the output:

    INTACCT_SENDER_ID, INTACCT_SENDER_PASSWORD      Web Services sender credentials
    INTACCT_COMPANY_ID, INTACCT_USER_ID, INTACCT_USER_PASSWORD   company login
    INTACCT_LOCATION_ID   optional: entity to sign in to (multi-entity shared companies)
    INTACCT_ENDPOINT      optional: gateway URL, default https://api.intacct.com/ia/xml/xmlgw.phtml

What it does (stdlib only, Python 3.10+):
  1. `getAPISession` with the login credentials; later calls use the returned session ID and endpoint.
  2. `inspect` with `<object>*</object>`: the list of objects the company exposes.
  3. `lookup` per object (`--batch` functions per request): fields (ID, label, description, required, read-only,
     data type, custom flag, valid values) and relationships, exactly as the API reports them.

What it writes to --out (and nothing else):
  inspect.xml            the `<data>` of the inspect result, custom objects removed
  lookup/<OBJECT>.xml    the `<data>` of each lookup result, custom fields (ISCUSTOM true) and relationships to
                         non-standard objects removed
  dropped.txt            objects, fields and relationships that were removed, for your review
  manifest.json          release, date, counts, failures (error number and description per object), gateway host
The `<control>` block of each response (sender ID), the session ID, the endpoint URL, the company ID and the user ID
are never written; the script refuses to write any file in which one of those values appears. Objects whose name
is not upper-case letters, digits and underscores are treated as custom (Platform Services) objects and dropped;
a standard object wrongly dropped by that rule is added back with `--objects NAME` into the same --out, which
merges into the existing dump (the object is restored in inspect.xml and the manifest is updated, not replaced).
Review `dropped.txt` and the output before sharing it. `--pack` then writes the zip that is committed under
`sources/sageintacct-assistant/`: `inspect.xml` with the document objects collapsed (`inspect` lists `SODOCUMENT`,
`PODOCUMENT`, `INVDOCUMENT`, their lines and recurring variants once per transaction definition, the generic entry
first and then one per definition labelled with the definition's name, which is company configuration; only the
first entry is kept), `lookup/*.xml` (re-scrubbed) and `manifest.json` with counts only; never `dropped.txt`. The pack
refuses a payload containing a response envelope or credential element, or the sender, company or user ID the dump
was made with, which must therefore be in the environment (or pass --allow-missing-identifiers knowingly).
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
import xml.etree.ElementTree as ET
import zipfile
from xml.sax.saxutils import escape

DEFAULT_ENDPOINT = "https://api.intacct.com/ia/xml/xmlgw.phtml"
STANDARD_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
FORBIDDEN = ("<control>", "<senderid>", "<password>", "<sessionid>", "<companyid>", "<userid>", "xmlgw.phtml")
IDENTIFIER_VARS = ("INTACCT_SENDER_ID", "INTACCT_COMPANY_ID", "INTACCT_USER_ID")


def env(name, required=True):
    v = os.environ.get(name, "")
    if required and not v:
        sys.exit(f"environment variable {name} is not set")
    return v


def request_xml(sender_id, sender_password, auth_xml, functions_xml, control_id):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<request>\n"
        "  <control>\n"
        f"    <senderid>{escape(sender_id)}</senderid>\n"
        f"    <password>{escape(sender_password)}</password>\n"
        f"    <controlid>{control_id}</controlid>\n"
        "    <uniqueid>false</uniqueid>\n"
        "    <dtdversion>3.0</dtdversion>\n"
        "    <includewhitespace>false</includewhitespace>\n"
        "  </control>\n"
        '  <operation transaction="false">\n'
        f"    <authentication>{auth_xml}</authentication>\n"
        f"    <content>\n{functions_xml}    </content>\n"
        "  </operation>\n"
        "</request>\n"
    )


def login_xml(company_id, user_id, password, location_id):
    loc = f"<locationid>{escape(location_id)}</locationid>" if location_id else ""
    return (f"<login><userid>{escape(user_id)}</userid><companyid>{escape(company_id)}</companyid>"
            f"<password>{escape(password)}</password>{loc}</login>")


def post(endpoint, body):
    req = urllib.request.Request(endpoint, data=body.encode("utf-8"),
                                 headers={"Content-Type": "application/xml", "User-Agent": "claude-skills object dump"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8")


def parse_response(text):
    """Return (control status, [result elements]) or raise with the gateway error text."""
    root = ET.fromstring(text)
    ctl = root.find("control")
    status = ctl.findtext("status") if ctl is not None else None
    err = root.find("errormessage")
    if err is not None and root.find("operation") is None:
        e = err.find("error")
        raise RuntimeError(f"gateway error {e.findtext('errorno') if e is not None else ''}: "
                           f"{e.findtext('description') if e is not None else ''} {e.findtext('description2') if e is not None else ''}")
    op = root.find("operation")
    auth = op.find("authentication") if op is not None else None
    if auth is not None and auth.findtext("status") == "failure":
        e = op.find(".//errormessage/error")
        raise RuntimeError(f"authentication failed: {e.findtext('description') if e is not None else ''} "
                           f"{e.findtext('description2') if e is not None else ''}")
    return status, (op.findall("result") if op is not None else [])


def result_error(result):
    e = result.find(".//errormessage/error")
    if e is None:
        return "unknown error"
    return f"{e.findtext('errorno')}: {e.findtext('description')} {e.findtext('description2') or ''}".strip()


def gateway_host(url):
    return re.sub(r"^https?://([^/]+).*$", r"\1", url)


def child_text(el, name):
    return next(((c.text or "").strip() for c in el if c.tag.lower() == name), "")


def type_name(el):
    return el.attrib.get("typename") or el.attrib.get("Name") or el.attrib.get("name")


def scrub_fields(data):
    """Remove every Field element whose ISCUSTOM (any case) is true; return the IDs removed."""
    removed = []
    for parent in data.iter():
        for child in list(parent):
            if child.tag.lower() == "field" and child_text(child, "iscustom").lower() in ("true", "1", "t"):
                removed.append(child_text(child, "id") or "?")
                parent.remove(child)
    return removed


def scrub_relationships(data, custom_objects=()):
    """Remove every Relationship whose related object is not a standard name, or is a removed custom object (a custom
    Platform Services object or user-defined dimension would otherwise keep its name in OBJECTNAME / OBJECTPATH /
    LABEL); return the object paths removed."""
    removed, custom = [], set(custom_objects)
    for parent in data.iter():
        for child in list(parent):
            if child.tag.lower() == "relationship":
                obj, path = child_text(child, "objectname"), child_text(child, "objectpath")
                if not STANDARD_NAME.match(obj) or obj in custom or not STANDARD_NAME.match(path or obj):
                    removed.append(path or obj or "?")
                    parent.remove(child)
    return removed


def inspect_names(data):
    """Object names from an inspect result, whatever the exact shape: an attribute typename/Name, or the element text."""
    names = []
    for el in data.iter():
        if el is data:
            continue
        n = type_name(el)
        if n:
            names.append(n.strip())
        elif el.tag.lower() in ("type", "object", "name") and el.text and el.text.strip() and len(el) == 0:
            names.append(el.text.strip())
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def remove_types(data, names):
    """Remove every entry of an inspect result whose name is in `names`."""
    names = set(names)
    for parent in data.iter():
        for child in list(parent):
            n = type_name(child) or (child.text or "").strip()
            if n in names:
                parent.remove(child)


def merge_inspect(existing_xml, data, names):
    """Return `existing_xml` with the entries of `data` for `names` appended when they are missing (re-adding a
    standard object that an earlier run dropped as custom)."""
    existing = ET.fromstring(existing_xml)
    present = set(inspect_names(existing))
    added = []
    for el in list(data):
        n = (type_name(el) or (el.text or "")).strip()
        if n in names and n not in present:
            existing.append(el)
            present.add(n)
            added.append(n)
    existing.set("count", str(len(present)))
    return ET.tostring(existing, encoding="unicode"), added


def collapse_inspect(text):
    """Keep one <type> per typename (the first, generic entry); return {name: entries dropped}."""
    data = ET.fromstring(text)
    seen, dropped = set(), {}
    for parent in list(data.iter()):
        for child in list(parent):
            n = type_name(child)
            if not n:
                continue
            if n in seen:
                parent.remove(child)
                dropped[n] = dropped.get(n, 0) + 1
            else:
                seen.add(n)
    data.set("count", str(len(seen)))
    return ET.tostring(data, encoding="unicode"), dropped


def counts_only(value):
    """A dump manifest lists removed names; the packed manifest carries counts only."""
    if isinstance(value, dict):
        return {k: (len(v) if isinstance(v, list) else v) for k, v in value.items()}
    if isinstance(value, list):
        return len(value)
    return value


def identifier_pattern(value):
    """Match `value` as a whole token, case-insensitively, so a short ID such as `admin` does not refuse a clean
    payload over the word 'Administrator'."""
    return re.compile(r"(?<![A-Za-z0-9_])" + re.escape(value) + r"(?![A-Za-z0-9_])", re.I)


def pack(folder, zip_path, allow_missing_identifiers=False):
    """Write the committable zip of a dump folder: collapsed inspect.xml, re-scrubbed lookup/*.xml, counts-only manifest.

    Every text is checked before the zip is created: no response envelope or credential element may appear, nor
    the sender, company or user ID in INTACCT_SENDER_ID / INTACCT_COMPANY_ID / INTACCT_USER_ID, which must be set
    (the pack usually runs in a later shell than the dump) unless `allow_missing_identifiers` is passed knowingly.
    """
    with open(os.path.join(folder, "inspect.xml"), encoding="utf-8") as f:
        inspect_xml, dropped = collapse_inspect(f.read())
    with open(os.path.join(folder, "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    custom_objects = manifest.get("custom_objects_removed", [])
    custom_objects = custom_objects if isinstance(custom_objects, list) else []
    lookups, fields_removed, rels_removed = [], {}, {}
    for name in sorted(os.listdir(os.path.join(folder, "lookup"))):
        if not name.endswith(".xml"):
            continue
        with open(os.path.join(folder, "lookup", name), encoding="utf-8") as f:
            data = ET.fromstring(f.read())
        obj = name[:-4]
        rf, rr = scrub_fields(data), scrub_relationships(data, custom_objects)  # a no-op on a scrubbed dump
        if rf:
            fields_removed[obj] = len(rf)
        if rr:
            rels_removed[obj] = len(rr)
        lookups.append((name, ET.tostring(data, encoding="unicode")))
    for key, extra in (("custom_fields_removed", fields_removed), ("custom_relationships_removed", rels_removed)):
        merged = counts_only(manifest.get(key, {}))
        merged = merged if isinstance(merged, dict) else {}
        for k, v in extra.items():
            merged[k] = merged.get(k, 0) + v
        manifest[key] = merged
    manifest["custom_objects_removed"] = counts_only(manifest.get("custom_objects_removed", []))
    manifest["inspect_entries_collapsed"] = dropped
    manifest_json = json.dumps(manifest, indent=1, sort_keys=True)

    identifiers = []
    for var in IDENTIFIER_VARS:
        v = os.environ.get(var, "")
        if v:
            identifiers.append((var, identifier_pattern(v)))
        elif not allow_missing_identifiers:
            sys.exit(f"not packed: {var} is not set, so the identifier guard cannot run. Set the identifiers the dump was "
                     "made with (the values never enter the zip), or pass --allow-missing-identifiers knowingly.")
    texts = [("inspect.xml", inspect_xml), ("manifest.json", manifest_json)] + [("lookup/" + n, t) for n, t in lookups]
    for fname, text in texts:
        low = text.lower()
        for needle in FORBIDDEN:
            if needle in low:
                sys.exit(f"not packed: {fname} contains {needle!r}")
        for var, pat in identifiers:
            if pat.search(text):
                sys.exit(f"not packed: {fname} contains the value of {var}")
    os.makedirs(os.path.dirname(os.path.abspath(zip_path)) or ".", exist_ok=True)
    tmp = zip_path + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("inspect.xml", inspect_xml)
        z.writestr("manifest.json", manifest_json)
        for name, text in lookups:
            z.writestr("lookup/" + name, text)
    os.replace(tmp, zip_path)
    print(f"packed {len(lookups)} lookups, inspect.xml (per-definition entries dropped: "
          + ", ".join(f"{k} x{v}" for k, v in dropped.items()) + f") and manifest.json -> {zip_path} "
          f"({os.path.getsize(zip_path) / 1e6:.1f} MB)"
          + (f"; scrubbed at pack time: {sum(fields_removed.values())} fields, {sum(rels_removed.values())} relationships" if fields_removed or rels_removed else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="output folder, outside the repository")
    ap.add_argument("--pack", help="pack an existing dump folder into --zip instead of dumping")
    ap.add_argument("--zip", help="zip to write with --pack, e.g. sources/sageintacct-assistant/object-definitions-2026-Release-3.zip")
    ap.add_argument("--allow-missing-identifiers", action="store_true", help="pack even if INTACCT_SENDER_ID / COMPANY_ID / USER_ID are not set")
    ap.add_argument("--release", default=None, help='the company\'s release, e.g. "2026 Release 3" (Help > About)')
    ap.add_argument("--objects", default=None, help="comma-separated object names: look up only these and merge into an existing --out")
    ap.add_argument("--batch", type=int, default=10, help="lookup functions per request")
    ap.add_argument("--delay", type=float, default=0.5, help="seconds between requests")
    ap.add_argument("--dry-run", action="store_true", help="print the first request with placeholders and exit")
    args = ap.parse_args()

    if args.pack:
        if not args.zip:
            sys.exit("--pack needs --zip")
        pack(args.pack, args.zip, args.allow_missing_identifiers)
        return
    if not args.out:
        sys.exit("--out is required")

    if args.dry_run:
        print(request_xml("<SENDER_ID>", "<SENDER_PASSWORD>", login_xml("<COMPANY_ID>", "<USER_ID>", "<PASSWORD>", ""),
                          '      <function controlid="getAPISession"><getAPISession/></function>\n', "dry-run"))
        print("then: <function controlid=\"...\"><inspect><object>*</object></inspect></function>")
        print("then: <function controlid=\"...\"><lookup><object>APBILL</object></lookup></function> (batched)")
        return

    sender_id, sender_pw = env("INTACCT_SENDER_ID"), env("INTACCT_SENDER_PASSWORD")
    company_id, user_id, user_pw = env("INTACCT_COMPANY_ID"), env("INTACCT_USER_ID"), env("INTACCT_USER_PASSWORD")
    location_id = env("INTACCT_LOCATION_ID", required=False)
    endpoint = env("INTACCT_ENDPOINT", required=False) or DEFAULT_ENDPOINT
    secrets = [v for v in (sender_id, sender_pw, company_id, user_id, user_pw) if v]

    lookup_dir = os.path.join(args.out, "lookup")
    os.makedirs(lookup_dir, exist_ok=True)
    manifest_path = os.path.join(args.out, "manifest.json")
    inspect_path = os.path.join(args.out, "inspect.xml")
    merging = args.objects is not None and os.path.exists(manifest_path)

    def guarded_write(path, text, mode="w"):
        for s in secrets + [session_id, session_endpoint]:
            if s and s in text:
                sys.exit(f"refusing to write {os.path.basename(path)}: it contains a credential, the session ID or the endpoint")
        with open(path, mode, encoding="utf-8", newline="\n") as f:
            f.write(text)

    # 1. session
    session_id = session_endpoint = ""
    body = request_xml(sender_id, sender_pw, login_xml(company_id, user_id, user_pw, location_id),
                       '      <function controlid="getAPISession"><getAPISession/></function>\n', str(uuid.uuid4()))
    _, results = parse_response(post(endpoint, body))
    if not results or results[0].findtext("status") != "success":
        sys.exit("getAPISession failed: " + (result_error(results[0]) if results else "no result"))
    api = results[0].find("data/api")
    session_id = api.findtext("sessionid")
    session_endpoint = api.findtext("endpoint") or endpoint
    host = gateway_host(session_endpoint)
    print(f"session opened; gateway host {host}")
    auth = f"<sessionid>{escape(session_id)}</sessionid>"
    time.sleep(args.delay)

    manifest = {"release": "not stated", "gateway_host": host, "dtdversion": "3.0", "location_id_used": bool(location_id),
                "objects": 0, "lookups_ok": 0, "lookups_failed": {}, "custom_fields_removed": {},
                "custom_relationships_removed": {}, "custom_objects_removed": [], "readded_objects": []}
    if merging:
        with open(manifest_path, encoding="utf-8") as f:
            manifest.update(json.load(f))
    if args.release:
        manifest["release"] = args.release
    manifest["dumped"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    dropped = []

    # 2. object list: always from inspect, so the committed inspect.xml is complete; --objects only restricts the lookups
    body = request_xml(sender_id, sender_pw, auth, '      <function controlid="inspect"><inspect><object>*</object></inspect></function>\n', str(uuid.uuid4()))
    _, results = parse_response(post(session_endpoint, body))
    if not results or results[0].findtext("status") != "success":
        sys.exit("inspect failed: " + (result_error(results[0]) if results else "no result"))
    data = results[0].find("data")
    all_names = inspect_names(data)
    requested = [n.strip() for n in args.objects.split(",") if n.strip()] if args.objects else None
    readded = [n for n in (requested or []) if not STANDARD_NAME.match(n)]
    custom = [n for n in all_names if not STANDARD_NAME.match(n) and n not in readded]
    standard = [n for n in all_names if n not in custom]
    if requested:
        unknown = [n for n in requested if n not in all_names]
        if unknown:
            sys.exit("inspect does not list: " + ", ".join(unknown))
        names = requested
    else:
        names = standard
    if merging:
        with open(inspect_path, encoding="utf-8") as f:
            merged_xml, added = merge_inspect(f.read(), data, set(names))
        guarded_write(inspect_path, merged_xml)
        manifest["custom_objects_removed"] = [n for n in manifest.get("custom_objects_removed", []) if n not in names]
        manifest["readded_objects"] = sorted(set(manifest.get("readded_objects", [])) | set(readded))
        print(f"inspect: {len(all_names)} objects; merged into the existing dump ({len(added)} entries restored in inspect.xml)")
    else:
        remove_types(data, custom)
        guarded_write(inspect_path, ET.tostring(data, encoding="unicode"))
        manifest["custom_objects_removed"] = custom
        manifest["readded_objects"] = readded
        dropped += [f"object {n} (name is not a standard upper-case object name)" for n in custom]
        print(f"inspect: {len(all_names)} objects, {len(custom)} treated as custom and dropped")
    manifest["objects"] = len(inspect_names(ET.parse(inspect_path).getroot()))
    time.sleep(args.delay)

    # 3. lookups, batched
    custom_set = set(manifest["custom_objects_removed"])
    for i in range(0, len(names), args.batch):
        batch = names[i:i + args.batch]
        fx = "".join(f'      <function controlid="{escape(n)}"><lookup><object>{escape(n)}</object></lookup></function>\n' for n in batch)
        try:
            _, results = parse_response(post(session_endpoint, request_xml(sender_id, sender_pw, auth, fx, str(uuid.uuid4()))))
        except (urllib.error.URLError, RuntimeError, ET.ParseError) as e:
            for n in batch:
                manifest["lookups_failed"][n] = f"request failed: {e}"
            print(f"  !! batch {batch[0]}..{batch[-1]}: {e}", file=sys.stderr)
            time.sleep(args.delay)
            continue
        for r in results:
            n = r.findtext("controlid")
            if r.findtext("status") != "success":
                manifest["lookups_failed"][n] = result_error(r)
                continue
            rdata = r.find("data")
            if rdata is None:
                manifest["lookups_failed"][n] = "no data element"
                continue
            removed_fields = scrub_fields(rdata)
            removed_rels = scrub_relationships(rdata, custom_set)
            if removed_fields:
                manifest["custom_fields_removed"][n] = removed_fields
                dropped += [f"field {n}.{f} (ISCUSTOM true)" for f in removed_fields]
            if removed_rels:
                manifest["custom_relationships_removed"][n] = removed_rels
                dropped += [f"relationship {n} -> {p} (non-standard related object)" for p in removed_rels]
            guarded_write(os.path.join(lookup_dir, f"{n}.xml"), ET.tostring(rdata, encoding="unicode"))
            manifest["lookups_failed"].pop(n, None)
        done = min(i + args.batch, len(names))
        if done % 50 < args.batch or done == len(names):
            print(f"  lookup {done}/{len(names)} failed={len(manifest['lookups_failed'])}")
        time.sleep(args.delay)

    manifest["lookups_ok"] = len([f for f in os.listdir(lookup_dir) if f.endswith(".xml")])
    guarded_write(os.path.join(args.out, "dropped.txt"), "\n".join(dropped) + ("\n" if dropped else ""), "a" if merging else "w")
    guarded_write(manifest_path, json.dumps(manifest, indent=1, sort_keys=True))
    print(f"done: {manifest['lookups_ok']} object definitions in {lookup_dir}, {len(manifest['lookups_failed'])} failed, "
          f"{sum(len(v) for v in manifest['custom_fields_removed'].values())} custom fields, "
          f"{sum(len(v) for v in manifest['custom_relationships_removed'].values())} relationships and "
          f"{len(manifest['custom_objects_removed'])} custom objects dropped (see dropped.txt)")


if __name__ == "__main__":
    main()
