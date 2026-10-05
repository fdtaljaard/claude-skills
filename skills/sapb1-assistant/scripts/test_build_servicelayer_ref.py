#!/usr/bin/env python3
import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("build_servicelayer_ref", HERE / "build_servicelayer_ref.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)

V4 = '''<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx Version="4.0" xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx">
 <edmx:DataServices><Schema Namespace="SAPB1" xmlns="http://docs.oasis-open.org/odata/ns/edm">
  <EnumType Name="BoCardTypes" UnderlyingType="Edm.Int32">
   <Member Name="cCustomer" Value="0"><Annotation Term="SAPB1.ValidValue" String="C"/></Member>
  </EnumType>
  <ComplexType Name="DocumentLine" OpenType="true">
   <Property Name="ItemCode" Type="Edm.String"><Annotation Term="SAPB1.ColumnName" String="ItemCode"/></Property>
   <Property Name="U_ClientField" Type="Edm.String"/>
  </ComplexType>
  <EntityType Name="Document" OpenType="true"><Key><PropertyRef Name="DocEntry"/></Key>
   <Property Name="DocEntry" Type="Edm.Int32" Nullable="false"/>
   <Property Name="DocumentLines" Type="Collection(SAPB1.DocumentLine)"/>
   <NavigationProperty Name="U_CustomLink" Type="SAPB1.Document"/>
  </EntityType>
  <Annotations Target="SAPB1.Document/DocEntry"><Annotation Term="Common.Label" String="Document Entry"/></Annotations>
  <Annotations Target="SAPB1.Document"><Annotation Term="SAPB1.TableName" String="ORDR"/></Annotations>
  <Action Name="Close" IsBound="true"><Parameter Name="Document" Type="SAPB1.Document"/></Action>
  <Function Name="Ping"><ReturnType Type="Edm.String"/></Function>
  <EntityContainer Name="ServiceLayer">
   <EntitySet Name="Orders" EntityType="SAPB1.Document"><Annotation Term="Common.Label" String="Sales Order"/></EntitySet>
   <EntitySet Name="@CLIENT_UDO" EntityType="SAPB1.Document"/>
   <ActionImport Name="CloseOrder" Action="SAPB1.Close"/>
   <FunctionImport Name="Ping" Function="SAPB1.Ping" IncludeInServiceDocument="true"/>
  </EntityContainer>
 </Schema></edmx:DataServices>
</edmx:Edmx>'''

V3 = '''<edmx:Edmx Version="1.0" xmlns:edmx="http://schemas.microsoft.com/ado/2007/06/edmx"><edmx:DataServices/></edmx:Edmx>'''


class BuildServiceLayerRefTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, xml=V4, excludes=(), property_excludes=()):
        src = self.root / "metadata.xml"
        out = self.root / "out"
        src.write_text(xml, encoding="utf-8")
        counts = mod.build(src, out, "2026-10-03", "synthetic OData v4 fixture", "test snapshot",
                           [mod.re.compile(x) for x in excludes],
                           [mod.re.compile(x) for x in property_excludes])
        return out, counts

    def test_builds_types_sets_operations_and_enums(self):
        out, counts = self.build()
        self.assertEqual(counts["entity_types"], 1)
        self.assertEqual(counts["complex_types"], 1)
        self.assertEqual(counts["actions"], 1)
        self.assertEqual(counts["functions"], 1)
        self.assertEqual(counts["enums"], 1)
        self.assertEqual(counts["operation_imports"], 2)
        self.assertIn("SAPB1.Document | EntityType | DocEntry", (out / "api" / "INDEX.md").read_text())
        self.assertIn("OpenType: true", (out / "api" / "types-01.md").read_text())
        self.assertIn("SAPB1.ColumnName=ItemCode", (out / "api" / "members.md").read_text())
        self.assertIn("SAPB1.Document.DocEntry : Edm.Int32 [required] {Common.Label=Document Entry}", (out / "api" / "members.md").read_text())
        self.assertIn("- SAPB1.TableName=ORDR", (out / "api" / "types-01.md").read_text())
        self.assertIn("SAPB1.ValidValue=C", (out / "enums" / "members.md").read_text())
        self.assertIn("Action SAPB1.Close", (out / "operations" / "members.md").read_text())
        self.assertIn("Common.Label=Sales Order", (out / "entity-sets.md").read_text())
        self.assertIn("CloseOrder | ActionImport | SAPB1.Close", (out / "operation-imports.md").read_text())

    def test_exclude_regex_removes_client_specific_names(self):
        out, counts = self.build(excludes=(r"@CLIENT_UDO",))
        self.assertEqual(counts["excluded"], 1)
        self.assertNotIn("@CLIENT_UDO", (out / "entity-sets.md").read_text())
        self.assertIn("@CLIENT_UDO", (out / "INDEX.md").read_text())

    def test_exclude_property_regex_removes_client_udfs(self):
        out, counts = self.build(property_excludes=(r"^U_",))
        self.assertEqual(counts["excluded_properties"], 2)  # U_ClientField property + U_CustomLink navigation
        self.assertEqual(counts["kept_key_properties"], 0)
        members = (out / "api" / "members.md").read_text()
        self.assertIn("SAPB1.DocumentLine.ItemCode", members)
        self.assertNotIn("U_ClientField", members)
        types = (out / "api" / "types-01.md").read_text()
        self.assertNotIn("U_CustomLink", types)
        self.assertNotIn("U_ClientField", types)
        self.assertIn("Filtered properties: 1", types)
        index = (out / "api" / "INDEX.md").read_text()
        self.assertIn("| SAPB1.DocumentLine | ComplexType |  | 1 | 0 | 1 |", index)
        self.assertIn("| SAPB1.Document | EntityType | DocEntry | 2 | 0 | 1 |", index)
        self.assertIn("property/name target: `^U_`", (out / "INDEX.md").read_text())

    def test_property_target_match_requires_slash_in_pattern(self):
        # An unanchored name fragment must not match the type name through the Type/Property target.
        out, counts = self.build(property_excludes=(r"^SAPB1\.",))
        self.assertEqual(counts["excluded_properties"], 0)
        self.assertIn("SAPB1.DocumentLine.ItemCode", (out / "api" / "members.md").read_text())
        self.tearDown(); self.setUp()
        out, counts = self.build(property_excludes=(r"DocumentLine/U_",))
        self.assertEqual(counts["excluded_properties"], 1)
        members = (out / "api" / "members.md").read_text()
        self.assertNotIn("U_ClientField", members)
        self.assertIn("SAPB1.Document.DocumentLines", members)

    def test_key_properties_survive_property_filter(self):
        out, counts = self.build(property_excludes=(r"DocEntry",))
        self.assertEqual(counts["excluded_properties"], 0)
        self.assertEqual(counts["kept_key_properties"], 1)
        types = (out / "api" / "types-01.md").read_text()
        self.assertIn("Key: DocEntry", types)
        self.assertIn("- DocEntry : Edm.Int32", types)
        self.assertNotIn("Filtered properties", types)

    def test_index_ranges_point_at_entries(self):
        out, _ = self.build()
        for idx in ("api", "enums", "operations"):
            for row in (out / idx / "INDEX.md").read_text().splitlines():
                cells = [c.strip() for c in row.strip("|").split("|")]
                if len(cells) < 3 or not cells[-2].isdigit():
                    continue
                name, fname, line, n = cells[0], cells[-3], int(cells[-2]), int(cells[-1])
                seg = (out / idx / fname).read_text().splitlines()[line - 1:line - 1 + n]
                self.assertTrue(seg and seg[0].startswith("# " + name.split("(")[0].strip()), (idx, name, seg[:1]))
                self.assertFalse(any(s.startswith("# ") for s in seg[1:]), (idx, name))

    def test_rejects_non_v4_metadata(self):
        src = self.root / "v3.xml"
        src.write_text(V3, encoding="utf-8")
        with self.assertRaises(SystemExit):
            mod.parse(src)


if __name__ == "__main__":
    unittest.main()
