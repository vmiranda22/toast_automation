# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "4b9a8e2d-64db-464e-b218-053f22ac13b1",
# META       "default_lakehouse_name": "fabrictest_lakehouse",
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977",
# META       "known_lakehouses": [
# META         {
# META           "id": "4b9a8e2d-64db-464e-b218-053f22ac13b1"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # Silver Layer Transformations for Teladoc EDS Dev Bronze Tables

# CELL ********************

# MAGIC %%configure 
# MAGIC { 
# MAGIC    "conf": {
# MAGIC        "spark.native.enabled": "true", 
# MAGIC    } 
# MAGIC } 

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Import required resources.

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, concat, current_date, expr, first, lit, lower, posexplode, row_number, split, when
from pyspark.sql.types import BooleanType, DateType, DoubleType, IntegerType, StringType, TimestampType
from pyspark.sql.window import Window

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Initialize SparkSession.

# CELL ********************

spark = SparkSession.builder.getOrCreate()
spark.conf.set("spark.sql.parquet.datetimeRebaseModeInRead", "LEGACY")
spark.conf.set("spark.sql.parquet.datetimeRebaseModeInWrite", "LEGACY")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Create Dictionary witch each Bronze table and its corresponding columns mapping to **rename, reorder, and specify Data Types**.

# CELL ********************

silver_tables_columns_mapping = {
    "teladoc_eds_dev_100_bronze_allowed_group_relations": {
        "allowed_group_relations_id": ("allowed_group_relation_id", StringType()),
        "source_group_id": ("allowed_group_relation_value", StringType()),
        "allowed_group_setting_id": ("allowed_group_relation_setting_id", StringType()),
        "group_id": ("group_id", StringType()),
        "effective_start_dt": ("effective_start_dt", DateType()),
        "effective_end_dt": ("effective_end_dt", DateType()),
        "exclusion_cd": ("exclusion_cd", StringType()),
        "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        "updated_at": ("updated_at", TimestampType())
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_allowed_group_settings": {
        "allowed_group_setting_id": ("allowed_group_setting_id", StringType()),
        "map": ("map_name", StringType()),
        "success_email_dist_list": ("success_email_distribution_list", StringType()),
        "failure_email_dist_list": ("failure_email_distribution_list", StringType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },
    
    "teladoc_eds_dev_100_bronze_alt_group_ids": {
        "alt_group_id": ("alt_group_id", StringType()),
        "group_id": ("group_id", StringType()),
        "alt_group_cd": ("alt_group_cd", StringType()),
        "alt_group_value": ("alt_group_value", StringType()),
        "exclusion_cd": ("exclusion_cd", StringType()),
        "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        "updated_at": ("updated_at", TimestampType())
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_billings": {
        "billing_id": ("billing_id", StringType()),
        "organization_id": ("organization_id", StringType()),
        "invoice_name": ("invoice_name", StringType()), # UI = Invoice name | Org Level
        "regards_to": ("regards_to", StringType()), # UI = Regards to | Org Level
        "eligible_day_of_month": ("eligible_day_of_month", IntegerType()), # UI = Eligibility day of month | Org Level
        "billing_accnt_uuid": ("billing_accnt_uuid", StringType()), # UI = Billing account uuid | Org Level
        "finance_name": ("finance_name", StringType()),     
        "client_subsegment_cd": ("client_subsegment_cd", StringType()), # UI = Finance subcategory | Org Level
        "self_remit_flg": ("self_remit", BooleanType()), # UI = Does client self-remit payment? | Org Level
        "member_pay_cd": ("member_pay_cd", StringType()), # UI = Invoiced person type | Org Level
        "payment_term_cd": ("payment_term_cd", StringType()), # UI = Payment terms | Org Level
        "invoice_delivery_cd": ("invoice_delivery_cd", StringType()), # UI = Invoice delivery | Org Level
        "risk_contract_flg": ("risk_contract", BooleanType()), # UI = Risk contract | Org Level
        "split_billing_flg": ("split_billing", BooleanType()), # NOT FOUND IN UI
        "send_expert_membership_flg": ("send_expert_membership", BooleanType()), # NOT FOUND IN UI
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_empi_namespace_org_relations": {
        "empi_namespace_org_relation_id": ("empi_namespace_organization_relation_id", StringType()),
        "empi_namespace_cd": ("empi_namespace_cd", StringType()),
        "benefit_restriction_cd": ("benefit_restriction_cd", StringType()),
        "organization_id": ("organization_id", StringType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_external_group_relations": {
        "external_group_relation_id": ("external_group_relation_id", StringType()),
        "external_group_id": ("external_group_relation_value", StringType()),
        "external_group_type_cd": ("external_group_relation_type", StringType()),
        "group_id": ("group_id", StringType()),
        "payer_id": ("payer_id", StringType()),
        "effective_start_dt": ("effective_start_dt", DateType()),
        "effective_end_dt": ("effective_end_dt", DateType()),
        "exclusion_cd": ("exclusion_cd", StringType()),
        "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        "updated_at": ("updated_at", TimestampType())
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_group_billing_relations": {
        "group_billing_relation_id": ("group_billing_relation_id", StringType()),
        "group_id": ("group_id", StringType()),
        "billing_id": ("billing_id", StringType()),
        "billing_fee_type_cd": ("billing_fee_type_cd", StringType()), # UI = Membership Fee Type | Group Level
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_group_empi_namespace_relations": {
        "group_empi_namespace_relation_id": ("group_billing_relation_id", StringType()),
        "group_id": ("group_id", StringType()),
        "empi_namespace_cd": ("empi_namespace_cd", StringType()),
        "benefit_restriction_cd": ("benefit_restriction_cd", StringType()),
        "effective_start_dt": ("effective_start_dt", DateType()),
        "effective_end_dt": ("effective_end_dt", DateType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_group_offers": {
        "group_offer_id": ("group_offer_id", StringType()),
        "group_id": ("group_id", StringType()),
        "promotion_cd": ("promotion_cd", StringType()),
        "dependent_promotion_cd": ("dependent_promotion_cd", StringType()),
        "promotion_type_cd": ("promotion_type_cd", StringType()),
        "promotion_start_dt": ("promotion_start_dt", DateType()),
        "promotion_end_dt": ("promotion_end_dt", DateType()),
        "clock_start_cd": ("clock_start_cd", StringType()),
        "clock_end_cd": ("clock_end_cd", StringType()),
        "discount_amount": ("discount_amount", IntegerType()),
        "discount_percent": ("discount_percent", IntegerType()),
        "interval_cd": ("interval_cd", StringType()),
        "num_of_intervals": ("num_of_intervals", IntegerType()),
        "num_per_interval": ("num_per_interval", IntegerType()),
        "family": ("family", BooleanType()),
        "additional": ("additional", BooleanType()),
        "premium_flg": ("premium", BooleanType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_group_payer_relations": {
        "group_payer_relation_id": ("group_payer_relation_id", StringType()),
        "group_id": ("group_id", StringType()),
        "payer_id": ("payer_id", StringType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_group_payer_service_specialty_relations": {
        "group_payer_service_specialty_relation_id": ("group_payer_service_specialty_relation_id", StringType()),
        "group_service_specialty_relation_id": ("group_service_specialty_relation_id", StringType()),
        "payer_id": ("payer_id", StringType()),
        "claim_payer_id": ("claim_payer_id", StringType()),
        "default_payer_flg": ("default_payer", BooleanType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_group_relation_pricings": {
        "group_relation_pricing_id": ("group_relation_pricing_id", StringType()),
        "pricing_type_cd": ("pricing_type_cd", StringType()),
        "relation_id": ("relation_id", StringType()),
        "relation_type": ("relation_type", StringType()),
        "invoice_method_cd": ("invoice_method_cd", StringType()),
        "invoice_submethod_cd": ("invoice_submethod_cd", StringType()),
        "amount": ("amount", DoubleType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_group_relations": {
        "group_relation_id": ("group_relation_id", StringType()),
        "group_relationship_cd": ("group_relationship_cd", StringType()),
        "group_id": ("group_id", StringType()),
        "related_group_id": ("related_group_id", StringType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_group_service_level_relations": {
        "group_service_level_relation_id": ("group_relation_id", StringType()),
        "group_id": ("group_id", StringType()),
        "standard_service_level_id": ("standard_service_level_id", StringType()),
        "vip_service_level_id": ("vip_service_level_id", StringType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_group_service_specialty_feature_relations": {
        "group_service_specialty_feature_relation_id": ("group_service_specialty_feature_relation_id", StringType()),
        "group_service_specialty_relation_id": ("group_service_specialty_relation_id", StringType()),
        "service_specialty_feature_cd": ("service_specialty_feature_cd", StringType()),
        "live_dt": ("effective_start_dt", DateType()),
        "termination_dt": ("effective_end_dt", DateType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_group_service_specialty_feature_settings": {
        "group_service_specialty_feature_setting_id": ("group_service_specialty_feature_setting_id", StringType()),
        "group_service_specialty_feature_relation_id": ("group_service_specialty_feature_relation_id", StringType()),
        "provider_selection_cd": ("provider_selection_cd", StringType()),
        "on_demand_consult": ("on_demand_consult", BooleanType()),
        "scheduled_consult": ("scheduled_consult", BooleanType()),
        "allow_preselected_provider": ("allow_preselected_provider", BooleanType()),
        "allow_first_available_provider": ("allow_first_available_provider", BooleanType()),
        "allow_searchable_provider": ("allow_searchable_provider", BooleanType()),
        "allow_consult_guest": ("allow_consult_guest", BooleanType()),
        "print_or_less": ("print_or_less", BooleanType()),
        "extended_family_benefit_cd": ("extended_family_benefit_cd", StringType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_group_service_specialty_relation_details": {
        "group_service_specialty_relation_detail_id": ("group_service_specialty_relation_detail_id", StringType()),
        "group_service_specialty_relation_id": ("group_service_specialty_relation_id", StringType()),
        "effective_start_dt": ("effective_start_dt", DateType()),
        "effective_end_dt": ("effective_end_dt", DateType()),
        "opportunity_uuid": ("opportunity_uuid", StringType()),
        "contract_num": ("contract_num", StringType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_group_service_specialty_relations": {
        "group_service_specialty_relation_id": ("group_service_specialty_relation_id", StringType()),
        "group_id": ("group_id", StringType()),
        "service_specialty_cd": ("service_specialty_cd", StringType()),
        "geographic_region_coverage_cd": ("geographic_region_coverage_cd", StringType()),
        "min_age": ("min_age", IntegerType()),
        "max_age": ("max_age", IntegerType()),
        "bundle_type_cd": ("bundle_type_cd", StringType()),
        "primary_contract_flg": ("primary_contract", StringType()),
        "override_billing_id": ("override_billing_id", StringType()),
        "billing_fee_type_cd": ("billing_fee_type_cd", StringType()), # Product Membership Fee Type
        "claim_billing_method_cd": ("claim_billing_method_cd", StringType()),
        "payer_fee_schedule_relation_id": ("payer_fee_schedule_relation_id", StringType()),
        "tpn_rule_id": ("tpn_rule_id", StringType()), # Routing Rule
        "condition_flg": ("condition", StringType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_group_settings": {
        "group_setting_id": ("group_setting_id", StringType()),
        "group_id": ("group_id", StringType()),
        "domestic_country_cd": ("domestic_country", StringType()),
        "lob_cd": ("lob_cd", StringType()),
        "sold_to_accnt_uuid": ("sold_to_account_uuid", StringType()),
        "sold_to_accnt_nm": ("sold_to_account_nm", StringType()),
        "min_age_for_primary_registration": ("min_age_for_primary_registration", IntegerType()),
        "min_age_for_dependent_registration": ("min_age_for_dependent_registration", IntegerType()),
        "max_age_for_dependent_registration": ("max_age_for_dependent_registration", IntegerType()),
        "allow_sla_reimbursement_flg": ("sla_waive_visit_fee_if_missed", BooleanType()),
        "one_app_flg": ("one_app_access", BooleanType()),
        "hhs_access_flg": ("hhs_access", BooleanType()),
        "sso_only_access_flg": ("sso_only_access", BooleanType()),
        "dual_access_allowed_flg": ("dual_access", BooleanType()),
        "web_access_flg": ("web_access", BooleanType()),
        "mobile_access_flg": ("mobile_access", BooleanType()),
        "send_ccr_to_pcp_flg": ("send_ccr_to_pcp", StringType()), # UI = Send CCR to PCP | Group Level
        "disable_excuse_note_flg": ("disable_excuse_note", BooleanType()),
        "send_card_flg": ("send_card", BooleanType()), # UI = Send Card | Group Level
        "allow_conversion_to_retail_flg": ("allow_conversion_to_retail", BooleanType()),
        "vip_flg": ("vip", BooleanType()), # UI = VIP Members | Group Level
        "ccr_cannot_access_member_phi_flg": ("restricted_phi_access", BooleanType()),
        # Caregiver Program Missing
        # Couples Therapy Missing
        "enable_geo_fencing": ("enable_geo_fencing", BooleanType()),
        "enable_two_factor_auth": ("enable_two_factor_authentication", BooleanType()),
        "authorized_consenter_allowed_flg": ("authorized_consenter_allowed", BooleanType()),
        "allow_manage_subscription_flg": ("allow_manage_subscription", BooleanType()),
        "allow_call_center_registration_flg": ("allow_call_center_registration", BooleanType()),
        "allow_call_center_consult_request_flg": ("allow_call_center_consult_request", BooleanType()),
        "allow_health_assistant_flg": ("allow_health_assistant", BooleanType()),
        "in_home_rx_delivery_flg": ("in_home_rx_delivery", BooleanType()),
        "send_promo_cd_flg": ("send_promo_cd", BooleanType()),
        "required_security_question_cnt": ("required_security_questions", IntegerType()),
        "chronic_care_referral_flg": ("enable_chronic_care_referrals", StringType()), # UI = Enable Chronic Care Referrals | Group Level
        "chronic_care_joint_eligibility_flg": ("livongo_combined_eligibility", BooleanType()), # UI = Enable Livongo Combined Eligibility | Group Level
        "prohibit_member_attachment_download_flg": ("prohibit_member_attachment_download", BooleanType()),
        "quick_registration_link_expiration_min": ("link_expiration_time", IntegerType()),
        "dob_can_be_null": ("date_of_birth_can_be_null", BooleanType()),
        "pg_flg": ("performance_guarantee", BooleanType()),
        "enable_wellness_content_flg": ("enable_wellness_content", BooleanType()),
        "minor_registration_flg": ("minor_registration", BooleanType()),
        "print_logo_filename": ("print_logo_filename", StringType()), # UI = Logo filename | Group Level
        "default_billing_fee_type_cd": ("membership_fee_type_cd", StringType()), # Group Membership Fee Type - INVESTIGATE
        "single_invoice_ccm_flg": ("cross_billing", BooleanType()), # UI = Include Livongo(CCM) PEPM Product in the Invoice | Group Level
        "consult_reimbursement_method_cd": ("consult_reimbursement_method_cd", StringType()),
        "refund_member_flg": ("refund_member", BooleanType()),
        "send_member_resolution_letter_flg": ("send_member_resolution_letter", BooleanType()),
        "send_problem_member_letter_flg": ("send_problem_member_letter", BooleanType()),
        "send_util_letter_flg": ("send_utilization_letter", BooleanType()),
        "send_fraud_waste_abuse_letter_flg": ("send_fraud_waste_abuse_letter", BooleanType()),
        "annual_checkup_trigger_cd": ("annual_checkup_trigger_cd", StringType()),
        "annual_checkup_start_month": ("annual_checkup_start_month", IntegerType()),
        "tpn_rule_id": ("tpn_rule_id", StringType()), # Routing Rule - INVESTIGATE
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_groups": {
        "group_id": ("group_id", StringType()),
        "legacy_group_id": ("legacy_group_id", StringType()),
        "group_nm": ("group_nm", StringType()),
        "group_type_cd": ("group_type_cd", StringType()),
        "registration_group_cd": ("registration_group_cd", StringType()),
        "card_nm": ("card_nm", StringType()),
        "effective_start_dt": ("effective_start_dt", DateType()),
        "effective_end_dt": ("effective_end_dt", DateType()),
        "source_group_root": ("source_group_root", StringType()),
        "source_group_identifer": ("source_group_id", StringType()),
        "notes_internal": ("notes_internal", StringType()),
        "notes_external": ("notes_external", StringType()),
        "template": ("template", BooleanType()),
        "exclusion_cd": ("exclusion_cd", StringType()),
        "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        "updated_at": ("updated_at", TimestampType())
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_offer_service_specialty_feature_relations": {
        "offer_service_specialty_feature_relation_id": ("offer_service_specialty_feature_relation_id", StringType()),
        "offer_id": ("offer_id", StringType()),
        "offer_type": ("offer_type", StringType()),
        "service_specialty_feature_cd": ("service_specialty_feature_cd", StringType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_organization_extensions": {
        "organization_extension_id": ("organization_extension_id", StringType()),
        "organization_id": ("organization_id", StringType()),
        "employer_flg": ("employer", BooleanType()),
        "print_url": ("print_url", StringType()),
        "print_phone": ("print_phone", StringType()),
        "additional_url": ("additional_url", StringType()),
        "snippet_id": ("snippet_id", IntegerType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_organization_marketing_communications": {
        "organization_marketing_communication_id": ("organization_marketing_communication_id", StringType()),
        "organization_id": ("organization_id", StringType()),
        "marketing_comm_type_cd": ("marketing_communication_type_cd", StringType()),
        "optout_cd": ("opt_out_cd", StringType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_organization_user_relations": {
        "organization_user_relation_id": ("organization_user_relation_id", StringType()),
        "organization_id": ("organization_id", StringType()),
        "user_id": ("user_id", StringType()),
        "user_type": ("user_type", StringType()),
        "purpose_relation_type_cd": ("purpose_relation_type_cd", StringType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_organizations": {
        "organization_id": ("organization_id", StringType()),
        "organization_nm": ("organization_nm", StringType()),
        # "sql_path": ("sql_path", StringType()),
        "ancestry": ("ancestry", StringType()),
        # "ancestry_depth": ("ancestry_depth", IntegerType()),
        "parent_id": ("parent_id", StringType()),
        "group_id": ("group_id", StringType()),
        "party_id": ("party_id", StringType()),
        "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        "updated_at": ("updated_at", TimestampType())
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_parties": {
        "party_id": ("party_id", StringType()),
        "party_name": ("party_nm", StringType()),
        "party_type_cd": ("party_type_cd", StringType()),
        "party_batch_id": ("party_batch_id", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_party_addresses": {
        "party_address_id": ("party_address_id", StringType()),
        "party_id": ("party_id", StringType()),
        "address_line1": ("address_line_1", StringType()),
        "address_line2": ("address_line_2", StringType()),
        "address_line3": ("address_line_3", StringType()),
        "county": ("county", StringType()),
        "city": ("city", StringType()),
        "state_province": ("state_province", StringType()),
        "postal": ("postal", StringType()),
        "country_cd": ("country_cd", StringType()),
        "address_type_cd": ("address_type_cd", StringType()),
        "preferred_flg": ("preferred", BooleanType()),
        "alert_flg": ("alert", BooleanType()),
        "batch_id": ("batch_id", StringType()),
        "temporary": ("temporary", BooleanType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_party_email_addresses": {
        "party_email_address_id": ("party_email_address_id", StringType()),
        "party_id": ("party_id", StringType()),
        "email_address": ("email_address", StringType()),
        "email_type_cd": ("email_type_cd", StringType()),
        "preferred_flg": ("preferred", BooleanType()),
        "alert_flg": ("alert", BooleanType()),
        "batch_id": ("batch_id", StringType()),
        "temporary": ("temporary", BooleanType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_payers": {
        "payer_id": ("payer_id", StringType()),
        "payer_nm": ("payer_nm", StringType()),
        "payer_cd": ("payer_cd", StringType()),
        "payer_flavor": ("payer_flavor", StringType()),
        "party_id": ("party_id", StringType()),
        "rte_gateway_enabled_flg": ("rte_gateway_enabled", BooleanType()),
        "rte_gateway_id": ("rte_gateway_id", StringType()),
        "claim_gateway_id": ("claim_gateway_id", StringType()),
        "allow_group_mover_flg": ("allow_group_mover", BooleanType()),
        "allow_encounter_claim_flg": ("allow_encounter_claim", BooleanType()),
        "encounter_gateway_id": ("encounter_gateway_id", StringType()),
        "do_not_turn_away_flg": ("do_not_turn_away", BooleanType()),
        "gateway_connection_id": ("gateway_connection_id", StringType()),
        "related_open_group_id": ("related_open_group_id", StringType()),
        "receiver_id": ("receiver_id", StringType()),
        "rendering_provider_cd": ("rendering_provider_cd", StringType()),
        "service_facility_flg": ("service_facility", BooleanType()),
        "billing_provider_state_cd": ("billing_provider_state", StringType()),
        "send_taxonomy_flg": ("send_taxonomy", BooleanType()),
        "info_only_flg": ("info_only", BooleanType()),
        "send_zero_dollar_claim_flg": ("send_zero_dollar_claim", BooleanType()),
        "provider_role_tin_override_cd": ("provider_role_tin_override", StringType()),
        "max_daily_claims": ("max_daily_claims", IntegerType()),
        "state_restriction_flg": ("state_restriction", BooleanType()),
        "allow_demog_update_flg": ("allow_demog_update", BooleanType()),
        "charge_member_cost_flg": ("charge_member_cost", BooleanType()),
        "clearinghouse_cd": ("clearinghouse", StringType()),
        "geographic_region_cd": ("geographic_region", StringType()),
        "emr_carrier_nm": ("emr_carrier_nm", StringType()),
        "emr_plan_code": ("emr_plan_cd", StringType()),
        "active_flg": ("active", BooleanType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_persons": {
        "person_id": ("person_id", StringType()),
        "party_id": ("party_id", StringType()),
        "person_type": ("person_type", StringType()),
        "first_nm": ("first_nm", StringType()),
        "last_nm": ("last_nm", StringType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_ref_countries": {
        "ref_country_id": ("ref_country_id", StringType()),
        "country_cd": ("country_cd", StringType()),
        "country_nm": ("country_nm", StringType()),
        "currency_cd": ("currency_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_ref_empi_namespaces": {
        "ref_empi_namespace_id": ("ref_empi_namespace_id", StringType()),
        "empi_namespace_cd": ("empi_namespace_cd", StringType()),
        "namespace_nm": ("namespace_nm", StringType()),
        "use_flg": ("use", BooleanType()),
        "active_flg": ("active", BooleanType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_ref_features": {
        "ref_feature_id": ("ref_feature_id", StringType()),
        "feature_cd": ("feature_cd", StringType()),
        "feature_nm": ("feature_nm", StringType()),
        "feature_family_cd": ("feature_family_cd", StringType()),
        "config_visible_flg": ("config_visible", BooleanType()),
        "support_visible_flg": ("support_visible", BooleanType()),
        "user_visible_flg": ("user_visible", BooleanType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_ref_geographic_regions": {
        "ref_geographic_region_id": ("ref_geographic_region_id", StringType()),
        "geographic_region_cd": ("geographic_region_cd", StringType()),
        "geographic_region_nm": ("geographic_region_nm", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_ref_reports": {
        "ref_report_id": ("ref_report_id", StringType()),
        "report_cd": ("report_cd", StringType()),
        "report_nm": ("report_nm", StringType()),
        "report_type_cd": ("report_type_cd", StringType()),
        "flavor_cd": ("flavor_cd", StringType()),
        "service_specialty_cd": ("service_specialty_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_ref_service_levels": {
        "ref_service_level_id": ("ref_service_level_id", StringType()),
        "service_level_nm": ("service_level_nm", StringType()),
        "level1": ("level1", IntegerType()),
        "level2": ("level2", IntegerType()),
        "level3": ("level3", IntegerType()),
        "service_level_interval": ("service_level_interval", IntegerType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_ref_service_specialties": {
        "ref_service_specialty_id": ("ref_service_specialty_id", StringType()),
        "service_specialty_cd": ("service_specialty_cd", StringType()),
        "service_specialty_nm": ("service_specialty_nm", StringType()),
        "service_specialty_uft": ("service_specialty_uft", StringType()),
        "service_offering_cd": ("service_offering_cd", StringType()),
        "servicing_platform_cd": ("servicing_platform_cd", StringType()),
        "default_min_age": ("default_min_age", IntegerType()),
        "default_max_age": ("default_max_age", IntegerType()),
        "config_visible_flg": ("config_visible", BooleanType()),
        "payer_visible_flg": ("payer_visible", BooleanType()),
        "support_visible_flg": ("support_visible", BooleanType()),
        "user_visible_flg": ("user_visible", BooleanType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_ref_service_specialty_features": {
        "ref_service_specialty_feature_id": ("ref_service_specialty_feature_id", StringType()),
        "service_specialty_feature_cd": ("service_specialty_feature_cd", StringType()),
        "service_specialty_feature_nm": ("service_specialty_feature_nm", StringType()),
        "service_specialty_cd": ("service_specialty_cd", StringType()),
        "feature_cd": ("feature_cd", StringType()),
        "rte_eligible_flg": ("rte_eligible", BooleanType()),
        "visible_flg": ("visible", BooleanType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_report_affiliation_relations": {
        "report_affiliation_relation_id": ("report_affiliation_relation_id", StringType()),
        "affiliation_type": ("affiliation_type", StringType()),
        "affiliation_id": ("affiliation_id", StringType()),
        "report_cd": ("report_cd", StringType()),
        "email_flavor_cd": ("email_flavor_cd", StringType()),
        "frequency_cd": ("frequency_cd", StringType()),
        "effective_start_dt": ("effective_start_dt", DateType()),
        "effective_end_dt": ("effective_end_dt", DateType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_report_email_relations": {
        "report_email_relation_id": ("report_email_relation_id", StringType()),
        "party_email_address_id": ("party_email_address_id", StringType()),
        "report_affiliation_relation_id": ("report_affiliation_relation_id", StringType()),
        "email_send_cd": ("email_send_cd", StringType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_sales_reps": {
        "sales_rep_id": ("sales_rep_id", StringType()),
        "person_id": ("person_id", StringType()),
        "sales_rep_type_cd": ("sales_rep_type_cd", StringType()),
        "effective_start_dt": ("effective_start_dt", DateType()),
        "effective_end_dt": ("effective_end_dt", DateType()),
        "exclusion_cd": ("exclusion_cd", StringType())
        # "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        # "updated_at": ("updated_at", TimestampType()),
        # "updated_by": ("updated_by", IntegerType())
    },

    "teladoc_eds_dev_100_bronze_valid_group_sources": {
        "valid_group_source_id": ("valid_group_source_id", StringType()),
        "group_id": ("group_id", StringType()),
        "primary_source_cd": ("primary_source_cd", StringType()),
        "dependent_source_cd": ("dependent_source_cd", StringType()),
        "exclusion_cd": ("exclusion_cd", StringType()),
        "created_at": ("created_at", TimestampType()),
        # "created_by": ("created_by", IntegerType()),
        "updated_at": ("updated_at", TimestampType())
        # "updated_by": ("updated_by", IntegerType())
    }
}

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Create Function to apply the columns mapping to each table.

# CELL ********************

def transform_bronze_table(df, columns_mapping):
    """
    Transforms a DataFrame by renaming columns, casting types, reordering, 
    and ensuring Boolean columns have correct values. If the column "exclusion_cd"
    exists, it filters the DataFrame to keep only rows where "exclusion_cd" = "IN".
    
    :param df: PySpark DataFrame to transform
    :param columns_mapping: Dictionary mapping old column names to (new column names, data types)
    :return: Transformed PySpark DataFrame
    """
    
    # Apply renaming, reordering, and Data Type casting
    df_transformed = df.select(
        [col(old_name).cast(new_type).alias(new_name) for old_name, (new_name, new_type) in columns_mapping.items()]
    )
    
    # Standardize Boolean columns
    for old_name, (new_name, new_type) in columns_mapping.items():
        if new_type == BooleanType():  # Check if column is Boolean
            # Ensure the column is casted to String first before applying transformation
            df_transformed = df_transformed.withColumn(
                new_name,
                when(col(new_name).cast(StringType()).isin("Yes", "Y", "1"), True)
                .when(col(new_name).cast(StringType()).isin("No", "N", "0"), False)
                .otherwise(col(new_name))  # Keep existing nulls
                .cast(BooleanType())  # Finally, cast to BooleanType
            )

    # Check if "exclusion_cd" column exists in the table; if so, keep only 'IN' values
    if "exclusion_cd" in df.columns:
        df_transformed = df_transformed.filter(col("exclusion_cd") == "IN")
        df_transformed = df_transformed.drop(df_transformed.exclusion_cd)
    
    return df_transformed

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Apply Function to transform each table and save as Silver Table in Lakehouse.

# CELL ********************

transformed_tables = {}  # Dictionary to store transformed DataFrames

for table_name, columns_mapping in silver_tables_columns_mapping.items():

    # Load the table from the Lakehouse
    df = spark.read.format("delta").load(f"abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/{table_name}")
    
    # Transform the DataFrame
    transformed_table = transform_bronze_table(df, columns_mapping)

    # Extract the name portion after "bronze_"
    if "bronze_" in table_name:
        table_suffix = table_name.split("bronze_")[1]
    else:
        raise ValueError(f"Table name '{table_name}' does not contain 'bronze_'")
    
    # Define the new table name
    new_table_name = f"teladoc_eds_dev_200_silver_{table_suffix}"
    
    # Store it in the dictionary
    transformed_tables[new_table_name] = transformed_table

    # Save back to Lakehouse
    transformed_table.write.format("delta") \
        .option("overwriteSchema", "true") \
        .mode("overwrite") \
        .save(f"abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/{new_table_name}")
    
    print(f"✅ Transformed and saved: {new_table_name}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Transform _**alt_group_ids**_.

# MARKDOWN ********************

# df_eds_dev_alt_group_ids = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_alt_group_ids")
# 
# display(df_eds_dev_alt_group_ids)

# CELL ********************

df_eds_dev_alt_group_ids = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_alt_group_ids")

# ALT_CHRONICCARECLIENTCODE

df_eds_dev_alt_group_ids_chroniccareclientcode = df_eds_dev_alt_group_ids.filter((df_eds_dev_alt_group_ids["alt_group_cd"] == "ALT_CHRONICCARECLIENTCODE"))

df_eds_dev_alt_group_ids_chroniccareclientcode = df_eds_dev_alt_group_ids_chroniccareclientcode.orderBy(["group_id", "updated_at"], ascending=[False, False])

df_eds_dev_alt_group_ids_chroniccareclientcode = df_eds_dev_alt_group_ids_chroniccareclientcode.dropDuplicates(["group_id"])

# ALT_CHRONICCAREREGCODE

df_eds_dev_alt_group_ids_chroniccareregcode = df_eds_dev_alt_group_ids.filter((df_eds_dev_alt_group_ids["alt_group_cd"] == "ALT_CHRONICCAREREGCODE"))

df_eds_dev_alt_group_ids_chroniccareregcode = df_eds_dev_alt_group_ids_chroniccareregcode.orderBy(["group_id", "updated_at"], ascending=[False, True])

df_eds_dev_alt_group_ids_chroniccareregcode = df_eds_dev_alt_group_ids_chroniccareregcode.dropDuplicates(["group_id"])

# ALT_MYSTRENGTHACCESSCODE

df_eds_dev_alt_group_ids_mystrengthaccesscode = df_eds_dev_alt_group_ids.filter((df_eds_dev_alt_group_ids["alt_group_cd"] == "ALT_MYSTRENGTHACCESSCODE"))

# Append DFs

df_eds_dev_alt_group_ids_transformed = df_eds_dev_alt_group_ids_chroniccareclientcode.union(df_eds_dev_alt_group_ids_chroniccareregcode).union(df_eds_dev_alt_group_ids_mystrengthaccesscode)

# Pivot the table
df_eds_dev_alt_group_ids_transformed = df_eds_dev_alt_group_ids_transformed.groupBy("group_id").pivot("alt_group_cd").agg(first("alt_group_value"))

# Rename columns to match the expected output
df_eds_dev_alt_group_ids_transformed = df_eds_dev_alt_group_ids_transformed.withColumnRenamed("ALT_CHRONICCAREREGCODE", "livongo_registration_code") \
                                                                            .withColumnRenamed("ALT_CHRONICCARECLIENTCODE", "livongo_client_code") \
                                                                            .withColumnRenamed("ALT_MYSTRENGTHACCESSCODE", "mystrength_global_access_code")

# Save back to Lakehouse
df_eds_dev_alt_group_ids_transformed.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_alt_group_ids")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Transform _**external_group_relations**_.

# CELL ********************

df_eds_dev_external_group_relations = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_external_group_relations")

df_eds_dev_external_group_relations = df_eds_dev_external_group_relations.withColumn(
                                        "cc_real_time_exclusion_cd",
                                        when((col("effective_end_dt") >= current_date()) | col("effective_end_dt").isNull(), "IN")
                                        .otherwise("EX")
                                        .cast(StringType())
                                    )

# Save back to Lakehouse
df_eds_dev_external_group_relations.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_external_group_relations")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Transform _**group_service_specialty_feature_settings**_.

# CELL ********************

df_eds_dev_group_service_specialty_feature_settings = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_service_specialty_feature_settings")

df_eds_dev_group_service_specialty_feature_settings = df_eds_dev_group_service_specialty_feature_settings.withColumn(
    "extended_family_benefit_cd",
    when(col("extended_family_benefit_cd") == "EXTENDEDFAMILY_INCLUDED", "Family Included")
    .when(col("extended_family_benefit_cd") == "EXTENDEDFAMILY_NA", "Not Applicable")
    .when(col("extended_family_benefit_cd") == "EXTENDEDFAMILY_NOTINCLUDED", "Family NOT Included")
    .otherwise(col("extended_family_benefit_cd"))  # Keeps original value if not matched
)

# Save back to Lakehouse
df_eds_dev_group_service_specialty_feature_settings.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_service_specialty_feature_settings")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Transform _**group_service_specialty_relations**_.

# CELL ********************

df_eds_dev_group_service_specialty_relations = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_service_specialty_relations")

df_eds_dev_group_service_specialty_relations = df_eds_dev_group_service_specialty_relations.withColumn(
    "bundle_type_cd",
    when(col("bundle_type_cd") == "BUNDLETYPE_STANDALONE", "Standalone")
    .when(col("bundle_type_cd") == "BUNDLETYPE_WPANCHOR", "WP Anchor")
    .when(col("bundle_type_cd") == "BUNDLETYPE_WPNONANCHOR", "WP Non-Anchor")
    .when(col("bundle_type_cd") == "BUNDLETYPE_WPNONANCHORSTANDALONE", "WP Non-Anchor Standalone")
    .otherwise(col("bundle_type_cd"))  # Keeps original value if not matched
)

df_eds_dev_group_service_specialty_relations = df_eds_dev_group_service_specialty_relations.withColumn(
    "billing_fee_type_cd",
    when(col("billing_fee_type_cd") == "MEMBERSHIPFEE_PEPM", "PEPM")
    .when(col("billing_fee_type_cd") == "MEMBERSHIPFEE_PMPM", "PMPM")
    .when(col("billing_fee_type_cd") == "MEMBERSHIPFEE_PPPM", "PPPM")
    .otherwise(col("billing_fee_type_cd"))  # Keeps original value if not matched
)

# Save back to Lakehouse
df_eds_dev_group_service_specialty_relations.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_service_specialty_relations")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Transform _**group_settings**_.

# CELL ********************

df_eds_dev_group_settings = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_settings")

# Keep Template = 0 and Type <> Test

df_eds_dev_group_settings = df_eds_dev_group_settings.withColumn(
    "send_ccr_to_pcp",
    when(col("send_ccr_to_pcp") == "N", "Optional")
    .when(col("send_ccr_to_pcp") == "Y", "Required")
    .when(col("send_ccr_to_pcp") == "Z", "Disallowed")
    .otherwise(col("send_ccr_to_pcp"))  # Keeps original value if not matched
)

df_eds_dev_group_settings = df_eds_dev_group_settings.withColumn(
    "enable_chronic_care_referrals",
    when(col("enable_chronic_care_referrals") == "A", "All")
    .when(col("enable_chronic_care_referrals") == "L", "Livongo")
    .when(col("enable_chronic_care_referrals") == "M", "myStrength Global")
    .when(col("enable_chronic_care_referrals") == "N", "None")
    .when(col("enable_chronic_care_referrals") == "Y", "")
    .otherwise(col("enable_chronic_care_referrals"))  # Keeps original value if not matched
)

df_eds_dev_group_settings = df_eds_dev_group_settings.withColumn(
    "lob_cd",
    when(col("lob_cd") == "LOBTYPE_ASO", "Commercial ASO")
    .when(col("lob_cd") == "LOBTYPE_FI", "Commercial FI")
    .when(col("lob_cd") == "LOBTYPE_MARKETPLACE", "Marketplace")
    .when(col("lob_cd") == "LOBTYPE_MEDICAID", "Medicaid Managed Care")
    .when(col("lob_cd") == "LOBTYPE_MEDICARE", "Medicare Advantage")
    .when(col("lob_cd") == "LOBTYPE_DSNP", "Dual Eligible Special Needs Plans (DSNP)")
    .when(col("lob_cd") == "LOBTYPE_NOTKNOWN", lit(None))
    .otherwise(col("lob_cd"))  # Keeps original value if not matched
)

df_eds_dev_group_settings = df_eds_dev_group_settings.withColumn(
    "membership_fee_type_cd",
    when(col("membership_fee_type_cd") == "MEMBERSHIPFEE_PEPM", "PEPM")
    .when(col("membership_fee_type_cd") == "MEMBERSHIPFEE_PMPM", "PMPM")
    .when(col("membership_fee_type_cd") == "MEMBERSHIPFEE_PPPM", "PPPM")
    .otherwise(col("membership_fee_type_cd"))  # Keeps original value if not matched
)

df_eds_dev_group_settings = df_eds_dev_group_settings.withColumn(
    "consult_reimbursement_method_cd",
    when(col("consult_reimbursement_method_cd") == "CONSULTREIMBURSEMENT_CLAIM", "Claims")
    .when(col("consult_reimbursement_method_cd") == "CONSULTREIMBURSEMENT_INFOCLAIM", "Informational Claims")
    .when(col("consult_reimbursement_method_cd") == "CONSULTREIMBURSEMENT_INVOICE", "Invoice")
    .when(col("consult_reimbursement_method_cd") == "CONSULTREIMBURSEMENT_NA", "N/A")
    .otherwise(col("consult_reimbursement_method_cd"))  # Keeps original value if not matched
)

# Save back to Lakehouse
df_eds_dev_group_settings.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_settings")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Transform **_groups_**.

# CELL ********************

df_eds_dev_groups = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_groups")

# Keep Template = 0 and Type <> Test

df_eds_dev_groups = df_eds_dev_groups.filter((df_eds_dev_groups["template"] == False) & (df_eds_dev_groups["group_type_cd"] != "GROUPTYPE_TEST"))

df_eds_dev_groups = df_eds_dev_groups.withColumn(
    "group_type_cd",
    when(col("group_type_cd") == "GROUPTYPE_COMPANY", "Company")
    .when(col("group_type_cd") == "GROUPTYPE_RESELLER", "Reseller")
    .when(col("group_type_cd") == "GROUPTYPE_CUSTOM", "Custom")
    .when(col("group_type_cd") == "GROUPTYPE_CARERECIPIENT", "Care Recipient")
    .when(col("group_type_cd") == "GROUPTYPE_RETAIL", "Retail")
    .when(col("group_type_cd") == "GROUPTYPE_TEST", "Test")
    .when(col("group_type_cd") == "GROUPTYPE_QUARANTINE", "Quarantine")
    .otherwise(col("group_type_cd"))  # Keeps original value if not matched
)

df_eds_dev_groups = df_eds_dev_groups.withColumn(
    "group_status",
    when((col("effective_end_dt").isNull()) & (col("effective_start_dt") < current_date()), "Group Active")
    .when((col("effective_end_dt") > current_date()) & (col("effective_start_dt") < current_date()), "Group Active")
    .otherwise("Group Inactive")
)

# Save back to Lakehouse
df_eds_dev_groups.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_groups")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Transform _**organization_marketing_communications**_.

# CELL ********************

df_eds_dev_organization_marketing_communications = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organization_marketing_communications")

# Replace optout_cd column values

df_eds_dev_organization_marketing_communications = df_eds_dev_organization_marketing_communications.withColumn("opt_out_cd",
                                                        when(col("opt_out_cd") == "MARKETINGCOMMOPT_OPTIN", "Opt In")
                                                        .when(col("opt_out_cd") == "MARKETINGCOMMOPT_OPTOUT", "Opt Out")
                                                        .when(col("opt_out_cd") == "MARKETINGCOMMOPT_APPROVAL", "Requires Approval")
                                                        .otherwise(col("opt_out_cd")))

# Pivot the table
df_eds_dev_organization_marketing_communications = df_eds_dev_organization_marketing_communications.groupBy("organization_id").pivot("marketing_communication_type_cd").agg(first("opt_out_cd"))

# Rename columns to match the expected output
df_eds_dev_organization_marketing_communications = df_eds_dev_organization_marketing_communications.withColumnRenamed("MARKETINGCOMMTYPE_DIRECTMAIL", "direct_mail") \
                                                                            .withColumnRenamed("MARKETINGCOMMTYPE_EMAIL", "email") \
                                                                            .withColumnRenamed("MARKETINGCOMMTYPE_INCENTIVE", "incentive") \
                                                                            .withColumnRenamed("MARKETINGCOMMTYPE_OUTBOUNDCALL", "outbound_calls") \
                                                                            .withColumnRenamed("MARKETINGCOMMTYPE_SMS", "sms_text")

# Save back to Lakehouse
df_eds_dev_organization_marketing_communications.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organization_marketing_communications")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Transform _**organization_user_relations**_.

# CELL ********************

df_eds_dev_organization_user_relations = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organization_user_relations")

# Keep Template = 0 and Type <> Test

df_eds_dev_organization_user_relations = df_eds_dev_organization_user_relations.filter((df_eds_dev_organization_user_relations["purpose_relation_type_cd"] == "RELATIONTYPE_ACCOUNTMANAGER") |
                                                                                    (df_eds_dev_organization_user_relations["purpose_relation_type_cd"] == "RELATIONTYPE_SALESAGENT"))

# Save back to Lakehouse
df_eds_dev_organization_user_relations.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organization_user_relations")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Transform _**organizations**_.

# CELL ********************

df_eds_dev_organizations = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organizations")

window_spec = Window.orderBy("organization_id")

df_eds_dev_organizations = df_eds_dev_organizations.withColumn("index", row_number().over(window_spec))

# Add custom cc_group_id column
df_eds_dev_organizations = df_eds_dev_organizations.withColumn("cc_group_id", when(col("group_id").isNull(), concat(lit("null"), col("Index").cast("string")))
                                    .otherwise(col("group_id").cast("string")))

# Add cc_master_organization column
df_eds_dev_organizations = df_eds_dev_organizations.withColumn("cc_master_organization_id", when(col("ancestry").contains("/"), split(col("ancestry"), "/")[1])
                                        .otherwise(col("ancestry")))

# Create DF to get parent organization names
parent_organizations = df_eds_dev_organizations.selectExpr(
    "organization_id",
    "organization_nm"
)

# First join to get cc_parent_nm
df_eds_dev_organizations = df_eds_dev_organizations.alias("orgs") \
    .join(parent_organizations.alias("parent"), 
          col("orgs.parent_id") == col("parent.organization_id"), 
          "left") \
    .select("orgs.*", col("parent.organization_nm").alias("cc_parent_nm"))

# Second join to get cc_master_organization_nm
df_eds_dev_organizations = df_eds_dev_organizations.alias("orgs") \
    .join(parent_organizations.alias("master"), 
          col("orgs.cc_master_organization_id") == col("master.organization_id"), 
          "left") \
    .select("orgs.*", col("master.organization_nm").alias("cc_master_organization_nm"))

# Drop index column
df_eds_dev_organizations = df_eds_dev_organizations.drop(df_eds_dev_organizations.index)

# Save back to Lakehouse
df_eds_dev_organizations.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organizations")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Transform _**ref_service_levels**_.

# CELL ********************

df_eds_dev_ref_service_levels = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_ref_service_levels")

df_eds_dev_ref_service_levels = df_eds_dev_ref_service_levels.withColumn(
    "cc_service_level_concat",
    concat("service_level_nm", lit(" : "), "level1", lit(" / "), "level2", lit(" / "), "level3")
)

# Save back to Lakehouse
df_eds_dev_ref_service_levels.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_ref_service_levels")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Transform _**sales_reps**_.

# CELL ********************

df_eds_dev_sales_reps = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_sales_reps")

# Keep Template = 0 and Type <> Test

df_eds_dev_sales_reps = df_eds_dev_sales_reps.filter((df_eds_dev_sales_reps["sales_rep_type_cd"] == "SALESREPTYPE_ACCOUNTMANAGER") |
                                                    (df_eds_dev_sales_reps["sales_rep_type_cd"] == "SALESREPTYPE_SALESAGENT"))

# Save back to Lakehouse
df_eds_dev_sales_reps.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_sales_reps")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Transform _**valid_group_sources**_.

# CELL ********************

df_eds_dev_valid_group_sources = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_valid_group_sources")

df_eds_dev_valid_group_sources = df_eds_dev_valid_group_sources.orderBy(["group_id", "updated_at"], ascending=[False, False])

df_eds_dev_valid_group_sources = df_eds_dev_valid_group_sources.dropDuplicates(["group_id"])

df_eds_dev_valid_group_sources = df_eds_dev_valid_group_sources.withColumn(
    "primary_source_cd",
    when(col("primary_source_cd") == "REGTYPE_APIHYBRID", "API (Staged Eligibility & Open)")
    .when(col("primary_source_cd") == "REGTYPE_HYBRID", "Staged Eligibility & RTE")
    .when(col("primary_source_cd") == "REGTYPE_OPEN", "Open")
    .when(col("primary_source_cd") == "REGTYPE_RTE", "RTE")
    .when(col("primary_source_cd") == "REGTYPE_STAGEDCLIENT", "Client Site")
    .when(col("primary_source_cd") == "REGTYPE_STAGEDELIGIBILITY", "Staged Eligibility")
    .when(col("primary_source_cd") == "REGTYPE_STAGEDREGISTRATION", "Staged Registration")
    .otherwise(col("primary_source_cd"))  # Keeps original value if not matched
)

df_eds_dev_valid_group_sources = df_eds_dev_valid_group_sources.withColumn(
    "dependent_source_cd",
    when(col("dependent_source_cd") == "REGTYPE_APIHYBRID", "API (Staged Eligibility & Open)")
    .when(col("dependent_source_cd") == "REGTYPE_HYBRID", "Staged Eligibility & RTE")
    .when(col("dependent_source_cd") == "REGTYPE_NODEPENDENTS", "Dependents CANNOT be added for this group")
    .when(col("dependent_source_cd") == "REGTYPE_OPEN", "Open")
    .when(col("dependent_source_cd") == "REGTYPE_RTE", "RTE")
    .when(col("dependent_source_cd") == "REGTYPE_STAGEDCLIENT", "Client Site")
    .when(col("dependent_source_cd") == "REGTYPE_STAGEDELIGIBILITY", "Staged Eligibility")
    .when(col("dependent_source_cd") == "REGTYPE_STAGEDREGISTRATION", "Staged Registration")
    .otherwise(col("dependent_source_cd"))  # Keeps original value if not matched
)

# Drop created_at and updated_at
df_eds_dev_valid_group_sources = df_eds_dev_valid_group_sources.drop("created_at", "updated_at")

# Save back to Lakehouse
df_eds_dev_valid_group_sources.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_valid_group_sources")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Get organization-inherited fields for each group_id.

# MARKDOWN ********************

# ##### Get _**print_url**_ and _**print_phone**_ for each _**group_id**_ in the _**groups**_ table and create _**web_url**_ column.

# CELL ********************

# Load data from Fabric Lakehouse (modify paths as needed)
organizations_df = spark.read.format("delta").load(
    "abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organizations"
)
organization_extensions_df = spark.read.format("delta").load(
    "abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organization_extensions"
)
groups_df = spark.read.format("delta").load(
    "abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_groups"
)

# Drop columns in groups_df
groups_df = groups_df.drop("print_phone_organization_id", "print_phone", "print_url_organization_id", "print_url", "web_url")

# Convert necessary columns to integer types
organizations_df = organizations_df.withColumn("group_id", col("group_id").cast("int")) \
                                   .withColumn("organization_id", col("organization_id").cast("int"))

organization_extensions_df = organization_extensions_df.withColumn("organization_id", col("organization_id").cast("int"))

# Split ancestry into an array, reverse it, and explode while keeping position
organizations_exploded = organizations_df.withColumn("ancestry_list", split(col("ancestry"), "/")) \
                                         .withColumn("ancestry_list", expr("reverse(ancestry_list)")) \
                                         .select("group_id", "organization_id", posexplode(col("ancestry_list")).alias("ancestry_position", "organization_id_exploded"))

# Join with organization_extensions to check which IDs have print_url and print_phone
organizations_with_extensions = organizations_exploded.join(
    organization_extensions_df, 
    organizations_exploded.organization_id_exploded == organization_extensions_df.organization_id, 
    "left"
)

# Define window specification to order by ancestry_position within each group_id
window_spec = Window.partitionBy("group_id").orderBy("ancestry_position")

# Select the first organization_id_exploded that has a non-null print_url AND get the actual value
organizations_ranked = organizations_with_extensions.withColumn(
    "print_url_organization_id", first(
        expr("CASE WHEN print_url IS NOT NULL THEN organization_id_exploded END"), ignorenulls=True
    ).over(window_spec)
).withColumn(
    "print_url", first(
        expr("CASE WHEN print_url IS NOT NULL THEN print_url END"), ignorenulls=True
    ).over(window_spec)
).withColumn(
    "print_phone_organization_id", first(
        expr("CASE WHEN print_phone IS NOT NULL THEN organization_id_exploded END"), ignorenulls=True
    ).over(window_spec)
).withColumn(
    "print_phone", first(
        expr("CASE WHEN print_phone IS NOT NULL THEN print_phone END"), ignorenulls=True
    ).over(window_spec)
)

# Keep only distinct values per group_id
result_df = organizations_ranked.select("group_id", "print_phone_organization_id", "print_phone", "print_url_organization_id", "print_url").dropDuplicates()

# Remove rows where both columns are NULL (fix for duplicate rows issue)
result_df = result_df.filter((col("print_url_organization_id").isNotNull()) | (col("print_phone_organization_id").isNotNull()))

# Directly join with groups_df and retain all original columns without needing additional joins later
final_df = groups_df.join(result_df, "group_id", "left")

# Sort DF
final_df = final_df.orderBy(["group_id"], ascending = [True])

# Add web_url column
final_df = final_df.withColumn("web_url", lower(concat(lit("www."), col("print_url"))))

# Save back to Lakehouse
final_df.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_groups")

# Show final result with print_url and print_phone
display(final_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Get _**Marketing Settings**_ for each _**group_id**_ in the _**groups**_ table.

# CELL ********************

# Load data from Fabric Lakehouse (modify paths as needed)
organizations_df = spark.read.format("delta").load(
    "abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organizations"
)
organization_marketing_communications_df = spark.read.format("delta").load(
    "abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organization_marketing_communications"
)
groups_df = spark.read.format("delta").load(
    "abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_groups"
)

# Drop columns in groups_df
groups_df = groups_df.drop("direct_mail_organization_id", "direct_mail", "email_organization_id", "email",
                            "incentive_organization_id", "incentive", "outbound_calls_organization_id", "outbound_calls",
                            "sms_text_organization_id", "sms_text")

# Convert necessary columns to integer types
organizations_df = organizations_df.withColumn("group_id", col("group_id").cast("int")) \
                                   .withColumn("organization_id", col("organization_id").cast("int"))

organization_marketing_communications_df = organization_marketing_communications_df.withColumn("organization_id", col("organization_id").cast("int"))

# Split ancestry into an array, reverse it, and explode while keeping position
organizations_exploded = organizations_df.withColumn("ancestry_list", split(col("ancestry"), "/")) \
                                         .withColumn("ancestry_list", expr("reverse(ancestry_list)")) \
                                         .select("group_id", "organization_id", posexplode(col("ancestry_list")).alias("ancestry_position", "organization_id_exploded"))

# Join with organization_extensions to check which IDs have Marketing Settings
organizations_with_extensions = organizations_exploded.join(
    organization_marketing_communications_df, 
    organizations_exploded.organization_id_exploded == organization_marketing_communications_df.organization_id, 
    "left"
)

# Define window specification to order by ancestry_position within each group_id
window_spec = Window.partitionBy("group_id").orderBy("ancestry_position")

# Select the first organization_id_exploded that has a non-null Marketing Setting
organizations_ranked = organizations_with_extensions.withColumn(
    "direct_mail_organization_id", first(
        expr("CASE WHEN direct_mail IS NOT NULL THEN organization_id_exploded END"), ignorenulls=True
    ).over(window_spec)
).withColumn(
    "direct_mail", first(
        expr("CASE WHEN direct_mail IS NOT NULL THEN direct_mail END"), ignorenulls=True
    ).over(window_spec)
).withColumn(
    "email_organization_id", first(
        expr("CASE WHEN email IS NOT NULL THEN organization_id_exploded END"), ignorenulls=True
    ).over(window_spec)
).withColumn(
    "email", first(
        expr("CASE WHEN email IS NOT NULL THEN email END"), ignorenulls=True
    ).over(window_spec)
).withColumn(
    "incentive_organization_id", first(
        expr("CASE WHEN incentive IS NOT NULL THEN organization_id_exploded END"), ignorenulls=True
    ).over(window_spec)
).withColumn(
    "incentive", first(
        expr("CASE WHEN incentive IS NOT NULL THEN incentive END"), ignorenulls=True
    ).over(window_spec)
).withColumn(
    "outbound_calls_organization_id", first(
        expr("CASE WHEN outbound_calls IS NOT NULL THEN organization_id_exploded END"), ignorenulls=True
    ).over(window_spec)
).withColumn(
    "outbound_calls", first(
        expr("CASE WHEN outbound_calls IS NOT NULL THEN outbound_calls END"), ignorenulls=True
    ).over(window_spec)
).withColumn(
    "sms_text_organization_id", first(
        expr("CASE WHEN sms_text IS NOT NULL THEN organization_id_exploded END"), ignorenulls=True
    ).over(window_spec)
).withColumn(
    "sms_text", first(
        expr("CASE WHEN sms_text IS NOT NULL THEN sms_text END"), ignorenulls=True
    ).over(window_spec)
)

# Keep only distinct values per group_id
result_df = organizations_ranked.select("group_id", "direct_mail_organization_id", "direct_mail", "email_organization_id", "email",
                                        "incentive_organization_id", "incentive", "outbound_calls_organization_id", "outbound_calls",
                                        "sms_text_organization_id", "sms_text").dropDuplicates()

# Remove rows where all columns are NULL (fix for duplicate rows issue)
result_df = result_df.filter((col("direct_mail_organization_id").isNotNull()) | (col("email_organization_id").isNotNull()) | (col("incentive_organization_id").isNotNull()) |
                            (col("outbound_calls_organization_id").isNotNull()) | (col("sms_text_organization_id").isNotNull()))

# Directly join with groups_df and retain all original columns without needing additional joins later
final_df = groups_df.join(result_df, "group_id", "left")

# Remove rows with NULLs in required columns
final_df = final_df.filter(
    col("print_url_organization_id").isNotNull() &
    col("print_url").isNotNull() &
    col("print_phone_organization_id").isNotNull() &
    col("print_phone").isNotNull() &
    col("direct_mail_organization_id").isNotNull() &
    col("direct_mail").isNotNull() &
    col("email_organization_id").isNotNull() &
    col("email").isNotNull() &
    col("incentive_organization_id").isNotNull() &
    col("incentive").isNotNull() &
    col("outbound_calls_organization_id").isNotNull() &
    col("outbound_calls").isNotNull() &
    col("sms_text_organization_id").isNotNull() &
    col("sms_text").isNotNull()
)

# Drop duplicates
final_df = final_df.dropDuplicates(["group_id"])

# Change group_id to String
final_df = final_df.withColumn("group_id", col("group_id").cast("string"))

# Sort DF
final_df = final_df.orderBy(["group_id"], ascending = [True])

# Save back to Lakehouse
final_df.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_groups")

# Show final result with print_url and print_phone
display(final_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Create auxiliar table to get Account Manager and Sales Agent
# 


# MARKDOWN ********************

# organizations_df = spark.read.format("delta").load(
#     "abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organizations"
# )
# 
# organization_user_relations_df = spark.read.format("delta").load(
#     "abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organization_user_relations"
# )
# 
# sales_reps_df = spark.read.format("delta").load(
#     "abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_sales_reps"
# )
# 
# persons_df = spark.read.format("delta").load(
#     "abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_persons"
# )
# 
# # Filter DFs
# 
# final_df = sales_reps_df.join(persons_df, "person_id", "inner")
# 
# display(final_df)
# 
# final_df = final_df.join(organization_user_relations_df, col("sales_rep_id") == col("user_id"), "left")
# 
# display(final_df)


# MARKDOWN ********************

# # Check Group count

# CELL ********************

row_count = final_df.count()  # Count the number of rows
print(f"Total rows: {row_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

bronze_groups_df = spark.read.format("delta").load(
    "abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_100_bronze_groups"
)

bronze_row_count = bronze_groups_df.count()  # Count the number of rows
print(f"Total rows: {bronze_row_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
