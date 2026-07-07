# -*- coding: utf-8 -*-
"""
Static reference data for the SublimeEDI package.

This module contains, for every supported EDI dialect:

* ``DIALECTS``      -- default delimiter definitions used when a message does
                       not declare its own service string (UNA / ISA / MSH).
* ``SEGMENTS``      -- a mapping of ``segment tag -> human readable name`` for
                       each dialect, used to render the non-destructive
                       "hints" that describe every segment.

The tables intentionally cover the segments that appear in real world traffic
rather than the full standards (which run to hundreds of segments). Unknown
tags simply render without a hint, so the tables can grow over time without any
code changes.
"""

# ---------------------------------------------------------------------------
# Delimiter dialects
# ---------------------------------------------------------------------------
#
# Every dialect describes the *default* delimiters. Messages that carry a
# service string advertisement (EDIFACT ``UNA``, X12 ``ISA``, HL7 ``MSH``)
# override these at parse time -- see ``edi_core.py``.

DIALECTS = {
    "edifact": {
        "label": "EDIFACT",
        "segment_terminator": "'",
        "element_separator": "+",
        "component_separator": ":",
        "repetition_separator": "*",
        "release_character": "?",
        "decimal_mark": ".",
        "tag_separator": None,      # tag runs up to the first element separator
    },
    "x12": {
        "label": "X12",
        "segment_terminator": "~",
        "element_separator": "*",
        "component_separator": ":",
        "repetition_separator": "^",
        "release_character": None,  # X12 has no release/escape character
        "decimal_mark": ".",
        "tag_separator": None,
    },
    "tradacoms": {
        "label": "TRADACOMS",
        "segment_terminator": "'",
        "element_separator": "+",
        "component_separator": ":",
        "repetition_separator": None,
        "release_character": "?",
        "decimal_mark": ".",
        "tag_separator": "=",       # e.g. ``MHD=...`` -- tag ends at ``=``
    },
    "hl7": {
        "label": "HL7",
        "segment_terminator": "\r",  # segments are carriage-return delimited
        "element_separator": "|",
        "component_separator": "^",
        "repetition_separator": "~",
        "release_character": "\\",
        "decimal_mark": ".",
        "tag_separator": None,       # first 3 characters are the tag
    },
}

# EDIFACT subsets share the EDIFACT dialect (delimiters and service strings are
# identical); they exist so the correct label can be reported on detection and
# so dialect-specific segment tables can be layered on top over time.
EDIFACT_SUBSETS = {
    "eancom": "EANCOM",
    "odette": "ODETTE",
    "edigas": "EDIG@S",
    "iata": "IATA/PADIS",
}


# ---------------------------------------------------------------------------
# Segment name tables
# ---------------------------------------------------------------------------

# UN/EDIFACT service + common standard segments.
EDIFACT_SEGMENTS = {
    # -- Service segments -------------------------------------------------
    "UNA": "Service String Advice",
    "UNB": "Interchange Header",
    "UNZ": "Interchange Trailer",
    "UNG": "Functional Group Header",
    "UNE": "Functional Group Trailer",
    "UNH": "Message Header",
    "UNT": "Message Trailer",
    "UNS": "Section Control",
    "UNO": "Object Header",
    "UNP": "Object Trailer",
    # -- Frequently used data segments -----------------------------------
    "BGM": "Beginning of Message",
    "DTM": "Date/Time/Period",
    "PAI": "Payment Instructions",
    "ALI": "Additional Information",
    "IMD": "Item Description",
    "FTX": "Free Text",
    "LOC": "Place/Location Identification",
    "GIS": "General Indicator",
    "DGS": "Dangerous Goods",
    "GIR": "Related Identification Numbers",
    "RFF": "Reference",
    "NAD": "Name and Address",
    "CTA": "Contact Information",
    "COM": "Communication Contact",
    "FII": "Financial Institution Information",
    "CUX": "Currencies",
    "PAT": "Payment Terms Basis",
    "TDT": "Transport Information",
    "TOD": "Terms of Delivery or Transport",
    "TSR": "Transport Service Requirements",
    "PAC": "Package",
    "MEA": "Measurements",
    "QTY": "Quantity",
    "DIM": "Dimensions",
    "HAN": "Handling Instructions",
    "SGP": "Split Goods Placement",
    "LIN": "Line Item",
    "PIA": "Additional Product ID",
    "QVR": "Quantity Variances",
    "MOA": "Monetary Amount",
    "PRI": "Price Details",
    "APR": "Additional Price Information",
    "RNG": "Range Details",
    "TAX": "Duty/Tax/Fee Details",
    "PCD": "Percentage Details",
    "ALC": "Allowance or Charge",
    "PCI": "Package Identification",
    "GIN": "Goods Identity Number",
    "EQD": "Equipment Details",
    "SEL": "Seal Number",
    "CNI": "Consignment Information",
    "CNT": "Control Total",
    "STS": "Status",
    "DOC": "Document/Message Details",
    "AJT": "Adjustment Details",
    "INP": "Parties and Instruction",
    "PYT": "Payment Terms",
    "GEI": "Processing Information",
    "AGR": "Agreement Identification",
    "PGI": "Product Group Information",
    "EQN": "Number of Units",
    "MKS": "Market/Sales Channel Information",
    "SCC": "Scheduling Conditions",
    "LIB": "Library",
    "UGH": "Grouping Header",
    "UGT": "Grouping Trailer",
}

# Reuse the EDIFACT table for the EDIFACT subsets.
EANCOM_SEGMENTS = dict(EDIFACT_SEGMENTS)
ODETTE_SEGMENTS = dict(EDIFACT_SEGMENTS)
EDIGAS_SEGMENTS = dict(EDIFACT_SEGMENTS)
IATA_SEGMENTS = dict(EDIFACT_SEGMENTS)

# ANSI ASC X12 common segments.
X12_SEGMENTS = {
    # -- Envelope / control ----------------------------------------------
    "ISA": "Interchange Control Header",
    "IEA": "Interchange Control Trailer",
    "GS": "Functional Group Header",
    "GE": "Functional Group Trailer",
    "ST": "Transaction Set Header",
    "SE": "Transaction Set Trailer",
    "TA1": "Interchange Acknowledgment",
    # -- Common data segments --------------------------------------------
    "BEG": "Beginning Segment for Purchase Order",
    "BAK": "Beginning Segment for PO Acknowledgment",
    "BIG": "Beginning Segment for Invoice",
    "BSN": "Beginning Segment for Ship Notice",
    "BHT": "Beginning of Hierarchical Transaction",
    "GS1": "Additional Beginning Segment",
    "REF": "Reference Identification",
    "PER": "Administrative Communications Contact",
    "N1": "Name",
    "N2": "Additional Name Information",
    "N3": "Address Information",
    "N4": "Geographic Location",
    "DMG": "Demographic Information",
    "DTM": "Date/Time Reference",
    "FOB": "F.O.B. Related Instructions",
    "CSH": "Sales Requirements",
    "ITD": "Terms of Sale / Deferred Terms",
    "TD1": "Carrier Details (Quantity and Weight)",
    "TD3": "Carrier Details (Equipment)",
    "TD5": "Carrier Details (Routing Sequence)",
    "PO1": "Purchase Order Baseline Item Data",
    "POC": "Line Item Change",
    "PID": "Product/Item Description",
    "PO4": "Item Physical Details",
    "CTP": "Pricing Information",
    "SAC": "Service, Promotion, Allowance or Charge",
    "IT1": "Invoice Baseline Item Data",
    "TXI": "Tax Information",
    "CTT": "Transaction Totals",
    "AMT": "Monetary Amount",
    "QTY": "Quantity",
    "MEA": "Measurements",
    "LIN": "Item Identification",
    "SN1": "Item Detail (Shipment)",
    "SLN": "Subline Item Detail",
    "HL": "Hierarchical Level",
    "MAN": "Marks and Numbers",
    "PKG": "Marking, Packaging, Loading",
    "MSG": "Message Text",
    "NTE": "Note / Special Instruction",
    "ISS": "Invoice Shipment Summary",
    "TDS": "Total Monetary Value Summary",
    "CAD": "Carrier Detail",
    "PWK": "Paperwork",
    "LDT": "Lead Time",
    "SCH": "Line Item Schedule",
    "AK1": "Functional Group Response Header",
    "AK9": "Functional Group Response Trailer",
}

# TRADACOMS (UK retail) common segments.
TRADACOMS_SEGMENTS = {
    "STX": "Start of Transmission",
    "END": "End of Transmission",
    "MHD": "Message Header",
    "MTR": "Message Trailer",
    "TYP": "Transaction Type",
    "SDT": "Supplier Details",
    "CDT": "Customer Details",
    "FIL": "File Details",
    "DNA": "Data Narrative",
    "ORD": "Order References",
    "OLD": "Order Line Detail",
    "OTR": "Order Trailer",
    "CLO": "Customer's Location",
    "DIN": "Delivery Instructions",
    "ILD": "Invoice Line Detail",
    "IRF": "Invoice References",
    "STL": "Settlement Terms",
    "TLR": "Trailer",
    "PYT": "Payment Terms",
    "TDT": "Total Data",
    "ODD": "Order Delivery Details",
    "VATURN": "VAT Turnover",
}

# HL7 v2.x common segments.
HL7_SEGMENTS = {
    "MSH": "Message Header",
    "EVN": "Event Type",
    "PID": "Patient Identification",
    "PD1": "Patient Additional Demographic",
    "NK1": "Next of Kin / Associated Parties",
    "PV1": "Patient Visit",
    "PV2": "Patient Visit - Additional Info",
    "OBR": "Observation Request",
    "OBX": "Observation / Result",
    "ORC": "Common Order",
    "AL1": "Patient Allergy Information",
    "DG1": "Diagnosis",
    "PR1": "Procedures",
    "GT1": "Guarantor",
    "IN1": "Insurance",
    "IN2": "Insurance - Additional Info",
    "NTE": "Notes and Comments",
    "MSA": "Message Acknowledgment",
    "ERR": "Error",
    "QRD": "Query Definition",
    "QRF": "Query Filter",
    "SPM": "Specimen",
    "SCH": "Scheduling Activity Information",
    "FT1": "Financial Transaction",
    "RXA": "Pharmacy/Treatment Administration",
    "RXR": "Pharmacy/Treatment Route",
    "ROL": "Role",
    "ZDS": "Custom / Z-Segment",
}

# Master lookup: dialect key -> segment table.
SEGMENTS = {
    "edifact": EDIFACT_SEGMENTS,
    "eancom": EANCOM_SEGMENTS,
    "odette": ODETTE_SEGMENTS,
    "edigas": EDIGAS_SEGMENTS,
    "iata": IATA_SEGMENTS,
    "x12": X12_SEGMENTS,
    "tradacoms": TRADACOMS_SEGMENTS,
    "hl7": HL7_SEGMENTS,
}


def dialect_family(dialect_key):
    """Return the delimiter family for a dialect key.

    EDIFACT subsets (EANCOM, ODETTE, ...) all resolve to the ``edifact``
    delimiter definition.
    """
    if dialect_key in EDIFACT_SUBSETS or dialect_key == "edifact":
        return "edifact"
    return dialect_key


def segment_name(dialect_key, tag):
    """Look up a human readable name for ``tag`` within ``dialect_key``.

    Falls back to the base EDIFACT table for EDIFACT subsets and returns an
    empty string when the tag is unknown.
    """
    table = SEGMENTS.get(dialect_key)
    if table and tag in table:
        return table[tag]
    if dialect_key in EDIFACT_SUBSETS:
        return EDIFACT_SEGMENTS.get(tag, "")
    return ""
