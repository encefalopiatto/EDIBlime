# -*- coding: utf-8 -*-
"""Unit tests for JSON normalization (named elements, envelope nesting)."""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import edi_core  # noqa: E402
from core import edi_normalize  # noqa: E402


# A real-world style EANCOM SLSRPT (sales data report): one interchange, one
# message, two levels of segment groups (LOC -> LIN -> QTY).
SLSRPT_LINES = [
    (1, "4007399434498", "76", "108", "39.95"),
    (2, "4007399434498", "76", "108", "39.95"),
    (3, "4007399434498", "76", "118", "39.95"),
    (4, "4007399434511", "951", "118", "39.95"),
    (5, "4007399434511", "951", "118", "39.95"),
    (6, "4007399435389", "76", "118", "64.95"),
    (7, "4007399477372", "76", "108", "11.95"),
    (8, "4007399477372", "76", "108", "11.95"),
    (9, "4007399477631", "76", "118", "12.95"),
    (10, "4007399477631", "76", "118", "12.95"),
    (11, "4007399477631", "76", "119", "12.95"),
    (12, "4007399477631", "76", "119", "12.95"),
]

SLSRPT_MSG = (
    "UNA:+.? '"
    "UNB+UNOC:3+4260026610003:14+4007399000006:14+260707:2216+202607072582'"
    "UNH+1+SLSRPT:D:96A:UN:EAN004'"
    "BGM+73E::9+729058+9'"
    "DTM+137:20260708:102'"
    "DTM+90:20260707:102'"
    "DTM+91:20260707:102'"
    "NAD+BY+4260026610102::9'"
    "NAD+SU+4007399000006::9'"
    "CUX+2:EUR:10'"
    "LOC+162+4260026610102::9'"
    "DTM+90:20260707:102'"
    "DTM+91:20260707:102'"
    "DTM+356:20260707:102'"
    + "".join(
        "LIN+%d++%s:EN'RFF+SA:%s'RFF+SP:%s'PRI+AAE:%s::RTP'QTY+153:1:PCE'"
        % line for line in SLSRPT_LINES
    )
    + "UNT+73+1'"
    "UNZ+1+202607072582'"
)


def _dtm(qualifier, value, fmt):
    return {
        "date_time_period_C507": {
            "date_time_period_qualifier_2005": qualifier,
            "date_time_period_2380": value,
            "date_time_period_format_qualifier_2379": fmt,
        }
    }


def _nad(qualifier, party_id):
    return {
        "name_and_address_NAD": {
            "party_qualifier_3035": qualifier,
            "party_identification_details_C082": {
                "party_id_identification_3039": party_id,
                "code_list_responsible_agency_coded_3055": "9",
            },
        }
    }


def _lin_group(number, ean, sa, sp, price):
    return {
        "line_item_LIN": {
            "line_item_number_1082": str(number),
            "item_number_identification_C212": {
                "item_number_7140": ean,
                "item_number_type_coded_7143": "EN",
            },
        },
        "reference_RFF_list": [
            {"reference_C506": {"reference_qualifier_1153": "SA",
                                "reference_number_1154": sa}},
            {"reference_C506": {"reference_qualifier_1153": "SP",
                                "reference_number_1154": sp}},
        ],
        "price_details_PRI_list": [
            {"price_information_C509": {
                "price_qualifier_5125": "AAE",
                "price_5118": price,
                "price_type_qualifier_5387": "RTP",
            }}
        ],
        "quantity_QTY_groups": [
            {"quantity_QTY": {"quantity_details_C186": {
                "quantity_qualifier_6063": "153",
                "quantity_6060": "1",
                "measure_unit_qualifier_6411": "PCE",
            }}}
        ],
    }


SLSRPT_EXPECTED = {
    "payloads": [
        {
            "interchange_header_UNB": {
                "syntax_identifier_S001": {
                    "syntax_identifier_0001": "UNOC",
                    "syntax_version_number_0002": "3",
                },
                "interchange_sender_S002": {
                    "sender_identification_0004": "4260026610003",
                    "partner_identification_code_qualifier_0007": "14",
                },
                "interchange_recipient_S003": {
                    "recipient_identification_0010": "4007399000006",
                    "partner_identification_code_qualifier_0007": "14",
                },
                "date_time_of_preparation_S004": {
                    "date_of_preparation_0017": "260707",
                    "time_of_preparation_0019": "2216",
                },
                "interchange_control_reference_0020": "202607072582",
            },
            "messages": [
                {
                    "MESSAGE_TYPE": "SLSRPT",
                    "message_header_UNH": {
                        "message_reference_number_0062": "1",
                        "message_identifier_S009": {
                            "message_type_0065": "SLSRPT",
                            "message_version_number_0052": "D",
                            "message_release_number_0054": "96A",
                            "controlling_agency_0051": "UN",
                            "association_assigned_code_0057": "EAN004",
                        },
                    },
                    "beginning_of_message_BGM": {
                        "document_message_name_C002": {
                            "document_message_name_coded_1001": "73E",
                            "code_list_responsible_agency_coded_3055": "9",
                        },
                        "document_message_number_1004": "729058",
                        "message_function_coded_1225": "9",
                    },
                    "date_time_period_DTM_list": [
                        _dtm("137", "20260708", "102"),
                        _dtm("90", "20260707", "102"),
                        _dtm("91", "20260707", "102"),
                    ],
                    "name_and_address_NAD_groups": [
                        _nad("BY", "4260026610102"),
                        _nad("SU", "4007399000006"),
                    ],
                    "currencies_CUX_groups": [
                        {"currencies_CUX": {"currency_details_C504": {
                            "currency_details_qualifier_6347": "2",
                            "currency_coded_6345": "EUR",
                            "currency_qualifier_6343": "10",
                        }}}
                    ],
                    "place_location_identification_LOC_groups": [
                        {
                            "place_location_identification_LOC": {
                                "place_location_qualifier_3227": "162",
                                "location_identification_C517": {
                                    "place_location_identification_3225":
                                        "4260026610102",
                                    "code_list_responsible_agency_coded_3055":
                                        "9",
                                },
                            },
                            "date_time_period_DTM_list": [
                                _dtm("90", "20260707", "102"),
                                _dtm("91", "20260707", "102"),
                                _dtm("356", "20260707", "102"),
                            ],
                            "line_item_LIN_groups": [
                                _lin_group(*line) for line in SLSRPT_LINES
                            ],
                        }
                    ],
                    "message_trailer_UNT": {
                        "number_of_segments_in_the_message_0074": "73",
                        "message_reference_number_0062": "1",
                    },
                }
            ],
            "interchange_trailer_UNZ": {
                "interchange_control_count_0036": "1",
                "interchange_control_reference_0020": "202607072582",
            },
        }
    ],
    "context": {},
}


X12_MSG = (
    "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
    "*200101*1200*U*00401*000000001*0*P*:~"
    "GS*PO*SENDER*RECEIVER*20200101*1200*1*X*004010~"
    "ST*850*0001~"
    "BEG*00*NE*PO12345**20200101~"
    "REF*DP*038~"
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
)


class SlsrptAcceptanceTests(unittest.TestCase):
    """The full SLSRPT sample must normalize to the exact expected tree."""

    def test_exact_normalized_tree(self):
        self.assertEqual(edi_normalize.normalize(SLSRPT_MSG), SLSRPT_EXPECTED)

    def test_to_json_round_trips(self):
        out = edi_normalize.to_json(SLSRPT_MSG)
        self.assertEqual(json.loads(out), SLSRPT_EXPECTED)

    def test_beautified_input_normalizes_identically(self):
        pretty = edi_core.beautify(SLSRPT_MSG)
        self.assertEqual(edi_normalize.normalize(pretty), SLSRPT_EXPECTED)


class EdifactNormalizeTests(unittest.TestCase):

    def test_unknown_message_type_falls_back_to_flat_lists(self):
        text = (
            "UNB+UNOC:3+S:14+R:14+200101:1200+1'"
            "UNH+1+XXYYZ:D:96A:UN'"
            "BGM+220+1+9'"
            "DTM+137:20200101:102'"
            "UNT+4+1'"
            "UNZ+1+1'"
        )
        msg = edi_normalize.normalize(text)["payloads"][0]["messages"][0]
        self.assertEqual(msg["MESSAGE_TYPE"], "XXYYZ")
        # No structure table: every body segment becomes a _list entry.
        self.assertIn("beginning_of_message_BGM_list", msg)
        self.assertIn("date_time_period_DTM_list", msg)
        self.assertIn("message_trailer_UNT", msg)

    def test_unknown_segment_and_extra_elements_degrade(self):
        text = (
            "UNH+1+XXYYZ:D:96A:UN'"
            "ZZZ+A+B:C'"
            "UNT+3+1'"
        )
        msg = edi_normalize.normalize(text)["payloads"][0]["messages"][0]
        zzz = msg["zzz_ZZZ_list"][0]
        self.assertEqual(zzz["element_1"], "A")
        self.assertEqual(zzz["element_2"], ["B", "C"])

    def test_functional_groups_nest_between_unb_and_unz(self):
        text = (
            "UNB+UNOC:3+S:14+R:14+200101:1200+1'"
            "UNG+ORDERS+SAPP:1+RAPP:1+200101:1200+77+UN+D:96A'"
            "UNH+1+ORDERS:D:96A:UN'"
            "BGM+220+PO1+9'"
            "UNT+3+1'"
            "UNE+1+77'"
            "UNZ+1+1'"
        )
        payload = edi_normalize.normalize(text)["payloads"][0]
        self.assertNotIn("messages", payload)
        group = payload["functional_groups"][0]
        header = group["functional_group_header_UNG"]
        self.assertEqual(header["functional_group_identification_0038"],
                         "ORDERS")
        self.assertEqual(
            header["application_senders_identification_S006"]
            ["application_sender_identification_0040"], "SAPP")
        self.assertEqual(group["messages"][0]["MESSAGE_TYPE"], "ORDERS")
        self.assertEqual(
            group["functional_group_trailer_UNE"]["number_of_messages_0060"],
            "1")

    def test_multiple_interchanges_become_multiple_payloads(self):
        one = (
            "UNB+UNOC:3+S:14+R:14+200101:1200+%s'"
            "UNH+1+XXYYZ:D:96A:UN'UNT+2+1'"
            "UNZ+1+%s'"
        )
        payloads = edi_normalize.normalize(one % (1, 1) + one % (2, 2))["payloads"]
        self.assertEqual(len(payloads), 2)
        for n, payload in enumerate(payloads, start=1):
            self.assertEqual(
                payload["interchange_trailer_UNZ"]
                ["interchange_control_reference_0020"], str(n))

    def test_stray_segment_collected_not_dropped(self):
        text = (
            "UNB+UNOC:3+S:14+R:14+200101:1200+1'"
            "FTX+AAI'"
            "UNZ+0+1'"
        )
        payload = edi_normalize.normalize(text)["payloads"][0]
        self.assertEqual(payload["unparsed_segments"], ["FTX+AAI"])

    def test_release_characters_are_decoded(self):
        text = (
            "UNA:+.? '"
            "UNH+1+XXYYZ:D:96A:UN'"
            "FTX+AAI++ABC+Plus ?+ and quote ?''"
            "UNT+3+1'"
        )
        msg = edi_normalize.normalize(text)["payloads"][0]["messages"][0]
        ftx = msg["free_text_FTX_list"][0]
        self.assertEqual(ftx["text_literal_C108"]["free_text_4440"],
                         "Plus + and quote '")

    def test_orders_line_items_group(self):
        text = (
            "UNB+UNOC:3+S:14+R:14+200101:1200+1'"
            "UNH+1+ORDERS:D:96A:UN:EAN008'"
            "BGM+220+PO12345+9'"
            "DTM+137:20200101:102'"
            "NAD+BY+5412345000013::9'"
            "NAD+SU+4012345500004::9'"
            "LIN+1++4000862141404:EN'"
            "QTY+21:48'"
            "LIN+2++4000862141405:EN'"
            "QTY+21:24'"
            "UNS+S'"
            "CNT+2:2'"
            "UNT+12+1'"
            "UNZ+1+1'"
        )
        msg = edi_normalize.normalize(text)["payloads"][0]["messages"][0]
        lines = msg["line_item_LIN_groups"]
        self.assertEqual(len(lines), 2)
        self.assertEqual(
            lines[0]["line_item_LIN"]["item_number_identification_C212"]
            ["item_number_7140"], "4000862141404")
        # In ORDERS (unlike SLSRPT) QTY is a plain repeatable segment of the
        # LIN group, not a group trigger.
        self.assertEqual(
            lines[1]["quantity_QTY_list"][0]
            ["quantity_details_C186"]["quantity_6060"], "24")
        self.assertEqual(msg["section_control_UNS"]
                         ["section_identification_0081"], "S")
        self.assertEqual(msg["control_total_CNT_list"][0]
                         ["control_C270"]["control_qualifier_6069"], "2")


class X12NormalizeTests(unittest.TestCase):

    def test_envelope_nesting_and_names(self):
        payload = edi_normalize.normalize(X12_MSG)["payloads"][0]
        isa = payload["interchange_control_header_ISA"]
        self.assertEqual(isa["interchange_sender_id_06"], "SENDER         ")
        self.assertEqual(isa["interchange_control_number_13"], "000000001")
        group = payload["functional_groups"][0]
        self.assertEqual(
            group["functional_group_header_GS"]
            ["functional_identifier_code_01"], "PO")
        message = group["messages"][0]
        self.assertEqual(message["MESSAGE_TYPE"], "850")
        self.assertEqual(
            message["transaction_set_header_ST"]
            ["transaction_set_identifier_code_01"], "850")
        self.assertEqual(
            message["transaction_set_trailer_SE"]
            ["number_of_included_segments_01"], "4")
        self.assertEqual(
            payload["interchange_control_trailer_IEA"]
            ["interchange_control_number_02"], "000000001")

    def test_body_segments_use_named_positions(self):
        message = edi_normalize.normalize(X12_MSG)["payloads"][0][
            "functional_groups"][0]["messages"][0]
        beg = message["beginning_segment_for_purchase_order_BEG_list"][0]
        self.assertEqual(beg["transaction_set_purpose_code_01"], "00")
        self.assertEqual(beg["purchase_order_number_03"], "PO12345")
        self.assertNotIn("release_number_04", beg)  # empty element omitted
        ref = message["reference_identification_REF_list"][0]
        self.assertEqual(ref["reference_identification_qualifier_01"], "DP")


class TradacomsNormalizeTests(unittest.TestCase):

    def test_envelope_and_message_nesting(self):
        payload = edi_normalize.normalize(TRADACOMS_MSG)["payloads"][0]
        stx = payload["start_of_transmission_STX"]
        self.assertEqual(
            stx["syntax_rules_identifier_01"]["syntax_rules_identifier"],
            "ANAA")
        self.assertEqual(
            stx["identity_of_transmission_sender_02"]["senders_ana_code"],
            "SENDER")
        message = payload["messages"][0]
        self.assertEqual(message["MESSAGE_TYPE"], "ORDHDR")
        mhd = message["message_header_MHD"]
        self.assertEqual(mhd["message_reference_01"], "1")
        self.assertEqual(mhd["type_of_message_02"]["message_type"], "ORDHDR")
        self.assertEqual(
            message["message_trailer_MTR"]["number_of_segments_in_message_01"],
            "3")
        self.assertEqual(
            payload["end_of_transmission_END"]
            ["number_of_messages_in_transmission_01"], "1")


class Hl7NormalizeTests(unittest.TestCase):

    def test_message_type_and_named_fields(self):
        payload = edi_normalize.normalize(HL7_MSG)["payloads"][0]
        message = payload["messages"][0]
        self.assertEqual(message["MESSAGE_TYPE"], "ADT_A01")
        msh = message["message_header_MSH"]
        self.assertEqual(msh["field_separator_1"], "|")
        self.assertEqual(msh["encoding_characters_2"], "^~\\&")
        self.assertEqual(msh["sending_application_3"], "SENDING")
        self.assertEqual(msh["message_type_9"], ["ADT", "A01"])
        pid = message["patient_identification_PID_list"][0]
        self.assertEqual(pid["patient_name_5"], ["DOE", "JOHN"])


class RobustnessTests(unittest.TestCase):

    def test_non_edi_raises(self):
        with self.assertRaises(ValueError):
            edi_normalize.normalize("definitely not edi")

    def test_message_without_interchange_still_normalizes(self):
        text = "UNH+1+XXYYZ:D:96A:UN'BGM+220+1+9'UNT+3+1'"
        payloads = edi_normalize.normalize(text)["payloads"]
        self.assertEqual(payloads[0]["messages"][0]["MESSAGE_TYPE"], "XXYYZ")

    def test_missing_unt_message_is_flushed(self):
        text = "UNB+UNOC:3+S:14+R:14+200101:1200+1'UNH+1+XXYYZ:D:96A:UN'BGM+220+1+9'"
        payloads = edi_normalize.normalize(text)["payloads"]
        msg = payloads[0]["messages"][0]
        self.assertIn("beginning_of_message_BGM_list", msg)
        self.assertNotIn("message_trailer_UNT", msg)


if __name__ == "__main__":
    unittest.main()
