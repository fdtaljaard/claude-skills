"""Tests for the object-definition dump helpers and the snapshot builder (maintenance only; not packaged).

    python -m unittest skills/sageintacct-assistant/scripts/test_build_object_snapshot.py
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dump_object_definitions as dump  # noqa: E402

LOOKUP = ('<data listtype="All" count="1"><Type Name="{name}" DocumentType=""><Fields>'
          '<Field><ID>RECORDNO</ID><LABEL>Record number</LABEL><DESCRIPTION>Record Number</DESCRIPTION><REQUIRED>false</REQUIRED>'
          '<READONLY>true</READONLY><DATATYPE>INTEGER</DATATYPE><ISCUSTOM>false</ISCUSTOM></Field>'
          '<Field><ID>STATE</ID><LABEL>State</LABEL><DESCRIPTION></DESCRIPTION><REQUIRED>true</REQUIRED><READONLY>false</READONLY>'
          '<DATATYPE>TEXT</DATATYPE><VALIDVALUES><VALIDVALUE>Draft</VALIDVALUE><VALIDVALUE>Posted</VALIDVALUE></VALIDVALUES>'
          '<ISCUSTOM>false</ISCUSTOM></Field>{extra}</Fields><Relationships><Relationship><OBJECTPATH>JOURNAL</OBJECTPATH>'
          '<OBJECTNAME>JOURNAL</OBJECTNAME><LABEL></LABEL><RELATIONSHIPTYPE>MANY2ONE</RELATIONSHIPTYPE><RELATEDBY>JOURNAL</RELATEDBY>'
          '</Relationship>{extra_rel}</Relationships></Type></data>')
CUSTOM = ('<Field><ID>X_CUSTOM</ID><LABEL>Custom</LABEL><DESCRIPTION></DESCRIPTION><REQUIRED>false</REQUIRED><READONLY>false</READONLY>'
          '<DATATYPE>TEXT</DATATYPE><ISCUSTOM>true</ISCUSTOM></Field>')
CUSTOM_REL = ('<Relationship><OBJECTPATH>my_udd</OBJECTPATH><OBJECTNAME>my_udd</OBJECTNAME><LABEL>My dimension</LABEL>'
              '<RELATIONSHIPTYPE>MANY2ONE</RELATIONSHIPTYPE><RELATEDBY>MY_UDDID</RELATEDBY></Relationship>')
INSPECT = ('<data listtype="All" count="4"><type typename="GLBATCH">Journal Entry</type><type typename="SODOCUMENT">Sales document</type>'
           '<type typename="SODOCUMENT">Sales Order</type><type typename="SODOCUMENT">SYS-Fulfillment Shipper</type></data>')
IDENTIFIERS = {"INTACCT_SENDER_ID": "acme_sender", "INTACCT_COMPANY_ID": "acme-DEV", "INTACCT_USER_ID": "admin"}


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def make_dump(folder, custom=False, custom_rel=False):
    os.makedirs(os.path.join(folder, "lookup"))
    with open(os.path.join(folder, "inspect.xml"), "w", encoding="utf-8") as f:
        f.write(INSPECT)
    for name in ("GLBATCH", "SODOCUMENT"):
        with open(os.path.join(folder, "lookup", name + ".xml"), "w", encoding="utf-8") as f:
            f.write(LOOKUP.format(name=name, extra=CUSTOM if (custom and name == "GLBATCH") else "",
                                  extra_rel=CUSTOM_REL if (custom_rel and name == "GLBATCH") else ""))
    with open(os.path.join(folder, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"release": "test", "dumped": "2026-10-13T00:00:00Z", "lookups_failed": {},
                   "custom_objects_removed": ["my_obj"], "custom_fields_removed": {"GLENTRY": ["GLE_FEE", "GLE_FROM"]}}, f)


class WithIdentifiers(unittest.TestCase):
    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in IDENTIFIERS}
        os.environ.update(IDENTIFIERS)

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class DumpHelpers(WithIdentifiers):
    def test_scrub_fields_removes_only_custom(self):
        d = ET.fromstring(LOOKUP.format(name="GLBATCH", extra=CUSTOM, extra_rel=""))
        removed = dump.scrub_fields(d)
        self.assertEqual(removed, ["X_CUSTOM"])
        self.assertEqual([f.findtext("ID") for f in d.iter("Field")], ["RECORDNO", "STATE"])

    def test_scrub_relationships_drops_non_standard_targets(self):
        d = ET.fromstring(LOOKUP.format(name="GLBATCH", extra="", extra_rel=CUSTOM_REL))
        self.assertEqual(dump.scrub_relationships(d), ["my_udd"])
        self.assertEqual([r.findtext("OBJECTNAME") for r in d.iter("Relationship")], ["JOURNAL"])
        d = ET.fromstring(LOOKUP.format(name="GLBATCH", extra="", extra_rel=""))
        self.assertEqual(dump.scrub_relationships(d, custom_objects=["JOURNAL"]), ["JOURNAL"])  # a removed custom object

    def test_inspect_names_collapse_and_merge(self):
        self.assertEqual(dump.inspect_names(ET.fromstring(INSPECT)), ["GLBATCH", "SODOCUMENT"])
        xml, dropped = dump.collapse_inspect(INSPECT)
        self.assertEqual(dropped, {"SODOCUMENT": 2})
        kept = ET.fromstring(xml)
        self.assertEqual([t.get("typename") for t in kept.iter("type")], ["GLBATCH", "SODOCUMENT"])
        self.assertEqual([t.text for t in kept.iter("type")][1], "Sales document")  # the generic label survives
        self.assertNotIn("SYS-", xml)
        fresh = ET.fromstring('<data><type typename="GLBATCH">Journal Entry</type><type typename="WQ_Order">Work queue</type></data>')
        merged, added = dump.merge_inspect('<data count="1"><type typename="GLBATCH">Journal Entry</type></data>', fresh, {"WQ_Order"})
        self.assertEqual(added, ["WQ_Order"])
        self.assertEqual(dump.inspect_names(ET.fromstring(merged)), ["GLBATCH", "WQ_Order"])

    def test_identifier_pattern_matches_whole_tokens(self):
        self.assertIsNone(dump.identifier_pattern("admin").search("<LABEL>Administrator</LABEL>"))
        self.assertIsNotNone(dump.identifier_pattern("admin").search("<LABEL>Created by ADMIN</LABEL>"))

    def test_pack_counts_only_scrub_and_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dump(os.path.join(tmp, "dump"), custom_rel=True)
            z = os.path.join(tmp, "out", "d.zip")
            dump.pack(os.path.join(tmp, "dump"), z)
            with zipfile.ZipFile(z) as zf:
                m = json.loads(zf.read("manifest.json"))
                self.assertEqual(m["custom_fields_removed"], {"GLENTRY": 2})
                self.assertEqual(m["custom_objects_removed"], 1)
                self.assertEqual(m["custom_relationships_removed"], {"GLBATCH": 1})  # scrubbed at pack time
                self.assertEqual(m["inspect_entries_collapsed"], {"SODOCUMENT": 2})
                self.assertNotIn("my_udd", zf.read("lookup/GLBATCH.xml").decode())
                self.assertEqual(sorted(zf.namelist()), ["inspect.xml", "lookup/GLBATCH.xml", "lookup/SODOCUMENT.xml", "manifest.json"])
            # the user ID as a whole token inside the payload refuses the pack; no zip is left behind
            with open(os.path.join(tmp, "dump", "lookup", "SODOCUMENT.xml"), "w", encoding="utf-8") as f:
                f.write(LOOKUP.format(name="SODOCUMENT", extra="", extra_rel="").replace("<LABEL>State</LABEL>", "<LABEL>Created by admin</LABEL>"))
            z2 = os.path.join(tmp, "out", "d2.zip")
            with self.assertRaises(SystemExit):
                dump.pack(os.path.join(tmp, "dump"), z2)
            self.assertFalse(os.path.exists(z2))
            # the same word as part of another token does not
            with open(os.path.join(tmp, "dump", "lookup", "SODOCUMENT.xml"), "w", encoding="utf-8") as f:
                f.write(LOOKUP.format(name="SODOCUMENT", extra="", extra_rel="").replace("<LABEL>State</LABEL>", "<LABEL>Administrator</LABEL>"))
            dump.pack(os.path.join(tmp, "dump"), z2)
            self.assertTrue(os.path.exists(z2))
            # a whole response envelope written as a lookup file (sender ID inside) refuses the pack
            with open(os.path.join(tmp, "dump", "lookup", "GLBATCH.xml"), "w", encoding="utf-8") as f:
                f.write("<response><control><senderid>x</senderid></control><operation>"
                        + LOOKUP.format(name="GLBATCH", extra="", extra_rel="") + "</operation></response>")
            with self.assertRaises(SystemExit):
                dump.pack(os.path.join(tmp, "dump"), os.path.join(tmp, "out", "d3.zip"))

    def test_pack_requires_identifiers_unless_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dump(os.path.join(tmp, "dump"))
            os.environ.pop("INTACCT_USER_ID")
            z = os.path.join(tmp, "d.zip")
            with self.assertRaises(SystemExit):
                dump.pack(os.path.join(tmp, "dump"), z)
            self.assertFalse(os.path.exists(z))
            dump.pack(os.path.join(tmp, "dump"), z, allow_missing_identifiers=True)
            self.assertTrue(os.path.exists(z))


class SnapshotBuilder(WithIdentifiers):
    def run_builder(self, dump_path, out):
        return subprocess.run([sys.executable, "-I", os.path.join(HERE, "build_object_snapshot.py"), "--dump", dump_path,
                               "--out", out, "--release", "2026 Release 3", "--verified", "2026-10-13"],
                              capture_output=True, text=True)

    def test_build_from_zip_line_ranges_and_pruning(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dump(os.path.join(tmp, "dump"))
            z = os.path.join(tmp, "object-definitions-test.zip")
            dump.pack(os.path.join(tmp, "dump"), z)
            out = os.path.join(tmp, "snapshot")
            os.makedirs(out)
            with open(os.path.join(out, "fields-07.md"), "w") as f:  # a stale bundle of an earlier build
                f.write("old\n")
            with open(os.path.join(out, "notes.md"), "w") as f:  # an unrelated file must survive
                f.write("keep\n")
            r = self.run_builder(z, out)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(sorted(os.listdir(out)), ["INDEX.md", "fields-01.md", "notes.md", "objects.md"])
            objects = read(os.path.join(out, "objects.md"))
            self.assertIn("scrubbed dump sources/sageintacct-assistant/object-definitions-test.zip", objects)
            bundle = read(os.path.join(out, "fields-01.md")).split("\n")
            rows = re.findall(r"^\| `([A-Z]+)` \| ([^|]*) \| (\d+) \| (\d+) \| \[(fields-01\.md)\]\(fields-01\.md#[a-z]+\) \| (\d+) \| (\d+) \|$", objects, re.M)
            self.assertEqual([(r[0], r[1].strip(), int(r[2]), int(r[3])) for r in rows],
                             [("GLBATCH", "Journal Entry", 2, 1), ("SODOCUMENT", "Sales document", 2, 1)])
            for name, _, _, _, _, line, n in rows:
                self.assertTrue(bundle[int(line) - 1].startswith(f'<a id="{name.lower()}"'))
                self.assertTrue(bundle[int(line)].startswith(f"## {name}"))
            self.assertIn("`Draft`, `Posted`", "\n".join(bundle))
            self.assertIn("1 custom objects, 2 custom fields and 0 relationships", read(os.path.join(out, "INDEX.md")))

    def test_refuses_wrong_out_folder_and_surviving_custom_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dump(os.path.join(tmp, "dump"), custom=True)
            r = self.run_builder(os.path.join(tmp, "dump"), os.path.join(tmp, "xml-api"))
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("named 'snapshot'", r.stderr + r.stdout)
            out = os.path.join(tmp, "snapshot")
            os.makedirs(out)
            with open(os.path.join(out, "objects.md"), "w", encoding="utf-8") as f:
                f.write("previous\n")
            r = self.run_builder(os.path.join(tmp, "dump"), out)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("custom fields survive", r.stderr + r.stdout)
            self.assertEqual(read(os.path.join(out, "objects.md")), "previous\n")
        with tempfile.TemporaryDirectory() as tmp:
            make_dump(os.path.join(tmp, "dump"), custom_rel=True)
            out = os.path.join(tmp, "snapshot")
            r = self.run_builder(os.path.join(tmp, "dump"), out)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("non-standard objects survive", r.stderr + r.stdout)


if __name__ == "__main__":
    unittest.main()
