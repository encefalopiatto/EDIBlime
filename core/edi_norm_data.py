# -*- coding: utf-8 -*-
"""
Static reference data for EDI normalization (:mod:`edi_normalize`).

Segment *definitions* map a segment tag to its official name and the ordered
list of element positions, so the normalizer can key every value by name::

    "BGM": ("beginning_of_message", (
        ("C002", "document_message_name", (          # composite element
            ("1001", "document_message_name_coded"),
            ...
        )),
        ("1004", "document_message_number"),          # simple element
        ...
    ))

Message *structures* describe which segments a message type allows, how often
they may repeat and how they nest into segment groups::

    ("DTM", 5)                      # segment, up to 5 repeats
    ("SG", 99, (("NAD", 1), ...))   # segment group, first child = trigger

Provenance:

* ``EDIFACT_SEGMENT_DEFS`` and ``EDIFACT_MESSAGE_STRUCTURES`` are extracted
  from the official UNECE UNTDID **D.96A** directory
  (https://service.unece.org/trade/untdid/d96a/) -- the segment directory
  (TRSD) and the message segment tables (TRMD). D.96A is by far the most
  widely deployed directory in retail EDI (it is the basis of EANCOM 1997),
  and element naming is stable enough across directories that these names are
  also used for messages declaring other versions.
* ``EDIFACT_SERVICE_SEGMENT_DEFS`` follows ISO 9735 (the UN/EDIFACT syntax
  rules, service segments UNB/UNZ/UNG/UNE/UNH/UNT/UNS and the S001..S010 /
  0001..0086 service data elements).
* The X12, TRADACOMS and HL7 tables are hand-curated from the respective
  standards (ASC X12 004010 element names, ANA TRADACOMS segment layouts,
  HL7 v2.5 field names). Like the tables in :mod:`edi_data` they cover the
  segments seen in real-world traffic and can grow over time; unknown tags
  degrade to positional keys instead of failing.

Name derivation is uniform: the official name, lowercased, apostrophes
dropped, every other run of non-alphanumerics collapsed to ``_``
("Document/message name, coded" -> ``document_message_name_coded``).
"""

# ---------------------------------------------------------------------------
# EDIFACT service segments (ISO 9735)
# ---------------------------------------------------------------------------

EDIFACT_SERVICE_SEGMENT_DEFS = {
    "UNB": ("interchange_header", (
        ("S001", "syntax_identifier", (
            ("0001", "syntax_identifier"),
            ("0002", "syntax_version_number"),
        )),
        ("S002", "interchange_sender", (
            ("0004", "sender_identification"),
            ("0007", "partner_identification_code_qualifier"),
            ("0008", "address_for_reverse_routing"),
        )),
        ("S003", "interchange_recipient", (
            ("0010", "recipient_identification"),
            ("0007", "partner_identification_code_qualifier"),
            ("0014", "routing_address"),
        )),
        ("S004", "date_time_of_preparation", (
            ("0017", "date_of_preparation"),
            ("0019", "time_of_preparation"),
        )),
        ("0020", "interchange_control_reference"),
        ("S005", "recipients_reference_password", (
            ("0022", "recipients_reference_password"),
            ("0025", "recipients_reference_password_qualifier"),
        )),
        ("0026", "application_reference"),
        ("0029", "processing_priority_code"),
        ("0031", "acknowledgement_request"),
        ("0032", "communications_agreement_id"),
        ("0035", "test_indicator"),
    )),
    "UNZ": ("interchange_trailer", (
        ("0036", "interchange_control_count"),
        ("0020", "interchange_control_reference"),
    )),
    "UNG": ("functional_group_header", (
        ("0038", "functional_group_identification"),
        ("S006", "application_senders_identification", (
            ("0040", "application_sender_identification"),
            ("0007", "partner_identification_code_qualifier"),
        )),
        ("S007", "application_recipients_identification", (
            ("0044", "application_recipient_identification"),
            ("0007", "partner_identification_code_qualifier"),
        )),
        ("S004", "date_time_of_preparation", (
            ("0017", "date_of_preparation"),
            ("0019", "time_of_preparation"),
        )),
        ("0048", "functional_group_reference_number"),
        ("0051", "controlling_agency"),
        ("S008", "message_version", (
            ("0052", "message_version_number"),
            ("0054", "message_release_number"),
            ("0057", "association_assigned_code"),
        )),
        ("0058", "application_password"),
    )),
    "UNE": ("functional_group_trailer", (
        ("0060", "number_of_messages"),
        ("0048", "functional_group_reference_number"),
    )),
    "UNH": ("message_header", (
        ("0062", "message_reference_number"),
        ("S009", "message_identifier", (
            ("0065", "message_type"),
            ("0052", "message_version_number"),
            ("0054", "message_release_number"),
            ("0051", "controlling_agency"),
            ("0057", "association_assigned_code"),
        )),
        ("0068", "common_access_reference"),
        ("S010", "status_of_the_transfer", (
            ("0070", "sequence_of_transfers"),
            ("0073", "first_and_last_transfer"),
        )),
    )),
    "UNT": ("message_trailer", (
        ("0074", "number_of_segments_in_the_message"),
        ("0062", "message_reference_number"),
    )),
    "UNS": ("section_control", (
        ("0081", "section_identification"),
    )),
}


# ---------------------------------------------------------------------------
# EDIFACT segment directory
# ---------------------------------------------------------------------------
# Extracted from the UNECE UNTDID D.96A segment directory (TRSD). Every
# segment of the directory is present; do not edit by hand -- correct the
# extraction instead.

EDIFACT_SEGMENT_DEFS = {
    "ADR": ("address", (
        ("C817", "address_usage", (
            ("3299", "address_purpose_coded"),
            ("3131", "address_type_coded"),
            ("3475", "address_status_coded"),
        )),
        ("C090", "address_details", (
            ("3477", "address_format_coded"),
            ("3286", "address_component"),
            ("3286", "address_component"),
            ("3286", "address_component"),
            ("3286", "address_component"),
            ("3286", "address_component"),
        )),
        ("3164", "city_name"),
        ("3251", "postcode_identification"),
        ("3207", "country_coded"),
        ("C819", "country_sub_entity_details", (
            ("3229", "country_sub_entity_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("3228", "country_sub_entity"),
        )),
        ("C517", "location_identification", (
            ("3225", "place_location_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("3224", "place_location"),
        )),
    )),
    "AGR": ("agreement_identification", (
        ("C543", "agreement_type_identification", (
            ("7431", "agreement_type_qualifier"),
            ("7433", "agreement_type_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7434", "agreement_type_description"),
        )),
        ("9419", "service_layer_coded"),
    )),
    "AJT": ("adjustment_details", (
        ("4465", "adjustment_reason_coded"),
        ("1082", "line_item_number"),
    )),
    "ALC": ("allowance_or_charge", (
        ("5463", "allowance_or_charge_qualifier"),
        ("C552", "allowance_charge_information", (
            ("1230", "allowance_or_charge_number"),
            ("5189", "charge_allowance_description_coded"),
        )),
        ("4471", "settlement_coded"),
        ("1227", "calculation_sequence_indicator_coded"),
        ("C214", "special_services_identification", (
            ("7161", "special_services_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7160", "special_service"),
            ("7160", "special_service"),
        )),
    )),
    "ALI": ("additional_information", (
        ("3239", "country_of_origin_coded"),
        ("9213", "type_of_duty_regime_coded"),
        ("4183", "special_conditions_coded"),
        ("4183", "special_conditions_coded"),
        ("4183", "special_conditions_coded"),
        ("4183", "special_conditions_coded"),
        ("4183", "special_conditions_coded"),
    )),
    "APR": ("additional_price_information", (
        ("4043", "class_of_trade_coded"),
        ("C138", "price_multiplier_information", (
            ("5394", "price_multiplier"),
            ("5393", "price_multiplier_qualifier"),
        )),
        ("C960", "reason_for_change", (
            ("4295", "change_reason_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4294", "change_reason"),
        )),
    )),
    "ARD": ("amounts_relationship_details", (
        ("C549", "monetary_function", (
            ("5007", "monetary_function_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
    )),
    "ARR": ("array_information", (
        ("C778", "position_identification", (
            ("7164", "hierarchical_id_number"),
            ("1050", "sequence_number"),
        )),
        ("C770", "array_cell_details", (
            ("9424", "array_cell_information"),
        )),
    )),
    "ASI": ("array_structure_identification", (
        ("C779", "array_structure_identification", (
            ("9428", "array_structure_identifier"),
            ("7405", "identity_number_qualifier"),
        )),
        ("C082", "party_identification_details", (
            ("3039", "party_id_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("4405", "status_coded"),
        ("4513", "maintenance_operation_coded"),
    )),
    "ATT": ("attribute", (
        ("9017", "attribute_function_qualifier"),
        ("C955", "attribute_type", (
            ("9021", "attribute_type_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C956", "attribute_details", (
            ("9019", "attribute_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("9018", "attribute"),
        )),
    )),
    "AUT": ("authentication_result", (
        ("9280", "validation_result"),
        ("9282", "validation_key_identification"),
    )),
    "BGM": ("beginning_of_message", (
        ("C002", "document_message_name", (
            ("1001", "document_message_name_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("1000", "document_message_name"),
        )),
        ("1004", "document_message_number"),
        ("1225", "message_function_coded"),
        ("4343", "response_type_coded"),
    )),
    "BII": ("structure_identification", (
        ("7429", "indexing_structure_qualifier"),
        ("C045", "bill_level_identification", (
            ("7436", "level_one_id"),
            ("7438", "level_two_id"),
            ("7440", "level_three_id"),
            ("7442", "level_four_id"),
            ("7444", "level_five_id"),
            ("7446", "level_six_id"),
        )),
        ("7140", "item_number"),
    )),
    "BUS": ("business_function", (
        ("C521", "business_function", (
            ("4027", "business_function_qualifier"),
            ("4025", "business_function_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4022", "business_description"),
        )),
        ("3279", "geographic_environment_coded"),
        ("4487", "type_of_financial_transaction_coded"),
        ("C551", "bank_operation", (
            ("4383", "bank_operation_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("4463", "intra_company_payment_coded"),
    )),
    "CAV": ("characteristic_value", (
        ("C889", "characteristic_value", (
            ("7111", "characteristic_value_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7110", "characteristic_value"),
            ("7110", "characteristic_value"),
        )),
    )),
    "CCD": ("credit_cover_details", (
        ("4505", "credit_cover_request_coded"),
        ("4507", "credit_cover_response_coded"),
        ("4509", "credit_cover_reason_coded"),
    )),
    "CCI": ("characteristic_class_id", (
        ("7059", "property_class_coded"),
        ("C502", "measurement_details", (
            ("6313", "measurement_dimension_coded"),
            ("6321", "measurement_significance_coded"),
            ("6155", "measurement_attribute_coded"),
            ("6154", "measurement_attribute"),
        )),
        ("C240", "product_characteristic", (
            ("7037", "characteristic_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7036", "characteristic"),
            ("7036", "characteristic"),
        )),
    )),
    "CDI": ("cdi", (
        ("7001", "physical_or_logical_state_qualifier"),
        ("C564", "physical_or_logical_state_information", (
            ("7007", "physical_or_logical_state_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7006", "physical_or_logical_state"),
        )),
    )),
    "CDS": ("code_set_identification", (
        ("C702", "code_set_identification", (
            ("9150", "simple_data_element_tag"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("1507", "class_designator_coded"),
        ("4513", "maintenance_operation_coded"),
    )),
    "CDV": ("code_value_definition", (
        ("9426", "code_value"),
        ("9434", "code_name"),
        ("4513", "maintenance_operation_coded"),
    )),
    "CED": ("computer_environment_details", (
        ("1501", "computer_environment_details_qualifier"),
        ("C079", "computer_environment_identification", (
            ("1511", "computer_environment_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("1510", "computer_environment"),
            ("1056", "version"),
            ("1058", "release"),
            ("7402", "identity_number"),
        )),
    )),
    "CMP": ("composite_data_element_identification", (
        ("9146", "composite_data_element_tag"),
        ("1507", "class_designator_coded"),
        ("4513", "maintenance_operation_coded"),
    )),
    "CNI": ("consignment_information", (
        ("1490", "consolidation_item_number"),
        ("C503", "document_message_details", (
            ("1004", "document_message_number"),
            ("1373", "document_message_status_coded"),
            ("1366", "document_message_source"),
            ("3453", "language_coded"),
        )),
        ("1312", "consignment_load_sequence_number"),
    )),
    "CNT": ("control_total", (
        ("C270", "control", (
            ("6069", "control_qualifier"),
            ("6066", "control_value"),
            ("6411", "measure_unit_qualifier"),
        )),
    )),
    "COD": ("component_details", (
        ("C823", "type_of_unit_component", (
            ("7505", "type_of_unit_component_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7504", "type_of_unit_component"),
        )),
        ("C824", "component_material", (
            ("7507", "component_material_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7506", "component_material"),
        )),
    )),
    "COM": ("communication_contact", (
        ("C076", "communication_contact", (
            ("3148", "communication_number"),
            ("3155", "communication_channel_qualifier"),
        )),
    )),
    "COT": ("contribution_details", (
        ("5047", "contribution_qualifier"),
        ("C953", "contribution_type", (
            ("5049", "contribution_type_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("5048", "contribution_type"),
        )),
        ("C522", "instruction", (
            ("4403", "instruction_qualifier"),
            ("4401", "instruction_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4400", "instruction"),
        )),
        ("C203", "rate_tariff_class", (
            ("5243", "rate_tariff_class_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("5242", "rate_tariff_class"),
            ("5275", "supplementary_rate_tariff_basis_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("5275", "supplementary_rate_tariff_basis_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C960", "reason_for_change", (
            ("4295", "change_reason_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4294", "change_reason"),
        )),
    )),
    "CPI": ("charge_payment_instructions", (
        ("C229", "charge_category", (
            ("5237", "charge_category_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C231", "method_of_payment", (
            ("4215", "transport_charges_method_of_payment_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("4237", "prepaid_collect_indicator_coded"),
    )),
    "CPS": ("consignment_packing_sequence", (
        ("7164", "hierarchical_id_number"),
        ("7166", "hierarchical_parent_id"),
        ("7075", "packaging_level_coded"),
    )),
    "CST": ("customs_status_of_goods", (
        ("1496", "goods_item_number"),
        ("C246", "customs_identity_codes", (
            ("7361", "customs_code_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C246", "customs_identity_codes", (
            ("7361", "customs_code_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C246", "customs_identity_codes", (
            ("7361", "customs_code_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C246", "customs_identity_codes", (
            ("7361", "customs_code_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C246", "customs_identity_codes", (
            ("7361", "customs_code_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
    )),
    "CTA": ("contact_information", (
        ("3139", "contact_function_coded"),
        ("C056", "department_or_employee_details", (
            ("3413", "department_or_employee_identification"),
            ("3412", "department_or_employee"),
        )),
    )),
    "CUX": ("currencies", (
        ("C504", "currency_details", (
            ("6347", "currency_details_qualifier"),
            ("6345", "currency_coded"),
            ("6343", "currency_qualifier"),
            ("6348", "currency_rate_base"),
        )),
        ("C504", "currency_details", (
            ("6347", "currency_details_qualifier"),
            ("6345", "currency_coded"),
            ("6343", "currency_qualifier"),
            ("6348", "currency_rate_base"),
        )),
        ("5402", "rate_of_exchange"),
        ("6341", "currency_market_exchange_coded"),
    )),
    "DAM": ("damage", (
        ("7493", "damage_details_qualifier"),
        ("C821", "type_of_damage", (
            ("7501", "type_of_damage_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7500", "type_of_damage"),
        )),
        ("C822", "damage_area", (
            ("7503", "damage_area_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7502", "damage_area"),
        )),
        ("C825", "damage_severity", (
            ("7509", "damage_severity_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7508", "damage_severity"),
        )),
        ("C826", "action", (
            ("1229", "action_request_notification_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("1228", "action_request_notification"),
        )),
    )),
    "DGS": ("dangerous_goods", (
        ("8273", "dangerous_goods_regulations_coded"),
        ("C205", "hazard_code", (
            ("8351", "hazard_code_identification"),
            ("8078", "hazard_substance_item_page_number"),
            ("8092", "hazard_code_version_number"),
        )),
        ("C234", "undg_information", (
            ("7088", "dangerous_goods_flashpoint"),
        )),
        ("C223", "dangerous_goods_shipment_flashpoint", (
            ("6411", "measure_unit_qualifier"),
        )),
        ("8339", "packing_group_coded"),
        ("8364", "ems_number"),
        ("8410", "mfag"),
        ("8126", "trem_card_number"),
        ("C235", "hazard_identification", (
            ("8158", "hazard_identification_number_upper_part"),
            ("8186", "substance_identification_number_lower_part"),
        )),
        ("C236", "dangerous_goods_label", (
            ("8246", "dangerous_goods_label_marking"),
            ("8246", "dangerous_goods_label_marking"),
            ("8246", "dangerous_goods_label_marking"),
        )),
        ("8255", "packing_instruction_coded"),
        ("8325", "category_of_means_of_transport_coded"),
        ("8211", "permission_for_transport_coded"),
    )),
    "DII": ("directory_identification", (
        ("1056", "version"),
        ("1058", "release"),
        ("9148", "directory_status"),
        ("1476", "control_agency"),
        ("3453", "language_coded"),
        ("4513", "maintenance_operation_coded"),
    )),
    "DIM": ("dimensions", (
        ("6145", "dimension_qualifier"),
        ("C211", "dimensions", (
            ("6411", "measure_unit_qualifier"),
            ("6168", "length_dimension"),
            ("6140", "width_dimension"),
            ("6008", "height_dimension"),
        )),
    )),
    "DLI": ("document_line_identification", (
        ("1073", "document_line_indicator_coded"),
        ("1082", "line_item_number"),
    )),
    "DLM": ("delivery_limitations", (
        ("4455", "back_order_coded"),
        ("C522", "instruction", (
            ("4403", "instruction_qualifier"),
            ("4401", "instruction_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4400", "instruction"),
        )),
        ("C214", "special_services_identification", (
            ("7161", "special_services_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7160", "special_service"),
            ("7160", "special_service"),
        )),
        ("4457", "product_service_substitution_coded"),
    )),
    "DMS": ("document_message_summary", (
        ("1004", "document_message_number"),
        ("1001", "document_message_name_coded"),
        ("7240", "total_number_of_items"),
    )),
    "DOC": ("document_message_details", (
        ("C002", "document_message_name", (
            ("1001", "document_message_name_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("1000", "document_message_name"),
        )),
        ("C503", "document_message_details", (
            ("1004", "document_message_number"),
            ("1373", "document_message_status_coded"),
            ("1366", "document_message_source"),
            ("3453", "language_coded"),
        )),
        ("3153", "communication_channel_identifier_coded"),
        ("1220", "number_of_copies_of_document_required"),
        ("1218", "number_of_originals_of_document_required"),
    )),
    "DSI": ("data_set_identification", (
        ("C782", "data_set_identification", (
            ("1520", "data_set_identifier"),
            ("7405", "identity_number_qualifier"),
        )),
        ("C082", "party_identification_details", (
            ("3039", "party_id_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("4405", "status_coded"),
        ("C286", "sequence_information", (
            ("1050", "sequence_number"),
            ("1159", "sequence_number_source_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("1060", "revision_number"),
    )),
    "DTM": ("date_time_period", (
        ("C507", "date_time_period", (
            ("2005", "date_time_period_qualifier"),
            ("2380", "date_time_period"),
            ("2379", "date_time_period_format_qualifier"),
        )),
    )),
    "EFI": ("external_file_link_identification", (
        ("C077", "file_identification", (
            ("1508", "file_name"),
            ("7008", "item_description"),
        )),
        ("C099", "file_details", (
            ("1516", "file_format"),
            ("1056", "version"),
            ("1503", "data_format_coded"),
            ("1502", "data_format"),
        )),
        ("1050", "sequence_number"),
    )),
    "ELM": ("simple_data_element_details", (
        ("9150", "simple_data_element_tag"),
        ("9153", "simple_data_element_character_representation"),
        ("9155", "simple_data_element_length_type_coded"),
        ("9156", "simple_data_element_maximum_length"),
        ("9158", "simple_data_element_minimum_length"),
        ("9161", "code_set_indicator_coded"),
        ("1507", "class_designator_coded"),
        ("4513", "maintenance_operation_coded"),
    )),
    "ELU": ("data_element_usage_details", (
        ("9162", "data_element_tag"),
        ("7299", "requirement_designator_coded"),
        ("1050", "sequence_number"),
        ("4513", "maintenance_operation_coded"),
    )),
    "EMP": ("employment_details", (
        ("9003", "employment_qualifier"),
        ("C948", "employment_category", (
            ("9005", "employment_category_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("9004", "employment_category"),
        )),
        ("C951", "occupation", (
            ("9009", "occupation_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("9008", "occupation"),
            ("9008", "occupation"),
        )),
        ("C950", "qualification_classification", (
            ("9007", "qualification_classification_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("9006", "qualification_classification"),
            ("9006", "qualification_classification"),
        )),
        ("3494", "job_title"),
        ("9035", "qualification_area_coded"),
    )),
    "EQA": ("attached_equipment", (
        ("8053", "equipment_qualifier"),
        ("C237", "equipment_identification", (
            ("8260", "equipment_identification_number"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("3207", "country_coded"),
        )),
    )),
    "EQD": ("equipment_details", (
        ("8053", "equipment_qualifier"),
        ("C237", "equipment_identification", (
            ("8260", "equipment_identification_number"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("3207", "country_coded"),
        )),
        ("C224", "equipment_size_and_type", (
            ("8155", "equipment_size_and_type_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("8154", "equipment_size_and_type"),
        )),
        ("8077", "equipment_supplier_coded"),
        ("8249", "equipment_status_coded"),
        ("8169", "full_empty_indicator_coded"),
    )),
    "EQN": ("number_of_units", (
        ("C523", "number_of_unit_details", (
            ("6350", "number_of_units"),
            ("6353", "number_of_units_qualifier"),
        )),
    )),
    "ERC": ("application_error_information", (
        ("C901", "application_error_detail", (
            ("9321", "application_error_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
    )),
    "ERP": ("error_point_details", (
        ("C701", "error_point_details", (
            ("1049", "message_section_coded"),
            ("1052", "message_item_number"),
            ("1054", "message_sub_item_number"),
        )),
    )),
    "FCA": ("financial_charges_allocation", (
        ("4471", "settlement_coded"),
        ("C878", "charge_allowance_account", (
            ("3434", "institution_branch_number"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("3194", "account_holder_number"),
            ("6345", "currency_coded"),
        )),
    )),
    "FII": ("financial_institution_information", (
        ("3035", "party_qualifier"),
        ("C078", "account_identification", (
            ("3194", "account_holder_number"),
            ("3192", "account_holder_name"),
            ("3192", "account_holder_name"),
            ("6345", "currency_coded"),
        )),
        ("C088", "institution_identification", (
            ("3433", "institution_name_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("3434", "institution_branch_number"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("3432", "institution_name"),
            ("3436", "institution_branch_place"),
        )),
        ("3207", "country_coded"),
    )),
    "FNS": ("footnote_set", (
        ("C783", "footnote_set_identification", (
            ("9430", "footnote_set_identifier"),
            ("7405", "identity_number_qualifier"),
        )),
        ("C082", "party_identification_details", (
            ("3039", "party_id_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("4405", "status_coded"),
        ("4513", "maintenance_operation_coded"),
    )),
    "FNT": ("footnote", (
        ("C784", "footnote_identification", (
            ("9432", "footnote_identifier"),
            ("7405", "identity_number_qualifier"),
        )),
        ("C082", "party_identification_details", (
            ("3039", "party_id_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("4405", "status_coded"),
        ("4513", "maintenance_operation_coded"),
    )),
    "FTX": ("free_text", (
        ("4451", "text_subject_qualifier"),
        ("4453", "text_function_coded"),
        ("C107", "text_reference", (
            ("4441", "free_text_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C108", "text_literal", (
            ("4440", "free_text"),
            ("4440", "free_text"),
            ("4440", "free_text"),
            ("4440", "free_text"),
            ("4440", "free_text"),
        )),
        ("3453", "language_coded"),
    )),
    "GDS": ("nature_of_cargo", (
        ("C703", "nature_of_cargo", (
            ("7085", "nature_of_cargo_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
    )),
    "GID": ("goods_item_details", (
        ("1496", "goods_item_number"),
        ("C213", "number_and_type_of_packages", (
            ("7224", "number_of_packages"),
            ("7065", "type_of_packages_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7064", "type_of_packages"),
        )),
        ("C213", "number_and_type_of_packages", (
            ("7224", "number_of_packages"),
            ("7065", "type_of_packages_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7064", "type_of_packages"),
        )),
        ("C213", "number_and_type_of_packages", (
            ("7224", "number_of_packages"),
            ("7065", "type_of_packages_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7064", "type_of_packages"),
        )),
    )),
    "GIN": ("goods_identity_number", (
        ("7405", "identity_number_qualifier"),
        ("C208", "identity_number_range", (
            ("7402", "identity_number"),
            ("7402", "identity_number"),
        )),
        ("C208", "identity_number_range", (
            ("7402", "identity_number"),
            ("7402", "identity_number"),
        )),
        ("C208", "identity_number_range", (
            ("7402", "identity_number"),
            ("7402", "identity_number"),
        )),
        ("C208", "identity_number_range", (
            ("7402", "identity_number"),
            ("7402", "identity_number"),
        )),
        ("C208", "identity_number_range", (
            ("7402", "identity_number"),
            ("7402", "identity_number"),
        )),
    )),
    "GIR": ("related_identification_numbers", (
        ("7297", "set_identification_qualifier"),
        ("C206", "identification_number", (
            ("7402", "identity_number"),
            ("7405", "identity_number_qualifier"),
            ("4405", "status_coded"),
        )),
        ("C206", "identification_number", (
            ("7402", "identity_number"),
            ("7405", "identity_number_qualifier"),
            ("4405", "status_coded"),
        )),
        ("C206", "identification_number", (
            ("7402", "identity_number"),
            ("7405", "identity_number_qualifier"),
            ("4405", "status_coded"),
        )),
        ("C206", "identification_number", (
            ("7402", "identity_number"),
            ("7405", "identity_number_qualifier"),
            ("4405", "status_coded"),
        )),
        ("C206", "identification_number", (
            ("7402", "identity_number"),
            ("7405", "identity_number_qualifier"),
            ("4405", "status_coded"),
        )),
    )),
    "GIS": ("general_indicator", (
        ("C529", "processing_indicator", (
            ("7365", "processing_indicator_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7187", "process_type_identification"),
        )),
    )),
    "GOR": ("governmental_requirements", (
        ("8323", "transport_movement_coded"),
        ("C232", "government_action", (
            ("9415", "government_agency_coded"),
            ("9411", "government_involvement_coded"),
            ("9417", "government_action_coded"),
            ("9353", "government_procedure_coded"),
        )),
        ("C232", "government_action", (
            ("9415", "government_agency_coded"),
            ("9411", "government_involvement_coded"),
            ("9417", "government_action_coded"),
            ("9353", "government_procedure_coded"),
        )),
        ("C232", "government_action", (
            ("9415", "government_agency_coded"),
            ("9411", "government_involvement_coded"),
            ("9417", "government_action_coded"),
            ("9353", "government_procedure_coded"),
        )),
        ("C232", "government_action", (
            ("9415", "government_agency_coded"),
            ("9411", "government_involvement_coded"),
            ("9417", "government_action_coded"),
            ("9353", "government_procedure_coded"),
        )),
    )),
    "GRU": ("segment_group_usage_details", (
        ("9164", "group_identification"),
        ("7299", "requirement_designator_coded"),
        ("6176", "maximum_number_of_occurrences"),
        ("4513", "maintenance_operation_coded"),
        ("1050", "sequence_number"),
    )),
    "HAN": ("handling_instructions", (
        ("C524", "handling_instructions", (
            ("4079", "handling_instructions_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4078", "handling_instructions"),
        )),
        ("C218", "hazardous_material", (
            ("7419", "hazardous_material_class_code_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
    )),
    "ICD": ("insurance_cover_description", (
        ("C330", "insurance_cover_type", (
            ("4497", "insurance_cover_type_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C331", "insurance_cover_details", (
            ("4495", "insurance_cover_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4494", "insurance_cover"),
            ("4494", "insurance_cover"),
        )),
    )),
    "IDE": ("identity", (
        ("7495", "identification_qualifier"),
        ("C206", "identification_number", (
            ("7402", "identity_number"),
            ("7405", "identity_number_qualifier"),
            ("4405", "status_coded"),
        )),
        ("C082", "party_identification_details", (
            ("3039", "party_id_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("4405", "status_coded"),
        ("1222", "configuration_level"),
        ("C778", "position_identification", (
            ("7164", "hierarchical_id_number"),
            ("1050", "sequence_number"),
        )),
        ("C240", "product_characteristic", (
            ("7037", "characteristic_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7036", "characteristic"),
            ("7036", "characteristic"),
        )),
    )),
    "IHC": ("person_characteristic", (
        ("3289", "person_characteristic_qualifier"),
        ("C818", "person_inherited_characteristic_details", (
            ("3311", "person_inherited_characteristic_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("3310", "person_inherited_characteristic"),
        )),
    )),
    "IMD": ("item_description", (
        ("7077", "item_description_type_coded"),
        ("7081", "item_characteristic_coded"),
        ("C273", "item_description", (
            ("7009", "item_description_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7008", "item_description"),
            ("7008", "item_description"),
            ("3453", "language_coded"),
        )),
        ("7383", "surface_layer_indicator_coded"),
    )),
    "IND": ("index_details", (
        ("C545", "index_identification", (
            ("5013", "index_qualifier"),
            ("5027", "index_type_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C546", "index_value", (
            ("5030", "index_value"),
            ("5039", "index_value_representation_coded"),
        )),
    )),
    "INP": ("parties_to_instruction", (
        ("C849", "parties_to_instruction", (
            ("3301", "party_enacting_instruction_identification"),
            ("3285", "recipient_of_the_instruction_identification"),
        )),
        ("C522", "instruction", (
            ("4403", "instruction_qualifier"),
            ("4401", "instruction_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4400", "instruction"),
        )),
        ("C850", "status_of_instruction", (
            ("4405", "status_coded"),
            ("3036", "party_name"),
        )),
        ("1229", "action_request_notification_coded"),
    )),
    "INV": ("inventory_management_related_details", (
        ("4501", "inventory_movement_direction_coded"),
        ("7491", "type_of_inventory_affected_coded"),
        ("4499", "reason_for_inventory_movement_coded"),
        ("4503", "inventory_balance_method_coded"),
        ("C522", "instruction", (
            ("4403", "instruction_qualifier"),
            ("4401", "instruction_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4400", "instruction"),
        )),
    )),
    "IRQ": ("information_required", (
        ("C333", "information_request", (
            ("4511", "requested_information_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4510", "requested_information"),
        )),
    )),
    "LAN": ("language", (
        ("3455", "language_qualifier"),
        ("C508", "language_details", (
            ("3453", "language_coded"),
            ("3452", "language"),
        )),
    )),
    "LIN": ("line_item", (
        ("1082", "line_item_number"),
        ("1229", "action_request_notification_coded"),
        ("C212", "item_number_identification", (
            ("7140", "item_number"),
            ("7143", "item_number_type_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C829", "sub_line_information", (
            ("5495", "sub_line_indicator_coded"),
            ("1082", "line_item_number"),
        )),
        ("1222", "configuration_level"),
        ("7083", "configuration_coded"),
    )),
    "LOC": ("place_location_identification", (
        ("3227", "place_location_qualifier"),
        ("C517", "location_identification", (
            ("3225", "place_location_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("3224", "place_location"),
        )),
        ("C519", "related_location_one_identification", (
            ("3223", "related_place_location_one_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("3222", "related_place_location_one"),
        )),
        ("C553", "related_location_two_identification", (
            ("3233", "related_place_location_two_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("3232", "related_place_location_two"),
        )),
        ("5479", "relation_coded"),
    )),
    "MEA": ("measurements", (
        ("6311", "measurement_application_qualifier"),
        ("C502", "measurement_details", (
            ("6313", "measurement_dimension_coded"),
            ("6321", "measurement_significance_coded"),
            ("6155", "measurement_attribute_coded"),
            ("6154", "measurement_attribute"),
        )),
        ("C174", "value_range", (
            ("6411", "measure_unit_qualifier"),
            ("6314", "measurement_value"),
            ("6162", "range_minimum"),
            ("6152", "range_maximum"),
            ("6432", "significant_digits"),
        )),
        ("7383", "surface_layer_indicator_coded"),
    )),
    "MEM": ("membership_details", (
        ("7449", "membership_qualifier"),
        ("C942", "membership_category", (
            ("7451", "membership_category_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7450", "membership_category"),
        )),
        ("C944", "membership_status", (
            ("7453", "membership_status_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7452", "membership_status"),
        )),
        ("C945", "membership_level", (
            ("7455", "membership_level_qualifier"),
            ("7457", "membership_level_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7456", "membership_level"),
        )),
        ("C203", "rate_tariff_class", (
            ("5243", "rate_tariff_class_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("5242", "rate_tariff_class"),
            ("5275", "supplementary_rate_tariff_basis_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("5275", "supplementary_rate_tariff_basis_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C960", "reason_for_change", (
            ("4295", "change_reason_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4294", "change_reason"),
        )),
    )),
    "MKS": ("market_sales_channel_information", (
        ("7293", "sector_subject_identification_qualifier"),
        ("C332", "sales_channel_identification", (
            ("3496", "sales_channel_identifier"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("1229", "action_request_notification_coded"),
    )),
    "MOA": ("monetary_amount", (
        ("C516", "monetary_amount", (
            ("5025", "monetary_amount_type_qualifier"),
            ("5004", "monetary_amount"),
            ("6345", "currency_coded"),
            ("6343", "currency_qualifier"),
            ("4405", "status_coded"),
        )),
    )),
    "MSG": ("message_type_identification", (
        ("C709", "message_identifier", (
            ("1475", "message_type_identifier"),
            ("1056", "version"),
            ("1058", "release"),
            ("1476", "control_agency"),
            ("1523", "association_assigned_identification"),
            ("1060", "revision_number"),
        )),
        ("1507", "class_designator_coded"),
        ("4513", "maintenance_operation_coded"),
    )),
    "NAD": ("name_and_address", (
        ("3035", "party_qualifier"),
        ("C082", "party_identification_details", (
            ("3039", "party_id_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C058", "name_and_address", (
            ("3124", "name_and_address_line"),
            ("3124", "name_and_address_line"),
            ("3124", "name_and_address_line"),
            ("3124", "name_and_address_line"),
            ("3124", "name_and_address_line"),
        )),
        ("C080", "party_name", (
            ("3036", "party_name"),
            ("3036", "party_name"),
            ("3036", "party_name"),
            ("3036", "party_name"),
            ("3036", "party_name"),
            ("3045", "party_name_format_coded"),
        )),
        ("C059", "street", (
            ("3042", "street_and_number_p_o_box"),
            ("3042", "street_and_number_p_o_box"),
            ("3042", "street_and_number_p_o_box"),
            ("3042", "street_and_number_p_o_box"),
        )),
        ("3164", "city_name"),
        ("3229", "country_sub_entity_identification"),
        ("3251", "postcode_identification"),
        ("3207", "country_coded"),
    )),
    "NAT": ("nationality", (
        ("3493", "nationality_qualifier"),
        ("C042", "nationality_details", (
            ("3293", "nationality_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
    )),
    "PAC": ("package", (
        ("7224", "number_of_packages"),
        ("C531", "packaging_details", (
            ("7075", "packaging_level_coded"),
            ("7233", "packaging_related_information_coded"),
            ("7073", "packaging_terms_and_conditions_coded"),
        )),
        ("C202", "package_type", (
            ("7065", "type_of_packages_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7064", "type_of_packages"),
        )),
        ("C402", "package_type_identification", (
            ("7077", "item_description_type_coded"),
            ("7064", "type_of_packages"),
            ("7143", "item_number_type_coded"),
            ("7064", "type_of_packages"),
            ("7143", "item_number_type_coded"),
        )),
        ("C532", "returnable_package_details", (
            ("8395", "returnable_package_freight_payment_responsibility"),
            ("8393", "returnable_package_load_contents_coded"),
        )),
    )),
    "PAI": ("payment_instructions", (
        ("C534", "payment_instruction_details", (
            ("4439", "payment_conditions_coded"),
            ("4431", "payment_guarantee_coded"),
            ("4461", "payment_means_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4435", "payment_channel_coded"),
        )),
    )),
    "PAT": ("payment_terms_basis", (
        ("4279", "payment_terms_type_qualifier"),
        ("C110", "payment_terms", (
            ("4277", "terms_of_payment_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4276", "terms_of_payment"),
            ("4276", "terms_of_payment"),
        )),
        ("C112", "terms_time_information", (
            ("2475", "payment_time_reference_coded"),
            ("2009", "time_relation_coded"),
            ("2151", "type_of_period_coded"),
            ("2152", "number_of_periods"),
        )),
    )),
    "PCD": ("percentage_details", (
        ("C501", "percentage_details", (
            ("5245", "percentage_qualifier"),
            ("5482", "percentage"),
            ("5249", "percentage_basis_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
    )),
    "PCI": ("package_identification", (
        ("4233", "marking_instructions_coded"),
        ("C210", "marks_labels", (
            ("7102", "shipping_marks"),
            ("7102", "shipping_marks"),
            ("7102", "shipping_marks"),
            ("7102", "shipping_marks"),
            ("7102", "shipping_marks"),
            ("7102", "shipping_marks"),
            ("7102", "shipping_marks"),
            ("7102", "shipping_marks"),
            ("7102", "shipping_marks"),
            ("7102", "shipping_marks"),
        )),
        ("8275", "container_package_status_coded"),
        ("C827", "type_of_marking", (
            ("7511", "type_of_marking_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
    )),
    "PDI": ("person_demographic_information", (
        ("3499", "sex_coded"),
        ("C085", "marital_status_details", (
            ("3479", "marital_status_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("3478", "marital_status"),
        )),
        ("C101", "religion_details", (
            ("3483", "religion_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("3482", "religion"),
        )),
    )),
    "PGI": ("product_group_information", (
        ("5379", "product_group_type_coded"),
        ("C288", "product_group", (
            ("5389", "product_group_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("5388", "product_group"),
        )),
    )),
    "PIA": ("additional_product_id", (
        ("4347", "product_id_function_qualifier"),
        ("C212", "item_number_identification", (
            ("7140", "item_number"),
            ("7143", "item_number_type_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C212", "item_number_identification", (
            ("7140", "item_number"),
            ("7143", "item_number_type_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C212", "item_number_identification", (
            ("7140", "item_number"),
            ("7143", "item_number_type_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C212", "item_number_identification", (
            ("7140", "item_number"),
            ("7143", "item_number_type_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C212", "item_number_identification", (
            ("7140", "item_number"),
            ("7143", "item_number_type_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
    )),
    "PIT": ("pit", (
        ("1082", "line_item_number"),
        ("1229", "action_request_notification_coded"),
        ("C292", "price_change_information", (
            ("5377", "price_change_indicator_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("7011", "article_availability_coded"),
        ("5495", "sub_line_indicator_coded"),
        ("1222", "configuration_level"),
        ("7083", "configuration_coded"),
    )),
    "PNA": ("party_name", (
        ("3035", "party_qualifier"),
        ("C206", "identification_number", (
            ("7402", "identity_number"),
            ("7405", "identity_number_qualifier"),
            ("4405", "status_coded"),
        )),
        ("C082", "party_identification_details", (
            ("3039", "party_id_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("3403", "name_type_coded"),
        ("3397", "name_status_coded"),
        ("C816", "name_component_details", (
            ("3405", "name_component_qualifier"),
            ("3398", "name_component"),
            ("3401", "name_component_status_coded"),
            ("3295", "name_component_original_representation_coded"),
        )),
        ("C816", "name_component_details", (
            ("3405", "name_component_qualifier"),
            ("3398", "name_component"),
            ("3401", "name_component_status_coded"),
            ("3295", "name_component_original_representation_coded"),
        )),
        ("C816", "name_component_details", (
            ("3405", "name_component_qualifier"),
            ("3398", "name_component"),
            ("3401", "name_component_status_coded"),
            ("3295", "name_component_original_representation_coded"),
        )),
        ("C816", "name_component_details", (
            ("3405", "name_component_qualifier"),
            ("3398", "name_component"),
            ("3401", "name_component_status_coded"),
            ("3295", "name_component_original_representation_coded"),
        )),
        ("C816", "name_component_details", (
            ("3405", "name_component_qualifier"),
            ("3398", "name_component"),
            ("3401", "name_component_status_coded"),
            ("3295", "name_component_original_representation_coded"),
        )),
    )),
    "PRC": ("process_identification", (
        ("C242", "process_type_and_description", (
            ("7187", "process_type_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7186", "process_type"),
            ("7186", "process_type"),
        )),
    )),
    "PRI": ("price_details", (
        ("C509", "price_information", (
            ("5125", "price_qualifier"),
            ("5118", "price"),
            ("5375", "price_type_coded"),
            ("5387", "price_type_qualifier"),
            ("5284", "unit_price_basis"),
            ("6411", "measure_unit_qualifier"),
        )),
        ("5213", "sub_line_price_change_coded"),
    )),
    "PSD": ("psd", (
        ("4407", "sample_process_status_coded"),
        ("7039", "sample_selection_method_coded"),
        ("C526", "frequency_details", (
            ("6071", "frequency_qualifier"),
            ("6072", "frequency_value"),
            ("6411", "measure_unit_qualifier"),
        )),
        ("7045", "sample_description_coded"),
        ("7047", "sample_direction_coded"),
        ("C514", "sample_location_details", (
            ("3237", "sample_location_coded"),
            ("3236", "sample_location"),
        )),
        ("C514", "sample_location_details", (
            ("3237", "sample_location_coded"),
            ("3236", "sample_location"),
        )),
        ("C514", "sample_location_details", (
            ("3237", "sample_location_coded"),
            ("3236", "sample_location"),
        )),
    )),
    "PTY": ("priority", (
        ("4035", "priority_qualifier"),
        ("C585", "priority_details", (
            ("4037", "priority_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4036", "priority"),
        )),
    )),
    "QTY": ("quantity", (
        ("C186", "quantity_details", (
            ("6063", "quantity_qualifier"),
            ("6060", "quantity"),
            ("6411", "measure_unit_qualifier"),
        )),
    )),
    "QVR": ("quantity_variances", (
        ("C279", "quantity_difference_information", (
            ("6064", "quantity_difference"),
            ("6063", "quantity_qualifier"),
        )),
        ("4221", "discrepancy_coded"),
        ("C960", "reason_for_change", (
            ("4295", "change_reason_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4294", "change_reason"),
        )),
    )),
    "RCS": ("requirements_and_conditions", (
        ("7293", "sector_subject_identification_qualifier"),
        ("C550", "requirement_condition_identification", (
            ("7295", "requirement_condition_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7294", "requirement_or_condition"),
        )),
        ("1229", "action_request_notification_coded"),
    )),
    "REL": ("relationship", (
        ("9141", "relationship_qualifier"),
        ("C941", "relationship", (
            ("9143", "relationship_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("9142", "relationship"),
        )),
    )),
    "RFF": ("reference", (
        ("C506", "reference", (
            ("1153", "reference_qualifier"),
            ("1154", "reference_number"),
            ("1156", "line_number"),
            ("4000", "reference_version_number"),
        )),
    )),
    "RNG": ("range_details", (
        ("6167", "range_type_qualifier"),
        ("C280", "range", (
            ("6411", "measure_unit_qualifier"),
            ("6162", "range_minimum"),
            ("6152", "range_maximum"),
        )),
    )),
    "RTE": ("rate_details", (
        ("C128", "rate_details", (
            ("5419", "rate_type_qualifier"),
            ("5420", "rate_per_unit"),
            ("5284", "unit_price_basis"),
            ("6411", "measure_unit_qualifier"),
        )),
    )),
    "SAL": ("remuneration_type_identification", (
        ("C049", "remuneration_type_identification", (
            ("5315", "remuneration_type_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("5314", "remuneration_type"),
            ("5314", "remuneration_type"),
        )),
    )),
    "SCC": ("scheduling_conditions", (
        ("4017", "delivery_plan_status_indicator_coded"),
        ("4493", "delivery_requirements_coded"),
        ("C329", "pattern_description", (
            ("2013", "frequency_coded"),
            ("2015", "despatch_pattern_coded"),
            ("2017", "despatch_pattern_timing_coded"),
        )),
    )),
    "SCD": ("structure_component_definition", (
        ("7497", "component_function_qualifier"),
        ("C786", "structure_component_identification", (
            ("7512", "structure_component_identifier"),
            ("7405", "identity_number_qualifier"),
        )),
        ("C082", "party_identification_details", (
            ("3039", "party_id_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("4405", "status_coded"),
        ("1222", "configuration_level"),
        ("C778", "position_identification", (
            ("7164", "hierarchical_id_number"),
            ("1050", "sequence_number"),
        )),
        ("C240", "product_characteristic", (
            ("7037", "characteristic_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7036", "characteristic"),
            ("7036", "characteristic"),
        )),
    )),
    "SEG": ("segment_identification", (
        ("9166", "segment_tag"),
        ("1507", "class_designator_coded"),
        ("4513", "maintenance_operation_coded"),
    )),
    "SEL": ("seal_number", (
        ("9308", "seal_number"),
        ("C215", "seal_issuer", (
            ("9303", "sealing_party_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("9302", "sealing_party"),
        )),
        ("4517", "seal_condition_coded"),
    )),
    "SEQ": ("sequence_details", (
        ("1245", "status_indicator_coded"),
        ("C286", "sequence_information", (
            ("1050", "sequence_number"),
            ("1159", "sequence_number_source_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
    )),
    "SFI": ("safety_information", (
        ("7164", "hierarchical_id_number"),
        ("C814", "safety_section", (
            ("4046", "safety_section"),
            ("4044", "safety_section_name"),
        )),
        ("C815", "additional_safety_information", (
            ("4039", "additional_safety_information_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4038", "additional_safety_information"),
        )),
        ("4513", "maintenance_operation_coded"),
    )),
    "SGP": ("split_goods_placement", (
        ("C237", "equipment_identification", (
            ("8260", "equipment_identification_number"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("3207", "country_coded"),
        )),
        ("7224", "number_of_packages"),
    )),
    "SGU": ("segment_usage_details", (
        ("9166", "segment_tag"),
        ("7299", "requirement_designator_coded"),
        ("6176", "maximum_number_of_occurrences"),
        ("7168", "level_number"),
        ("1050", "sequence_number"),
        ("1049", "message_section_coded"),
        ("4513", "maintenance_operation_coded"),
    )),
    "SPS": ("sampling_parameters_for_summary_statistics", (
        ("C526", "frequency_details", (
            ("6071", "frequency_qualifier"),
            ("6072", "frequency_value"),
            ("6411", "measure_unit_qualifier"),
        )),
        ("6074", "confidence_limit"),
        ("C512", "size_details", (
            ("6173", "size_qualifier"),
            ("6174", "size"),
        )),
        ("C512", "size_details", (
            ("6173", "size_qualifier"),
            ("6174", "size"),
        )),
        ("C512", "size_details", (
            ("6173", "size_qualifier"),
            ("6174", "size"),
        )),
        ("C512", "size_details", (
            ("6173", "size_qualifier"),
            ("6174", "size"),
        )),
        ("C512", "size_details", (
            ("6173", "size_qualifier"),
            ("6174", "size"),
        )),
    )),
    "STA": ("statistics", (
        ("6331", "statistic_type_coded"),
        ("C527", "statistical_details", (
            ("6314", "measurement_value"),
            ("6411", "measure_unit_qualifier"),
            ("6313", "measurement_dimension_coded"),
            ("6321", "measurement_significance_coded"),
        )),
    )),
    "STC": ("statistical_concept", (
        ("C785", "statistical_concept_identification", (
            ("6434", "statistical_concept_identifier"),
            ("7405", "identity_number_qualifier"),
        )),
        ("C082", "party_identification_details", (
            ("3039", "party_id_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("4405", "status_coded"),
        ("4513", "maintenance_operation_coded"),
    )),
    "STG": ("stages", (
        ("9421", "stages_qualifier"),
        ("6426", "number_of_stages"),
        ("6428", "actual_stage_count"),
    )),
    "STS": ("status", (
        ("C601", "status_type", (
            ("9015", "status_type_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C555", "status_event", (
            ("9011", "status_event_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("9010", "status_event"),
        )),
        ("C556", "status_reason", (
            ("9013", "status_reason_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("9012", "status_reason"),
        )),
        ("C556", "status_reason", (
            ("9013", "status_reason_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("9012", "status_reason"),
        )),
        ("C556", "status_reason", (
            ("9013", "status_reason_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("9012", "status_reason"),
        )),
        ("C556", "status_reason", (
            ("9013", "status_reason_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("9012", "status_reason"),
        )),
        ("C556", "status_reason", (
            ("9013", "status_reason_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("9012", "status_reason"),
        )),
    )),
    "TAX": ("duty_tax_fee_details", (
        ("5283", "duty_tax_fee_function_qualifier"),
        ("C241", "duty_tax_fee_type", (
            ("5153", "duty_tax_fee_type_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("5152", "duty_tax_fee_type"),
        )),
        ("C533", "duty_tax_fee_account_detail", (
            ("5289", "duty_tax_fee_account_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("5286", "duty_tax_fee_assessment_basis"),
        ("C243", "duty_tax_fee_detail", (
            ("5279", "duty_tax_fee_rate_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("5278", "duty_tax_fee_rate"),
            ("5273", "duty_tax_fee_rate_basis_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("5305", "duty_tax_fee_category_coded"),
        ("3446", "party_tax_identification_number"),
    )),
    "TCC": ("transport_charge_rate_calculations", (
        ("C200", "charge", (
            ("8023", "freight_and_charges_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("8022", "freight_and_charges"),
            ("4237", "prepaid_collect_indicator_coded"),
            ("7140", "item_number"),
        )),
        ("C203", "rate_tariff_class", (
            ("5243", "rate_tariff_class_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("5242", "rate_tariff_class"),
            ("5275", "supplementary_rate_tariff_basis_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("5275", "supplementary_rate_tariff_basis_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C528", "commodity_rate_detail", (
            ("7357", "commodity_rate_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C554", "rate_tariff_class_detail", (
            ("5243", "rate_tariff_class_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
    )),
    "TDT": ("details_of_transport", (
        ("8051", "transport_stage_qualifier"),
        ("8028", "conveyance_reference_number"),
        ("C220", "mode_of_transport", (
            ("8067", "mode_of_transport_coded"),
            ("8066", "mode_of_transport"),
        )),
        ("C228", "transport_means", (
            ("8179", "type_of_means_of_transport_identification"),
            ("8178", "type_of_means_of_transport"),
        )),
        ("C040", "carrier", (
            ("3127", "carrier_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("3128", "carrier_name"),
        )),
        ("8101", "transit_direction_coded"),
        ("C401", "excess_transportation_information", (
            ("8457", "excess_transportation_reason_coded"),
            ("8459", "excess_transportation_responsibility_coded"),
            ("7130", "customer_authorization_number"),
        )),
        ("C222", "transport_identification", (
            ("8213", "id_of_means_of_transport_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("8212", "id_of_the_means_of_transport"),
            ("8453", "nationality_of_means_of_transport_coded"),
        )),
        ("8281", "transport_ownership_coded"),
    )),
    "TEM": ("test_method", (
        ("C244", "test_method", (
            ("4415", "test_method_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4416", "test_description"),
        )),
        ("4419", "test_route_of_administering_coded"),
        ("3077", "test_media_coded"),
        ("6311", "measurement_application_qualifier"),
        ("7188", "test_revision_number"),
        ("C515", "test_reason", (
            ("4425", "test_reason_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4424", "test_reason"),
        )),
    )),
    "TMD": ("tmd", (
        ("C219", "movement_type", (
            ("8335", "movement_type_coded"),
            ("8334", "movement_type"),
        )),
        ("8332", "equipment_plan"),
        ("8341", "haulage_arrangements_coded"),
    )),
    "TMP": ("temperature", (
        ("6245", "temperature_qualifier"),
        ("C239", "temperature_setting", (
            ("6411", "measure_unit_qualifier"),
        )),
    )),
    "TOD": ("terms_of_delivery_or_transport", (
        ("4055", "terms_of_delivery_or_transport_function_coded"),
        ("4215", "transport_charges_method_of_payment_coded"),
        ("C100", "terms_of_delivery_or_transport", (
            ("4053", "terms_of_delivery_or_transport_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("4052", "terms_of_delivery_or_transport"),
            ("4052", "terms_of_delivery_or_transport"),
        )),
    )),
    "TPL": ("transport_placement", (
        ("C222", "transport_identification", (
            ("8213", "id_of_means_of_transport_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("8212", "id_of_the_means_of_transport"),
            ("8453", "nationality_of_means_of_transport_coded"),
        )),
    )),
    "TSR": ("transport_service_requirements", (
        ("C536", "contract_and_carriage_condition", (
            ("4065", "contract_and_carriage_condition_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C233", "service", (
            ("7273", "service_requirement_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7273", "service_requirement_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C537", "transport_priority", (
            ("4219", "transport_priority_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("C703", "nature_of_cargo", (
            ("7085", "nature_of_cargo_coded"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
    )),
    "VLI": ("value_list_identification", (
        ("C780", "value_list_identification", (
            ("1518", "value_list_identifier"),
            ("7405", "identity_number_qualifier"),
        )),
        ("C082", "party_identification_details", (
            ("3039", "party_id_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
        )),
        ("4405", "status_coded"),
        ("1514", "value_list_name"),
        ("1507", "class_designator_coded"),
        ("1505", "value_list_type_coded"),
        ("C240", "product_characteristic", (
            ("7037", "characteristic_identification"),
            ("1131", "code_list_qualifier"),
            ("3055", "code_list_responsible_agency_coded"),
            ("7036", "characteristic"),
            ("7036", "characteristic"),
        )),
        ("4513", "maintenance_operation_coded"),
    )),
}

# Merged lookup used by the normalizer: data segments + service segments.
EDIFACT_ALL_SEGMENT_DEFS = dict(EDIFACT_SEGMENT_DEFS)
EDIFACT_ALL_SEGMENT_DEFS.update(EDIFACT_SERVICE_SEGMENT_DEFS)


# ---------------------------------------------------------------------------
# EDIFACT message structures
# ---------------------------------------------------------------------------
# Segment tables of the most common message types, extracted from the UNECE
# UNTDID D.96A message directory (TRMD). UNH/UNT are handled by the envelope
# logic and are not part of the entries. Message types without a table here
# still normalize -- flat, without group nesting.

EDIFACT_MESSAGE_STRUCTURES = {
    "ORDERS": (
        ("BGM", 1),
        ("DTM", 35),
        ("PAI", 1),
        ("ALI", 5),
        ("IMD", 1),
        ("FTX", 99),
        ("SG", 10, (
            ("RFF", 1),
            ("DTM", 5),
        )),
        ("SG", 99, (
            ("NAD", 1),
            ("LOC", 25),
            ("FII", 5),
            ("SG", 10, (
                ("RFF", 1),
                ("DTM", 5),
            )),
            ("SG", 5, (
                ("DOC", 1),
                ("DTM", 5),
            )),
            ("SG", 5, (
                ("CTA", 1),
                ("COM", 5),
            )),
        )),
        ("SG", 5, (
            ("TAX", 1),
            ("MOA", 1),
            ("LOC", 5),
        )),
        ("SG", 5, (
            ("CUX", 1),
            ("PCD", 5),
            ("DTM", 5),
        )),
        ("SG", 10, (
            ("PAT", 1),
            ("DTM", 5),
            ("PCD", 1),
            ("MOA", 1),
        )),
        ("SG", 10, (
            ("TDT", 1),
            ("SG", 10, (
                ("LOC", 1),
                ("DTM", 5),
            )),
        )),
        ("SG", 5, (
            ("TOD", 1),
            ("LOC", 2),
        )),
        ("SG", 10, (
            ("PAC", 1),
            ("MEA", 5),
            ("SG", 5, (
                ("PCI", 1),
                ("RFF", 1),
                ("DTM", 5),
                ("GIN", 10),
            )),
        )),
        ("SG", 10, (
            ("EQD", 1),
            ("HAN", 5),
            ("MEA", 5),
            ("FTX", 5),
        )),
        ("SG", 10, (
            ("SCC", 1),
            ("FTX", 5),
            ("RFF", 5),
            ("SG", 10, (
                ("QTY", 1),
                ("DTM", 5),
            )),
        )),
        ("SG", 25, (
            ("APR", 1),
            ("DTM", 5),
            ("RNG", 1),
        )),
        ("SG", 15, (
            ("ALC", 1),
            ("ALI", 5),
            ("DTM", 5),
            ("SG", 1, (
                ("QTY", 1),
                ("RNG", 1),
            )),
            ("SG", 1, (
                ("PCD", 1),
                ("RNG", 1),
            )),
            ("SG", 2, (
                ("MOA", 1),
                ("RNG", 1),
            )),
            ("SG", 1, (
                ("RTE", 1),
                ("RNG", 1),
            )),
            ("SG", 5, (
                ("TAX", 1),
                ("MOA", 1),
            )),
        )),
        ("SG", 100, (
            ("RCS", 1),
            ("RFF", 5),
            ("DTM", 5),
            ("FTX", 5),
        )),
        ("SG", 200000, (
            ("LIN", 1),
            ("PIA", 25),
            ("IMD", 99),
            ("MEA", 5),
            ("QTY", 10),
            ("PCD", 5),
            ("ALI", 5),
            ("DTM", 35),
            ("MOA", 10),
            ("GIN", 1000),
            ("GIR", 1000),
            ("QVR", 1),
            ("DOC", 5),
            ("PAI", 1),
            ("FTX", 99),
            ("SG", 999, (
                ("CCI", 1),
                ("CAV", 10),
                ("MEA", 10),
            )),
            ("SG", 10, (
                ("PAT", 1),
                ("DTM", 5),
                ("PCD", 1),
                ("MOA", 1),
            )),
            ("SG", 25, (
                ("PRI", 1),
                ("CUX", 1),
                ("APR", 1),
                ("RNG", 1),
                ("DTM", 5),
            )),
            ("SG", 10, (
                ("RFF", 1),
                ("DTM", 5),
            )),
            ("SG", 10, (
                ("PAC", 1),
                ("MEA", 5),
                ("QTY", 5),
                ("DTM", 5),
                ("SG", 1, (
                    ("RFF", 1),
                    ("DTM", 5),
                )),
                ("SG", 5, (
                    ("PCI", 1),
                    ("RFF", 1),
                    ("DTM", 5),
                    ("GIN", 10),
                )),
            )),
            ("SG", 9999, (
                ("LOC", 1),
                ("QTY", 1),
                ("DTM", 5),
            )),
            ("SG", 10, (
                ("TAX", 1),
                ("MOA", 1),
                ("LOC", 5),
            )),
            ("SG", 99, (
                ("NAD", 1),
                ("LOC", 5),
                ("SG", 5, (
                    ("RFF", 1),
                    ("DTM", 5),
                )),
                ("SG", 5, (
                    ("DOC", 1),
                    ("DTM", 5),
                )),
                ("SG", 5, (
                    ("CTA", 1),
                    ("COM", 5),
                )),
            )),
            ("SG", 99, (
                ("ALC", 1),
                ("ALI", 5),
                ("DTM", 5),
                ("SG", 1, (
                    ("QTY", 1),
                    ("RNG", 1),
                )),
                ("SG", 1, (
                    ("PCD", 1),
                    ("RNG", 1),
                )),
                ("SG", 2, (
                    ("MOA", 1),
                    ("RNG", 1),
                )),
                ("SG", 1, (
                    ("RTE", 1),
                    ("RNG", 1),
                )),
                ("SG", 5, (
                    ("TAX", 1),
                    ("MOA", 1),
                )),
            )),
            ("SG", 10, (
                ("TDT", 1),
                ("SG", 10, (
                    ("LOC", 1),
                    ("DTM", 5),
                )),
            )),
            ("SG", 5, (
                ("TOD", 1),
                ("LOC", 2),
            )),
            ("SG", 10, (
                ("EQD", 1),
                ("HAN", 5),
                ("MEA", 5),
                ("FTX", 5),
            )),
            ("SG", 100, (
                ("SCC", 1),
                ("FTX", 5),
                ("RFF", 5),
                ("SG", 10, (
                    ("QTY", 1),
                    ("DTM", 5),
                )),
            )),
            ("SG", 100, (
                ("RCS", 1),
                ("RFF", 5),
                ("DTM", 5),
                ("FTX", 5),
            )),
            ("SG", 10, (
                ("STG", 1),
                ("SG", 3, (
                    ("QTY", 1),
                    ("MOA", 1),
                )),
            )),
        )),
        ("UNS", 1),
        ("MOA", 12),
        ("CNT", 10),
        ("SG", 10, (
            ("ALC", 1),
            ("ALI", 1),
            ("MOA", 2),
        )),
    ),
    "ORDCHG": (
        ("BGM", 1),
        ("DTM", 35),
        ("PAI", 1),
        ("ALI", 5),
        ("IMD", 1),
        ("FTX", 99),
        ("SG", 10, (
            ("RFF", 1),
            ("DTM", 5),
        )),
        ("SG", 1, (
            ("AJT", 1),
            ("FTX", 5),
        )),
        ("SG", 99, (
            ("NAD", 1),
            ("LOC", 25),
            ("FII", 5),
            ("SG", 10, (
                ("RFF", 1),
                ("DTM", 5),
            )),
            ("SG", 5, (
                ("DOC", 1),
                ("DTM", 5),
            )),
            ("SG", 5, (
                ("CTA", 1),
                ("COM", 5),
            )),
        )),
        ("SG", 5, (
            ("TAX", 1),
            ("MOA", 1),
            ("LOC", 5),
        )),
        ("SG", 5, (
            ("CUX", 1),
            ("PCD", 5),
            ("DTM", 5),
        )),
        ("SG", 10, (
            ("PAT", 1),
            ("DTM", 5),
            ("PCD", 1),
            ("MOA", 1),
        )),
        ("SG", 10, (
            ("TDT", 1),
            ("SG", 10, (
                ("LOC", 1),
                ("DTM", 5),
            )),
        )),
        ("SG", 5, (
            ("TOD", 1),
            ("LOC", 2),
        )),
        ("SG", 10, (
            ("PAC", 1),
            ("MEA", 5),
            ("SG", 5, (
                ("PCI", 1),
                ("RFF", 1),
                ("DTM", 5),
                ("GIN", 10),
            )),
        )),
        ("SG", 10, (
            ("EQD", 1),
            ("HAN", 5),
            ("MEA", 5),
            ("FTX", 5),
        )),
        ("SG", 10, (
            ("SCC", 1),
            ("FTX", 5),
            ("RFF", 5),
            ("SG", 10, (
                ("QTY", 1),
                ("DTM", 5),
            )),
        )),
        ("SG", 25, (
            ("APR", 1),
            ("DTM", 5),
            ("RNG", 1),
        )),
        ("SG", 15, (
            ("ALC", 1),
            ("ALI", 5),
            ("DTM", 5),
            ("SG", 1, (
                ("QTY", 1),
                ("RNG", 1),
            )),
            ("SG", 1, (
                ("PCD", 1),
                ("RNG", 1),
            )),
            ("SG", 2, (
                ("MOA", 1),
                ("RNG", 1),
            )),
            ("SG", 1, (
                ("RTE", 1),
                ("RNG", 1),
            )),
            ("SG", 5, (
                ("TAX", 1),
                ("MOA", 1),
            )),
        )),
        ("SG", 100, (
            ("RCS", 1),
            ("RFF", 5),
            ("DTM", 5),
            ("FTX", 5),
        )),
        ("SG", 200000, (
            ("LIN", 1),
            ("PIA", 25),
            ("IMD", 99),
            ("MEA", 5),
            ("QTY", 10),
            ("PCD", 5),
            ("ALI", 5),
            ("DTM", 35),
            ("MOA", 10),
            ("GIN", 1000),
            ("GIR", 1000),
            ("QVR", 1),
            ("DOC", 5),
            ("PAI", 1),
            ("FTX", 99),
            ("SG", 999, (
                ("CCI", 1),
                ("CAV", 10),
                ("MEA", 10),
            )),
            ("SG", 10, (
                ("PAT", 1),
                ("DTM", 5),
                ("PCD", 1),
                ("MOA", 1),
            )),
            ("SG", 1, (
                ("AJT", 1),
                ("FTX", 5),
            )),
            ("SG", 25, (
                ("PRI", 1),
                ("CUX", 1),
                ("APR", 1),
                ("RNG", 1),
                ("DTM", 5),
            )),
            ("SG", 999, (
                ("RFF", 1),
                ("DTM", 5),
            )),
            ("SG", 10, (
                ("PAC", 1),
                ("MEA", 5),
                ("QTY", 5),
                ("DTM", 5),
                ("SG", 1, (
                    ("RFF", 1),
                    ("DTM", 5),
                )),
                ("SG", 5, (
                    ("PCI", 1),
                    ("RFF", 1),
                    ("DTM", 5),
                    ("GIN", 10),
                )),
            )),
            ("SG", 9999, (
                ("LOC", 1),
                ("QTY", 1),
                ("DTM", 5),
            )),
            ("SG", 10, (
                ("TAX", 1),
                ("MOA", 1),
                ("LOC", 5),
            )),
            ("SG", 10, (
                ("NAD", 1),
                ("LOC", 5),
                ("SG", 5, (
                    ("RFF", 1),
                    ("DTM", 5),
                )),
                ("SG", 5, (
                    ("DOC", 1),
                    ("DTM", 5),
                )),
                ("SG", 5, (
                    ("CTA", 1),
                    ("COM", 5),
                )),
            )),
            ("SG", 99, (
                ("ALC", 1),
                ("ALI", 5),
                ("DTM", 5),
                ("SG", 1, (
                    ("QTY", 1),
                    ("RNG", 1),
                )),
                ("SG", 1, (
                    ("PCD", 1),
                    ("RNG", 1),
                )),
                ("SG", 2, (
                    ("MOA", 1),
                    ("RNG", 1),
                )),
                ("SG", 1, (
                    ("RTE", 1),
                    ("RNG", 1),
                )),
                ("SG", 5, (
                    ("TAX", 1),
                    ("MOA", 1),
                )),
            )),
            ("SG", 10, (
                ("TDT", 1),
                ("SG", 10, (
                    ("LOC", 1),
                    ("DTM", 5),
                )),
            )),
            ("SG", 5, (
                ("TOD", 1),
                ("LOC", 2),
            )),
            ("SG", 10, (
                ("EQD", 1),
                ("HAN", 5),
                ("MEA", 5),
                ("FTX", 5),
            )),
            ("SG", 100, (
                ("SCC", 1),
                ("FTX", 5),
                ("RFF", 5),
                ("SG", 10, (
                    ("QTY", 1),
                    ("DTM", 5),
                )),
            )),
            ("SG", 100, (
                ("RCS", 1),
                ("RFF", 5),
                ("DTM", 5),
                ("FTX", 5),
            )),
            ("SG", 10, (
                ("STG", 1),
                ("SG", 3, (
                    ("QTY", 1),
                    ("MOA", 1),
                )),
            )),
        )),
        ("UNS", 1),
        ("MOA", 12),
        ("CNT", 10),
        ("SG", 10, (
            ("ALC", 1),
            ("ALI", 1),
            ("MOA", 2),
        )),
    ),
    "ORDRSP": (
        ("BGM", 1),
        ("DTM", 35),
        ("PAI", 1),
        ("ALI", 5),
        ("IMD", 1),
        ("FTX", 99),
        ("SG", 10, (
            ("RFF", 1),
            ("DTM", 5),
        )),
        ("SG", 1, (
            ("AJT", 1),
            ("FTX", 5),
        )),
        ("SG", 99, (
            ("NAD", 1),
            ("LOC", 25),
            ("FII", 5),
            ("SG", 10, (
                ("RFF", 1),
                ("DTM", 5),
            )),
            ("SG", 5, (
                ("DOC", 1),
                ("DTM", 5),
            )),
            ("SG", 5, (
                ("CTA", 1),
                ("COM", 5),
            )),
        )),
        ("SG", 5, (
            ("TAX", 1),
            ("MOA", 1),
            ("LOC", 5),
        )),
        ("SG", 5, (
            ("CUX", 1),
            ("PCD", 5),
            ("DTM", 5),
        )),
        ("SG", 10, (
            ("PAT", 1),
            ("DTM", 5),
            ("PCD", 1),
            ("MOA", 1),
        )),
        ("SG", 10, (
            ("TDT", 1),
            ("SG", 10, (
                ("LOC", 1),
                ("DTM", 5),
            )),
        )),
        ("SG", 5, (
            ("TOD", 1),
            ("LOC", 2),
        )),
        ("SG", 10, (
            ("PAC", 1),
            ("MEA", 5),
            ("SG", 5, (
                ("PCI", 1),
                ("RFF", 1),
                ("DTM", 5),
                ("GIN", 99),
            )),
        )),
        ("SG", 10, (
            ("EQD", 1),
            ("HAN", 5),
            ("MEA", 5),
            ("FTX", 5),
        )),
        ("SG", 10, (
            ("SCC", 1),
            ("FTX", 5),
            ("RFF", 5),
            ("SG", 10, (
                ("QTY", 1),
                ("DTM", 5),
            )),
        )),
        ("SG", 25, (
            ("APR", 1),
            ("DTM", 5),
            ("RNG", 1),
        )),
        ("SG", 15, (
            ("ALC", 1),
            ("ALI", 5),
            ("DTM", 5),
            ("SG", 1, (
                ("QTY", 1),
                ("RNG", 1),
            )),
            ("SG", 1, (
                ("PCD", 1),
                ("RNG", 1),
            )),
            ("SG", 2, (
                ("MOA", 1),
                ("RNG", 1),
            )),
            ("SG", 1, (
                ("RTE", 1),
                ("RNG", 1),
            )),
            ("SG", 5, (
                ("TAX", 1),
                ("MOA", 1),
            )),
        )),
        ("SG", 100, (
            ("RCS", 1),
            ("RFF", 5),
            ("DTM", 5),
            ("FTX", 5),
        )),
        ("SG", 200000, (
            ("LIN", 1),
            ("PIA", 25),
            ("IMD", 99),
            ("MEA", 5),
            ("QTY", 10),
            ("PCD", 5),
            ("ALI", 5),
            ("DTM", 35),
            ("MOA", 10),
            ("GIN", 1000),
            ("GIR", 1000),
            ("QVR", 1),
            ("DOC", 5),
            ("PAI", 1),
            ("FTX", 99),
            ("SG", 999, (
                ("CCI", 1),
                ("CAV", 10),
                ("MEA", 10),
            )),
            ("SG", 10, (
                ("PAT", 1),
                ("DTM", 5),
                ("PCD", 1),
                ("MOA", 1),
            )),
            ("SG", 1, (
                ("AJT", 1),
                ("FTX", 5),
            )),
            ("SG", 25, (
                ("PRI", 1),
                ("CUX", 1),
                ("APR", 1),
                ("RNG", 1),
                ("DTM", 5),
            )),
            ("SG", 999, (
                ("RFF", 1),
                ("DTM", 5),
            )),
            ("SG", 10, (
                ("PAC", 1),
                ("MEA", 5),
                ("QTY", 5),
                ("DTM", 5),
                ("SG", 1, (
                    ("RFF", 1),
                    ("DTM", 5),
                )),
                ("SG", 5, (
                    ("PCI", 1),
                    ("RFF", 1),
                    ("DTM", 5),
                    ("GIN", 99),
                )),
            )),
            ("SG", 9999, (
                ("LOC", 1),
                ("QTY", 1),
                ("DTM", 5),
            )),
            ("SG", 10, (
                ("TAX", 1),
                ("MOA", 1),
                ("LOC", 5),
            )),
            ("SG", 99, (
                ("NAD", 1),
                ("LOC", 5),
                ("SG", 5, (
                    ("RFF", 1),
                    ("DTM", 5),
                )),
                ("SG", 5, (
                    ("DOC", 1),
                    ("DTM", 5),
                )),
                ("SG", 5, (
                    ("CTA", 1),
                    ("COM", 5),
                )),
            )),
            ("SG", 99, (
                ("ALC", 1),
                ("ALI", 5),
                ("DTM", 5),
                ("SG", 1, (
                    ("QTY", 1),
                    ("RNG", 1),
                )),
                ("SG", 1, (
                    ("PCD", 1),
                    ("RNG", 1),
                )),
                ("SG", 2, (
                    ("MOA", 1),
                    ("RNG", 1),
                )),
                ("SG", 1, (
                    ("RTE", 1),
                    ("RNG", 1),
                )),
                ("SG", 5, (
                    ("TAX", 1),
                    ("MOA", 1),
                )),
            )),
            ("SG", 10, (
                ("TDT", 1),
                ("SG", 10, (
                    ("LOC", 1),
                    ("DTM", 5),
                )),
            )),
            ("SG", 5, (
                ("TOD", 1),
                ("LOC", 2),
            )),
            ("SG", 10, (
                ("EQD", 1),
                ("HAN", 5),
                ("MEA", 5),
                ("FTX", 5),
            )),
            ("SG", 100, (
                ("SCC", 1),
                ("FTX", 5),
                ("RFF", 5),
                ("SG", 10, (
                    ("QTY", 1),
                    ("DTM", 5),
                )),
            )),
            ("SG", 100, (
                ("RCS", 1),
                ("RFF", 5),
                ("DTM", 5),
                ("FTX", 5),
            )),
            ("SG", 10, (
                ("STG", 1),
                ("SG", 3, (
                    ("QTY", 1),
                    ("MOA", 1),
                )),
            )),
        )),
        ("UNS", 1),
        ("MOA", 12),
        ("CNT", 10),
        ("SG", 10, (
            ("ALC", 1),
            ("ALI", 1),
            ("MOA", 2),
        )),
    ),
    "DESADV": (
        ("BGM", 1),
        ("DTM", 10),
        ("ALI", 5),
        ("MEA", 5),
        ("MOA", 5),
        ("SG", 10, (
            ("RFF", 1),
            ("DTM", 1),
        )),
        ("SG", 10, (
            ("NAD", 1),
            ("LOC", 10),
            ("SG", 10, (
                ("RFF", 1),
                ("DTM", 1),
            )),
            ("SG", 10, (
                ("CTA", 1),
                ("COM", 5),
            )),
        )),
        ("SG", 10, (
            ("TOD", 1),
            ("LOC", 5),
            ("FTX", 5),
        )),
        ("SG", 10, (
            ("TDT", 1),
            ("PCD", 6),
            ("SG", 10, (
                ("LOC", 1),
                ("DTM", 10),
            )),
        )),
        ("SG", 10, (
            ("EQD", 1),
            ("MEA", 5),
            ("SEL", 25),
            ("EQA", 5),
            ("SG", 10, (
                ("HAN", 1),
                ("FTX", 10),
            )),
        )),
        ("SG", 9999, (
            ("CPS", 1),
            ("FTX", 5),
            ("SG", 9999, (
                ("PAC", 1),
                ("MEA", 10),
                ("QTY", 10),
                ("SG", 10, (
                    ("HAN", 1),
                    ("FTX", 10),
                )),
                ("SG", 1000, (
                    ("PCI", 1),
                    ("RFF", 1),
                    ("DTM", 5),
                    ("GIR", 99),
                    ("SG", 99, (
                        ("GIN", 1),
                        ("DLM", 10),
                    )),
                )),
            )),
            ("SG", 9999, (
                ("LIN", 1),
                ("PIA", 10),
                ("IMD", 25),
                ("MEA", 10),
                ("QTY", 10),
                ("ALI", 10),
                ("GIN", 100),
                ("GIR", 100),
                ("DLM", 100),
                ("DTM", 5),
                ("FTX", 5),
                ("MOA", 5),
                ("SG", 10, (
                    ("RFF", 1),
                    ("DTM", 1),
                )),
                ("SG", 10, (
                    ("DGS", 1),
                    ("QTY", 1),
                    ("FTX", 5),
                )),
                ("SG", 100, (
                    ("LOC", 1),
                    ("NAD", 1),
                    ("DTM", 1),
                    ("QTY", 10),
                )),
                ("SG", 1000, (
                    ("SGP", 1),
                    ("QTY", 10),
                )),
                ("SG", 9999, (
                    ("PCI", 1),
                    ("DTM", 5),
                    ("MEA", 10),
                    ("QTY", 1),
                    ("SG", 10, (
                        ("GIN", 1),
                        ("DLM", 100),
                    )),
                    ("SG", 10, (
                        ("HAN", 1),
                        ("FTX", 5),
                        ("GIN", 1000),
                    )),
                )),
                ("SG", 10, (
                    ("QVR", 1),
                    ("DTM", 5),
                )),
            )),
        )),
        ("CNT", 5),
    ),
    "RECADV": (
        ("BGM", 1),
        ("DTM", 10),
        ("ALI", 5),
        ("SG", 10, (
            ("RFF", 1),
            ("DTM", 1),
        )),
        ("SG", 10, (
            ("DOC", 1),
            ("SG", 10, (
                ("CDI", 1),
                ("INP", 5),
            )),
        )),
        ("SG", 10, (
            ("NAD", 1),
            ("LOC", 10),
            ("SG", 10, (
                ("RFF", 1),
                ("DTM", 1),
            )),
            ("SG", 10, (
                ("CTA", 1),
                ("COM", 5),
            )),
        )),
        ("SG", 10, (
            ("TOD", 1),
            ("SG", 10, (
                ("CDI", 1),
                ("INP", 5),
            )),
            ("SG", 10, (
                ("LOC", 1),
                ("CDI", 10),
            )),
        )),
        ("SG", 10, (
            ("TDT", 1),
            ("DTM", 10),
            ("CDI", 10),
        )),
        ("SG", 9999, (
            ("EQD", 1),
            ("SG", 10, (
                ("CDI", 1),
                ("INP", 5),
            )),
            ("SG", 25, (
                ("SEL", 1),
                ("CDI", 10),
            )),
            ("SG", 10, (
                ("EQA", 1),
                ("SG", 10, (
                    ("CDI", 1),
                    ("INP", 5),
                )),
            )),
        )),
        ("SG", 9999, (
            ("CPS", 1),
            ("SG", 9999, (
                ("PAC", 1),
                ("QVR", 1),
                ("SG", 999, (
                    ("PCI", 1),
                    ("RFF", 1),
                    ("SG", 10, (
                        ("CDI", 1),
                        ("INP", 5),
                    )),
                    ("SG", 999, (
                        ("GIN", 1),
                        ("SG", 10, (
                            ("CDI", 1),
                            ("INP", 5),
                        )),
                    )),
                )),
            )),
            ("SG", 9999, (
                ("LIN", 1),
                ("PIA", 10),
                ("IMD", 25),
                ("QTY", 10),
                ("QVR", 10),
                ("DTM", 5),
                ("SG", 10, (
                    ("CDI", 1),
                    ("INP", 5),
                )),
                ("SG", 10, (
                    ("DOC", 1),
                    ("SG", 10, (
                        ("CDI", 1),
                        ("INP", 5),
                    )),
                )),
                ("SG", 99, (
                    ("GIN", 1),
                    ("SG", 10, (
                        ("CDI", 1),
                        ("INP", 5),
                    )),
                )),
                ("SG", 10, (
                    ("RFF", 1),
                    ("DTM", 1),
                )),
                ("SG", 9999, (
                    ("PCI", 1),
                    ("QTY", 1),
                    ("QVR", 1),
                    ("SG", 10, (
                        ("CDI", 1),
                        ("INP", 5),
                    )),
                    ("SG", 10, (
                        ("GIN", 1),
                        ("SG", 10, (
                            ("CDI", 1),
                            ("INP", 5),
                        )),
                    )),
                )),
            )),
        )),
        ("CNT", 1),
    ),
    "INVOIC": (
        ("BGM", 1),
        ("DTM", 35),
        ("PAI", 1),
        ("ALI", 5),
        ("IMD", 1),
        ("FTX", 10),
        ("SG", 99, (
            ("RFF", 1),
            ("DTM", 5),
        )),
        ("SG", 99, (
            ("NAD", 1),
            ("LOC", 25),
            ("FII", 5),
            ("SG", 9999, (
                ("RFF", 1),
                ("DTM", 5),
            )),
            ("SG", 5, (
                ("DOC", 1),
                ("DTM", 5),
            )),
            ("SG", 5, (
                ("CTA", 1),
                ("COM", 5),
            )),
        )),
        ("SG", 5, (
            ("TAX", 1),
            ("MOA", 1),
            ("LOC", 5),
        )),
        ("SG", 5, (
            ("CUX", 1),
            ("DTM", 5),
        )),
        ("SG", 10, (
            ("PAT", 1),
            ("DTM", 5),
            ("PCD", 1),
            ("MOA", 1),
            ("PAI", 1),
            ("FII", 1),
        )),
        ("SG", 10, (
            ("TDT", 1),
            ("SG", 10, (
                ("LOC", 1),
                ("DTM", 5),
            )),
            ("SG", 9999, (
                ("RFF", 1),
                ("DTM", 5),
            )),
        )),
        ("SG", 5, (
            ("TOD", 1),
            ("LOC", 2),
        )),
        ("SG", 1000, (
            ("PAC", 1),
            ("MEA", 5),
            ("SG", 5, (
                ("PCI", 1),
                ("RFF", 1),
                ("DTM", 5),
                ("GIN", 5),
            )),
        )),
        ("SG", 9999, (
            ("ALC", 1),
            ("ALI", 5),
            ("SG", 5, (
                ("RFF", 1),
                ("DTM", 5),
            )),
            ("SG", 1, (
                ("QTY", 1),
                ("RNG", 1),
            )),
            ("SG", 1, (
                ("PCD", 1),
                ("RNG", 1),
            )),
            ("SG", 2, (
                ("MOA", 1),
                ("RNG", 1),
            )),
            ("SG", 1, (
                ("RTE", 1),
                ("RNG", 1),
            )),
            ("SG", 5, (
                ("TAX", 1),
                ("MOA", 1),
            )),
        )),
        ("SG", 100, (
            ("RCS", 1),
            ("RFF", 5),
            ("DTM", 5),
            ("FTX", 5),
        )),
        ("SG", 1, (
            ("AJT", 1),
            ("FTX", 5),
        )),
        ("SG", 1, (
            ("INP", 1),
            ("FTX", 5),
        )),
        ("SG", 9999999, (
            ("LIN", 1),
            ("PIA", 25),
            ("IMD", 10),
            ("MEA", 5),
            ("QTY", 5),
            ("PCD", 1),
            ("ALI", 5),
            ("DTM", 35),
            ("GIN", 1000),
            ("GIR", 1000),
            ("QVR", 1),
            ("EQD", 1),
            ("FTX", 5),
            ("SG", 5, (
                ("MOA", 1),
                ("CUX", 1),
            )),
            ("SG", 10, (
                ("PAT", 1),
                ("DTM", 5),
                ("PCD", 1),
                ("MOA", 1),
            )),
            ("SG", 25, (
                ("PRI", 1),
                ("APR", 1),
                ("RNG", 1),
                ("DTM", 5),
            )),
            ("SG", 10, (
                ("RFF", 1),
                ("DTM", 5),
            )),
            ("SG", 10, (
                ("PAC", 1),
                ("MEA", 10),
                ("SG", 10, (
                    ("PCI", 1),
                    ("RFF", 1),
                    ("DTM", 5),
                    ("GIN", 10),
                )),
            )),
            ("SG", 9999, (
                ("LOC", 1),
                ("QTY", 100),
                ("DTM", 5),
            )),
            ("SG", 99, (
                ("TAX", 1),
                ("MOA", 1),
                ("LOC", 5),
            )),
            ("SG", 20, (
                ("NAD", 1),
                ("LOC", 5),
                ("SG", 5, (
                    ("RFF", 1),
                    ("DTM", 5),
                )),
                ("SG", 5, (
                    ("DOC", 1),
                    ("DTM", 5),
                )),
                ("SG", 5, (
                    ("CTA", 1),
                    ("COM", 5),
                )),
            )),
            ("SG", 15, (
                ("ALC", 1),
                ("ALI", 5),
                ("DTM", 5),
                ("SG", 1, (
                    ("QTY", 1),
                    ("RNG", 1),
                )),
                ("SG", 1, (
                    ("PCD", 1),
                    ("RNG", 1),
                )),
                ("SG", 2, (
                    ("MOA", 1),
                    ("RNG", 1),
                )),
                ("SG", 1, (
                    ("RTE", 1),
                    ("RNG", 1),
                )),
                ("SG", 5, (
                    ("TAX", 1),
                    ("MOA", 1),
                )),
            )),
            ("SG", 10, (
                ("TDT", 1),
                ("SG", 10, (
                    ("LOC", 1),
                    ("DTM", 5),
                )),
            )),
            ("SG", 5, (
                ("TOD", 1),
                ("LOC", 2),
            )),
            ("SG", 100, (
                ("RCS", 1),
                ("RFF", 5),
                ("DTM", 5),
                ("FTX", 5),
            )),
        )),
        ("UNS", 1),
        ("CNT", 10),
        ("SG", 100, (
            ("MOA", 1),
            ("SG", 1, (
                ("RFF", 1),
                ("DTM", 5),
            )),
        )),
        ("SG", 10, (
            ("TAX", 1),
            ("MOA", 2),
        )),
        ("SG", 15, (
            ("ALC", 1),
            ("ALI", 1),
            ("MOA", 2),
        )),
    ),
    "REMADV": (
        ("BGM", 1),
        ("DTM", 5),
        ("RFF", 5),
        ("FII", 5),
        ("PAI", 1),
        ("FTX", 5),
        ("SG", 99, (
            ("NAD", 1),
            ("SG", 5, (
                ("CTA", 1),
                ("COM", 5),
            )),
        )),
        ("SG", 5, (
            ("CUX", 1),
            ("DTM", 1),
        )),
        ("SG", 9999, (
            ("DOC", 1),
            ("MOA", 5),
            ("DTM", 5),
            ("RFF", 5),
            ("NAD", 2),
            ("SG", 5, (
                ("CUX", 1),
                ("DTM", 1),
            )),
            ("SG", 100, (
                ("AJT", 1),
                ("MOA", 1),
                ("RFF", 1),
                ("FTX", 5),
            )),
            ("SG", 5, (
                ("INP", 1),
                ("FTX", 5),
            )),
            ("SG", 9999, (
                ("DLI", 1),
                ("MOA", 5),
                ("PIA", 5),
                ("DTM", 5),
                ("SG", 5, (
                    ("CUX", 1),
                    ("DTM", 1),
                )),
                ("SG", 10, (
                    ("AJT", 1),
                    ("MOA", 1),
                    ("RFF", 1),
                    ("FTX", 5),
                )),
            )),
        )),
        ("UNS", 1),
        ("MOA", 5),
    ),
    "PRICAT": (
        ("BGM", 1),
        ("DTM", 35),
        ("ALI", 5),
        ("FTX", 99),
        ("SG", 99, (
            ("RFF", 1),
            ("DTM", 5),
        )),
        ("SG", 99, (
            ("NAD", 1),
            ("LOC", 25),
            ("SG", 10, (
                ("RFF", 1),
                ("DTM", 5),
            )),
            ("SG", 5, (
                ("CTA", 1),
                ("COM", 5),
            )),
        )),
        ("SG", 5, (
            ("TAX", 1),
            ("MOA", 1),
        )),
        ("SG", 5, (
            ("CUX", 1),
            ("DTM", 5),
        )),
        ("SG", 10, (
            ("PAT", 1),
            ("DTM", 5),
            ("PCD", 1),
            ("MOA", 1),
        )),
        ("SG", 10, (
            ("TDT", 1),
            ("LOC", 10),
        )),
        ("SG", 5, (
            ("TOD", 1),
            ("LOC", 2),
        )),
        ("SG", 10, (
            ("ALC", 1),
            ("ALI", 5),
            ("DTM", 9),
            ("SG", 1, (
                ("QTY", 1),
                ("RNG", 1),
            )),
            ("SG", 1, (
                ("PCD", 1),
                ("RNG", 1),
            )),
            ("SG", 2, (
                ("MOA", 1),
                ("RNG", 1),
            )),
            ("SG", 1, (
                ("RTE", 1),
                ("RNG", 1),
            )),
            ("SG", 5, (
                ("TAX", 1),
                ("MOA", 1),
            )),
        )),
        ("SG", 1000, (
            ("PGI", 1),
            ("DTM", 15),
            ("QTY", 10),
            ("ALI", 5),
            ("FTX", 5),
            ("SG", 10, (
                ("CUX", 1),
                ("DTM", 5),
            )),
            ("SG", 100, (
                ("PRI", 1),
                ("CUX", 1),
                ("APR", 1),
                ("RNG", 1),
                ("DTM", 5),
            )),
            ("SG", 10, (
                ("TAX", 1),
                ("MOA", 1),
            )),
            ("SG", 99, (
                ("ALC", 1),
                ("ALI", 5),
                ("SG", 1, (
                    ("QTY", 1),
                    ("RNG", 1),
                )),
                ("SG", 1, (
                    ("PCD", 1),
                    ("RNG", 1),
                )),
                ("SG", 2, (
                    ("MOA", 1),
                    ("RNG", 1),
                )),
                ("SG", 1, (
                    ("RTE", 1),
                    ("RNG", 1),
                )),
                ("SG", 5, (
                    ("TAX", 1),
                    ("MOA", 1),
                )),
            )),
            ("SG", 20, (
                ("NAD", 1),
                ("LOC", 5),
                ("SG", 10, (
                    ("RFF", 1),
                    ("DTM", 5),
                )),
                ("SG", 5, (
                    ("CTA", 1),
                    ("COM", 5),
                )),
            )),
            ("SG", 10, (
                ("PAT", 1),
                ("DTM", 5),
                ("PCD", 1),
                ("MOA", 1),
            )),
            ("SG", 10, (
                ("TDT", 1),
                ("LOC", 10),
            )),
            ("SG", 5, (
                ("TOD", 1),
                ("LOC", 2),
            )),
            ("SG", 10, (
                ("PAC", 1),
                ("MEA", 10),
                ("HAN", 5),
            )),
            ("SG", 999999, (
                ("LIN", 1),
                ("PIA", 10),
                ("IMD", 999),
                ("MEA", 10),
                ("QTY", 10),
                ("HAN", 5),
                ("ALI", 5),
                ("DTM", 10),
                ("NAD", 99),
                ("RFF", 1),
                ("LOC", 1),
                ("DOC", 1),
                ("FTX", 5),
                ("SG", 999, (
                    ("CCI", 1),
                    ("CAV", 10),
                    ("MEA", 10),
                )),
                ("SG", 10, (
                    ("TAX", 1),
                    ("MOA", 1),
                )),
                ("SG", 5, (
                    ("CUX", 1),
                    ("DTM", 5),
                )),
                ("SG", 100, (
                    ("PRI", 1),
                    ("CUX", 1),
                    ("APR", 1),
                    ("RNG", 1),
                    ("DTM", 5),
                    ("PCD", 5),
                )),
                ("SG", 99, (
                    ("ALC", 1),
                    ("ALI", 5),
                    ("DTM", 9),
                    ("SG", 1, (
                        ("QTY", 1),
                        ("RNG", 1),
                    )),
                    ("SG", 1, (
                        ("PCD", 1),
                        ("RNG", 1),
                    )),
                    ("SG", 2, (
                        ("MOA", 1),
                        ("RNG", 1),
                    )),
                    ("SG", 1, (
                        ("RTE", 1),
                        ("RNG", 1),
                    )),
                    ("SG", 5, (
                        ("TAX", 1),
                        ("MOA", 1),
                    )),
                )),
                ("SG", 10, (
                    ("PAC", 1),
                    ("MEA", 10),
                    ("HAN", 5),
                )),
                ("SG", 10, (
                    ("PAT", 1),
                    ("DTM", 5),
                    ("PCD", 1),
                    ("MOA", 1),
                )),
                ("SG", 10, (
                    ("TDT", 1),
                    ("LOC", 10),
                )),
                ("SG", 5, (
                    ("TOD", 1),
                    ("LOC", 2),
                )),
            )),
        )),
    ),
    "SLSRPT": (
        ("BGM", 1),
        ("DTM", 5),
        ("SG", 5, (
            ("NAD", 1),
            ("SG", 5, (
                ("CTA", 1),
                ("COM", 5),
            )),
        )),
        ("SG", 5, (
            ("RFF", 1),
            ("DTM", 5),
        )),
        ("SG", 5, (
            ("CUX", 1),
            ("DTM", 5),
        )),
        ("SG", 200000, (
            ("LOC", 1),
            ("DTM", 5),
            ("SG", 99, (
                ("RFF", 1),
                ("DTM", 5),
            )),
            ("SG", 200000, (
                ("LIN", 1),
                ("PIA", 5),
                ("IMD", 5),
                ("PAC", 5),
                ("RFF", 5),
                ("DOC", 5),
                ("ALI", 5),
                ("MOA", 5),
                ("PRI", 5),
                ("GIN", 9999),
                ("SG", 999, (
                    ("QTY", 1),
                    ("MKS", 1),
                    ("NAD", 1),
                )),
            )),
        )),
    ),
    "INVRPT": (
        ("BGM", 1),
        ("DTM", 10),
        ("SG", 10, (
            ("RFF", 1),
            ("DTM", 1),
        )),
        ("SG", 20, (
            ("NAD", 1),
            ("LOC", 5),
            ("SG", 10, (
                ("RFF", 1),
                ("DTM", 1),
            )),
            ("SG", 10, (
                ("CTA", 1),
                ("COM", 5),
            )),
        )),
        ("SG", 5, (
            ("CUX", 1),
            ("DTM", 1),
        )),
        ("SG", 9999, (
            ("CPS", 1),
            ("SG", 999, (
                ("PAC", 1),
                ("PCI", 1000),
                ("SG", 9999, (
                    ("QTY", 1),
                    ("GIN", 9999),
                    ("DTM", 5),
                )),
            )),
        )),
        ("SG", 9999, (
            ("LIN", 1),
            ("PIA", 10),
            ("IMD", 10),
            ("MEA", 10),
            ("ALI", 10),
            ("LOC", 5),
            ("DTM", 5),
            ("SG", 10, (
                ("RFF", 1),
                ("DTM", 1),
            )),
            ("SG", 9999, (
                ("QTY", 1),
                ("INV", 1),
                ("GIN", 9999),
                ("LOC", 5),
                ("DTM", 5),
                ("STS", 9),
                ("SG", 5, (
                    ("NAD", 1),
                    ("LOC", 1),
                )),
                ("SG", 5, (
                    ("PRI", 1),
                    ("CUX", 1),
                    ("DTM", 1),
                )),
                ("SG", 10, (
                    ("RFF", 1),
                    ("DTM", 1),
                )),
                ("SG", 9999, (
                    ("CPS", 1),
                    ("SG", 9999, (
                        ("PAC", 1),
                        ("MEA", 10),
                        ("QTY", 10),
                        ("SG", 9999, (
                            ("PCI", 1),
                            ("RFF", 1),
                            ("DTM", 5),
                            ("GIN", 9999),
                        )),
                    )),
                )),
            )),
        )),
    ),
    "DELFOR": (
        ("BGM", 1),
        ("DTM", 10),
        ("SG", 10, (
            ("RFF", 1),
            ("DTM", 1),
        )),
        ("SG", 20, (
            ("NAD", 1),
            ("LOC", 10),
            ("SG", 5, (
                ("CTA", 1),
                ("COM", 5),
            )),
        )),
        ("UNS", 1),
        ("SG", 500, (
            ("NAD", 1),
            ("LOC", 10),
            ("FTX", 5),
            ("SG", 10, (
                ("DOC", 1),
                ("DTM", 10),
            )),
            ("SG", 5, (
                ("CTA", 1),
                ("COM", 5),
            )),
            ("SG", 10, (
                ("TDT", 1),
                ("DTM", 5),
            )),
            ("SG", 9999, (
                ("LIN", 1),
                ("PIA", 10),
                ("IMD", 10),
                ("MEA", 5),
                ("ALI", 5),
                ("GIN", 100),
                ("GIR", 100),
                ("LOC", 100),
                ("DTM", 5),
                ("FTX", 5),
                ("SG", 5, (
                    ("CTA", 1),
                    ("COM", 5),
                )),
                ("SG", 10, (
                    ("RFF", 1),
                    ("DTM", 1),
                )),
                ("SG", 10, (
                    ("TDT", 1),
                    ("DTM", 5),
                )),
                ("SG", 200, (
                    ("QTY", 1),
                    ("SCC", 1),
                    ("DTM", 2),
                    ("SG", 10, (
                        ("RFF", 1),
                        ("DTM", 1),
                    )),
                )),
                ("SG", 50, (
                    ("PAC", 1),
                    ("MEA", 10),
                    ("QTY", 5),
                    ("DTM", 5),
                    ("SG", 10, (
                        ("PCI", 1),
                        ("GIN", 10),
                    )),
                    ("SG", 10, (
                        ("QVR", 1),
                        ("DTM", 5),
                        ("SG", 10, (
                            ("RFF", 1),
                            ("DTM", 1),
                        )),
                    )),
                )),
            )),
        )),
        ("SG", 9999, (
            ("LIN", 1),
            ("PIA", 10),
            ("IMD", 10),
            ("MEA", 5),
            ("ALI", 5),
            ("GIN", 100),
            ("GIR", 100),
            ("DTM", 5),
            ("FTX", 5),
            ("SG", 10, (
                ("RFF", 1),
                ("DTM", 1),
            )),
            ("SG", 50, (
                ("QTY", 1),
                ("SCC", 1),
                ("DTM", 2),
                ("SG", 10, (
                    ("RFF", 1),
                    ("DTM", 1),
                )),
            )),
            ("SG", 10, (
                ("PAC", 1),
                ("MEA", 10),
                ("QTY", 5),
                ("DTM", 5),
                ("SG", 10, (
                    ("PCI", 1),
                    ("GIN", 10),
                )),
            )),
            ("SG", 500, (
                ("NAD", 1),
                ("LOC", 10),
                ("FTX", 5),
                ("SG", 10, (
                    ("DOC", 1),
                    ("DTM", 1),
                )),
                ("SG", 5, (
                    ("CTA", 1),
                    ("COM", 5),
                )),
                ("SG", 50, (
                    ("QTY", 1),
                    ("SCC", 1),
                    ("DTM", 2),
                    ("SG", 10, (
                        ("RFF", 1),
                        ("DTM", 1),
                    )),
                )),
                ("SG", 10, (
                    ("QVR", 1),
                    ("DTM", 5),
                    ("SG", 10, (
                        ("RFF", 1),
                        ("DTM", 1),
                    )),
                )),
                ("SG", 10, (
                    ("TDT", 1),
                    ("DTM", 5),
                )),
            )),
        )),
        ("UNS", 1),
        ("CNT", 5),
        ("FTX", 5),
    ),
    "DELJIT": (
        ("BGM", 1),
        ("DTM", 10),
        ("SG", 10, (
            ("RFF", 1),
            ("DTM", 1),
        )),
        ("SG", 20, (
            ("NAD", 1),
            ("LOC", 10),
            ("FTX", 5),
            ("SG", 5, (
                ("CTA", 1),
                ("COM", 5),
            )),
        )),
        ("SG", 9999, (
            ("SEQ", 1),
            ("DTM", 5),
            ("GIR", 99),
            ("LOC", 5),
            ("SG", 5, (
                ("PAC", 1),
                ("SG", 999, (
                    ("PCI", 1),
                    ("GIN", 10),
                )),
            )),
            ("SG", 9999, (
                ("LIN", 1),
                ("PIA", 10),
                ("IMD", 10),
                ("ALI", 5),
                ("GIR", 5),
                ("TDT", 5),
                ("FTX", 5),
                ("PAC", 5),
                ("DTM", 5),
                ("SG", 5, (
                    ("RFF", 1),
                    ("DTM", 1),
                )),
                ("SG", 5, (
                    ("LOC", 1),
                    ("SG", 5, (
                        ("CTA", 1),
                        ("COM", 5),
                    )),
                )),
                ("SG", 100, (
                    ("QTY", 1),
                    ("SCC", 1),
                    ("DTM", 2),
                    ("SG", 5, (
                        ("RFF", 1),
                        ("DTM", 1),
                    )),
                )),
            )),
        )),
        ("FTX", 5),
    ),
    "PARTIN": (
        ("BGM", 1),
        ("DTM", 5),
        ("FII", 10),
        ("FTX", 5),
        ("SG", 5, (
            ("RFF", 1),
            ("DTM", 1),
        )),
        ("SG", 2, (
            ("NAD", 1),
            ("SG", 5, (
                ("CTA", 1),
                ("COM", 5),
            )),
        )),
        ("UNS", 1),
        ("SG", 200000, (
            ("NAD", 1),
            ("DTM", 5),
            ("FII", 10),
            ("SG", 99, (
                ("LOC", 1),
                ("DTM", 2),
            )),
            ("SG", 15, (
                ("RFF", 1),
                ("DTM", 1),
            )),
            ("SG", 5, (
                ("CTA", 1),
                ("COM", 5),
            )),
            ("SG", 10, (
                ("SCC", 1),
                ("DTM", 2),
            )),
            ("SG", 1, (
                ("TOD", 1),
                ("LOC", 1),
            )),
            ("SG", 1, (
                ("PAI", 1),
                ("PAT", 1),
                ("CUX", 2),
            )),
        )),
    ),
    "REQOTE": (
        ("BGM", 1),
        ("DTM", 35),
        ("PAI", 1),
        ("ALI", 5),
        ("IMD", 1),
        ("IRQ", 10),
        ("FTX", 99),
        ("SG", 10, (
            ("RFF", 1),
            ("DTM", 5),
        )),
        ("SG", 1, (
            ("AJT", 1),
            ("FTX", 5),
        )),
        ("SG", 5, (
            ("TAX", 1),
            ("MOA", 1),
            ("LOC", 5),
        )),
        ("SG", 5, (
            ("CUX", 1),
            ("DTM", 5),
        )),
        ("SG", 10, (
            ("PAT", 1),
            ("DTM", 5),
            ("PCD", 1),
            ("MOA", 1),
        )),
        ("SG", 10, (
            ("TOD", 1),
            ("LOC", 2),
        )),
        ("SG", 10, (
            ("EQD", 1),
            ("HAN", 5),
            ("MEA", 5),
            ("FTX", 5),
        )),
        ("SG", 10, (
            ("RCS", 1),
            ("RFF", 5),
            ("DTM", 5),
            ("FTX", 5),
        )),
        ("SG", 25, (
            ("APR", 1),
            ("PRI", 1),
            ("QTY", 2),
            ("DTM", 1),
            ("MOA", 2),
            ("RNG", 2),
        )),
        ("SG", 1, (
            ("DLM", 1),
            ("MOA", 1),
            ("DTM", 1),
        )),
        ("SG", 99, (
            ("NAD", 1),
            ("LOC", 25),
            ("FII", 5),
            ("SG", 10, (
                ("RFF", 1),
                ("DTM", 5),
            )),
            ("SG", 5, (
                ("DOC", 1),
                ("DTM", 1),
            )),
            ("SG", 5, (
                ("CTA", 1),
                ("COM", 5),
            )),
        )),
        ("SG", 10, (
            ("TDT", 1),
            ("QTY", 5),
            ("SG", 10, (
                ("LOC", 1),
                ("DTM", 5),
            )),
        )),
        ("SG", 10, (
            ("PAC", 1),
            ("MEA", 5),
            ("SG", 10, (
                ("PCI", 1),
                ("RFF", 1),
                ("DTM", 5),
                ("GIN", 10),
            )),
        )),
        ("SG", 10, (
            ("SCC", 1),
            ("FTX", 5),
            ("SG", 10, (
                ("QTY", 1),
                ("DTM", 5),
            )),
        )),
        ("SG", 15, (
            ("ALC", 1),
            ("ALI", 5),
            ("SG", 1, (
                ("QTY", 1),
                ("RNG", 1),
            )),
            ("SG", 1, (
                ("PCD", 1),
                ("RNG", 1),
            )),
            ("SG", 2, (
                ("MOA", 1),
                ("RNG", 1),
            )),
            ("SG", 1, (
                ("RTE", 1),
                ("RNG", 1),
            )),
            ("SG", 5, (
                ("TAX", 1),
                ("MOA", 1),
            )),
        )),
        ("SG", 200000, (
            ("LIN", 1),
            ("PIA", 25),
            ("IMD", 99),
            ("MEA", 5),
            ("QTY", 5),
            ("PCD", 1),
            ("ALI", 5),
            ("DTM", 35),
            ("GIN", 1000),
            ("GIR", 1000),
            ("QVR", 1),
            ("FTX", 99),
            ("PAI", 1),
            ("DOC", 1),
            ("SG", 999, (
                ("CCI", 1),
                ("CAV", 10),
                ("MEA", 10),
            )),
            ("SG", 100, (
                ("MOA", 1),
                ("QTY", 2),
                ("IMD", 1),
                ("CUX", 1),
                ("DTM", 2),
            )),
            ("SG", 1, (
                ("AJT", 1),
                ("FTX", 5),
            )),
            ("SG", 99, (
                ("PRI", 1),
                ("APR", 1),
                ("RNG", 1),
                ("CUX", 5),
                ("DTM", 5),
            )),
            ("SG", 99, (
                ("RFF", 1),
                ("DTM", 5),
            )),
            ("SG", 100, (
                ("LOC", 1),
                ("QTY", 1),
                ("DTM", 5),
            )),
            ("SG", 10, (
                ("TAX", 1),
                ("MOA", 1),
                ("LOC", 5),
            )),
            ("SG", 5, (
                ("TOD", 1),
                ("LOC", 2),
            )),
            ("SG", 10, (
                ("EQD", 1),
                ("HAN", 5),
                ("MEA", 5),
                ("FTX", 5),
            )),
            ("SG", 10, (
                ("RCS", 1),
                ("RFF", 5),
                ("DTM", 5),
                ("FTX", 5),
            )),
            ("SG", 10, (
                ("PAT", 1),
                ("DTM", 5),
                ("PCD", 1),
                ("MOA", 1),
            )),
            ("SG", 10, (
                ("PAC", 1),
                ("MEA", 5),
                ("QTY", 5),
                ("DTM", 5),
                ("SG", 5, (
                    ("RFF", 1),
                    ("DTM", 5),
                )),
                ("SG", 10, (
                    ("PCI", 1),
                    ("RFF", 1),
                    ("DTM", 5),
                    ("GIN", 10),
                )),
            )),
            ("SG", 99, (
                ("NAD", 1),
                ("LOC", 5),
                ("SG", 5, (
                    ("RFF", 1),
                    ("DTM", 5),
                )),
                ("SG", 5, (
                    ("DOC", 1),
                    ("DTM", 5),
                )),
                ("SG", 5, (
                    ("CTA", 1),
                    ("COM", 5),
                )),
            )),
            ("SG", 99, (
                ("ALC", 1),
                ("ALI", 5),
                ("SG", 1, (
                    ("QTY", 1),
                    ("RNG", 1),
                )),
                ("SG", 1, (
                    ("PCD", 1),
                    ("RNG", 1),
                )),
                ("SG", 2, (
                    ("MOA", 1),
                    ("RNG", 1),
                )),
                ("SG", 1, (
                    ("RTE", 1),
                    ("RNG", 1),
                )),
                ("SG", 5, (
                    ("TAX", 1),
                    ("MOA", 1),
                )),
            )),
            ("SG", 10, (
                ("TDT", 1),
                ("QTY", 5),
                ("SG", 10, (
                    ("LOC", 1),
                    ("DTM", 5),
                )),
            )),
            ("SG", 100, (
                ("SCC", 1),
                ("FTX", 5),
                ("SG", 10, (
                    ("QTY", 1),
                    ("DTM", 5),
                )),
            )),
        )),
        ("UNS", 1),
        ("MOA", 15),
        ("CNT", 10),
        ("SG", 10, (
            ("ALC", 1),
            ("MOA", 1),
            ("ALI", 1),
        )),
    ),
    "QUOTES": (
        ("BGM", 1),
        ("DTM", 35),
        ("PAI", 1),
        ("ALI", 5),
        ("IMD", 1),
        ("IRQ", 10),
        ("FTX", 99),
        ("SG", 10, (
            ("RFF", 1),
            ("DTM", 5),
        )),
        ("SG", 1, (
            ("AJT", 1),
            ("FTX", 5),
        )),
        ("SG", 5, (
            ("TAX", 1),
            ("MOA", 1),
            ("LOC", 5),
        )),
        ("SG", 5, (
            ("CUX", 1),
            ("PCD", 5),
            ("DTM", 5),
        )),
        ("SG", 10, (
            ("PAT", 1),
            ("DTM", 5),
            ("PCD", 1),
            ("MOA", 1),
        )),
        ("SG", 10, (
            ("TOD", 1),
            ("LOC", 2),
        )),
        ("SG", 10, (
            ("EQD", 1),
            ("HAN", 5),
            ("MEA", 5),
            ("FTX", 5),
        )),
        ("SG", 10, (
            ("RCS", 1),
            ("RFF", 5),
            ("DTM", 5),
            ("FTX", 5),
        )),
        ("SG", 25, (
            ("APR", 1),
            ("PRI", 1),
            ("QTY", 2),
            ("DTM", 1),
            ("MOA", 2),
            ("RNG", 2),
        )),
        ("SG", 1, (
            ("DLM", 1),
            ("MOA", 1),
            ("DTM", 1),
        )),
        ("SG", 99, (
            ("NAD", 1),
            ("LOC", 25),
            ("FII", 5),
            ("SG", 10, (
                ("RFF", 1),
                ("DTM", 5),
                ("LOC", 5),
            )),
            ("SG", 5, (
                ("DOC", 1),
                ("DTM", 1),
            )),
            ("SG", 5, (
                ("CTA", 1),
                ("COM", 5),
            )),
        )),
        ("SG", 10, (
            ("TDT", 1),
            ("QTY", 5),
            ("SG", 10, (
                ("LOC", 1),
                ("DTM", 5),
            )),
        )),
        ("SG", 10, (
            ("PAC", 1),
            ("MEA", 5),
            ("SG", 10, (
                ("PCI", 1),
                ("RFF", 1),
                ("DTM", 5),
                ("GIN", 10),
            )),
        )),
        ("SG", 10, (
            ("SCC", 1),
            ("FTX", 5),
            ("SG", 10, (
                ("QTY", 1),
                ("DTM", 5),
            )),
        )),
        ("SG", 15, (
            ("ALC", 1),
            ("ALI", 5),
            ("DTM", 5),
            ("SG", 1, (
                ("QTY", 1),
                ("RNG", 1),
            )),
            ("SG", 1, (
                ("PCD", 1),
                ("RNG", 1),
            )),
            ("SG", 2, (
                ("MOA", 1),
                ("RNG", 1),
            )),
            ("SG", 1, (
                ("RTE", 1),
                ("RNG", 1),
            )),
            ("SG", 5, (
                ("TAX", 1),
                ("MOA", 1),
            )),
        )),
        ("SG", 200000, (
            ("LIN", 1),
            ("PIA", 25),
            ("IMD", 99),
            ("MEA", 5),
            ("QTY", 5),
            ("PCD", 1),
            ("ALI", 5),
            ("DTM", 35),
            ("GIN", 1000),
            ("GIR", 1000),
            ("QVR", 1),
            ("FTX", 99),
            ("DGS", 1),
            ("PAI", 1),
            ("DOC", 1),
            ("SG", 999, (
                ("CCI", 1),
                ("CAV", 10),
                ("MEA", 10),
            )),
            ("SG", 100, (
                ("MOA", 1),
                ("QTY", 2),
                ("IMD", 1),
                ("CUX", 1),
                ("DTM", 2),
            )),
            ("SG", 1, (
                ("AJT", 1),
                ("FTX", 5),
            )),
            ("SG", 99, (
                ("PRI", 1),
                ("APR", 1),
                ("RNG", 1),
                ("CUX", 5),
                ("DTM", 5),
            )),
            ("SG", 99, (
                ("RFF", 1),
                ("DTM", 5),
            )),
            ("SG", 100, (
                ("LOC", 1),
                ("QTY", 1),
                ("DTM", 5),
            )),
            ("SG", 10, (
                ("TAX", 1),
                ("MOA", 1),
                ("LOC", 5),
            )),
            ("SG", 5, (
                ("TOD", 1),
                ("LOC", 2),
            )),
            ("SG", 10, (
                ("EQD", 1),
                ("HAN", 5),
                ("MEA", 5),
                ("FTX", 5),
            )),
            ("SG", 10, (
                ("RCS", 1),
                ("RFF", 5),
                ("DTM", 5),
                ("FTX", 5),
            )),
            ("SG", 10, (
                ("PAT", 1),
                ("DTM", 5),
                ("PCD", 1),
                ("MOA", 1),
            )),
            ("SG", 10, (
                ("PAC", 1),
                ("MEA", 5),
                ("QTY", 5),
                ("DTM", 5),
                ("SG", 5, (
                    ("RFF", 1),
                    ("DTM", 5),
                )),
                ("SG", 10, (
                    ("PCI", 1),
                    ("RFF", 1),
                    ("DTM", 5),
                    ("GIN", 10),
                )),
            )),
            ("SG", 99, (
                ("NAD", 1),
                ("LOC", 5),
                ("SG", 5, (
                    ("RFF", 1),
                    ("DTM", 5),
                )),
                ("SG", 5, (
                    ("DOC", 1),
                    ("DTM", 5),
                )),
                ("SG", 5, (
                    ("CTA", 1),
                    ("COM", 5),
                )),
            )),
            ("SG", 99, (
                ("ALC", 1),
                ("ALI", 5),
                ("DTM", 5),
                ("SG", 10, (
                    ("QTY", 1),
                    ("RNG", 1),
                )),
                ("SG", 10, (
                    ("PCD", 1),
                    ("RNG", 1),
                )),
                ("SG", 10, (
                    ("MOA", 1),
                    ("RNG", 1),
                )),
                ("SG", 10, (
                    ("RTE", 1),
                    ("RNG", 1),
                )),
                ("SG", 5, (
                    ("TAX", 1),
                    ("MOA", 1),
                )),
            )),
            ("SG", 10, (
                ("TDT", 1),
                ("QTY", 5),
                ("SG", 10, (
                    ("LOC", 1),
                    ("DTM", 5),
                )),
            )),
            ("SG", 100, (
                ("SCC", 1),
                ("FTX", 5),
                ("SG", 10, (
                    ("QTY", 1),
                    ("DTM", 5),
                )),
            )),
        )),
        ("UNS", 1),
        ("MOA", 15),
        ("CNT", 10),
        ("SG", 10, (
            ("ALC", 1),
            ("MOA", 1),
            ("ALI", 1),
        )),
    ),
}

# --- BODY-DEFS-START (X12/TRADACOMS/HL7 data segment tables) ---

X12_BODY_SEGMENT_DEFS = {
    "AK1": ("functional_group_response_header", (
        "functional_identifier_code",
        "group_control_number",
    )),
    "AK2": ("transaction_set_response_header", (
        "transaction_set_identifier_code",
        "transaction_set_control_number",
    )),
    "AK5": ("transaction_set_response_trailer", (
        "transaction_set_acknowledgment_code",
        "transaction_set_syntax_error_code",
        "transaction_set_syntax_error_code",
        "transaction_set_syntax_error_code",
        "transaction_set_syntax_error_code",
        "transaction_set_syntax_error_code",
    )),
    "AK9": ("functional_group_response_trailer", (
        "functional_group_acknowledge_code",
        "number_of_transaction_sets_included",
        "number_of_received_transaction_sets",
        "number_of_accepted_transaction_sets",
        "functional_group_syntax_error_code",
        "functional_group_syntax_error_code",
        "functional_group_syntax_error_code",
        "functional_group_syntax_error_code",
        "functional_group_syntax_error_code",
    )),
    "AMT": ("monetary_amount", (
        "amount_qualifier_code",
        "monetary_amount",
        "credit_debit_flag_code",
    )),
    "BAK": ("beginning_segment_for_purchase_order_acknowledgment", (
        "transaction_set_purpose_code",
        "acknowledgment_type",
        "purchase_order_number",
        "date",
        "release_number",
        "request_reference_number",
        "contract_number",
        "reference_identification",
        "date",
        "transaction_type_code",
    )),
    "BEG": ("beginning_segment_for_purchase_order", (
        "transaction_set_purpose_code",
        "purchase_order_type_code",
        "purchase_order_number",
        "release_number",
        "date",
        "contract_number",
        "acknowledgment_type",
        "invoice_type_code",
        "contract_type_code",
        "purchase_category",
        "security_level_code",
        "transaction_type_code",
    )),
    "BHT": ("beginning_of_hierarchical_transaction", (
        "hierarchical_structure_code",
        "transaction_set_purpose_code",
        "reference_identification",
        "date",
        "time",
        "transaction_type_code",
    )),
    "BIG": ("beginning_segment_for_invoice", (
        "date",
        "invoice_number",
        "date",
        "purchase_order_number",
        "release_number",
        "change_order_sequence_number",
        "transaction_type_code",
        "transaction_set_purpose_code",
        "action_code",
        "invoice_number",
    )),
    "BSN": ("beginning_segment_for_ship_notice", (
        "transaction_set_purpose_code",
        "shipment_identification",
        "date",
        "time",
        "hierarchical_structure_code",
        "transaction_type_code",
        "status_reason_code",
    )),
    "CAD": ("carrier_detail", (
        "transportation_method_type_code",
        "equipment_initial",
        "equipment_number",
        "standard_carrier_alpha_code",
        "routing",
        "shipment_order_status_code",
        "reference_identification_qualifier",
        "reference_identification",
        "service_level_code",
    )),
    "CSH": ("sales_requirements", (
        "sales_requirement_code",
        "action_code",
        "amount",
        "account_number",
        "date",
        "agency_qualifier_code",
        "special_services_code",
        "product_service_substitution_code",
        "percent",
    )),
    "CTP": ("pricing_information", (
        "class_of_trade_code",
        "price_identifier_code",
        "unit_price",
        "quantity",
        "composite_unit_of_measure",
        "price_multiplier_qualifier",
        "multiplier",
        "monetary_amount",
        "basis_of_unit_price_code",
        "condition_value",
        "multiple_price_quantity",
    )),
    "CTT": ("transaction_totals", (
        "number_of_line_items",
        "hash_total",
        "weight",
        "unit_or_basis_for_measurement_code",
        "volume",
        "unit_or_basis_for_measurement_code",
        "description",
    )),
    "CUR": ("currency", (
        "entity_identifier_code",
        "currency_code",
        "exchange_rate",
        "entity_identifier_code",
        "currency_code",
        "currency_market_exchange_code",
        "date_time_qualifier",
        "date",
        "time",
        "date_time_qualifier",
        "date",
        "time",
        "date_time_qualifier",
        "date",
        "time",
        "date_time_qualifier",
        "date",
        "time",
        "date_time_qualifier",
        "date",
        "time",
    )),
    "DMG": ("demographic_information", (
        "date_time_period_format_qualifier",
        "date_time_period",
        "gender_code",
        "marital_status_code",
        "race_or_ethnicity_code",
        "citizenship_status_code",
        "country_code",
        "basis_of_verification_code",
        "quantity",
    )),
    "DTM": ("date_time_reference", (
        "date_time_qualifier",
        "date",
        "time",
        "time_code",
        "date_time_period_format_qualifier",
        "date_time_period",
    )),
    "FOB": ("f_o_b_related_instructions", (
        "shipment_method_of_payment",
        "location_qualifier",
        "description",
        "transportation_terms_qualifier_code",
        "transportation_terms_code",
        "location_qualifier",
        "description",
        "risk_of_loss_code",
        "description",
    )),
    "HL": ("hierarchical_level", (
        "hierarchical_id_number",
        "hierarchical_parent_id_number",
        "hierarchical_level_code",
        "hierarchical_child_code",
    )),
    "ISS": ("invoice_shipment_summary", (
        "number_of_units_shipped",
        "unit_or_basis_for_measurement_code",
        "weight",
        "unit_or_basis_for_measurement_code",
        "volume",
        "unit_or_basis_for_measurement_code",
    )),
    "IT1": ("baseline_item_data_invoice", (
        "assigned_identification",
        "quantity_invoiced",
        "unit_or_basis_for_measurement_code",
        "unit_price",
        "basis_of_unit_price_code",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
    )),
    "ITD": ("terms_of_sale_deferred_terms_of_sale", (
        "terms_type_code",
        "terms_basis_date_code",
        "terms_discount_percent",
        "terms_discount_due_date",
        "terms_discount_days_due",
        "terms_net_due_date",
        "terms_net_days",
        "terms_discount_amount",
        "deferred_due_date",
        "deferred_amount_due",
        "percent_of_invoice_payable",
        "description",
        "day_of_month",
        "payment_method_code",
        "percent",
    )),
    "LDT": ("lead_time", (
        "lead_time_code",
        "quantity",
        "unit_of_time_period_or_interval",
        "date",
    )),
    "LIN": ("item_identification", (
        "assigned_identification",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
    )),
    "MAN": ("marks_and_numbers", (
        "marks_and_numbers_qualifier",
        "marks_and_numbers",
        "marks_and_numbers",
        "marks_and_numbers_qualifier",
        "marks_and_numbers",
        "marks_and_numbers",
    )),
    "MEA": ("measurements", (
        "measurement_reference_id_code",
        "measurement_qualifier",
        "measurement_value",
        "composite_unit_of_measure",
        "range_minimum",
        "range_maximum",
        "measurement_significance_code",
        "measurement_attribute_code",
        "surface_layer_position_code",
        "measurement_method_or_device",
    )),
    "MSG": ("message_text", (
        "free_form_message_text",
        "printer_carriage_control_code",
        "number",
    )),
    "N1": ("name", (
        "entity_identifier_code",
        "name",
        "identification_code_qualifier",
        "identification_code",
        "entity_relationship_code",
        "entity_identifier_code",
    )),
    "N2": ("additional_name_information", (
        "name",
        "name",
    )),
    "N3": ("address_information", (
        "address_information",
        "address_information",
    )),
    "N4": ("geographic_location", (
        "city_name",
        "state_or_province_code",
        "postal_code",
        "country_code",
        "location_qualifier",
        "location_identifier",
    )),
    "NTE": ("note_special_instruction", (
        "note_reference_code",
        "description",
    )),
    "PER": ("administrative_communications_contact", (
        "contact_function_code",
        "name",
        "communication_number_qualifier",
        "communication_number",
        "communication_number_qualifier",
        "communication_number",
        "communication_number_qualifier",
        "communication_number",
        "contact_inquiry_reference",
    )),
    "PID": ("product_item_description", (
        "item_description_type",
        "product_process_characteristic_code",
        "agency_qualifier_code",
        "product_description_code",
        "description",
        "surface_layer_position_code",
        "source_subqualifier",
        "yes_no_condition_or_response_code",
        "language_code",
    )),
    "PKG": ("marking_packaging_loading", (
        "item_description_type",
        "packaging_characteristic_code",
        "agency_qualifier_code",
        "packaging_description_code",
        "description",
        "unit_load_option_code",
    )),
    "PO1": ("baseline_item_data", (
        "assigned_identification",
        "quantity_ordered",
        "unit_or_basis_for_measurement_code",
        "unit_price",
        "basis_of_unit_price_code",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
    )),
    "PO4": ("item_physical_details", (
        "pack",
        "size",
        "unit_or_basis_for_measurement_code",
        "packaging_code",
        "weight_qualifier",
        "gross_weight_per_pack",
        "unit_or_basis_for_measurement_code",
        "gross_volume_per_pack",
        "unit_or_basis_for_measurement_code",
        "length",
        "width",
        "height",
        "unit_or_basis_for_measurement_code",
        "inner_pack",
        "surface_layer_position_code",
        "assigned_identification",
        "assigned_identification",
        "number",
    )),
    "POC": ("line_item_change", (
        "assigned_identification",
        "change_or_response_type_code",
        "quantity_ordered",
        "quantity_left_to_receive",
        "composite_unit_of_measure",
        "unit_price",
        "basis_of_unit_price_code",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
    )),
    "PRF": ("purchase_order_reference", (
        "purchase_order_number",
        "release_number",
        "change_order_sequence_number",
        "date",
        "assigned_identification",
        "contract_number",
        "purchase_order_type_code",
    )),
    "PWK": ("paperwork", (
        "report_type_code",
        "report_transmission_code",
        "report_copies_needed",
        "entity_identifier_code",
        "identification_code_qualifier",
        "identification_code",
        "description",
        "actions_indicated",
        "request_category_code",
    )),
    "QTY": ("quantity", (
        "quantity_qualifier",
        "quantity",
        "composite_unit_of_measure",
        "free_form_message",
    )),
    "REF": ("reference_identification", (
        "reference_identification_qualifier",
        "reference_identification",
        "description",
        "reference_identifier",
    )),
    "SAC": ("service_promotion_allowance_or_charge_information", (
        "allowance_or_charge_indicator",
        "service_promotion_allowance_or_charge_code",
        "agency_qualifier_code",
        "agency_service_promotion_allowance_or_charge_code",
        "amount",
        "allowance_charge_percent_qualifier",
        "percent",
        "rate",
        "unit_or_basis_for_measurement_code",
        "quantity",
        "quantity",
        "allowance_or_charge_method_of_handling_code",
        "reference_identification",
        "option_number",
        "description",
        "language_code",
    )),
    "SCH": ("line_item_schedule", (
        "quantity",
        "unit_or_basis_for_measurement_code",
        "entity_identifier_code",
        "name",
        "date_time_qualifier",
        "date",
        "time",
        "date_time_qualifier",
        "date",
        "time",
        "request_reference_number",
        "assigned_identification",
    )),
    "SLN": ("subline_item_detail", (
        "assigned_identification",
        "assigned_identification",
        "relationship_code",
        "quantity",
        "composite_unit_of_measure",
        "unit_price",
        "basis_of_unit_price_code",
        "relationship_code",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
        "product_service_id_qualifier",
        "product_service_id",
    )),
    "SN1": ("item_detail_shipment", (
        "assigned_identification",
        "number_of_units_shipped",
        "unit_or_basis_for_measurement_code",
        "quantity_shipped_to_date",
        "quantity_ordered",
        "unit_or_basis_for_measurement_code",
        "returnable_container_load_make_up_code",
        "line_item_status_code",
    )),
    "TD1": ("carrier_details_quantity_and_weight", (
        "packaging_code",
        "lading_quantity",
        "commodity_code_qualifier",
        "commodity_code",
        "lading_description",
        "weight_qualifier",
        "weight",
        "unit_or_basis_for_measurement_code",
        "volume",
        "unit_or_basis_for_measurement_code",
    )),
    "TD3": ("carrier_details_equipment", (
        "equipment_description_code",
        "equipment_initial",
        "equipment_number",
        "weight_qualifier",
        "weight",
        "unit_or_basis_for_measurement_code",
        "ownership_code",
        "seal_status_code",
        "seal_number",
    )),
    "TD5": ("carrier_details_routing_sequence_transit_time", (
        "routing_sequence_code",
        "identification_code_qualifier",
        "identification_code",
        "transportation_method_type_code",
        "routing",
        "shipment_order_status_code",
        "location_qualifier",
        "location_identifier",
        "transit_direction_code",
        "transit_time_direction_qualifier",
        "transit_time",
        "service_level_code",
        "service_level_code",
        "service_level_code",
        "country_code",
    )),
    "TDS": ("total_monetary_value_summary", (
        "amount",
        "amount",
        "amount",
        "amount",
    )),
    "TXI": ("tax_information", (
        "tax_type_code",
        "monetary_amount",
        "percent",
        "tax_jurisdiction_code_qualifier",
        "tax_jurisdiction_code",
        "tax_exempt_code",
        "relationship_code",
        "dollar_basis_for_percent",
        "tax_identification_number",
        "assigned_identification",
    )),
}


TRADACOMS_BODY_SEGMENT_DEFS = {
    "CDT": ("customer_details", (
        ("customers_identity", (
            "customers_ana_location_code",
            "customers_identity_allocated_by_supplier",
        )),
        "customers_name",
        ("customers_address", (
            "customers_address_line_1",
            "customers_address_line_2",
            "customers_address_line_3",
            "customers_address_line_4",
            "customers_post_code",
        )),
        "customers_vat_registration_number",
    )),
    "CLO": ("customers_location", (
        ("customers_location_identity", (
            "customers_ana_location_code",
            "customers_own_location_code",
        )),
        "customers_location_name",
        ("customers_location_address", (
            "customers_address_line_1",
            "customers_address_line_2",
            "customers_address_line_3",
            "customers_address_line_4",
            "customers_post_code",
        )),
    )),
    "FIL": ("file_details", (
        "file_generation_number",
        "file_version_number",
        "file_creation_date",
    )),
    "IRF": ("invoice_references", (
        "invoice_number",
        "invoice_date",
        "tax_point_date",
    )),
    "ORD": ("order_references", (
        ("order_number", (
            "customers_order_number",
            "suppliers_order_number",
            "date_order_placed_by_customer",
        )),
    )),
    "OTR": ("order_trailer", (
        "total_number_of_order_lines",
    )),
    "SDT": ("supplier_details", (
        ("suppliers_identity", (
            "suppliers_ana_location_code",
            "suppliers_identity_allocated_by_customer",
        )),
        "suppliers_name",
        ("suppliers_address", (
            "suppliers_address_line_1",
            "suppliers_address_line_2",
            "suppliers_address_line_3",
            "suppliers_address_line_4",
            "suppliers_post_code",
        )),
        "suppliers_vat_registration_number",
    )),
    "TYP": ("transaction_type", (
        "transaction_code",
        "transaction_type",
    )),
}


HL7_BODY_SEGMENT_DEFS = {
    "AL1": ("patient_allergy_information", (
        "set_id_al1",
        "allergen_type_code",
        "allergen_code_mnemonic_description",
        "allergy_severity_code",
        "allergy_reaction_code",
        "identification_date",
    )),
    "DG1": ("diagnosis", (
        "set_id_dg1",
        "diagnosis_coding_method",
        "diagnosis_code_dg1",
        "diagnosis_description",
        "diagnosis_date_time",
        "diagnosis_type",
    )),
    "ERR": ("error", (
        "error_code_and_location",
        "error_location",
        "hl7_error_code",
        "severity",
    )),
    "EVN": ("event_type", (
        "event_type_code",
        "recorded_date_time",
        "date_time_planned_event",
        "event_reason_code",
        "operator_id",
        "event_occurred",
        "event_facility",
    )),
    "FT1": ("financial_transaction", (
        "set_id_ft1",
        "transaction_id",
        "transaction_batch_id",
        "transaction_date",
        "transaction_posting_date",
        "transaction_type",
        "transaction_code",
    )),
    "GT1": ("guarantor", (
        "set_id_gt1",
        "guarantor_number",
        "guarantor_name",
        "guarantor_spouse_name",
        "guarantor_address",
        "guarantor_ph_num_home",
        "guarantor_ph_num_business",
        "guarantor_date_time_of_birth",
        "guarantor_administrative_sex",
        "guarantor_type",
        "guarantor_relationship",
    )),
    "IN1": ("insurance", (
        "set_id_in1",
        "insurance_plan_id",
        "insurance_company_id",
        "insurance_company_name",
        "insurance_company_address",
        "insurance_co_contact_person",
        "insurance_co_phone_number",
        "group_number",
        "group_name",
        "insureds_group_emp_id",
        "insureds_group_emp_name",
        "plan_effective_date",
        "plan_expiration_date",
    )),
    "IN2": ("insurance_additional_information", (
        "insureds_employee_id",
        "insureds_social_security_number",
        "insureds_employers_name_and_id",
    )),
    "MSA": ("message_acknowledgment", (
        "acknowledgment_code",
        "message_control_id",
        "text_message",
        "expected_sequence_number",
        "delayed_acknowledgment_type",
        "error_condition",
    )),
    "NK1": ("next_of_kin_associated_parties", (
        "set_id_nk1",
        "name",
        "relationship",
        "address",
        "phone_number",
        "business_phone_number",
        "contact_role",
        "start_date",
        "end_date",
    )),
    "NTE": ("notes_and_comments", (
        "set_id_nte",
        "source_of_comment",
        "comment",
        "comment_type",
    )),
    "OBR": ("observation_request", (
        "set_id_obr",
        "placer_order_number",
        "filler_order_number",
        "universal_service_identifier",
        "priority_obr",
        "requested_date_time",
        "observation_date_time",
        "observation_end_date_time",
        "collection_volume",
        "collector_identifier",
        "specimen_action_code",
        "danger_code",
        "relevant_clinical_information",
        "specimen_received_date_time",
        "specimen_source",
        "ordering_provider",
    )),
    "OBX": ("observation_result", (
        "set_id_obx",
        "value_type",
        "observation_identifier",
        "observation_sub_id",
        "observation_value",
        "units",
        "references_range",
        "abnormal_flags",
        "probability",
        "nature_of_abnormal_test",
        "observation_result_status",
        "effective_date_of_reference_range",
        "user_defined_access_checks",
        "date_time_of_the_observation",
    )),
    "ORC": ("common_order", (
        "order_control",
        "placer_order_number",
        "filler_order_number",
        "placer_group_number",
        "order_status",
        "response_flag",
        "quantity_timing",
        "parent",
        "date_time_of_transaction",
        "entered_by",
        "verified_by",
        "ordering_provider",
    )),
    "PD1": ("patient_additional_demographic", (
        "living_dependency",
        "living_arrangement",
        "patient_primary_facility",
        "patient_primary_care_provider_name_id_no",
    )),
    "PID": ("patient_identification", (
        "set_id_pid",
        "patient_id",
        "patient_identifier_list",
        "alternate_patient_id_pid",
        "patient_name",
        "mothers_maiden_name",
        "date_time_of_birth",
        "administrative_sex",
        "patient_alias",
        "race",
        "patient_address",
        "county_code",
        "phone_number_home",
        "phone_number_business",
        "primary_language",
        "marital_status",
        "religion",
        "patient_account_number",
        "ssn_number_patient",
        "drivers_license_number_patient",
        "mothers_identifier",
        "ethnic_group",
        "birth_place",
        "multiple_birth_indicator",
        "birth_order",
        "citizenship",
        "veterans_military_status",
        "nationality",
        "patient_death_date_and_time",
        "patient_death_indicator",
    )),
    "PR1": ("procedures", (
        "set_id_pr1",
        "procedure_coding_method",
        "procedure_code",
        "procedure_description",
        "procedure_date_time",
        "procedure_functional_type",
    )),
    "PV1": ("patient_visit", (
        "set_id_pv1",
        "patient_class",
        "assigned_patient_location",
        "admission_type",
        "preadmit_number",
        "prior_patient_location",
        "attending_doctor",
        "referring_doctor",
        "consulting_doctor",
        "hospital_service",
        "temporary_location",
        "preadmit_test_indicator",
        "re_admission_indicator",
        "admit_source",
        "ambulatory_status",
        "vip_indicator",
        "admitting_doctor",
        "patient_type",
        "visit_number",
        "financial_class",
    )),
    "PV2": ("patient_visit_additional_information", (
        "prior_pending_location",
        "accommodation_code",
        "admit_reason",
        "transfer_reason",
    )),
    "QRD": ("query_definition", (
        "query_date_time",
        "query_format_code",
        "query_priority",
        "query_id",
        "deferred_response_type",
        "deferred_response_date_time",
        "quantity_limited_request",
        "who_subject_filter",
        "what_subject_filter",
        "what_department_data_code",
    )),
    "QRF": ("query_filter", (
        "where_subject_filter",
        "when_data_start_date_time",
        "when_data_end_date_time",
    )),
    "ROL": ("role", (
        "role_instance_id",
        "action_code",
        "role_rol",
        "role_person",
    )),
    "RXA": ("pharmacy_treatment_administration", (
        "give_sub_id_counter",
        "administration_sub_id_counter",
        "date_time_start_of_administration",
        "date_time_end_of_administration",
        "administered_code",
        "administered_amount",
        "administered_units",
        "administered_dosage_form",
        "administration_notes",
        "administering_provider",
    )),
    "RXR": ("pharmacy_treatment_route", (
        "route",
        "administration_site",
        "administration_device",
        "administration_method",
    )),
    "SCH": ("scheduling_activity_information", (
        "placer_appointment_id",
        "filler_appointment_id",
        "occurrence_number",
        "placer_group_number",
        "schedule_id",
        "event_reason",
        "appointment_reason",
        "appointment_type",
        "appointment_duration",
        "appointment_duration_units",
        "appointment_timing_quantity",
    )),
    "SPM": ("specimen", (
        "set_id_spm",
        "specimen_id",
        "specimen_parent_ids",
        "specimen_type",
    )),
}

# --- BODY-DEFS-END ---


# ---------------------------------------------------------------------------
# ANSI ASC X12
# ---------------------------------------------------------------------------
# X12 names elements by position (BEG01, BEG02, ...), so definitions are a
# plain tuple of position names; keys get a two-digit position suffix
# ("purchase_order_number_03"). A position may also be a
# ("name", ("component", ...)) pair for composite elements. Names follow the
# 004010 release.

X12_ENVELOPE_SEGMENT_DEFS = {
    "ISA": ("interchange_control_header", (
        "authorization_information_qualifier",
        "authorization_information",
        "security_information_qualifier",
        "security_information",
        "interchange_id_qualifier",
        "interchange_sender_id",
        "interchange_id_qualifier",
        "interchange_receiver_id",
        "interchange_date",
        "interchange_time",
        "interchange_control_standards_identifier",
        "interchange_control_version_number",
        "interchange_control_number",
        "acknowledgment_requested",
        "usage_indicator",
        "component_element_separator",
    )),
    "IEA": ("interchange_control_trailer", (
        "number_of_included_functional_groups",
        "interchange_control_number",
    )),
    "GS": ("functional_group_header", (
        "functional_identifier_code",
        "application_senders_code",
        "application_receivers_code",
        "date",
        "time",
        "group_control_number",
        "responsible_agency_code",
        "version_release_industry_identifier_code",
    )),
    "GE": ("functional_group_trailer", (
        "number_of_transaction_sets_included",
        "group_control_number",
    )),
    "ST": ("transaction_set_header", (
        "transaction_set_identifier_code",
        "transaction_set_control_number",
        "implementation_convention_reference",
    )),
    "SE": ("transaction_set_trailer", (
        "number_of_included_segments",
        "transaction_set_control_number",
    )),
    "TA1": ("interchange_acknowledgment", (
        "interchange_control_number",
        "interchange_date",
        "interchange_time",
        "interchange_acknowledgment_code",
        "interchange_note_code",
    )),
}

X12_SEGMENT_DEFS = dict(X12_BODY_SEGMENT_DEFS)
X12_SEGMENT_DEFS.update(X12_ENVELOPE_SEGMENT_DEFS)


# ---------------------------------------------------------------------------
# TRADACOMS
# ---------------------------------------------------------------------------
# TRADACOMS elements are also positional and frequently composite; component
# names follow the ANA TRADACOMS manuals.

TRADACOMS_ENVELOPE_SEGMENT_DEFS = {
    "STX": ("start_of_transmission", (
        ("syntax_rules_identifier", (
            "syntax_rules_identifier",
            "syntax_version_number",
        )),
        ("identity_of_transmission_sender", (
            "senders_ana_code",
            "senders_name",
        )),
        ("identity_of_transmission_recipient", (
            "recipients_ana_code",
            "recipients_name",
        )),
        ("date_and_time_of_transmission", (
            "date_of_transmission",
            "time_of_transmission",
        )),
        "senders_transmission_reference",
        "recipients_transmission_reference",
        "application_reference",
        "transmission_priority_code",
    )),
    "END": ("end_of_transmission", (
        "number_of_messages_in_transmission",
    )),
    "MHD": ("message_header", (
        "message_reference",
        ("type_of_message", (
            "message_type",
            "message_version_number",
        )),
    )),
    "MTR": ("message_trailer", (
        "number_of_segments_in_message",
    )),
}

TRADACOMS_SEGMENT_DEFS = dict(TRADACOMS_BODY_SEGMENT_DEFS)
TRADACOMS_SEGMENT_DEFS.update(TRADACOMS_ENVELOPE_SEGMENT_DEFS)


# ---------------------------------------------------------------------------
# HL7 v2.x
# ---------------------------------------------------------------------------
# HL7 names fields by position (PID-3, ...); keys get an unpadded position
# suffix ("patient_identifier_list_3"). Field names follow HL7 v2.5.

HL7_ENVELOPE_SEGMENT_DEFS = {
    "MSH": ("message_header", (
        "field_separator",
        "encoding_characters",
        "sending_application",
        "sending_facility",
        "receiving_application",
        "receiving_facility",
        "date_time_of_message",
        "security",
        "message_type",
        "message_control_id",
        "processing_id",
        "version_id",
        "sequence_number",
        "continuation_pointer",
        "accept_acknowledgment_type",
        "application_acknowledgment_type",
        "country_code",
        "character_set",
        "principal_language_of_message",
    )),
}

HL7_SEGMENT_DEFS = dict(HL7_BODY_SEGMENT_DEFS)
HL7_SEGMENT_DEFS.update(HL7_ENVELOPE_SEGMENT_DEFS)
