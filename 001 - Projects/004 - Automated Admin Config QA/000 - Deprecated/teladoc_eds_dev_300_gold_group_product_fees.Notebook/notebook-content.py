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

# ### Product & Services fees, not settings.


# MARKDOWN ********************

# Comments:
# - Not all member groups have all product and services, so what I'm doing is calculate all fees and then join with a table containing member groups and the products and services enabled for each of them.
# - The group_relation_pricings.relation_type column indicates how to use the group_relation_pricings.relation_id column of the same table. According to the group_relation_pricings.relacion_type column, the group_relation_pricings.relation_id links to different tables.
# - For group_relation_pricings.relation_type = 'GroupServiceSpecialtyFeatureRelation', column group_relation_pricings.relation_id links to group_service_specialty_feature_relations on group_service_specialty_feature_relations.group_service_specialty_feature_relation_id = group_relation_pricings.relation_id.
# - For group_relation_pricings.relation_type = 'GroupOffer', column group_relation_pricings.relation_id links to group_offers on group_offers.group_offer_id = group_relation_pricings.relation_id.
# 
# Reference:
# - Primary Care New Patient Visit Fee - Member = Primary Care Follow-up Visit Fee - Member + Primary Care New Patient Visit Fee - Member. 
# - Primary Care Annual Checkup Visit Fee - Member = Primary Care Follow-up Visit Fee - Member + Primary Care Annual Checkup Visit Fee - Member. 
# - Diabetes Care Follow-up Visit Fee - Client = Primary Care Follow-up Visit Fee - Client + Diabetes Care Follow-up Visit Fee - Client. 
# - Diabetes Care Follow-up Visit Fee - Member = Primary Care Follow-up Visit Fee - Member + Diabetes Care Follow-up Visit Fee - Member. 
# - Diabetes Care New Patient Visit Fee - Member = Diabetes Care Follow-up Visit Fee - Member + Diabetes Care New Patient Visit Fee - Member.
# - Diabetes Care New Patient Visit Fee - Client = Diabetes Care Follow-up Visit Fee - Client + Diabetes Care New Patient Visit Client - Member. 


# MARKDOWN ********************

# Import.

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Initialize session.

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

# Load required tables.

# CELL ********************

df_teladoc_eds_dev_organizations = (
    spark.read.format("delta")
    .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organizations")
)

df_teladoc_eds_dev_groups = (
    spark.read.format("delta")
    .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_groups")
)

df_teladoc_eds_dev_group_service_specialty_relations = (
    spark.read.format("delta")
    .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_service_specialty_relations")
)

df_teladoc_eds_dev_ref_service_specialties = (
    spark.read.format("delta")
    .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_ref_service_specialties")
)

df_teladoc_eds_dev_group_service_specialty_feature_relations = (
    spark.read.format("delta")
    .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_service_specialty_feature_relations")
)

df_teladoc_eds_dev_group_relation_pricings = (
    spark.read.format("delta")
    .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_relation_pricings")
)

df_teladoc_eds_dev_group_service_specialty_feature_settings = (
    spark.read.format("delta")
    .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_service_specialty_feature_settings")
)

df_teladoc_eds_dev_ref_service_specialty_features = (
    spark.read.format("delta")
    .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_ref_service_specialty_features")
)

df_teladoc_eds_dev_ref_features = (
    spark.read.format("delta")
    .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_ref_features")
)

df_teladoc_eds_dev_ref_geographic_regions = (
    spark.read.format("delta")
    .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_ref_geographic_regions")
)

df_teladoc_eds_dev_group_offers = (
    spark.read.format("delta")
    .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_offers")
)

df_teladoc_eds_dev_offer_service_specialty_feature_relations = (
    spark.read.format("delta")
    .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_offer_service_specialty_feature_relations")
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }

# MARKDOWN ********************

# Select columns.


# CELL ********************

df_teladoc_eds_dev_organizations = (
    df_teladoc_eds_dev_organizations.select(
        "organization_id",
        "organization_nm",
        "parent_id",
        "ancestry",
        "group_id",
        "party_id"
    )
)

df_teladoc_eds_dev_groups = (
    df_teladoc_eds_dev_groups.select(
        "group_id",
        "group_nm",
        "effective_start_dt",
        "effective_end_dt",
        "registration_group_cd",
        "card_nm",
        "source_group_root",
        "group_type_cd",
        "legacy_group_id"
    )
)

df_teladoc_eds_dev_group_service_specialty_relations = (
    df_teladoc_eds_dev_group_service_specialty_relations.select(
        "group_id",
        "service_specialty_cd",
        "geographic_region_coverage_cd",
        "group_service_specialty_relation_id",
        "min_age",
        "max_age"
    )
)

df_teladoc_eds_dev_ref_service_specialties = (
    df_teladoc_eds_dev_ref_service_specialties.select(
        "service_specialty_cd",
        "service_specialty_nm"
    )
)

df_teladoc_eds_dev_group_service_specialty_feature_relations = (
    df_teladoc_eds_dev_group_service_specialty_feature_relations.select(
        "group_service_specialty_feature_relation_id",
        "group_service_specialty_relation_id",
        "service_specialty_feature_cd"
    )
)

df_teladoc_eds_dev_group_service_specialty_feature_settings = (
    df_teladoc_eds_dev_group_service_specialty_feature_settings.select(
        "group_service_specialty_feature_relation_id"
    )
)

df_teladoc_eds_dev_ref_service_specialty_features = (
    df_teladoc_eds_dev_ref_service_specialty_features.select(
        "service_specialty_feature_cd",
        "service_specialty_feature_nm",
        "feature_cd"
    )
)

df_teladoc_eds_dev_ref_features = (
    df_teladoc_eds_dev_ref_features.select(
        "feature_cd"
    )
)

df_teladoc_eds_dev_group_relation_pricings = (
    df_teladoc_eds_dev_group_relation_pricings.select(
        "relation_id",
        "relation_type",
        "pricing_type_cd",
        "invoice_method_cd",
        "invoice_submethod_cd",
        "amount"
    )
)

df_teladoc_eds_dev_ref_geographic_regions = (
    df_teladoc_eds_dev_ref_geographic_regions.select(
        "geographic_region_cd"
    )
)

df_teladoc_eds_dev_group_offers = (
    df_teladoc_eds_dev_group_offers.select(
        "group_offer_id",
        "group_id",
        "promotion_cd"
    )
)

df_teladoc_eds_dev_offer_service_specialty_feature_relations = (
    df_teladoc_eds_dev_offer_service_specialty_feature_relations.select(
        "offer_id",
        "service_specialty_feature_cd"
    )
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Function to add prefix.

# CELL ********************

def add_prefix(df, prefix):
    """
    Adds a prefix to all column names in a PySpark DataFrame.

    Args:
    df (DataFrame): The input PySpark DataFrame.
    prefix (str): The prefix to add.

    Returns:
    DataFrame: A new DataFrame with renamed columns.
    """
    renamed_columns = [F.col(c).alias(f"{prefix}{c}") for c in df.columns]
    return df.select(*renamed_columns)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Apply prefix.

# CELL ********************

df_teladoc_eds_dev_organizations = add_prefix(df_teladoc_eds_dev_organizations, "o_")
df_teladoc_eds_dev_groups = add_prefix(df_teladoc_eds_dev_groups, "g_")
df_teladoc_eds_dev_group_service_specialty_relations = add_prefix(df_teladoc_eds_dev_group_service_specialty_relations, "gssr_")
df_teladoc_eds_dev_ref_service_specialties = add_prefix(df_teladoc_eds_dev_ref_service_specialties, "rss_")
df_teladoc_eds_dev_group_service_specialty_feature_relations = add_prefix(df_teladoc_eds_dev_group_service_specialty_feature_relations, "gssfr_")
df_teladoc_eds_dev_group_service_specialty_feature_settings = add_prefix(df_teladoc_eds_dev_group_service_specialty_feature_settings, "gssfs_")
df_teladoc_eds_dev_ref_service_specialty_features = add_prefix(df_teladoc_eds_dev_ref_service_specialty_features, "rssf_")
df_teladoc_eds_dev_ref_features = add_prefix(df_teladoc_eds_dev_ref_features, "rf_")
df_teladoc_eds_dev_group_relation_pricings = add_prefix(df_teladoc_eds_dev_group_relation_pricings, "grp_")
df_teladoc_eds_dev_ref_geographic_regions = add_prefix(df_teladoc_eds_dev_ref_geographic_regions, "rgr_")
df_teladoc_eds_dev_group_offers = add_prefix(df_teladoc_eds_dev_group_offers, "go_")
df_teladoc_eds_dev_offer_service_specialty_feature_relations = add_prefix(df_teladoc_eds_dev_offer_service_specialty_feature_relations, "ossfr_")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Joins required to get the group_product_relations dataset, which will be used at the end to remove those fees for products not enabled.

# CELL ********************

group_product_relations = df_teladoc_eds_dev_organizations.join(
    df_teladoc_eds_dev_groups,
    df_teladoc_eds_dev_organizations["o_group_id"] == df_teladoc_eds_dev_groups["g_group_id"],
    how="inner"
)

group_product_relations = group_product_relations.join(
    df_teladoc_eds_dev_group_service_specialty_relations,
    group_product_relations["g_group_id"] == df_teladoc_eds_dev_group_service_specialty_relations["gssr_group_id"],
    how="inner"
)

group_product_relations = group_product_relations.join(
    df_teladoc_eds_dev_ref_service_specialties,
    group_product_relations["gssr_service_specialty_cd"] == df_teladoc_eds_dev_ref_service_specialties["rss_service_specialty_cd"],
    how="inner"
)

group_product_relations = group_product_relations.join(
    df_teladoc_eds_dev_ref_geographic_regions,
    group_product_relations["gssr_geographic_region_coverage_cd"] == df_teladoc_eds_dev_ref_geographic_regions["rgr_geographic_region_cd"],
    how="inner"
)

group_product_relations = group_product_relations.join(
    df_teladoc_eds_dev_group_service_specialty_feature_relations,
    group_product_relations["gssr_group_service_specialty_relation_id"] == df_teladoc_eds_dev_group_service_specialty_feature_relations["gssfr_group_service_specialty_relation_id"],
    how="inner"
)

group_product_relations = group_product_relations.join(
    df_teladoc_eds_dev_ref_service_specialty_features,
    group_product_relations["gssfr_service_specialty_feature_cd"] == df_teladoc_eds_dev_ref_service_specialty_features["rssf_service_specialty_feature_cd"],
    how="inner"
)

group_product_relations = group_product_relations.join(
    df_teladoc_eds_dev_ref_features,
    group_product_relations["rssf_feature_cd"] == df_teladoc_eds_dev_ref_features["rf_feature_cd"],
    how="inner"
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

group_product_relations = group_product_relations.select(
    "g_group_id",
    "g_legacy_group_id",
    "rss_service_specialty_nm",
    "rssf_service_specialty_feature_nm"
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Joins required to get the product_fees_raw_1 dataset. Used in the first query of the Power BI report.

# CELL ********************

product_fees_raw_1 = df_teladoc_eds_dev_groups.join(
    df_teladoc_eds_dev_group_service_specialty_relations,
    df_teladoc_eds_dev_groups["g_group_id"] == df_teladoc_eds_dev_group_service_specialty_relations["gssr_group_id"],
    how="inner"
)

product_fees_raw_1 = product_fees_raw_1.join(
    df_teladoc_eds_dev_ref_service_specialties,
    product_fees_raw_1["gssr_service_specialty_cd"] == df_teladoc_eds_dev_ref_service_specialties["rss_service_specialty_cd"],
    how="inner"
)

product_fees_raw_1 = product_fees_raw_1.join(
    df_teladoc_eds_dev_ref_geographic_regions,
    product_fees_raw_1["gssr_geographic_region_coverage_cd"] == df_teladoc_eds_dev_ref_geographic_regions["rgr_geographic_region_cd"],
    how="inner"
)

product_fees_raw_1 = product_fees_raw_1.join(
    df_teladoc_eds_dev_group_service_specialty_feature_relations,
    product_fees_raw_1["gssr_group_service_specialty_relation_id"] == df_teladoc_eds_dev_group_service_specialty_feature_relations["gssfr_group_service_specialty_relation_id"],
    how="inner"
)

product_fees_raw_1 = product_fees_raw_1.join(
    df_teladoc_eds_dev_ref_service_specialty_features,
    product_fees_raw_1["gssfr_service_specialty_feature_cd"] == df_teladoc_eds_dev_ref_service_specialty_features["rssf_service_specialty_feature_cd"],
    how="inner"
)

product_fees_raw_1 = product_fees_raw_1.join(
    df_teladoc_eds_dev_ref_features,
    product_fees_raw_1["rssf_feature_cd"] == df_teladoc_eds_dev_ref_features["rf_feature_cd"],
    how="inner"
)

product_fees_raw_1 = product_fees_raw_1.join(
    df_teladoc_eds_dev_group_relation_pricings,
    (product_fees_raw_1["gssfr_group_service_specialty_feature_relation_id"] == df_teladoc_eds_dev_group_relation_pricings["grp_relation_id"]) &
    (df_teladoc_eds_dev_group_relation_pricings["grp_relation_type"] == "GroupServiceSpecialtyFeatureRelation"),
    how="inner"
)

product_fees_raw_1 = product_fees_raw_1.join(
    df_teladoc_eds_dev_group_service_specialty_feature_settings,
    product_fees_raw_1["gssfr_group_service_specialty_feature_relation_id"] == df_teladoc_eds_dev_group_service_specialty_feature_settings["gssfs_group_service_specialty_feature_relation_id"],
    how="left"
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Joins required to get the product_fees_raw_2 dataset.

# CELL ********************

product_fees_raw_2 = df_teladoc_eds_dev_organizations.join(
    df_teladoc_eds_dev_groups,
    df_teladoc_eds_dev_organizations["o_group_id"] == df_teladoc_eds_dev_groups["g_group_id"],
    how="inner"
)

product_fees_raw_2 = product_fees_raw_2.join(
    df_teladoc_eds_dev_group_offers,
    product_fees_raw_2["g_group_id"] == df_teladoc_eds_dev_group_offers["go_group_id"],
    how="inner"
)

product_fees_raw_2 = product_fees_raw_2.join(
    df_teladoc_eds_dev_group_relation_pricings,
    product_fees_raw_2["go_group_offer_id"] == df_teladoc_eds_dev_group_relation_pricings["grp_relation_id"],
    how="inner"
)

product_fees_raw_2 = product_fees_raw_2.join(
    df_teladoc_eds_dev_offer_service_specialty_feature_relations,
    product_fees_raw_2["go_group_offer_id"] == df_teladoc_eds_dev_offer_service_specialty_feature_relations["ossfr_offer_id"],
    how="inner"
)

product_fees_raw_2 = product_fees_raw_2.join(
    df_teladoc_eds_dev_group_service_specialty_relations,
    product_fees_raw_2["g_group_id"] == df_teladoc_eds_dev_group_service_specialty_relations["gssr_group_id"],
    how="inner"
)

product_fees_raw_2 = product_fees_raw_2.join(
    df_teladoc_eds_dev_ref_service_specialties,
    product_fees_raw_2["gssr_service_specialty_cd"] == df_teladoc_eds_dev_ref_service_specialties["rss_service_specialty_cd"],
    how="inner"
)

product_fees_raw_2 = product_fees_raw_2.join(
    df_teladoc_eds_dev_ref_geographic_regions,
    product_fees_raw_2["gssr_geographic_region_coverage_cd"] == df_teladoc_eds_dev_ref_geographic_regions["rgr_geographic_region_cd"],
    how="inner"
)

product_fees_raw_2 = product_fees_raw_2.join(
    df_teladoc_eds_dev_group_service_specialty_feature_relations,
    product_fees_raw_2["gssr_group_service_specialty_relation_id"] == df_teladoc_eds_dev_group_service_specialty_feature_relations["gssfr_group_service_specialty_relation_id"],
    how="inner"
)

product_fees_raw_2 = product_fees_raw_2.join(
    df_teladoc_eds_dev_ref_service_specialty_features,
    product_fees_raw_2["gssfr_service_specialty_feature_cd"] == df_teladoc_eds_dev_ref_service_specialty_features["rssf_service_specialty_feature_cd"],
    how="inner"
)

product_fees_raw_2 = product_fees_raw_2.join(
    df_teladoc_eds_dev_ref_features,
    product_fees_raw_2["rssf_feature_cd"] == df_teladoc_eds_dev_ref_features["rf_feature_cd"],
    how="inner"
)

product_fees_raw_2 = product_fees_raw_2.join(
    df_teladoc_eds_dev_group_service_specialty_feature_settings,
    product_fees_raw_2["gssfr_group_service_specialty_feature_relation_id"] == df_teladoc_eds_dev_group_service_specialty_feature_settings["gssfs_group_service_specialty_feature_relation_id"],
    how="left"
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Fees that do not require aggregation.
# - Base Service Specialty Features Visit Fees. 
# - Primary Care Follow-up Visit Fees.
# - Membership Fees.

# CELL ********************

# Query 1.
no_aggregation_fees = product_fees_raw_1.withColumn(
    "fee_name",
    F.when(
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_BILLING") &
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("grp_invoice_submethod_cd") == "INVOICESUBMETHOD_BILLEDAMOUNT") &
        (F.col("rf_feature_cd") == "BASE"),
        "Membership Fee"
    ).when(
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("rf_feature_cd") == "BASE"),
        "Visit Fee - Client"
    ).when(
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("rf_feature_cd") == "BASE"),
        "Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("rssf_service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Client"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("rssf_service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Member"
    ).otherwise(None)
)

no_aggregation_fees = no_aggregation_fees.filter(
    (F.col("fee_name").isNotNull())
)

no_aggregation_fees = no_aggregation_fees.select(
    "g_group_id",
    "g_legacy_group_id",
    "rss_service_specialty_nm",
    "rssf_service_specialty_feature_nm",
    "fee_name",
    "grp_amount"
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Fees that require aggregation.
# aggregated_fees_part_1 is needed to get the following fees:
# - Therapy Visit Fees
# - Mental Health Membership Fee.
# - Psychiatry Ongoing Visit Fee.
# - Primary Care Follow-up Visit Fee.
# - Primary Care Membership Fee.
# - Primary Care Visit Fees.

# CELL ********************

# Start of Query 2.
aggregated_fees_part_1 = product_fees_raw_1.withColumn(
    "fee_name",
    F.when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "BEHAVHEALTH_BASE"),
        "Therapy Visit Fee - Client"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "BEHAVHEALTH_BASE"),
        "Therapy Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_BILLING") &
        (F.col("grp_invoice_submethod_cd") == "INVOICESUBMETHOD_BILLEDAMOUNT") &
        (F.col("gssfr_service_specialty_feature_cd") == "BEHAVHEALTH_BASE"),
        "Mental Health Membership Fee"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "BEHAVHEALTH_MD"),
        "Psychiatry Ongoing Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "BEHAVHEALTH_MD"),
        "Psychiatry Ongoing Visit Fee - Client"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_BASE"),
        "Primary Care Visit Fee - Client"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_BASE"),
        "Primary Care Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Client"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_BILLING") &
        (F.col("grp_invoice_submethod_cd") == "INVOICESUBMETHOD_BILLEDAMOUNT") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_BASE"),
        "Primary Care Membership Fee"
    ).otherwise(None)
)

aggregated_fees_part_1 = aggregated_fees_part_1.select(
    "g_group_id",
    "g_legacy_group_id",
    "rss_service_specialty_nm",
    "rssf_service_specialty_feature_nm",
    "fee_name",
    "grp_amount"
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# aggregated_fees_part_2 is needed to get the following fees:
# - Psychiatry Initial Visit Fee.
# - Primary Care Annual Checkup Visit Fee.
# - Primary Care New Patient Visit Fee.

# CELL ********************

aggregated_fees_part_2 = product_fees_raw_2.withColumn(
    "fee_name",
    F.when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("ossfr_service_specialty_feature_cd") == "BEHAVHEALTH_MD") &
        (F.col("rss_service_specialty_cd") == "BEHAVHEALTH") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_PREMIUM"),
        "Psychiatry Initial Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("ossfr_service_specialty_feature_cd") == "BEHAVHEALTH_MD") &
        (F.col("rss_service_specialty_cd") == "BEHAVHEALTH") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_PREMIUM"),
        "Psychiatry Initial Visit Fee - Client"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("ossfr_service_specialty_feature_cd") == "VPC_MD") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
        (F.col("go_promotion_cd") == "PREMIUM_ANNUALWITHSPECIALTYFEATURE"),
        "Primary Care Annual Checkup Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("ossfr_service_specialty_feature_cd") == "VPC_MD") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
        (F.col("go_promotion_cd") == "PREMIUM_ANNUALWITHSPECIALTYFEATURE"),
        "Primary Care Annual Checkup Visit Fee - Client"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("ossfr_service_specialty_feature_cd") == "VPC_MD") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
        (F.col("go_promotion_cd") == "PREMIUM_FIRSTWITHSPECIALTYFEATURE"),
        "Primary Care New Patient Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("ossfr_service_specialty_feature_cd") == "VPC_MD") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
        (F.col("go_promotion_cd") == "PREMIUM_FIRSTWITHSPECIALTYFEATURE"),
        "Primary Care New Patient Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_part_2 = aggregated_fees_part_2.filter(
    (F.col("grp_pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
    (F.col("grp_relation_type") == "GroupOffer") &
    (F.col("ossfr_service_specialty_feature_cd") == F.col("gssfr_service_specialty_feature_cd"))
)

aggregated_fees_part_2 = aggregated_fees_part_2.select(
    "g_group_id",
    "g_legacy_group_id",
    "rss_service_specialty_nm",
    "rssf_service_specialty_feature_nm",
    "fee_name",
    "grp_amount"
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# aggregated_fees_final_part_1 is needed to get the following fees:
# - Psychiatry Initial Visit Fees.
# - Primary Care Annual Checkup Visit Fees.

# CELL ********************

aggregated_fees_final_part_1 = aggregated_fees_part_1.unionByName(aggregated_fees_part_2)

aggregated_fees_final_part_1 = aggregated_fees_final_part_1.withColumn(
    "fee_name",
    F.when(
        F.col("fee_name").isin(
            "Psychiatry Initial Visit Fee - Member",
            "Psychiatry Ongoing Visit Fee - Member",
            "Therapy Visit Fee - Member"
        ),
        "Psychiatry Initial Visit Fee - Member"
    ).when(
        F.col("fee_name").isin(
            "Psychiatry Initial Visit Fee - Client",
            "Psychiatry Ongoing Visit Fee - Client",
            "Therapy Visit Fee - Client"
        ),
        "Psychiatry Initial Visit Fee - Client"
    ).when(
        F.col("fee_name").isin(
            "Primary Care Annual Checkup Visit Fee - Member",
            "Primary Care Follow-up Visit Fee - Member",
            "Primary Care Visit Fee - Member"
        ),
        "Primary Care Annual Checkup Visit Fee - Member"
    ).when(
        F.col("fee_name").isin(
            "Primary Care Annual Checkup Visit Fee - Client",
            "Primary Care Follow-up Visit Fee - Client",
            "Primary Care Fee - Client"
        ),
        "Primary Care Annual Checkup Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_final_part_1 = (
    aggregated_fees_final_part_1
    .groupBy(
        "g_group_id", 
        "fee_name"
    )
    .agg(
        F.sum("grp_amount").alias("grp_amount"),
        F.first("g_legacy_group_id").alias("g_legacy_group_id"),
        F.first("rss_service_specialty_nm").alias("rss_service_specialty_nm"), 
        F.first("rssf_service_specialty_feature_nm").alias("rssf_service_specialty_feature_nm")
    )
    .filter(F.col("fee_name").isNotNull())
)
# End of Query 2.

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# aggregated_fees_part_3 is needed to get the following fees:
# - Therapy Visit Fees.
# - Mental Health Membership Fee.
# - Psychiatry Ongoing Visit Fee.
# - Primary Care Follow-up Visit Fee.
# - Primary Care Membership Fee.
# - Primary Care Visit Fees.

# CELL ********************

# Start of Query 3.
aggregated_fees_part_3 = product_fees_raw_1.withColumn(
    "fee_name",
    F.when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "BEHAVHEALTH_BASE"),
        "Therapy Visit Fee - Client"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "BEHAVHEALTH_BASE"),
        "Therapy Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_BILLING") &
        (F.col("grp_invoice_submethod_cd") == "INVOICESUBMETHOD_BILLEDAMOUNT") &
        (F.col("gssfr_service_specialty_feature_cd") == "BEHAVHEALTH_BASE"),
        "Mental Health Membership Fee"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "BEHAVHEALTH_MD"),
        "Psychiatry Ongoing Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "BEHAVHEALTH_MD"),
        "Psychiatry Ongoing Visit Fee - Client"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_BASE"),
        "Primary Care Visit Fee - Client"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_BASE"),
        "Primary Care Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Client"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_BILLING") &
        (F.col("grp_invoice_submethod_cd") == "INVOICESUBMETHOD_BILLEDAMOUNT") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_BASE"),
        "Primary Care Membership Fee"
    ).otherwise(None)
)

aggregated_fees_part_3 = aggregated_fees_part_3.select(
    "g_group_id",
    "g_legacy_group_id",
    "rss_service_specialty_nm",
    "rssf_service_specialty_feature_nm",
    "fee_name",
    "grp_amount"
) 

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# aggregated_fees_part_4 is needed to get the following fees:
# - Psychiatry Initial Visit Fee.
# - Primary Care Annual Checkup Visit Fee.
# - Primary Care New Patient Visit Fee.

# CELL ********************

aggregated_fees_part_4 = product_fees_raw_2.withColumn(
    "fee_name",
    F.when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("ossfr_service_specialty_feature_cd") == "BEHAVHEALTH_MD") &
        (F.col("rss_service_specialty_cd") == "BEHAVHEALTH") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_PREMIUM"),
        "Psychiatry Initial Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("ossfr_service_specialty_feature_cd") == "BEHAVHEALTH_MD") &
        (F.col("rss_service_specialty_cd") == "BEHAVHEALTH") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_PREMIUM"),
        "Psychiatry Initial Visit Fee - Client"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("ossfr_service_specialty_feature_cd") == "VPC_MD") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
        (F.col("go_promotion_cd") == "PREMIUM_ANNUALWITHSPECIALTYFEATURE"),
        "Primary Care Annual Checkup Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("ossfr_service_specialty_feature_cd") == "VPC_MD") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
        (F.col("go_promotion_cd") == "PREMIUM_ANNUALWITHSPECIALTYFEATURE"),
        "Primary Care Annual Checkup Visit Fee - Client"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("ossfr_service_specialty_feature_cd") == "VPC_MD") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
        (F.col("go_promotion_cd") == "PREMIUM_FIRSTWITHSPECIALTYFEATURE"),
        "Primary Care New Patient Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("ossfr_service_specialty_feature_cd") == "VPC_MD") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
        (F.col("go_promotion_cd") == "PREMIUM_FIRSTWITHSPECIALTYFEATURE"),
        "Primary Care New Patient Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_part_4 = aggregated_fees_part_4.filter(
    (F.col("grp_pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
    (F.col("grp_relation_type") == "GroupOffer") &
    (F.col("ossfr_service_specialty_feature_cd") == F.col("gssfr_service_specialty_feature_cd"))
)

aggregated_fees_part_4 = aggregated_fees_part_4.select(
    "g_group_id",
    "g_legacy_group_id",
    "rss_service_specialty_nm",
    "rssf_service_specialty_feature_nm",
    "fee_name",
    "grp_amount"
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# aggregated_fees_final_part_2 is needed to get the following fees:
# - Psychiatry Ongoing Visit Fees.
# - Primary Care New Patient Visit Fees.

# CELL ********************

aggregated_fees_final_part_2 = aggregated_fees_part_3.unionByName(aggregated_fees_part_4)

aggregated_fees_final_part_2 = aggregated_fees_final_part_2.withColumn(
    "fee_name",
    F.when(
        F.col("fee_name").isin(
            "Psychiatry Ongoing Visit Fee - Member",
            "Therapy Visit Fee - Member"
        ),
        "Psychiatry Ongoing Visit Fee - Member"
    ).when(
        F.col("fee_name").isin(
            "Psychiatry Ongoing Visit Fee - Client",
            "Therapy Visit Fee - Client"
        ),
        "Psychiatry Ongoing Visit Fee - Client"
    ).when(
        F.col("fee_name").isin(
            "Primary Care New Patient Visit Fee - Member",
            "Primary Care Follow-up Visit Fee - Member",
            "Primary Care Visit Fee - Member"
        ),
        "Primary Care New Patient Visit Fee - Member"
    ).when(
        F.col("fee_name").isin(
            "Primary Care New Patient Visit Fee - Client",
            "Primary Care Follow-up Visit Fee - Client",
            "Primary Care Fee - Client"
        ),
        "Primary Care New Patient Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_final_part_2 = (
    aggregated_fees_final_part_2
    .groupBy(
        "g_group_id", 
        "fee_name"
    )
    .agg(
        F.sum("grp_amount").alias("grp_amount"),
        F.first("g_legacy_group_id").alias("g_legacy_group_id"),
        F.first("rss_service_specialty_nm").alias("rss_service_specialty_nm"), 
        F.first("rssf_service_specialty_feature_nm").alias("rssf_service_specialty_feature_nm")
    )
    .filter(F.col("fee_name").isNotNull())
)
# End of Query 3.

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# aggregated_fees_part_5 is needed to get the following fees:
# - Therapy Visit Fees.
# - Mental Health Membership Fee.
# - Psychiatry Ongoing Visit Fee.
# - Primary Care Follow-up Visit Fee.
# - Primary Care Membership Fee.
# - Primary Care Visit Fee.

# CELL ********************

# Start of Query 5-
# Start of Subquery 1.
aggregated_fees_part_5 = product_fees_raw_1.withColumn(
    "fee_name",
    F.when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_DM"),
        "Diabetes Care Follow-Up Visit Fee - Client"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_DM"),
        "Diabetes Care Follow-Up Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Client"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_DM"),
        "Diabetes Care Follow-Up Visit Fee - Clientt"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_DM"),
        "Diabetes Care Follow-Up Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_BILLING") &
        (F.col("grp_invoice_submethod_cd") == "INVOICESUBMETHOD_BILLEDAMOUNT") &
        (F.col("gssfr_service_specialty_feature_cd") == "DM_BASE"),
        "Diabetes Care Membership Fee"
    ).otherwise(None)
)

aggregated_fees_part_5 = aggregated_fees_part_5.select(
    "g_group_id",
    "g_legacy_group_id",
    "rss_service_specialty_nm",
    "rssf_service_specialty_feature_nm",
    "fee_name",
    "grp_amount"
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# aggregated_fees_part_6 is needed to get the following fees:
# - Psychiatry Initial Visit Fee.
# - Primary Care Annual Checkup Visit Fee.
# - Primary Care New Patient Visit Fee.

# CELL ********************

aggregated_fees_part_6 = product_fees_raw_2.withColumn(
    "fee_name",
    F.when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("rf_feature_cd") == "DM") &
        (F.col("ossfr_service_specialty_feature_cd") == "VPC_DM") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_PREMIUM"),
        "Diabetes Care New Patient Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("rf_feature_cd") == "DM") &
        (F.col("ossfr_service_specialty_feature_cd") == "VPC_DM") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_PREMIUM"),
        "Diabetes Care New Patient Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_part_6 = aggregated_fees_part_6.filter(
    (F.col("grp_pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
    (F.col("grp_relation_type") == "GroupOffer") &
    (F.col("ossfr_service_specialty_feature_cd") == F.col("gssfr_service_specialty_feature_cd"))
)

aggregated_fees_part_6 = aggregated_fees_part_6.select(
    "g_group_id",
    "g_legacy_group_id",
    "rss_service_specialty_nm",
    "rssf_service_specialty_feature_nm",
    "fee_name",
    "grp_amount"
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# aggregated_fees_final_part_3 is needed to get the following fees:
# - Diabetes Care New Patient Visit Fees.

# CELL ********************

aggregated_fees_final_part_3 = aggregated_fees_part_5.unionByName(aggregated_fees_part_6)

aggregated_fees_final_part_3 = aggregated_fees_final_part_3.withColumn(
    "fee_name",
    F.when(
        F.col("fee_name").isin(
            "Diabetes Care Follow-Up Visit Fee - Member",
            "Diabetes Care New Patient Visit Fee - Member",
            "Primary Care Follow-up Visit Fee - Member",
            "Diabetes Care Visit Fee - Member"
        ),
        "Diabetes Care New Patient Visit Fee - Member"
    ).when(
        F.col("fee_name").isin(
            "Diabetes Care Follow-Up Visit Fee - Client",
            "Diabetes Care New Patient Visit Fee - Client",
            "Primary Care Follow-up Visit Fee - Client",
            "Diabetes Care Visit Fee - Client"
        ),
        "Diabetes Care New Patient Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_final_part_3 = (
    aggregated_fees_final_part_3
    .groupBy(
        "g_group_id", 
        "fee_name"
    )
    .agg(
        F.sum("grp_amount").alias("grp_amount"),
        F.first("g_legacy_group_id").alias("g_legacy_group_id"),
        F.first("rss_service_specialty_nm").alias("rss_service_specialty_nm"), 
        F.first("rssf_service_specialty_feature_nm").alias("rssf_service_specialty_feature_nm")
    )
    .filter(F.col("fee_name").isNotNull())
)
# End of Subquery 1.

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# aggregated_fees_part_7 is needed to get the following fees:
# - Primary Care Follow-up Visit Fee.

# CELL ********************

# Start of Subquery 2.
aggregated_fees_part_7 = product_fees_raw_1.withColumn(
    "fee_name",
    F.when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("rssf_service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Client"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("rss_service_specialty_cd") == "VPC") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("rf_feature_cd") == "MD") &
        (F.col("rssf_service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_DM"),
        "Diabetes Care Follow-Up Visit Fee - Client"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (F.col("gssfr_service_specialty_feature_cd") == "VPC_DM"),
        "Diabetes Care Follow-Up Visit Fee - Member"
    ).when(
        (F.col("grp_invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (F.col("grp_pricing_type_cd") == "PRICINGTYPE_BILLING") &
        (F.col("grp_invoice_submethod_cd") == "INVOICESUBMETHOD_BILLEDAMOUNT") &
        (F.col("gssfr_service_specialty_feature_cd") == "DM_BASE"),
        "Diabetes Care Membership Fee"
    ).otherwise(None)
)

aggregated_fees_part_7 = aggregated_fees_part_7.select(
    "g_group_id",
    "g_legacy_group_id",
    "rss_service_specialty_nm",
    "rssf_service_specialty_feature_nm",
    "fee_name",
    "grp_amount"
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

aggregated_fees_final_part_4 = aggregated_fees_part_7.withColumn(
    "fee_name",
    F.when(
        F.col("fee_name").isin(
            "Diabetes Care Follow-up Visit Fee - Member",
            "Primary Care Follow-up Visit Fee - Member",
            "Diabetes Care Visit Fee - Member"
        ),
        "Diabetes Care Follow-up Visit Fee - Member"
    ).when(
        F.col("fee_name").isin(
            "Diabetes Care Follow-up Visit Fee - Client",
            "Primary Care Follow-up Visit Fee - Client",
            "Diabetes Care Visit Fee - Client"
        ),
        "Diabetes Care Follow-up Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_final_part_4 = (
    aggregated_fees_final_part_4
    .groupBy(
        "g_group_id", 
        "fee_name"
    )
    .agg(
        F.sum("grp_amount").alias("grp_amount"),
        F.first("g_legacy_group_id").alias("g_legacy_group_id"),
        F.first("rss_service_specialty_nm").alias("rss_service_specialty_nm"), 
        F.first("rssf_service_specialty_feature_nm").alias("rssf_service_specialty_feature_nm")
    )
    .filter(F.col("fee_name").isNotNull())
)
# End of Subquery 2.
# End of Query 5.

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Final union.

# CELL ********************

aggregated_fees_final = aggregated_fees_final_part_1.unionByName(aggregated_fees_final_part_2).unionByName(aggregated_fees_final_part_3).unionByName(aggregated_fees_final_part_4)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

aggregated_fees_final = aggregated_fees_final.unionByName(no_aggregation_fees)
aggregated_fees_final = aggregated_fees_final.filter(F.col("fee_name").isNotNull())

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# By doing the following join, I'm only bringing from the aggregated_fees_final dataset those fees that are valid.

# CELL ********************

group_product_relations_alias = group_product_relations.alias("gpr")
aggregated_fees_final_alias = aggregated_fees_final.alias("agg")

fees = group_product_relations_alias.join(
    aggregated_fees_final_alias, 
    (F.col("gpr.g_group_id") == F.col("agg.g_group_id")) & 
    (F.col("gpr.rssf_service_specialty_feature_nm") == F.col("agg.rssf_service_specialty_feature_nm")), 
    "inner"
)

fees = fees.filter(F.col("gpr.g_group_id") == '10072')

fees = fees.select(
    F.col("gpr.g_group_id").alias("group_id"),
    F.col("gpr.g_legacy_group_id").alias("legacy_group_id"),
    F.col("gpr.rss_service_specialty_nm").alias("service_specialty_name"),
    F.col("gpr.rssf_service_specialty_feature_nm").alias("service_specialty_feature_name"),
    F.col("fee_name"),
    F.col("grp_amount")
)

display(fees)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Save to lakehouse with new schema.

# CELL ********************

fees.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_group_product_fees")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }
