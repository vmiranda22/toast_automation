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

# ### Product & Services settings, not fees.


# MARKDOWN ********************

# Comments:

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
    .filter(F.col("template") == 0)
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

df_teladoc_eds_dev_group_service_specialty_relation_details = (
    spark.read.format("delta")
    .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_service_specialty_relation_details")
)

df_teladoc_eds_dev_group_payer_service_specialty_relations = (
    spark.read.format("delta")
    .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_payer_service_specialty_relations")
)

df_teladoc_eds_dev_payers = (
    spark.read.format("delta")
    .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_payers")
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
        "group_service_specialty_feature_relation_id",
        "print_or_less",
        "allow_preselected_provider"
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

df_teladoc_eds_dev_group_service_specialty_relation_details = (
    df_teladoc_eds_dev_group_service_specialty_relation_details.select(
        "group_service_specialty_relation_id",
        "effective_start_dt",
        "effective_end_dt"
    )
)

df_teladoc_eds_dev_group_payer_service_specialty_relations = (
    df_teladoc_eds_dev_group_payer_service_specialty_relations.select(
        "group_service_specialty_relation_id",
        "payer_id"
    )
)

df_teladoc_eds_dev_payers = (
    df_teladoc_eds_dev_payers.select(
        "payer_id",
        "payer_nm"  
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
df_teladoc_eds_dev_group_service_specialty_relation_details = add_prefix(df_teladoc_eds_dev_group_service_specialty_relation_details, "gssrd_")
df_teladoc_eds_dev_group_payer_service_specialty_relations = add_prefix(df_teladoc_eds_dev_group_payer_service_specialty_relations, "gpssr_")
df_teladoc_eds_dev_payers = add_prefix(df_teladoc_eds_dev_payers, "p_")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Joins required to get the group_product_relations dataset.

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
    df_teladoc_eds_dev_group_service_specialty_relation_details,
    group_product_relations["gssr_group_service_specialty_relation_id"] == df_teladoc_eds_dev_group_service_specialty_relation_details["gssrd_group_service_specialty_relation_id"],
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

group_product_relations = group_product_relations.join(
    df_teladoc_eds_dev_group_payer_service_specialty_relations,
    group_product_relations["gssr_group_service_specialty_relation_id"] == df_teladoc_eds_dev_group_payer_service_specialty_relations["gpssr_group_service_specialty_relation_id"],
    how="inner"
)

group_product_relations = group_product_relations.join(
    df_teladoc_eds_dev_payers,
    group_product_relations["gpssr_payer_id"] == df_teladoc_eds_dev_payers["p_payer_id"],
    how="inner"
)

group_product_relations = group_product_relations.join(
    df_teladoc_eds_dev_group_service_specialty_feature_settings,
    group_product_relations["gssfr_group_service_specialty_feature_relation_id"] == df_teladoc_eds_dev_group_service_specialty_feature_settings["gssfs_group_service_specialty_feature_relation_id"],
    how="left"
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

group_product_relations = group_product_relations.select(
    F.col("g_group_id").alias("group_id"),
    F.col("g_legacy_group_id").alias("legacy_group_id"),
    F.col("rss_service_specialty_nm").alias("service_specialty_name"),
    F.col("rssf_service_specialty_feature_nm").alias("service_specialty_feature_name"),
    F.col("gssfs_print_or_less").alias("print_or_less"),
    F.col("gssfs_allow_preselected_provider").alias("teladoc_select"),
    F.col("gssfr_live_dt").alias("revenue_effective_date"),
    F.col("gssfr_termination_dt").alias("term_date"),
    F.col("p_payer_nm").alias("payer_name"),
    F.col("gssr_min_age").alias("min_age"),
    F.col("gssr_max_age").alias("max_age")
)

print(group_product_relations.rows)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Save to lakehouse with new schema.

# CELL ********************

group_product_relations.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_group_product_settings")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }
