# -*- coding: utf-8 -*-
"""
Static reference data for the EDIBlime package.

This module contains, for every supported EDI dialect:

* ``DIALECTS``        -- default delimiter definitions used when a message does
                         not declare its own service string (UNA / ISA / MSH).
* ``SEGMENTS``        -- ``segment tag -> short human readable name``, used for
                         the inline hint annotations.
* ``SEGMENT_DETAILS`` -- ``segment tag -> full description`` explaining what the
                         segment means and does; used by hover popups, the
                         "Explain Segment" command and JSONC conversion.
* ``ELEMENT_NAMES``   -- positional element names for well-known segments; used
                         to break a segment down element-by-element.

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
# Segment name tables (short names for inline hints)
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
    "AK2": "Transaction Set Response Header",
    "AK5": "Transaction Set Response Trailer",
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
    "ODD": "Order and Delivery Details",
    "STL": "Sub-Total (per VAT rate)",
    "TLR": "Invoice Trailer",
    "PYT": "Payment Terms",
    "VRS": "VAT Rate Summary",
    "TOT": "File Totals",
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


# ---------------------------------------------------------------------------
# Detailed segment descriptions ("what does this segment mean and do?")
# ---------------------------------------------------------------------------

EDIFACT_DETAILS = {
    "UNA": "Defines the six service characters used throughout the interchange, in fixed order: component separator, element separator, decimal mark, release (escape) character, reserved, segment terminator. Optional; when present it must be the very first characters of the interchange.",
    "UNB": "Opens the interchange. Carries the syntax identifier and version (e.g. UNOC:3), the sender and recipient identifications with their code qualifiers, the preparation date and time, and the interchange control reference that must be repeated in UNZ.",
    "UNZ": "Closes the interchange. Carries the count of messages (or functional groups) contained in the interchange and repeats the control reference from UNB, allowing the receiver to verify that nothing was lost in transit.",
    "UNG": "Opens a functional group of messages of the same type inside an interchange (rarely used in Western European traffic). Mirrors UNB at group level and is closed by UNE.",
    "UNE": "Closes a functional group. Carries the number of messages in the group and repeats the group reference number from UNG.",
    "UNH": "Opens a single message. Carries a unique message reference number (repeated in UNT) and the message identifier: type, version, release and controlling agency, e.g. ORDERS:D:96A:UN — an ORDERS message of directory D.96A.",
    "UNT": "Closes a message. Carries the total number of segments in the message (counting UNH and UNT themselves) and repeats the message reference number from UNH, allowing integrity checking.",
    "UNS": "Separates the sections of a message: UNS+D marks the start of the detail section, UNS+S the start of the summary section. Used where the same segment types may appear in more than one section.",
    "UNO": "Opens a package of binary or external data (an object) transmitted inside the interchange. Closed by UNP.",
    "UNP": "Closes a data object opened by UNO and carries its length and reference for verification.",
    "BGM": "Identifies the purpose of the whole message: the document/message type code (e.g. 220 = purchase order, 380 = commercial invoice, 351 = despatch advice), the document number assigned by the sender, and the message function code (e.g. 9 = original, 5 = replacement, 1 = cancellation).",
    "DTM": "Communicates a date, time or period, qualified by a function code: 137 = document date, 2 = requested delivery date, 35 = actual delivery date, 63/64 = latest/earliest delivery. The last component is the format code, e.g. 102 = CCYYMMDD, 203 = CCYYMMDDHHMM.",
    "PAI": "Specifies how payment will be made: payment conditions, guarantee and means (e.g. 42 = bank transfer, 20 = cheque).",
    "ALI": "Gives additional item information such as country of origin, customs regime or special condition codes (e.g. returnable, promotion).",
    "IMD": "Describes a line item either in coded form or free text: format code (C = coded, F = free-form), the description code or text, and the agency responsible for the code list.",
    "FTX": "Carries free text for the whole message or the current line: a subject qualifier (e.g. AAI = general information, DEL = delivery note text), a function code, optionally a coded text reference, and up to five lines of literal text.",
    "LOC": "Identifies a place or location relevant to the message, qualified by function: 7 = place of delivery, 9 = place of loading, 11 = place of discharge. The location itself may be a coded identifier (e.g. a GLN or UN/LOCODE) or a name.",
    "GIS": "Carries a general processing indicator that tells the receiver how to process the message (legacy segment, replaced by GEI in later directories).",
    "DGS": "Declares dangerous goods: regulation code (e.g. IMD = IMDG), hazard class, UN number, packing group and shipment flashpoint.",
    "GIR": "Groups related identification numbers for one item, e.g. serial numbers, batch numbers or equipment numbers, each with a type qualifier.",
    "RFF": "References another document or number, qualified by type: ON = buyer's order number, IV = invoice number, DQ = delivery note number, CT = contract number, AAK = despatch advice number. Usually followed by a DTM carrying the referenced document's date.",
    "NAD": "Identifies a party by role and address. The first element is the party qualifier: BY = buyer, SU = supplier, DP = delivery party, IV = invoice party, SF = ship from. The party is given as a coded identification (typically a GLN with qualifier 9) and/or a structured name and address.",
    "CTA": "Names a department or person that serves as a contact for the party in the preceding NAD, qualified by function (e.g. OC = order contact, AD = accounting).",
    "COM": "Gives a communication number for the preceding contact: the number or address plus a channel qualifier, e.g. TE = telephone, EM = e-mail, FX = fax.",
    "FII": "Identifies a financial institution and account: account holder number (e.g. IBAN), institution name/code (e.g. BIC) — typically the beneficiary's bank in payment or invoice messages.",
    "CUX": "Establishes the currencies used in the message: a reference currency and optionally a target currency with the applicable exchange rate, e.g. 2:EUR:9 = EUR is the invoicing currency.",
    "PAT": "States the payment terms basis: terms type (e.g. 1 = basic, 22 = cash discount), and the reference date plus number of days on which the terms are based (superseded by PYT in later directories).",
    "PYT": "States the payment terms: terms type qualifier, and how the payment period is computed (reference date code and number of days).",
    "TDT": "Specifies transport details for a stage of the journey: stage qualifier (e.g. 20 = main carriage), conveyance reference, mode of transport (e.g. 30 = road), carrier identification and means of transport identity.",
    "TOD": "States the delivery or transport terms, usually as an Incoterm: function code, service level and terms code, e.g. CIF, DDP, EXW.",
    "TSR": "States contract, carriage and service conditions for the transport, e.g. priority or pre-carriage requirements.",
    "PAC": "Describes the packages: number of packages, handling code, and package type (e.g. CT = carton, PX = pallet).",
    "MEA": "Communicates a physical measurement, qualified by purpose and dimension: e.g. AAE = measurement, WT = gross weight, VOL = volume, with value and unit (KGM, MTQ, ...).",
    "QTY": "States a quantity, qualified by type: 21 = ordered quantity, 12 = despatched quantity, 46 = delivered quantity, 47 = invoiced quantity, 59 = consumer units in the traded unit. The optional third component is the measurement unit.",
    "DIM": "Gives the dimensions (length, width, height and unit) of the package or piece of equipment referenced by the preceding segment.",
    "HAN": "Specifies how the goods must be handled and, where relevant, hazardous material classes, e.g. keep frozen, fragile.",
    "SGP": "Places (part of) a line item's goods into a specific piece of transport equipment, linking split consignments to containers.",
    "LIN": "Starts a new line item: the line number, an optional action code (e.g. 1 = added) and the main item identification — typically a GTIN with code type EN (EAN) or UP (UPC). All segments that follow until the next LIN describe this line.",
    "PIA": "Adds further identifications for the current line item, e.g. 1 = additional identification, 5 = product identification: the buyer's article number (BP/IN), the supplier's article number (SA), HS/customs codes, etc.",
    "QVR": "Explains a variance between ordered and delivered/invoiced quantity: the variance amount and a reason code (e.g. BP = shipment partial, AA = out of stock).",
    "MOA": "States a monetary amount, qualified by type: 77 = invoice amount, 79 = total line items amount, 66 = goods item total, 124 = tax amount, 203 = line item amount. The optional third component carries the currency.",
    "PRI": "States a price for the current line: qualifier (AAA = net unit price, AAB = gross unit price), the price value, price type, and the unit price basis with its measurement unit (e.g. per 100 pieces).",
    "APR": "Gives additional price information such as price multipliers, mark-ups or trade class rates.",
    "RNG": "Defines a range (minimum and maximum) that qualifies the preceding segment, e.g. an allowance valid for a quantity range.",
    "TAX": "Specifies duty, tax or fee details: function (7 = tax), type (VAT), rate or amount, and the tax category (e.g. S = standard rate, Z = zero rated, E = exempt). Amounts usually follow in MOA+124.",
    "PCD": "States a percentage, qualified by purpose: 1 = allowance, 2 = charge, 3 = discount, 12 = basis for allowance/charge calculation.",
    "ALC": "Introduces an allowance (A) or charge (C) that applies to the message or line: sequence and calculation information plus the reason code (e.g. FC = freight charge, DI = discount). Details follow in PCD (percentage), MOA (amount) or RTE (rate).",
    "PCI": "Specifies how packages are marked: marking instruction code and the actual marks and numbers on the packages.",
    "GIN": "Carries goods identity numbers, qualified by type: BJ = SSCC (serial shipping container code), BX = batch number, SN = serial number. Ranges may be given as pairs.",
    "EQD": "Identifies a piece of transport equipment: equipment qualifier (e.g. CN = container), identification number, size/type code, and full/empty indicator.",
    "SEL": "Carries a seal number that secures the equipment or package, with the party that affixed the seal.",
    "CNI": "Identifies a consignment within the transport details of the message, linking it to its documents.",
    "CNT": "Carries a control total for verification, qualified by type: 1 = total quantity, 2 = number of line items in the message. Receivers compare it against what they actually parsed.",
    "STS": "Reports a status event, e.g. transport status or the processing status of a referenced document, with reason codes.",
    "DOC": "Identifies documents required for, or referenced by, the transaction: document code, number of copies and originals required.",
    "AJT": "Gives the reason code for an adjustment made to an amount, e.g. in remittance advice or invoice list messages.",
    "INP": "Instructs a party to perform an action: which party gives the instruction, which party executes it, and the instruction code itself.",
    "GEI": "Carries a general processing indicator group that qualifies how the message data is to be processed (successor of GIS).",
    "AGR": "Identifies the agreement or contract (type and number) under which the transaction takes place.",
    "PGI": "Identifies a product group, price group or promotional grouping that the following line items belong to.",
    "EQN": "States a number of units, e.g. how many pieces of equipment or how many identical packages the preceding segment describes.",
    "MKS": "Identifies the market (geographic area, sales channel or distribution branch) to which the transaction applies.",
    "SCC": "Establishes a delivery schedule pattern: status (e.g. 1 = firm), and the pattern type and timing used by delivery forecast messages.",
}

X12_DETAILS = {
    "ISA": "Opens the interchange. A fixed-width 106-character segment: authorization and security information, sender and receiver IDs with qualifiers (e.g. ZZ = mutually defined, 01 = DUNS), date/time, repetition separator, control version, the interchange control number (repeated in IEA), acknowledgment request flag, usage indicator (P = production, T = test) and — as its final data element — the component separator. Its last character defines the segment terminator.",
    "IEA": "Closes the interchange. Carries the number of functional groups included and repeats the interchange control number from ISA13 so the receiver can verify integrity.",
    "GS": "Opens a functional group of related transaction sets. Carries the functional identifier code (PO = purchase orders, IN = invoices, SH = ship notices, FA = functional acknowledgments), application sender's and receiver's codes, date/time, the group control number (repeated in GE), the responsible agency and the version/release (e.g. 004010).",
    "GE": "Closes a functional group. Carries the number of transaction sets included and repeats the group control number from GS06.",
    "ST": "Opens a transaction set (one business document). Carries the transaction set identifier code (850 = purchase order, 810 = invoice, 856 = ship notice, 997 = functional acknowledgment) and a control number repeated in SE02.",
    "SE": "Closes a transaction set. Carries the number of segments in the set (counting ST and SE themselves) and repeats the control number from ST02, allowing integrity checking.",
    "TA1": "Interchange-level acknowledgment: reports whether a received interchange envelope (identified by its control number, date and time) was accepted, accepted with errors, or rejected, with a note code giving the reason.",
    "BEG": "Begins an 850 purchase order: transaction set purpose (00 = original, 01 = cancellation), purchase order type (NE = new order, SA = stand-alone), the purchase order number and the order date.",
    "BAK": "Begins an 855 purchase order acknowledgment: purpose code, acknowledgment type (AC = acknowledge with detail, AD = acknowledge with detail and change), the original PO number and its date.",
    "BIG": "Begins an 810 invoice: invoice date and invoice number, plus the purchase order date and number the invoice refers to, and the transaction type code.",
    "BSN": "Begins an 856 ship notice/manifest: purpose code, the shipment identification number, date and time of the notice, and the hierarchical structure code describing how the HL loops are organised (e.g. 0001 = shipment/order/pack/item).",
    "BHT": "Begins a hierarchical transaction (270/271 eligibility, 837 claims, ...): the hierarchical structure code, transaction purpose, a reference identification, and the creation date/time.",
    "REF": "Carries a reference number, qualified by type: DP = department number, IA = internal vendor number, BM = bill of lading, PO = purchase order number, VN = vendor order number.",
    "PER": "Names an administrative contact person or department (qualifier, e.g. BD = buyer, IC = information contact) together with up to three communication numbers, each preceded by a qualifier (TE = telephone, EM = e-mail).",
    "N1": "Starts a party loop: entity identifier code (ST = ship to, BT = bill to, SF = ship from, VN = vendor, BY = buying party), the party's name, and/or a coded identification (92 = assigned by buyer, UL = GLN, 1 = DUNS). N2/N3/N4 complete the address.",
    "N2": "Continues the party's name from N1 when it does not fit into a single element.",
    "N3": "Gives the party's street address (one or two address lines).",
    "N4": "Completes the party's address with city, state/province code, postal code and country code.",
    "DMG": "Carries demographic information, typically for healthcare transactions: date of birth (with format qualifier), gender code and marital status.",
    "DTM": "Communicates a date and/or time, qualified by function: 002 = requested delivery, 010 = requested ship, 011 = shipped, 035 = delivered, 036 = expiration.",
    "FOB": "States the shipment method of payment (who pays the freight): e.g. PP = prepaid, CC = collect, plus the location where responsibility transfers.",
    "CSH": "States header-level sales requirements, e.g. SC = ship complete, N = no back order.",
    "ITD": "States the terms of sale: terms type (e.g. 01 = basic, 08 = basic discount), discount percent, discount due date/days, and net due date/days — e.g. 2% 10 net 30.",
    "TD1": "Describes what is being shipped at carrier level: packaging code (e.g. CTN25), lading quantity, weight qualifier, gross weight and unit.",
    "TD3": "Identifies the transport equipment: equipment description code (e.g. TL = trailer), equipment number and ownership.",
    "TD5": "Describes the routing: routing sequence code, carrier identification (usually a SCAC code with qualifier 2), transportation method (M = motor, R = rail, A = air) and service level.",
    "PO1": "One purchase order line: assigned line number, quantity ordered, unit of measure, unit price and price basis, followed by repeating pairs of product ID qualifier and number — UP = UPC, VN = vendor part number, BP = buyer part number, EN = EAN/GTIN.",
    "POC": "One line of an 860 purchase order change: line reference, change type code (e.g. QI = quantity increase, DI = delete item), original and new quantities, and the item identification pairs.",
    "PID": "Describes the product: description type (F = free-form, S = structured), and the description text or code.",
    "PO4": "Gives the item's physical details: pack size (units per inner pack), inner packs per outer pack, and the packaging unit of measure.",
    "CTP": "Carries pricing information beyond the baseline price: price qualifier (e.g. RTL = retail, LPR = list), unit price and basis.",
    "SAC": "Details a service, promotion, allowance or charge: indicator (A = allowance, C = charge, N = no allowance or charge), the type code (e.g. F050 = other), the amount or percentage, and how it is handled (e.g. 06 = charge to be paid by customer).",
    "IT1": "One invoice line of an 810: assigned identification, quantity invoiced, unit of measure, unit price and basis, followed by repeating product ID qualifier/number pairs.",
    "TXI": "Carries tax information: tax type (e.g. ST = state sales tax, VA = VAT), amount or percentage, and jurisdiction codes.",
    "CTT": "Closes the detail area with transaction totals: the number of line items, and optionally a hash total of quantities that the receiver can verify against the parsed lines.",
    "AMT": "Carries a monetary amount qualified by type, e.g. TT = total transaction amount, BAP = amount prior to adjustment.",
    "QTY": "Carries a quantity qualified by type, e.g. 38 = original quantity, QT = quantity on hand.",
    "MEA": "Carries a measurement: reference code, dimension qualifier (WT = weight, HT = height), value and unit.",
    "LIN": "Identifies an item with repeating pairs of ID qualifier and number (UP = UPC, VN = vendor part, LT = lot number) — used in 856 item loops and other transactions instead of PO1.",
    "SN1": "Item detail for a shipment (856): units shipped, unit of measure, and quantities ordered/backordered for reconciliation.",
    "SLN": "Describes a subline of the current line item, e.g. the components of a kit, with its own quantity and price.",
    "HL": "Structures an 856 (and other hierarchical transactions) into nested loops: each HL has an ID, a parent ID and a level code — S = shipment, O = order, P = pack, I = item. All following segments belong to this level until the next HL.",
    "MAN": "Carries marks and numbers, most importantly the SSCC-18 license plate of a pallet or carton (qualifier GM), linking physical packages to the ASN data.",
    "PKG": "Describes marking, packaging and loading requirements for the item or shipment.",
    "MSG": "Carries free-form message text at the position it appears.",
    "NTE": "Carries a free-form note or special instruction that applies to the whole transaction set.",
    "ISS": "Summarises an invoice's shipment: number of units shipped, weight and volume — used for reconciliation at summary level.",
    "TDS": "States the total invoice amount (in the lowest currency denomination, e.g. cents): the amount the receiver is expected to pay before terms discounts.",
    "CAD": "Identifies the carrier at summary/detail level: transportation method, equipment, SCAC code and routing.",
    "PWK": "Identifies paperwork or supporting documentation that accompanies the transaction, and how it is transmitted.",
    "LDT": "States a lead time: qualifier, quantity and unit of time periods — e.g. delivery lead time after order receipt.",
    "SCH": "Schedules part of a PO1 line: quantity, unit, date qualifier and date — used when one order line has several delivery dates.",
    "AK1": "Starts a 997 functional acknowledgment: identifies the functional group being acknowledged by its functional ID code and group control number.",
    "AK2": "Identifies one transaction set within the acknowledged group, by its transaction set ID and control number.",
    "AK5": "Reports the acknowledgment status of the transaction set identified by AK2: A = accepted, R = rejected, E = accepted with errors, plus error codes.",
    "AK9": "Closes the 997: overall group status (A/P/R), the number of transaction sets included, received, and accepted.",
}

TRADACOMS_DETAILS = {
    "STX": "Opens the transmission. Carries the syntax identifier and version (ANA:1 or ANAA:1), the sender's and recipient's ANA codes (with optional names), the transmission date and time, the sender's transmission reference, and optionally the recipient's reference and application code.",
    "END": "Closes the transmission. Carries the total number of messages transmitted, allowing the receiver to check that no message was lost.",
    "MHD": "Opens one message within the transmission. Carries the message sequence number (starting at 1 and incrementing) and the message type with its version, e.g. ORDHDR:9 = order file header, ORDERS:9 = order detail, INVFIL:9 = invoice file header.",
    "MTR": "Closes the current message. Carries the total number of segments in the message, counting MHD and MTR themselves.",
    "TYP": "States the transaction code and description that classifies the whole file, e.g. 0430 = new orders, 0700 = invoices.",
    "SDT": "Identifies the supplier: ANA location code (and/or supplier's own code) plus name and address details, and the supplier's VAT registration number.",
    "CDT": "Identifies the customer: ANA location code (and/or customer's own code) plus name and address details, and the customer's VAT registration number.",
    "FIL": "Carries the file details: file generation number (incremented for every file exchanged between the two parties), file version number and the file creation date — the receiver uses the generation number to detect missing or duplicate files.",
    "DNA": "Carries data narrative: coded narrative and/or free text that applies to the surrounding message.",
    "ORD": "Carries the order references: the customer's order number, the supplier's order number and the date the order was placed.",
    "OLD": "One order line: line number, product codes (supplier's code, and the consumer unit EAN or traded unit code), the quantity ordered with its unit, the cost price, and the product description.",
    "OTR": "Closes the order message with the total number of order lines, for verification.",
    "CLO": "Identifies the customer's location the order/delivery relates to: ANA location code and/or the customer's own location code, plus name and address.",
    "DIN": "Carries the delivery instructions: earliest and latest delivery dates and any special delivery instructions narrative.",
    "ILD": "One invoice line: line number, product codes (EAN/supplier's), the invoiced quantity, unit cost price exclusive of VAT, VAT rate category, line total, and description.",
    "IRF": "Carries the invoice references: invoice number, invoice date and tax point date — the date on which VAT becomes chargeable.",
    "ODD": "Within an invoice, references the order and delivery the invoice line relates to: order number and date, delivery note number and date.",
    "STL": "Sub-totals the invoice per VAT rate category: number of lines, goods total, settlement discount, and the VAT-able amount at this rate — one STL per distinct VAT rate.",
    "TLR": "Closes the invoice with its grand totals: total goods value, total VAT and the total amount payable.",
    "PYT": "States the settlement/payment terms: terms description and settlement discount percentage the customer may deduct for prompt payment.",
    "VRS": "Summarises one VAT rate across the whole invoice file (in the VATTLR message): rate, number of invoices, goods total, VAT amount and payable amount at this rate.",
    "TOT": "Carries the grand totals for the whole file (in the file trailer message): total goods value, total VAT and total payable across all invoices.",
}

HL7_DETAILS = {
    "MSH": "Opens every HL7 message. MSH-1 is the field separator itself and MSH-2 the four encoding characters (component ^, repetition ~, escape \\, subcomponent &). Then: sending/receiving application and facility, message date/time, the message type and trigger event (e.g. ADT^A01 = patient admit), a unique message control ID (echoed in acknowledgments), processing ID (P = production, T = training) and the HL7 version.",
    "EVN": "Describes the trigger event: event type code, the date/time the event occurred, and the operator who recorded it.",
    "PID": "Identifies the patient: patient identifier list (each ID with assigning authority and type, e.g. MR = medical record number), name (family^given), date of birth, administrative sex, race, address, phone numbers, and account number.",
    "PD1": "Carries additional patient demographics: primary care provider, patient living arrangement and publicity/protection indicators.",
    "NK1": "Identifies the patient's next of kin or another associated party: name, relationship code (SPO = spouse, FTH = father), address and contact numbers. Repeats for each party.",
    "PV1": "Describes the patient visit: patient class (I = inpatient, O = outpatient, E = emergency), assigned location (ward^room^bed), attending/referring/consulting doctors, hospital service, admit source, and admit/discharge date-times.",
    "PV2": "Continues the visit description: expected admit/discharge dates, accommodation code, visit reason and estimated length of stay.",
    "OBR": "Requests an observation/study or heads a result report: placer and filler order numbers, the universal service identifier (what was ordered, e.g. a lab panel), observation date/time, ordering provider, and result status.",
    "OBX": "Carries one observation result: set ID, the value type (NM = numeric, ST = string, CE = coded), the observation identifier (what was measured, e.g. a LOINC code), the value itself, units, reference range, abnormal flags (H/L/HH/LL) and the result status (F = final, P = preliminary).",
    "ORC": "Carries order control information common to all order types: order control code (NW = new order, CA = cancel, RE = observations to follow), placer and filler order numbers, order status, and the ordering provider.",
    "AL1": "Reports one patient allergy: allergen type (DA = drug, FA = food), the allergen code/text, severity and reaction.",
    "DG1": "Carries one diagnosis: coding method, diagnosis code (typically ICD), description, date/time and diagnosis type (A = admitting, W = working, F = final).",
    "PR1": "Describes one procedure performed: coding method, procedure code, description, date/time, and the surgeon.",
    "GT1": "Identifies the guarantor — the person or organisation financially responsible for the patient's account: name, address, phone, and relationship to the patient.",
    "IN1": "Carries insurance policy details: insurance plan ID, insurance company ID/name/address, group numbers, the insured's name and relationship to the patient, and policy limits.",
    "IN2": "Continues insurance details: insured's employment information, social security number, and special coverage data.",
    "NTE": "Carries free-text notes and comments that attach to the immediately preceding segment (e.g. remarks on an OBX result).",
    "MSA": "Acknowledges a received message: acknowledgment code (AA = accepted, AE = application error, AR = rejected) and the message control ID of the message being acknowledged.",
    "ERR": "Details errors found while processing a message: the location of the error (segment/field) and coded error condition.",
    "QRD": "Defines a query in older query/response messages: query date/time, format, priority, query ID and the subject filter.",
    "QRF": "Refines the preceding QRD query with additional filter criteria such as date ranges.",
    "SPM": "Describes a specimen: specimen ID, type (e.g. blood, urine), collection method, source site, and collection date/time.",
    "SCH": "Carries appointment/schedule information: placer and filler appointment IDs, event reason, appointment type and duration, and its timing.",
    "FT1": "Carries one financial transaction for billing: transaction ID, date, posting reference, transaction type (CG = charge, PY = payment), code, amount and department.",
    "RXA": "Documents a pharmacy/treatment administration, e.g. one vaccine dose: administration date/time, the administered code (e.g. CVX for vaccines), amount, lot number, and the administering provider.",
    "RXR": "States the route by which the treatment was/should be administered (e.g. IM = intramuscular, PO = oral) and the body site.",
    "ROL": "Names a person playing a role in the encounter (e.g. PP = primary care provider), with the role period.",
}

SEGMENT_DETAILS = {
    "edifact": EDIFACT_DETAILS,
    "x12": X12_DETAILS,
    "tradacoms": TRADACOMS_DETAILS,
    "hl7": HL7_DETAILS,
}


# ---------------------------------------------------------------------------
# Positional element names for well-known segments
# ---------------------------------------------------------------------------
#
# Index 0 = first data element after the tag. For HL7 the numbering follows the
# standard's convention (MSH-1 is the field separator itself; for all other
# segments XXX-1 is the first field after the tag), which ``edi_core`` mirrors.

EDIFACT_ELEMENT_NAMES = {
    "UNB": [
        "Syntax identifier : version (e.g. UNOC:3)",
        "Interchange sender (id : qualifier)",
        "Interchange recipient (id : qualifier)",
        "Date : time of preparation (YYMMDD:HHMM)",
        "Interchange control reference (repeated in UNZ)",
        "Recipient's reference / password",
        "Application reference",
        "Processing priority code",
        "Acknowledgement request (1 = requested)",
        "Interchange agreement identifier",
        "Test indicator (1 = test)",
    ],
    "UNH": [
        "Message reference number (repeated in UNT)",
        "Message identifier (type : version : release : agency [: association])",
        "Common access reference",
        "Status of the transfer",
    ],
    "UNT": [
        "Number of segments in the message (incl. UNH and UNT)",
        "Message reference number (must match UNH)",
    ],
    "UNZ": [
        "Interchange control count (messages or groups)",
        "Interchange control reference (must match UNB)",
    ],
    "UNG": [
        "Functional group identification",
        "Application sender (id : qualifier)",
        "Application recipient (id : qualifier)",
        "Date : time of preparation",
        "Group reference number (repeated in UNE)",
        "Controlling agency",
        "Message version (version : release)",
    ],
    "UNE": [
        "Number of messages in the group",
        "Group reference number (must match UNG)",
    ],
    "UNS": ["Section identification (D = detail, S = summary)"],
    "BGM": [
        "Document/message type (code [: list : agency : name])",
        "Document number",
        "Message function (9 = original, 5 = replacement, 1 = cancellation)",
        "Response type",
    ],
    "DTM": ["Date/time/period (qualifier : value : format code)"],
    "RFF": ["Reference (qualifier : number [: line : version])"],
    "NAD": [
        "Party qualifier (BY = buyer, SU = supplier, DP = delivery party, ...)",
        "Party identification (code : list : agency, e.g. GLN with 9)",
        "Name and address (unstructured lines)",
        "Party name",
        "Street and number",
        "City",
        "Region / county",
        "Postal code",
        "Country code",
    ],
    "CTA": ["Contact function (OC = order contact, ...)", "Contact (department code : name)"],
    "COM": ["Communication contact (number : channel, e.g. EM = e-mail, TE = phone)"],
    "CUX": [
        "Currency details 1 (usage : currency : qualifier, e.g. 2:EUR:9)",
        "Currency details 2",
        "Rate of exchange",
    ],
    "LIN": [
        "Line item number",
        "Action code (1 = added, ...)",
        "Item number (id : type, EN = EAN/GTIN, UP = UPC)",
        "Sub-line information",
    ],
    "PIA": [
        "Product id function (1 = additional, 5 = product id)",
        "Item number (id : type, SA = supplier's, BP = buyer's, IN = buyer's item no.)",
    ],
    "IMD": [
        "Description format (C = coded, F = free-form)",
        "Item characteristic",
        "Item description (code : list : agency : text)",
    ],
    "QTY": ["Quantity (qualifier : amount [: unit], 21 = ordered, 12 = despatched)"],
    "MOA": ["Monetary amount (qualifier : amount [: currency], 77 = invoice total)"],
    "PRI": ["Price (qualifier : amount : type : basis [: per unit], AAA = net)"],
    "TAX": [
        "Function (7 = tax)",
        "Tax type (VAT, ...)",
        "Account detail",
        "Assessment basis",
        "Rate (category : rate)",
        "Category (S = standard, Z = zero, E = exempt)",
    ],
    "ALC": [
        "Allowance or charge indicator (A / C)",
        "Information (coded)",
        "Settlement",
        "Calculation sequence",
        "Reason (code, e.g. FC = freight, DI = discount)",
    ],
    "PCD": ["Percentage (qualifier : value, 1 = allowance, 2 = charge)"],
    "PAC": ["Number of packages", "Handling (instructions)", "Package type (CT = carton, PX = pallet)"],
    "MEA": [
        "Purpose (AAE = measurement)",
        "Dimension (WT = weight, VOL = volume)",
        "Value (unit : value)",
    ],
    "FTX": [
        "Subject (AAI = general, DEL = delivery)",
        "Function",
        "Text reference (coded)",
        "Text literal (up to 5 lines)",
        "Language code",
    ],
    "TDT": [
        "Stage qualifier (20 = main carriage)",
        "Conveyance reference",
        "Mode of transport (30 = road)",
        "Means of transport",
        "Carrier (id : list : agency : name)",
    ],
    "LOC": ["Function (7 = delivery, 9 = loading)", "Location (id : list : agency : name)"],
    "CNT": ["Control (qualifier : value, 2 = number of line items)"],
    "GIN": ["Identity number type (BJ = SSCC, BX = batch, SN = serial)", "Identity number (or range start : end)"],
}

X12_ELEMENT_NAMES = {
    "ISA": [
        "Authorization information qualifier (00 = none)",
        "Authorization information",
        "Security information qualifier (00 = none)",
        "Security information",
        "Sender ID qualifier (ZZ = mutually defined, 01 = DUNS)",
        "Interchange sender ID (15 chars, space padded)",
        "Receiver ID qualifier",
        "Interchange receiver ID (15 chars, space padded)",
        "Interchange date (YYMMDD)",
        "Interchange time (HHMM)",
        "Repetition separator (control standard in <00402)",
        "Interchange control version (e.g. 00401)",
        "Interchange control number (repeated in IEA02)",
        "Acknowledgment requested (0/1)",
        "Usage indicator (P = production, T = test)",
        "Component element separator",
    ],
    "IEA": [
        "Number of included functional groups",
        "Interchange control number (must match ISA13)",
    ],
    "GS": [
        "Functional identifier (PO = orders, IN = invoices, FA = 997s)",
        "Application sender's code",
        "Application receiver's code",
        "Date (CCYYMMDD)",
        "Time (HHMM)",
        "Group control number (repeated in GE02)",
        "Responsible agency (X = ASC X12)",
        "Version / release / industry code (e.g. 004010)",
    ],
    "GE": [
        "Number of included transaction sets",
        "Group control number (must match GS06)",
    ],
    "ST": [
        "Transaction set identifier (850, 810, 856, 997, ...)",
        "Transaction set control number (repeated in SE02)",
        "Implementation convention reference",
    ],
    "SE": [
        "Number of included segments (incl. ST and SE)",
        "Transaction set control number (must match ST02)",
    ],
    "BEG": [
        "Purpose (00 = original, 01 = cancellation)",
        "Purchase order type (NE = new order, SA = stand-alone)",
        "Purchase order number",
        "Release number",
        "Purchase order date (CCYYMMDD)",
    ],
    "BIG": [
        "Invoice date (CCYYMMDD)",
        "Invoice number",
        "Purchase order date",
        "Purchase order number",
        "Release number",
        "Change order sequence",
        "Transaction type code",
    ],
    "BSN": [
        "Purpose (00 = original)",
        "Shipment identification",
        "Date (CCYYMMDD)",
        "Time (HHMM)",
        "Hierarchical structure code (0001 = shipment/order/pack/item)",
    ],
    "REF": [
        "Reference qualifier (DP = department, BM = bill of lading, IA = vendor no.)",
        "Reference identification",
        "Description",
    ],
    "PER": [
        "Contact function (BD = buyer, IC = information contact)",
        "Name",
        "Communication qualifier (TE = phone, EM = e-mail)",
        "Communication number",
    ],
    "N1": [
        "Entity identifier (ST = ship to, BT = bill to, VN = vendor)",
        "Name",
        "Identification code qualifier (92 = assigned by buyer, UL = GLN)",
        "Identification code",
    ],
    "N3": ["Address line 1", "Address line 2"],
    "N4": ["City", "State/province", "Postal code", "Country code"],
    "DTM": ["Date qualifier (002 = requested delivery, 011 = shipped)", "Date (CCYYMMDD)", "Time"],
    "ITD": [
        "Terms type (08 = basic discount)",
        "Terms basis date code",
        "Discount percent",
        "Discount due date",
        "Discount days due",
        "Net due date",
        "Net days due",
    ],
    "TD5": [
        "Routing sequence code",
        "Carrier ID qualifier (2 = SCAC)",
        "Carrier identification (SCAC)",
        "Transportation method (M = motor, R = rail, A = air)",
        "Routing / service level",
    ],
    "PO1": [
        "Assigned line number",
        "Quantity ordered",
        "Unit of measure (EA = each, CA = case)",
        "Unit price",
        "Price basis (PE = per each)",
        "Product ID qualifier (UP = UPC, VN = vendor part, BP = buyer part)",
        "Product ID",
        "Product ID qualifier 2",
        "Product ID 2",
    ],
    "IT1": [
        "Assigned identification",
        "Quantity invoiced",
        "Unit of measure",
        "Unit price",
        "Price basis",
        "Product ID qualifier",
        "Product ID",
    ],
    "PID": [
        "Description type (F = free-form, S = structured)",
        "Characteristic code",
        "Agency qualifier",
        "Description code",
        "Description text",
    ],
    "SAC": [
        "Indicator (A = allowance, C = charge, N = neither)",
        "Type code (e.g. F050)",
        "Agency qualifier",
        "Agency service code",
        "Amount (implied 2 decimals)",
    ],
    "CTT": ["Number of line items", "Hash total (sum of quantities)"],
    "TDS": ["Total invoice amount (implied 2 decimals, e.g. cents)"],
    "HL": [
        "Hierarchical ID number",
        "Parent hierarchical ID",
        "Level code (S = shipment, O = order, P = pack, I = item)",
        "Child indicator (1 = has children)",
    ],
    "LIN": [
        "Assigned identification",
        "Product ID qualifier (UP = UPC, VN = vendor part, LT = lot)",
        "Product ID",
        "Product ID qualifier 2",
        "Product ID 2",
    ],
    "SN1": [
        "Assigned identification",
        "Number of units shipped",
        "Unit of measure",
        "Quantity shipped to date",
        "Quantity ordered",
        "Unit of measure (ordered)",
    ],
    "MAN": ["Marks/numbers qualifier (GM = SSCC-18)", "Marks and numbers (e.g. the SSCC)"],
    "TA1": [
        "Interchange control number being acknowledged",
        "Interchange date",
        "Interchange time",
        "Acknowledgment code (A = accepted, E = errors, R = rejected)",
        "Note code (reason)",
    ],
    "AK1": ["Functional ID code of the acknowledged group", "Group control number"],
    "AK9": [
        "Acknowledgment code (A = accepted, P = partial, R = rejected)",
        "Number of transaction sets included",
        "Number received",
        "Number accepted",
    ],
}

TRADACOMS_ELEMENT_NAMES = {
    "STX": [
        "Syntax (standard : version, e.g. ANA:1)",
        "Sender (ANA code : name)",
        "Recipient (ANA code : name)",
        "Transmission date : time (YYMMDD:HHMMSS)",
        "Sender's transmission reference",
        "Recipient's transmission reference",
        "Application reference (e.g. ORDHDR)",
        "Transmission priority",
    ],
    "END": ["Number of messages in the transmission"],
    "MHD": [
        "Message sequence number (1, 2, 3, ...)",
        "Message type : version (ORDHDR:9, ORDERS:9, INVFIL:9)",
    ],
    "MTR": ["Number of segments in the message (incl. MHD and MTR)"],
    "TYP": ["Transaction code (0430 = new orders, 0700 = invoices)", "Transaction description"],
    "SDT": ["Supplier (ANA code : supplier's own code)", "Supplier name", "Address", "VAT registration number"],
    "CDT": ["Customer (ANA code : customer's own code)", "Customer name", "Address", "VAT registration number"],
    "FIL": ["File generation number", "File version number", "File creation date (YYMMDD)"],
    "ORD": ["Customer's order number : date", "Supplier's order number : date", "Order code"],
    "CLO": ["Customer's location (ANA code : own code)", "Location name", "Location address"],
    "OLD": [
        "Line number",
        "Supplier's product code",
        "Consumer unit EAN",
        "Traded unit code (EAN/DUN)",
        "Number of traded units ordered",
        "Consumer units in traded unit",
        "Cost price per traded unit",
        "Description",
    ],
    "OTR": ["Number of order lines in the message"],
    "IRF": ["Invoice number", "Invoice date (YYMMDD)", "Tax point date (YYMMDD)"],
    "ILD": [
        "Line number",
        "Product code (EAN)",
        "Supplier's product code",
        "Invoiced quantity : unit",
        "Unit cost price (excl. VAT)",
        "VAT rate category (S/Z/E...)",
        "Line total (excl. VAT)",
        "Description",
    ],
    "STL": [
        "Sub-total number",
        "VAT rate category : rate",
        "Number of lines at this rate",
        "Goods total at this rate (excl. VAT)",
        "Settlement discount",
        "VAT amount",
        "Total incl. VAT",
    ],
    "TLR": ["Total goods value (excl. VAT)", "Total VAT", "Total payable"],
}

HL7_ELEMENT_NAMES = {
    "MSH": [
        "Field separator (the | itself)",
        "Encoding characters (^~\\& = component, repetition, escape, subcomponent)",
        "Sending application",
        "Sending facility",
        "Receiving application",
        "Receiving facility",
        "Message date/time (YYYYMMDDHHMMSS)",
        "Security",
        "Message type (type ^ trigger event, e.g. ADT^A01)",
        "Message control ID (echoed in ACKs)",
        "Processing ID (P = production, T = training, D = debug)",
        "HL7 version (e.g. 2.5)",
    ],
    "EVN": ["Event type code", "Recorded date/time", "Planned date/time", "Reason code", "Operator ID"],
    "PID": [
        "Set ID",
        "Patient ID (deprecated)",
        "Patient identifier list (id ^^^ authority ^ type, MR = medical record)",
        "Alternate patient ID (deprecated)",
        "Patient name (family ^ given ^ middle)",
        "Mother's maiden name",
        "Date of birth (YYYYMMDD)",
        "Administrative sex (M/F/O/U)",
        "Patient alias",
        "Race",
        "Patient address (street ^^ city ^ state ^ zip)",
        "County code",
        "Home phone",
        "Business phone",
    ],
    "PV1": [
        "Set ID",
        "Patient class (I = inpatient, O = outpatient, E = emergency)",
        "Assigned location (ward ^ room ^ bed)",
        "Admission type",
        "Preadmit number",
        "Prior location",
        "Attending doctor (id ^ family ^ given)",
        "Referring doctor",
        "Consulting doctor",
        "Hospital service",
    ],
    "OBR": [
        "Set ID",
        "Placer order number",
        "Filler order number",
        "Universal service identifier (what was ordered)",
        "Priority",
        "Requested date/time",
        "Observation date/time",
    ],
    "OBX": [
        "Set ID",
        "Value type (NM = numeric, ST = string, CE = coded)",
        "Observation identifier (code ^ text ^ system, e.g. LOINC)",
        "Observation sub-ID",
        "Observation value",
        "Units",
        "Reference range",
        "Abnormal flags (H/L/HH/LL/N)",
        "Probability",
        "Nature of abnormal test",
        "Result status (F = final, P = preliminary, C = corrected)",
    ],
    "MSA": [
        "Acknowledgment code (AA = accepted, AE = error, AR = rejected)",
        "Message control ID being acknowledged",
        "Text message",
    ],
    "NK1": [
        "Set ID",
        "Name (family ^ given)",
        "Relationship (SPO = spouse, FTH = father)",
        "Address",
        "Phone number",
    ],
    "DG1": [
        "Set ID",
        "Diagnosis coding method",
        "Diagnosis code (typically ICD)",
        "Diagnosis description",
        "Diagnosis date/time",
        "Diagnosis type (A = admitting, W = working, F = final)",
    ],
    "AL1": [
        "Set ID",
        "Allergen type (DA = drug, FA = food)",
        "Allergen code/description",
        "Severity",
        "Reaction",
    ],
    "IN1": [
        "Set ID",
        "Insurance plan ID",
        "Insurance company ID",
        "Insurance company name",
        "Insurance company address",
    ],
}

ELEMENT_NAMES = {
    "edifact": EDIFACT_ELEMENT_NAMES,
    "x12": X12_ELEMENT_NAMES,
    "tradacoms": TRADACOMS_ELEMENT_NAMES,
    "hl7": HL7_ELEMENT_NAMES,
}


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------

def dialect_family(dialect_key):
    """Return the delimiter family for a dialect key.

    EDIFACT subsets (EANCOM, ODETTE, ...) all resolve to the ``edifact``
    delimiter definition.
    """
    if dialect_key in EDIFACT_SUBSETS or dialect_key == "edifact":
        return "edifact"
    return dialect_key


def segment_name(dialect_key, tag):
    """Look up a short human readable name for ``tag`` within ``dialect_key``.

    Falls back to the base EDIFACT table for EDIFACT subsets and returns an
    empty string when the tag is unknown.
    """
    table = SEGMENTS.get(dialect_key)
    if table and tag in table:
        return table[tag]
    if dialect_key in EDIFACT_SUBSETS:
        return EDIFACT_SEGMENTS.get(tag, "")
    return ""


def segment_detail(dialect_key, tag):
    """Look up the full description of what ``tag`` means and does.

    Returns an empty string when no detailed description is available.
    """
    family = dialect_family(dialect_key)
    return SEGMENT_DETAILS.get(family, {}).get(tag, "")


def element_names(dialect_key, tag):
    """Return the positional element name list for ``tag`` (may be empty)."""
    family = dialect_family(dialect_key)
    return ELEMENT_NAMES.get(family, {}).get(tag, [])
