# -*- coding: utf-8 -*-
"""Unit tests for element parsing, conversion (JSON/JSONC/XML) and validation."""

import json
import os
import re
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import edi_convert  # noqa: E402
import edi_core  # noqa: E402
import edi_validate  # noqa: E402


EDIFACT_MSG = (
    "UNA:+.? '"
    "UNB+UNOC:3+SENDER:14+RECEIVER:14+200101:1200+1'"
    "UNH+1+ORDERS:D:96A:UN:EAN008'"
    "BGM+220+PO12345+9'"
    "DTM+137:20200101:102'"
    "NAD+BY+5412345000013::9'"
    "UNT+5+1'"
    "UNZ+1+1'"
)

X12_MSG = (
    "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
    "*200101*1200*U*00401*000000001*0*P*:~"
    "GS*PO*SENDER*RECEIVER*20200101*1200*1*X*004010~"
    "ST*850*0001~"
    "BEG*00*NE*PO12345**20200101~"
    "SE*3*0001~"
    "GE*1*1~"
    "IEA*1*000000001~"
)

TRADACOMS_MSG = (
    "STX=ANAA:1+SENDER+RECEIVER+200101:1200+1'"
    "MHD=1+ORDHDR:9'"
    "TYP=0430+NEW-ORDERS'"
    "MTR=3'"
    "END=1'"
)

HL7_MSG = (
    "MSH|^~\\&|SENDING|FACILITY|RECEIVING|FACILITY|202001011200||ADT^A01|MSG1|P|2.5\r"
    "EVN|A01|202001011200\r"
    "PID|1||12345^^^HOSP^MR||DOE^JOHN||19700101|M\r"
)


class ElementParsingTests(unittest.TestCase):

    def test_edifact_elements_and_components(self):
        d = edi_core.detect(EDIFACT_MSG)
        unb = d.split_segments(EDIFACT_MSG)[1]
        elements = unb.elements()
        self.assertEqual(elements[0], ["UNOC", "3"])
        self.assertEqual(elements[1], ["SENDER", "14"])
        self.assertEqual(elements[4], ["1"])

    def test_edifact_release_character_unescaped(self):
        text = "UNA:+.? 'FTX+AAI++ABC+Contains ?+ plus and ?' quote'"
        d = edi_core.detect(text)
        ftx = d.split_segments(text)[1]
        elements = ftx.elements()
        self.assertEqual(elements[3], ["Contains + plus and ' quote"])

    def test_edifact_una_is_not_split(self):
        d = edi_core.detect(EDIFACT_MSG)
        una = d.split_segments(EDIFACT_MSG)[0]
        self.assertEqual(una.elements(), [[":+.? "]])

    def test_x12_elements(self):
        d = edi_core.detect(X12_MSG)
        beg = [s for s in d.split_segments(X12_MSG) if s.tag == "BEG"][0]
        elements = beg.elements()
        self.assertEqual(elements[0], ["00"])
        self.assertEqual(elements[2], ["PO12345"])
        self.assertEqual(elements[3], [""])  # empty element preserved

    def test_tradacoms_elements_after_tag_separator(self):
        d = edi_core.detect(TRADACOMS_MSG)
        stx = d.split_segments(TRADACOMS_MSG)[0]
        elements = stx.elements()
        self.assertEqual(elements[0], ["ANAA", "1"])
        self.assertEqual(elements[1], ["SENDER"])

    def test_hl7_msh_field_numbering(self):
        d = edi_core.detect(HL7_MSG)
        msh = d.split_segments(HL7_MSG)[0]
        elements = msh.elements()
        self.assertEqual(elements[0], ["|"])        # MSH-1: field separator
        self.assertEqual(elements[1], ["^~\\&"])    # MSH-2: encoding characters
        self.assertEqual(elements[2], ["SENDING"])  # MSH-3
        self.assertEqual(elements[8], ["ADT", "A01"])

    def test_hl7_standard_escapes_decoded(self):
        text = "MSH|^~\\&|APP|FAC|APP2|FAC2|2020||ADT^A01|1|P|2.5\rNTE|1||A \\F\\ B \\T\\ C\r"
        d = edi_core.detect(text)
        nte = d.split_segments(text)[1]
        self.assertEqual(nte.elements()[2], ["A | B & C"])


class JsonConversionTests(unittest.TestCase):

    def test_json_is_valid_and_structured(self):
        out = edi_convert.to_json(EDIFACT_MSG)
        tree = json.loads(out)
        self.assertEqual(tree["dialect"], "EDIFACT")
        self.assertEqual(tree["delimiters"]["segment"], "'")
        tags = [s["tag"] for s in tree["segments"]]
        self.assertEqual(
            tags, ["UNA", "UNB", "UNH", "BGM", "DTM", "NAD", "UNT", "UNZ"])

    def test_json_collapses_single_component_elements(self):
        tree = json.loads(edi_convert.to_json(EDIFACT_MSG))
        bgm = [s for s in tree["segments"] if s["tag"] == "BGM"][0]
        self.assertEqual(bgm["elements"], ["220", "PO12345", "9"])
        self.assertEqual(bgm["name"], "Beginning of Message")

    def test_json_keeps_composite_elements_as_lists(self):
        tree = json.loads(edi_convert.to_json(EDIFACT_MSG))
        dtm = [s for s in tree["segments"] if s["tag"] == "DTM"][0]
        self.assertEqual(dtm["elements"], [["137", "20200101", "102"]])

    def test_json_x12(self):
        tree = json.loads(edi_convert.to_json(X12_MSG))
        self.assertEqual(tree["dialect"], "X12")
        st = [s for s in tree["segments"] if s["tag"] == "ST"][0]
        self.assertEqual(st["elements"], ["850", "0001"])

    def test_json_hl7(self):
        tree = json.loads(edi_convert.to_json(HL7_MSG))
        msh = tree["segments"][0]
        self.assertEqual(msh["elements"][0], "|")
        self.assertEqual(msh["elements"][1], "^~\\&")
        self.assertEqual(msh["elements"][8], ["ADT", "A01"])

    def test_non_edi_raises(self):
        with self.assertRaises(ValueError):
            edi_convert.to_json("definitely not edi")


class JsoncConversionTests(unittest.TestCase):

    def _strip_comments(self, jsonc):
        # Comments in our output always start with "//" outside of strings and
        # are either whole-line or trailing after a value; strings in the data
        # could contain "//" so only strip when preceded by structural chars.
        lines = []
        for line in jsonc.splitlines():
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            # Trailing comments follow "," or a JSON value; our generator puts
            # exactly two spaces before them.
            idx = line.find("  // ")
            if idx != -1:
                line = line[:idx]
            lines.append(line)
        return "\n".join(lines)

    def test_jsonc_strips_to_valid_json(self):
        out = edi_convert.to_jsonc(EDIFACT_MSG)
        tree = json.loads(self._strip_comments(out))
        self.assertEqual(tree["dialect"], "EDIFACT")
        self.assertEqual(len(tree["segments"]), 8)

    def test_jsonc_contains_descriptions(self):
        out = edi_convert.to_jsonc(EDIFACT_MSG)
        self.assertIn("// UNB — Interchange Header", out)
        self.assertIn("Opens the interchange", out)

    def test_jsonc_contains_element_names(self):
        out = edi_convert.to_jsonc(EDIFACT_MSG)
        self.assertIn("Interchange control reference", out)

    def test_jsonc_matches_json_structure(self):
        jsonc_tree = json.loads(self._strip_comments(edi_convert.to_jsonc(X12_MSG)))
        json_tree = json.loads(edi_convert.to_json(X12_MSG))
        self.assertEqual(jsonc_tree, json_tree)


class XmlConversionTests(unittest.TestCase):

    def test_xml_is_well_formed(self):
        out = edi_convert.to_xml(EDIFACT_MSG)
        root = ET.fromstring(out)
        self.assertEqual(root.tag, "edi")
        self.assertEqual(root.get("dialect"), "EDIFACT")
        self.assertEqual(len(root.findall("segment")), 8)

    def test_xml_segments_carry_names(self):
        root = ET.fromstring(edi_convert.to_xml(EDIFACT_MSG))
        bgm = [s for s in root.findall("segment") if s.get("tag") == "BGM"][0]
        self.assertEqual(bgm.get("name"), "Beginning of Message")
        self.assertEqual(bgm.findall("element")[1].text, "PO12345")

    def test_xml_composite_elements_nest_components(self):
        root = ET.fromstring(edi_convert.to_xml(EDIFACT_MSG))
        dtm = [s for s in root.findall("segment") if s.get("tag") == "DTM"][0]
        comps = dtm.findall("element")[0].findall("component")
        self.assertEqual([c.text for c in comps], ["137", "20200101", "102"])

    def test_xml_escapes_special_characters(self):
        text = "UNA:+.? 'FTX+AAI++ABC+a<b & c?+d'"
        out = edi_convert.to_xml(text)
        root = ET.fromstring(out)  # must not raise
        ftx = [s for s in root.findall("segment") if s.get("tag") == "FTX"][0]
        self.assertEqual(ftx.findall("element")[3].text, "a<b & c+d")

    def test_xml_hl7(self):
        root = ET.fromstring(edi_convert.to_xml(HL7_MSG))
        msh = root.findall("segment")[0]
        self.assertEqual(msh.get("tag"), "MSH")
        self.assertEqual(msh.findall("element")[0].text, "|")


class ValidationTests(unittest.TestCase):

    def test_valid_edifact_passes(self):
        self.assertEqual(edi_validate.validate(EDIFACT_MSG), [])

    def test_valid_x12_passes(self):
        self.assertEqual(edi_validate.validate(X12_MSG), [])

    def test_valid_tradacoms_passes(self):
        self.assertEqual(edi_validate.validate(TRADACOMS_MSG), [])

    def test_valid_hl7_passes(self):
        self.assertEqual(edi_validate.validate(HL7_MSG), [])

    def test_edifact_wrong_unt_count_flagged(self):
        bad = EDIFACT_MSG.replace("UNT+5+1'", "UNT+9+1'")
        issues = edi_validate.validate(bad)
        self.assertTrue(any("UNT declares 9" in i["message"] for i in issues))

    def test_edifact_wrong_unz_reference_flagged(self):
        bad = EDIFACT_MSG.replace("UNZ+1+1'", "UNZ+1+999'")
        issues = edi_validate.validate(bad)
        self.assertTrue(any("UNZ control reference" in i["message"] for i in issues))

    def test_edifact_missing_unt_flagged(self):
        bad = EDIFACT_MSG.replace("UNT+5+1'", "")
        issues = edi_validate.validate(bad)
        self.assertTrue(any("never closed by UNT" in i["message"] for i in issues))

    def test_x12_wrong_se_count_flagged(self):
        bad = X12_MSG.replace("SE*3*0001~", "SE*9*0001~")
        issues = edi_validate.validate(bad)
        self.assertTrue(any("SE declares 9" in i["message"] for i in issues))

    def test_x12_mismatched_control_number_flagged(self):
        bad = X12_MSG.replace("SE*3*0001~", "SE*3*0002~")
        issues = edi_validate.validate(bad)
        self.assertTrue(any("does not match ST control number" in i["message"]
                            for i in issues))

    def test_tradacoms_wrong_mtr_count_flagged(self):
        bad = TRADACOMS_MSG.replace("MTR=3'", "MTR=5'")
        issues = edi_validate.validate(bad)
        self.assertTrue(any("MTR declares 5" in i["message"] for i in issues))

    def test_tradacoms_wrong_end_count_flagged(self):
        bad = TRADACOMS_MSG.replace("END=1'", "END=4'")
        issues = edi_validate.validate(bad)
        self.assertTrue(any("END declares 4" in i["message"] for i in issues))

    def test_hl7_missing_msh_flagged(self):
        bad = "EVN|A01|202001011200\rPID|1||123\r"
        d = edi_core.Dialect.from_family("hl7")
        issues = edi_validate.validate(bad, d)
        self.assertTrue(any("First segment must be MSH" in i["message"]
                            for i in issues))

    def test_issue_offsets_point_into_text(self):
        bad = EDIFACT_MSG.replace("UNT+5+1'", "UNT+9+1'")
        for issue in edi_validate.validate(bad):
            self.assertTrue(0 <= issue["offset"] < len(bad))
            self.assertTrue(bad[issue["offset"]:].startswith(("UNT", "UNZ", "UNB")))


class BeautifiedInputTests(unittest.TestCase):
    """Conversion and validation must also work on beautified input."""

    def test_convert_beautified_edifact(self):
        pretty = edi_core.beautify(EDIFACT_MSG)
        self.assertEqual(json.loads(edi_convert.to_json(pretty)),
                         json.loads(edi_convert.to_json(EDIFACT_MSG)))

    def test_validate_beautified_x12(self):
        pretty = edi_core.beautify(X12_MSG)
        self.assertEqual(edi_validate.validate(pretty), [])


if __name__ == "__main__":
    unittest.main()
