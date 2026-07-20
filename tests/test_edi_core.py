# -*- coding: utf-8 -*-
"""Unit tests for the Sublime-independent EDI engine (``edi_core``).

Run from the package root with::

    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import edi_core  # noqa: E402


# Sample messages -----------------------------------------------------------

EDIFACT_MSG = (
    "UNA:+.? '"
    "UNB+UNOC:3+SENDER:14+RECEIVER:14+200101:1200+1'"
    "UNH+1+ORDERS:D:96A:UN:EAN008'"
    "BGM+220+PO12345+9'"
    "DTM+137:20200101:102'"
    "NAD+BY+5412345000013::9'"
    "UNT+6+1'"
    "UNZ+1+1'"
)

EDIFACT_NO_UNA = (
    "UNB+UNOC:3+A+B+200101:1200+1'"
    "UNH+1+ORDERS:D:96A:UN'"
    "BGM+220+PO1+9'"
    "UNT+3+1'"
    "UNZ+1+1'"
)

X12_MSG = (
    "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
    "*200101*1200*U*00401*000000001*0*P*:~"
    "GS*PO*SENDER*RECEIVER*20200101*1200*1*X*004010~"
    "ST*850*0001~"
    "BEG*00*NE*PO12345**20200101~"
    "SE*4*0001~"
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
    "PV1|1|I|WARD^101^1\r"
)


class DetectionTests(unittest.TestCase):

    def test_detect_edifact_with_una(self):
        d = edi_core.detect(EDIFACT_MSG)
        self.assertIsNotNone(d)
        self.assertEqual(d.family, "edifact")
        self.assertEqual(d.segment_terminator, "'")
        self.assertEqual(d.element_separator, "+")
        self.assertEqual(d.component_separator, ":")
        self.assertEqual(d.release_character, "?")

    def test_detect_edifact_without_una(self):
        d = edi_core.detect(EDIFACT_NO_UNA)
        self.assertEqual(d.family, "edifact")
        self.assertEqual(d.segment_terminator, "'")

    def test_detect_x12_delimiters_from_isa(self):
        d = edi_core.detect(X12_MSG)
        self.assertEqual(d.family, "x12")
        self.assertEqual(d.element_separator, "*")
        self.assertEqual(d.component_separator, ":")
        self.assertEqual(d.segment_terminator, "~")

    def test_detect_tradacoms(self):
        d = edi_core.detect(TRADACOMS_MSG)
        self.assertEqual(d.family, "tradacoms")
        self.assertEqual(d.tag_separator, "=")

    def test_detect_hl7_encoding_chars(self):
        d = edi_core.detect(HL7_MSG)
        self.assertEqual(d.family, "hl7")
        self.assertEqual(d.element_separator, "|")
        self.assertEqual(d.component_separator, "^")
        self.assertEqual(d.repetition_separator, "~")
        self.assertEqual(d.release_character, "\\")

    def test_detect_non_edi_returns_none(self):
        self.assertIsNone(edi_core.detect("hello world\nthis is not edi"))
        self.assertIsNone(edi_core.detect(""))


class SegmentSplittingTests(unittest.TestCase):

    def test_edifact_segment_count_and_tags(self):
        d = edi_core.detect(EDIFACT_MSG)
        segs = d.split_segments(EDIFACT_MSG)
        tags = [s.tag for s in segs]
        self.assertEqual(tags, ["UNA", "UNB", "UNH", "BGM", "DTM", "NAD", "UNT", "UNZ"])

    def test_release_character_not_treated_as_terminator(self):
        # ``?'`` is an escaped apostrophe and must NOT split the segment.
        text = "UNA:+.? 'BGM+abc?'def+9'UNT+1+1'"
        d = edi_core.detect(text)
        segs = d.split_segments(text)
        tags = [s.tag for s in segs]
        self.assertEqual(tags, ["UNA", "BGM", "UNT"])
        bgm = [s for s in segs if s.tag == "BGM"][0]
        self.assertIn("abc?'def", bgm.content)

    def test_x12_tags(self):
        d = edi_core.detect(X12_MSG)
        tags = [s.tag for s in d.split_segments(X12_MSG)]
        self.assertEqual(tags, ["ISA", "GS", "ST", "BEG", "SE", "GE", "IEA"])

    def test_tradacoms_tag_before_equals(self):
        d = edi_core.detect(TRADACOMS_MSG)
        tags = [s.tag for s in d.split_segments(TRADACOMS_MSG)]
        self.assertEqual(tags, ["STX", "MHD", "TYP", "MTR", "END"])

    def test_hl7_first_three_chars_are_tag(self):
        d = edi_core.detect(HL7_MSG)
        tags = [s.tag for s in d.split_segments(HL7_MSG)]
        self.assertEqual(tags, ["MSH", "EVN", "PID", "PV1"])

    def test_spans_map_back_to_text(self):
        d = edi_core.detect(EDIFACT_MSG)
        for start, end, seg in d.segment_spans(EDIFACT_MSG):
            self.assertEqual(EDIFACT_MSG[start:end], seg.content)


class BeautifyMinifyTests(unittest.TestCase):

    def test_beautify_puts_each_segment_on_its_own_line(self):
        out = edi_core.beautify(EDIFACT_MSG)
        lines = out.rstrip("\n").split("\n")
        self.assertEqual(len(lines), 8)
        self.assertTrue(lines[1].startswith("UNB"))
        self.assertTrue(lines[1].endswith("'"))

    def test_beautify_is_idempotent(self):
        once = edi_core.beautify(EDIFACT_MSG)
        twice = edi_core.beautify(once)
        self.assertEqual(once, twice)

    def test_minify_round_trips_edifact(self):
        beautified = edi_core.beautify(EDIFACT_MSG)
        minified = edi_core.minify(beautified)
        self.assertEqual(minified, EDIFACT_MSG)

    def test_minify_round_trips_x12(self):
        self.assertEqual(edi_core.minify(edi_core.beautify(X12_MSG)), X12_MSG)

    def test_beautify_hl7_uses_newlines(self):
        out = edi_core.beautify(HL7_MSG)
        self.assertNotIn("\r", out)
        self.assertEqual(len(out.rstrip("\n").split("\n")), 4)

    def test_minify_hl7_restores_carriage_returns(self):
        self.assertEqual(edi_core.minify(edi_core.beautify(HL7_MSG)), HL7_MSG)

    def test_beautify_non_edi_is_noop(self):
        text = "not edi at all"
        self.assertEqual(edi_core.beautify(text), text)


class DescribeTests(unittest.TestCase):

    def test_describe_edifact_names(self):
        described = dict((s.tag, name)
                         for s, name in edi_core.describe_segments(EDIFACT_MSG))
        self.assertEqual(described["UNH"], "Message Header")
        self.assertEqual(described["BGM"], "Beginning of Message")
        self.assertEqual(described["NAD"], "Name and Address")

    def test_describe_x12_names(self):
        described = dict((s.tag, name)
                         for s, name in edi_core.describe_segments(X12_MSG))
        self.assertEqual(described["ISA"], "Interchange Control Header")
        self.assertEqual(described["BEG"], "Beginning Segment for Purchase Order")

    def test_describe_hl7_names(self):
        described = dict((s.tag, name)
                         for s, name in edi_core.describe_segments(HL7_MSG))
        self.assertEqual(described["MSH"], "Message Header")
        self.assertEqual(described["PID"], "Patient Identification")

    def test_unknown_tag_has_empty_name(self):
        text = "UNA:+.? 'ZZZ+foo'"
        described = dict((s.tag, name)
                         for s, name in edi_core.describe_segments(text))
        self.assertEqual(described.get("ZZZ"), "")

    def test_describe_spans_align_with_text(self):
        for start, end, seg, _name in edi_core.describe_spans(X12_MSG):
            self.assertEqual(X12_MSG[start:end], seg.content)


class SubsetTests(unittest.TestCase):

    def test_eancom_resolves_to_edifact_family(self):
        d = edi_core.Dialect.from_family("eancom")
        self.assertEqual(d.family, "edifact")
        self.assertEqual(d.label, "EANCOM")
        self.assertEqual(d.segment_terminator, "'")

    def test_subset_segment_names_fall_back_to_edifact(self):
        from core import edi_data
        self.assertEqual(edi_data.segment_name("odette", "BGM"),
                         "Beginning of Message")


if __name__ == "__main__":
    unittest.main()
