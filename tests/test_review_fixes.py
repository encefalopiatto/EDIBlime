# -*- coding: utf-8 -*-
"""Regression tests for the defects found by the multi-agent code review,
plus coverage for the features added alongside (repair, qualifier decoding,
element_at)."""

import json
import os
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import edi_convert  # noqa: E402
from core import edi_core  # noqa: E402
from core import edi_data  # noqa: E402
from core import edi_validate  # noqa: E402


class DetectionStrictnessTests(unittest.TestCase):
    """C02: ordinary text must never be claimed as EDI."""

    def test_prose_with_apostrophes_is_not_edi(self):
        self.assertIsNone(edi_core.detect("# Notes\nIt's a test. Don't panic.\n"))

    def test_code_with_string_quotes_is_not_edi(self):
        self.assertIsNone(edi_core.detect("x = 'a'\ny = 'b'\n"))

    def test_tilde_data_is_not_x12(self):
        self.assertIsNone(edi_core.detect("a~b~c~d\n"))

    def test_pipe_csv_is_not_hl7(self):
        self.assertIsNone(edi_core.detect("name|street|city\njohn|main|berlin\n"))

    def test_envelope_less_edifact_still_detected(self):
        d = edi_core.detect("BGM+220+PO1+9'DTM+137:20200101:102'")
        self.assertIsNotNone(d)
        self.assertEqual(d.family, "edifact")

    def test_envelope_less_x12_still_detected(self):
        d = edi_core.detect("BEG*00*NE*PO1**20200101~REF*DP*01~")
        self.assertIsNotNone(d)
        self.assertEqual(d.family, "x12")

    def test_hl7_fragment_detected(self):
        d = edi_core.detect("PID|1||12345^^^HOSP^MR||DOE^JOHN|")
        self.assertIsNotNone(d)
        self.assertEqual(d.family, "hl7")


class Hl7EscapeTerminatorTests(unittest.TestCase):
    """C03: a field ending in an escape sequence must not swallow the CR."""

    def test_trailing_escape_does_not_merge_segments(self):
        text = ("MSH|^~\\&|SND|FAC|RCV|FAC|202401011200||ADT^A01|MSG1|P|2.5\r"
                "NTE|1||50\\F\\\r"
                "PID|1||12345\r")
        d = edi_core.detect(text)
        tags = [s.tag for s in d.split_segments(text)]
        self.assertEqual(tags, ["MSH", "NTE", "PID"])
        nte = d.split_segments(text)[1]
        self.assertEqual(nte.elements()[2], ["50|"])


class UnaEdgeCaseTests(unittest.TestCase):
    """C04: UNA declaring 'no release character' via a space must stick."""

    def test_una_space_disables_release_character(self):
        text = "UNA:+.  'QTY+21:5?'NAD+BY'"
        d = edi_core.detect(text)
        self.assertIsNone(d.release_character)
        tags = [s.tag for s in d.split_segments(text)]
        self.assertEqual(tags, ["UNA", "QTY", "NAD"])
        qty = d.split_segments(text)[1]
        self.assertEqual(qty.elements()[0], ["21", "5?"])


class IsaDetectionTests(unittest.TestCase):
    """C05 + C17: ISA delimiter extraction edge cases."""

    ISA_LF = ("ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER"
              "       *200101*1200*U*00401*000000001*0*P*>\n"
              "GS*PO*S*R*20200101*1200*1*X*004010\n"
              "ST*850*0001\n"
              "N1*BY*ACME>DIV*92*001\n"
              "SE*3*0001\n"
              "GE*1*1\n"
              "IEA*1*000000001\n")

    def test_full_width_isa_with_lf_terminator_reads_component_separator(self):
        d = edi_core.detect(self.ISA_LF)
        self.assertEqual(d.segment_terminator, "\n")
        self.assertEqual(d.component_separator, ">")
        n1 = [s for s in d.split_segments(self.ISA_LF) if s.tag == "N1"][0]
        self.assertEqual(n1.elements()[1], ["ACME", "DIV"])

    def test_unpadded_isa_does_not_yield_garbage(self):
        text = ("ISA*00**00**ZZ*SENDER*ZZ*RECEIVER*240101*1200*U*00401"
                "*000000001*0*P*>~GS*PO*S*R*20240101*1200*1*X*004010~"
                "ST*850*0001~SE*2*0001~GE*1*1~IEA*1*000000001~")
        d = edi_core.detect(text)
        self.assertEqual(d.segment_terminator, "~")
        self.assertEqual(d.component_separator, ">")
        tags = [s.tag for s in d.split_segments(text)]
        self.assertEqual(tags, ["ISA", "GS", "ST", "SE", "GE", "IEA"])

    def test_pre_00402_isa11_is_not_a_repetition_separator(self):
        d = edi_core.detect(self.ISA_LF)
        self.assertIsNone(d.repetition_separator)


class BomAndNewlineTerminatorTests(unittest.TestCase):

    def test_bom_does_not_leak_into_first_tag(self):
        text = "﻿UNB+UNOC:3+S+R+240101:1200+1'UNZ+1+1'"
        d = edi_core.detect(text)
        segs = d.split_segments(text)
        self.assertEqual(segs[0].tag, "UNB")

    def test_newline_terminator_beautify_has_no_blank_lines(self):
        text = "UNA:+.? \nUNB+UNOA:4+S+R+240101:1200+1\nUNZ+1+1\n"
        d = edi_core.detect(text)
        self.assertEqual(d.segment_terminator, "\n")
        out = edi_core.beautify(text, d)
        self.assertNotIn("\n\n", out)
        self.assertEqual(len(out.rstrip("\n").split("\n")), 3)


class TradacomsElementTests(unittest.TestCase):
    """P01: a TRADACOMS segment written without '=' must not shift indices."""

    def test_plus_after_tag_is_stripped(self):
        d = edi_core.Dialect.from_family("tradacoms")
        seg = edi_core.Segment("MHD+1+ORDHDR:9", d)
        self.assertEqual(seg.elements(), [["1"], ["ORDHDR", "9"]])


class ValidatorRobustnessTests(unittest.TestCase):
    """C01 + C20: hostile count values must not crash and must be flagged."""

    def test_unicode_digit_count_does_not_crash(self):
        text = ("UNB+UNOC:3+A+B+200101:0000+1'UNH+M1+ORDERS:D:96A:UN'"
                "UNT+²+M1'UNZ+1+1'")
        issues = edi_validate.validate(text)  # must not raise
        self.assertTrue(any("non-numeric" in i["message"] for i in issues))

    def test_non_numeric_count_flagged(self):
        text = "UNB+UNOC:3+A+B+200101:0000+1'UNH+M1+ORDERS:D:96A:UN'UNT+XX+M1'UNZ+1+1'"
        issues = edi_validate.validate(text)
        self.assertTrue(any("non-numeric" in i["message"] for i in issues))


class X12StructureTests(unittest.TestCase):
    """C06: unclosed ST/GS and ST outside GS must be reported."""

    ISA = ("ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER"
           "       *200101*1200*U*00401*000000001*0*P*:~")

    def test_unclosed_st_flagged(self):
        text = (self.ISA + "GS*PO*S*R*20200101*1200*1*X*004010~"
                "ST*850*0001~ST*850*0002~SE*2*0002~GE*2*1~IEA*1*000000001~")
        issues = edi_validate.validate(text)
        self.assertTrue(any("ST found before the previous transaction set"
                            in i["message"] for i in issues))

    def test_unclosed_gs_flagged(self):
        text = (self.ISA + "GS*PO*S*R*20200101*1200*1*X*004010~"
                "GS*PO*S*R*20200101*1200*2*X*004010~"
                "ST*850*0001~SE*2*0001~GE*1*2~IEA*2*000000001~")
        issues = edi_validate.validate(text)
        self.assertTrue(any("GS found before the previous group"
                            in i["message"] for i in issues))

    def test_st_outside_gs_warns(self):
        text = self.ISA + "ST*850*0001~SE*2*0001~IEA*0*000000001~"
        issues = edi_validate.validate(text)
        self.assertTrue(any("outside any functional group" in i["message"]
                            for i in issues))


class EdifactGroupTests(unittest.TestCase):
    """C07: UNG/UNE must actually be validated."""

    BASE = ("UNB+UNOC:3+A+B+200101:0000+REF1'"
            "UNG+ORDERS+A+B+200101:0000+G1+UN+D:96A'"
            "UNH+M1+ORDERS:D:96A:UN'UNT+2+M1'"
            "UNE+1+G1'UNZ+1+REF1'")

    def test_valid_group_passes(self):
        issues = [i for i in edi_validate.validate(self.BASE)
                  if i["severity"] == "error"]
        self.assertEqual(issues, [])

    def test_wrong_une_count_flagged(self):
        bad = self.BASE.replace("UNE+1+G1'", "UNE+99+G1'")
        issues = edi_validate.validate(bad)
        self.assertTrue(any("UNE declares 99" in i["message"] for i in issues))

    def test_wrong_une_reference_flagged(self):
        bad = self.BASE.replace("UNE+1+G1'", "UNE+1+WRONG'")
        issues = edi_validate.validate(bad)
        self.assertTrue(any("does not match UNG reference" in i["message"]
                            for i in issues))

    def test_unclosed_ung_flagged(self):
        bad = self.BASE.replace("UNE+1+G1'", "")
        issues = edi_validate.validate(bad)
        self.assertTrue(any("never closed by UNE" in i["message"] for i in issues))


class ConverterHardeningTests(unittest.TestCase):
    """C08 + C09: adversarial data must not break the output contracts."""

    def _strip_comments(self, jsonc):
        lines = []
        for line in jsonc.splitlines():
            if line.strip().startswith("//"):
                continue
            idx = line.find("  // ")
            if idx != -1:
                line = line[:idx]
            lines.append(line)
        return "\n".join(lines)

    def test_jsonc_with_newline_in_tag_strips_to_valid_json(self):
        text = "UNB+UNOC:3+A+B+200101:0000+1'FO\nO+BAR'UNZ+1+1'"
        out = edi_convert.to_jsonc(text)
        json.loads(self._strip_comments(out))  # must not raise

    def test_xml_with_control_characters_is_well_formed(self):
        text = "UNB+UNOC:3+A+B+200101:0000+1'FTX+AAI+++hel\x01lo'UNZ+1+1'"
        ET.fromstring(edi_convert.to_xml(text))  # must not raise

    def test_xml_hl7_with_vertical_tab_is_well_formed(self):
        text = ("MSH|^~\\&|A|B|C|D|2020||ADT^A01|1|P|2.5\r"
                "PID|1||x\x0by\r")
        ET.fromstring(edi_convert.to_xml(text))  # must not raise


class RepairTests(unittest.TestCase):
    """F4: envelope repair recomputes counts and re-syncs references."""

    def test_repair_edifact(self):
        broken = ("UNB+UNOC:3+A+B+200101:0000+REF1'"
                  "UNH+M1+ORDERS:D:96A:UN'BGM+220+PO1+9'UNT+99+WRONG'"
                  "UNZ+9+NOPE'")
        fixed, changed = edi_validate.repair(broken)
        self.assertEqual(changed, 2)
        self.assertIn("UNT+3+M1'", fixed)
        self.assertIn("UNZ+1+REF1'", fixed)
        errors = [i for i in edi_validate.validate(fixed)
                  if i["severity"] == "error"]
        self.assertEqual(errors, [])

    def test_repair_x12(self):
        broken = ("ISA*00*          *00*          *ZZ*SENDER         *ZZ*"
                  "RECEIVER       *200101*1200*U*00401*000000001*0*P*:~"
                  "GS*PO*S*R*20200101*1200*1*X*004010~"
                  "ST*850*0001~BEG*00*NE*PO1**20200101~SE*9*9999~"
                  "GE*5*7~IEA*3*111111111~")
        fixed, changed = edi_validate.repair(broken)
        self.assertEqual(changed, 3)
        self.assertIn("SE*3*0001~", fixed)
        self.assertIn("GE*1*1~", fixed)
        self.assertIn("IEA*1*000000001~", fixed)
        errors = [i for i in edi_validate.validate(fixed)
                  if i["severity"] == "error"]
        self.assertEqual(errors, [])

    def test_repair_tradacoms(self):
        broken = ("STX=ANAA:1+S+R+200101:1200+1'MHD=1+ORDHDR:9'"
                  "TYP=0430+NEW'MTR=9'END=7'")
        fixed, changed = edi_validate.repair(broken)
        self.assertEqual(changed, 2)
        self.assertIn("MTR=3'", fixed)
        self.assertIn("END=1'", fixed)
        errors = [i for i in edi_validate.validate(fixed)
                  if i["severity"] == "error"]
        self.assertEqual(errors, [])

    def test_repair_is_noop_on_consistent_message(self):
        clean = ("UNB+UNOC:3+A+B+200101:0000+1'UNH+1+ORDERS:D:96A:UN'"
                 "BGM+220+PO1+9'UNT+3+1'UNZ+1+1'")
        fixed, changed = edi_validate.repair(clean)
        self.assertEqual(changed, 0)
        self.assertEqual(fixed, clean)

    def test_repair_preserves_beautified_layout(self):
        clean = ("UNB+UNOC:3+A+B+200101:0000+1'UNH+1+ORDERS:D:96A:UN'"
                 "BGM+220+PO1+9'UNT+9+1'UNZ+1+1'")
        pretty = edi_core.beautify(clean)
        fixed, changed = edi_validate.repair(pretty)
        self.assertEqual(changed, 1)
        self.assertEqual(len(fixed.splitlines()), len(pretty.splitlines()))


class QualifierDecodingTests(unittest.TestCase):
    """F2: common qualifier codes decode to their meanings."""

    def test_edifact_qualifiers(self):
        self.assertEqual(
            edi_data.qualifier_label("edifact", "DTM", 1, "137"),
            "Document/message date")
        self.assertEqual(
            edi_data.qualifier_label("edifact", "NAD", 1, "BY"), "Buyer")
        self.assertEqual(
            edi_data.qualifier_label("eancom", "QTY", 1, "21"),
            "Ordered quantity")

    def test_x12_qualifiers(self):
        self.assertEqual(
            edi_data.qualifier_label("x12", "ST", 1, "850"), "Purchase Order")
        self.assertEqual(
            edi_data.qualifier_label("x12", "HL", 3, "S"), "Shipment")

    def test_hl7_qualifiers(self):
        self.assertEqual(
            edi_data.qualifier_label("hl7", "PV1", 2, "I"), "Inpatient")
        self.assertEqual(
            edi_data.qualifier_label("hl7", "MSH", 9, "ADT"),
            "Admit/discharge/transfer")

    def test_unknown_code_returns_empty(self):
        self.assertEqual(edi_data.qualifier_label("edifact", "DTM", 1, "999"), "")
        self.assertEqual(edi_data.qualifier_label("x12", "NOPE", 1, "1"), "")

    def test_jsonc_embeds_decoded_qualifiers(self):
        text = "UNB+UNOC:3+A+B+200101:0000+1'DTM+137:20200101:102'UNZ+1+1'"
        out = edi_convert.to_jsonc(text)
        self.assertIn("[137 = Document/message date]", out)

    def test_xml_embeds_decoded_qualifiers(self):
        text = "UNB+UNOC:3+A+B+200101:0000+1'NAD+BY+123::9'UNZ+1+1'"
        root = ET.fromstring(edi_convert.to_xml(text))
        nad = [s for s in root.findall("segment") if s.get("tag") == "NAD"][0]
        self.assertEqual(nad.findall("element")[0].get("decoded"), "Buyer")


class ElementAtTests(unittest.TestCase):
    """F1: locating the element/component under an offset."""

    def test_edifact_positions(self):
        d = edi_core.Dialect.from_family("edifact")
        seg = edi_core.Segment("NAD+BY+5412345000013::9", d)
        self.assertEqual(edi_core.element_at(seg, 1), (0, 0))       # on tag
        self.assertEqual(edi_core.element_at(seg, 5), (1, 1))       # in BY
        self.assertEqual(edi_core.element_at(seg, 8), (2, 1))       # in id
        self.assertEqual(edi_core.element_at(seg, 22), (2, 3))      # in '9'

    def test_edifact_release_characters_do_not_count(self):
        d = edi_core.Dialect.from_family("edifact")
        seg = edi_core.Segment("FTX+AAI++X+a?+b+c", d)
        # 'c' is element 5 (AAI, '', X, 'a+b', c): the release-escaped '+'
        # inside element 4 must not advance the element counter.
        self.assertEqual(edi_core.element_at(seg, len(seg.content) - 1), (5, 1))
        # inside 'b' of the escaped element 4
        self.assertEqual(edi_core.element_at(seg, 14), (4, 1))

    def test_hl7_msh_numbering(self):
        d = edi_core.Dialect.from_family("hl7")
        seg = edi_core.Segment("MSH|^~\\&|SENDING|FAC", d)
        self.assertEqual(edi_core.element_at(seg, 5), (2, 1))    # encoding chars
        self.assertEqual(edi_core.element_at(seg, 10), (3, 1))   # SENDING

    def test_tradacoms_tag_separator(self):
        d = edi_core.Dialect.from_family("tradacoms")
        seg = edi_core.Segment("MHD=1+ORDHDR:9", d)
        self.assertEqual(edi_core.element_at(seg, 4), (1, 1))
        self.assertEqual(edi_core.element_at(seg, 7), (2, 1))
        self.assertEqual(edi_core.element_at(seg, 13), (2, 2))


class RawElementRoundTripTests(unittest.TestCase):
    """raw_elements + with_raw_elements must reproduce content exactly."""

    def test_round_trip_all_dialects(self):
        cases = [
            ("edifact", "NAD+BY+5412345000013::9"),
            ("edifact", "FTX+AAI++X+a?+b?'c"),
            ("edifact", "UNA:+.? "),
            ("x12", "N1*BY*ACME:DIV*92*001"),
            ("tradacoms", "MHD=1+ORDHDR:9"),
            ("hl7", "PID|1||12345^^^HOSP^MR||DOE^JOHN"),
        ]
        for family, content in cases:
            d = edi_core.Dialect.from_family(family)
            seg = edi_core.Segment(content, d)
            rebuilt = seg.with_raw_elements(seg.raw_elements())
            self.assertEqual(rebuilt, content, "family=%s" % family)


if __name__ == "__main__":
    unittest.main()
