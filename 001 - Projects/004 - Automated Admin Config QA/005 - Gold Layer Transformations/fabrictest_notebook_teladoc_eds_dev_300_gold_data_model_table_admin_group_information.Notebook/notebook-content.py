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
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977"
# META     }
# META   }
# META }

# MARKDOWN ********************

# # Gold Data Model Table - Admin Group Information

# MARKDOWN ********************

# ##### Import required resources.

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, collect_list, concat, concat_ws, current_date, expr, first, lit, lower, posexplode, row_number, split, when
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

# # Groups

# CELL ********************

groups_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_groups")

### display(groups_df)

# Print row count

row_count = groups_df.count()

print(f"Total Rows: {row_count}")

# Print unique group_id

unique_count = groups_df.select("group_id").distinct().count()

print(f"Unique values in group_id: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Organizations to Groups

# CELL ********************

# Load tables

organizations_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organizations")

organizations_df = organizations_df.select("group_id", "ancestry", "parent_id", "cc_parent_nm", "cc_master_organization_id", "cc_master_organization_nm")

organizations_df = organizations_df.withColumnsRenamed({"cc_parent_nm": "parent_nm", "cc_master_organization_id": "master_organization_id", "cc_master_organization_nm": "master_organization_nm"})

# Join groups with organizations (INNER)

organizations_to_groups_df = groups_df.join(organizations_df, "group_id", "inner")

final_df = organizations_to_groups_df

### display(final_df)

# Print row count

row_count = final_df.count()

print(f"Total Rows: {row_count}")

# Print unique group_id

unique_count = final_df.select("group_id").distinct().count()

print(f"Unique values in group_id: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Billing to Groups

# CELL ********************

# Load tables

group_billing_relations_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_billing_relations")

group_billing_relations_df = group_billing_relations_df.select("billing_id", "group_id")

billings_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_billings")

billings_df = billings_df.select("billing_id", "organization_id")

billing_organizations_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organizations")

billing_organizations_df = billing_organizations_df.select("organization_id", "organization_nm")

# Join tables

billing_to_groups_df = group_billing_relations_df.join(billings_df, "billing_id", "inner")

billing_to_groups_df = billing_to_groups_df.join(billing_organizations_df, "organization_id", "inner")

billing_to_groups_df = billing_to_groups_df.withColumn("cc_bill_to", concat("organization_nm", lit(" ("), "organization_id", lit(")")))

billing_to_groups_df = billing_to_groups_df.withColumnsRenamed({"organization_id": "billing_organization_id", "organization_nm": "billing_organization_nm", "cc_bill_to": "bill_to"})

billing_to_groups_df = billing_to_groups_df.select("group_id", "billing_organization_id", "billing_organization_nm", "bill_to")

### display(billing_to_groups_df)

# Join with groups (LEFT)

final_df = final_df.join(billing_to_groups_df, "group_id", "left")

### display(final_df)

# Print row count

row_count = final_df.count()

print(f"Total Rows: {row_count}")

# Print unique group_id

unique_count = final_df.select("group_id").distinct().count()

print(f"Unique values in group_id: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# #### Check duplicate rows

# CELL ********************

# Group by the column and count occurrences
duplicates_df = final_df.groupBy("group_id").count().filter(col("count") > 1)

# Show the duplicates
display(duplicates_df)

# Display duplicates information
duplicates_full_df = final_df.join(duplicates_df, "group_id", "inner")

display(duplicates_full_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# #### Drop duplicate rows

# CELL ********************

final_df = final_df.dropDuplicates()

# Print row count

row_count = final_df.count()

print(f"Total Rows: {row_count}")

# Print unique group_id

unique_count = final_df.select("group_id").distinct().count()

print(f"Unique values in group_id: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Payers to Groups

# CELL ********************

# Load tables

group_payer_relations_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_payer_relations")

group_payer_relations_df = group_payer_relations_df.select("payer_id", "group_id")

payers_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_payers")

payers_df = payers_df.select("payer_id", "payer_cd", "payer_nm")

# Join tables

payers_to_groups_df = group_payer_relations_df.join(payers_df, "payer_id", "inner")

payers_to_groups_df = payers_to_groups_df.withColumn("cc_payers", concat(col("payer_nm"), lit(" ("), col("payer_cd"), lit(")")))

payers_to_groups_df = payers_to_groups_df.select("group_id", "payer_id", "payer_cd", "payer_nm", "cc_payers")

# display(payers_to_groups_df)

# Group by `group_id` and aggregate `cc_payers`
grouped_payers_to_groups_df = payers_to_groups_df.groupBy("group_id").agg(
    concat_ws(", ", collect_list("payer_id")).alias("payer_id_combined"),
    concat_ws(", ", collect_list("payer_cd")).alias("payer_cd_combined"),
    concat_ws(", ", collect_list("payer_nm")).alias("payer_nm_combined"),
    concat_ws(", ", collect_list("cc_payers")).alias("payers_combined")
)

# display(grouped_payers_to_groups_df)

# Join with groups (LEFT)

final_df = final_df.join(grouped_payers_to_groups_df, "group_id", "left")

# display(final_df)

# Print row count

row_count = final_df.count()

print(f"Total Rows: {row_count}")

# Print unique group_id

unique_count = final_df.select("group_id").distinct().count()

print(f"Unique values in group_id: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Countries to Group Settings

# CELL ********************

# Load tables

ref_countries_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_ref_countries")

ref_countries_df = ref_countries_df.select("country_cd", "country_nm")

group_settings_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_settings")

group_settings_df = group_settings_df.drop("group_setting_id")

# Join tables

countries_to_group_settings_df = group_settings_df.join(ref_countries_df, col("domestic_country") == col("country_cd"), "inner")

countries_to_group_settings_df = countries_to_group_settings_df.drop("domestic_country", "country_cd")

# display(countries_to_group_settings_df)

# Join with groups (INNER)

final_df = final_df.join(countries_to_group_settings_df, "group_id", "left")

# display(final_df)

# Print row count

row_count = final_df.count()

print(f"Total Rows: {row_count}")

# Print unique group_id

unique_count = final_df.select("group_id").distinct().count()

print(f"Unique values in group_id: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Valid Group Sources to Groups

# CELL ********************

# Load tables

valid_group_sources_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_valid_group_sources")

valid_group_sources_df = valid_group_sources_df.drop("valid_group_source_id")

# Join with groups (INNER)

final_df = final_df.join(valid_group_sources_df, "group_id", "left")

# display(final_df)

# Print row count

row_count = final_df.count()

print(f"Total Rows: {row_count}")

# Print unique group_id

unique_count = final_df.select("group_id").distinct().count()

print(f"Unique values in group_id: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Empi Namespace Relations to Groups

# CELL ********************

# Load tables

group_empi_namespace_relations_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_empi_namespace_relations")

group_empi_namespace_relations_df = group_empi_namespace_relations_df.select("group_id", "empi_namespace_cd", "benefit_restriction_cd")

# Join with groups (LEFT)

final_df = final_df.join(group_empi_namespace_relations_df, "group_id", "left")

# display(final_df)

# Print row count

row_count = final_df.count()

print(f"Total Rows: {row_count}")

# Print unique group_id

unique_count = final_df.select("group_id").distinct().count()

print(f"Unique values in group_id: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Service Level Relations to Groups

# CELL ********************

# Load tables

group_service_level_relations_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_service_level_relations")

group_service_level_relations_df = group_service_level_relations_df.select("group_id", "standard_service_level_id", "vip_service_level_id")

ref_service_levels_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_ref_service_levels")

ref_service_levels_df = ref_service_levels_df.select("ref_service_level_id", "cc_service_level_concat")

# Join tables

# Get Standard Service Level

service_level_relations_to_groups_df = group_service_level_relations_df.join(ref_service_levels_df, col("standard_service_level_id") == col("ref_service_level_id"), "inner")

service_level_relations_to_groups_df = service_level_relations_to_groups_df.withColumnRenamed("cc_service_level_concat", "standard_service_level")

service_level_relations_to_groups_df = service_level_relations_to_groups_df.select("group_id", "standard_service_level", "vip_service_level_id")

# Get VIP Service Level

service_level_relations_to_groups_df = service_level_relations_to_groups_df.join(ref_service_levels_df, col("vip_service_level_id") == col("ref_service_level_id"), "inner")

service_level_relations_to_groups_df = service_level_relations_to_groups_df.withColumnRenamed("cc_service_level_concat", "vip_service_level")

service_level_relations_to_groups_df = service_level_relations_to_groups_df.select("group_id", "standard_service_level", "vip_service_level")

# display(service_level_relations_to_groups_df)

# Join with groups (LEFT)

final_df = final_df.join(service_level_relations_to_groups_df, "group_id", "left")

# display(final_df)

# Print row count

row_count = final_df.count()

print(f"Total Rows: {row_count}")

# Print unique group_id

unique_count = final_df.select("group_id").distinct().count()

print(f"Unique values in group_id: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Alt Group IDs to Groups

# CELL ********************

# Load tables

alt_group_ids_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_alt_group_ids")

# Join with groups (LEFT)

final_df = final_df.join(alt_group_ids_df, "group_id", "left")

# display(final_df)

# Print row count

row_count = final_df.count()

print(f"Total Rows: {row_count}")

# Print unique group_id

unique_count = final_df.select("group_id").distinct().count()

print(f"Unique values in group_id: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Save Admin Group Information Gold Table

# CELL ********************

# Save back to Lakehouse
final_df.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_admin_group_information")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Parties

# MARKDOWN ********************

# ## Party

# CELL ********************

df_parties = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_parties")

df_parties = df_parties.drop("created_at", "created_by", "updated_at", "updated_by", "exclusion_cd", "data_source_cd")

df_parties.dropDuplicates()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Sales Reps

# CELL ********************

df_sales_reps = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_sales_reps")

df_sales_reps = df_sales_reps.drop("created_at", "created_by", "updated_at", "updated_by", "exclusion_cd", "data_source_cd")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Persons

# CELL ********************

df_persons = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_persons")

df_persons = df_persons.filter(col("exclusion_cd") == "IN")

df_persons = df_persons.drop("created_at", "created_by", "updated_at", "updated_by", "exclusion_cd", "data_source_cd")

df_persons = df_persons.filter(col("party_id") != 88999990)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_persons.dropDuplicates()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Report emails

# CELL ********************

df_party_emails = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_party_email_addresses")

df_party_emails = df_party_emails.filter(col("exclusion_cd") == "IN")

df_party_emails = df_party_emails.drop("temporary", "created_at", "created_by", "updated_at", "updated_by", "exclusion_cd", "data_source_cd")

df_party_emails = df_party_emails.filter(col("party_id") != 88999990)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_party_emails.dropDuplicates()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Report emails relations

# CELL ********************

df_report_emails = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_report_email_relations")

df_report_emails = df_report_emails.filter(col("exclusion_cd") == "IN")

df_report_emails = df_report_emails.drop("report_email_relation_id", "created_at", "created_by", "updated_at", "updated_by", "exclusion_cd", "data_source_cd")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_report_emails.dropDuplicates()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Final Join

# CELL ********************

df_party_final = (
    #df_payers
    df_parties  
    .join(df_persons.drop("data_source_cd"), "party_id", "left")  
    .join(df_sales_reps.drop("data_source_cd"), "person_id", "left")  
    .join(df_party_emails.drop("data_source_cd"), "party_id", "left")  
    .join(df_report_emails.drop("data_source_cd"), "party_email_address_id", "left")  
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_party_final.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_parties")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Organizations

# CELL ********************

df_org = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_organizations")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_org_user_relations = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_organization_user_relations")

df_org_user_relations = df_org_user_relations.filter(col("exclusion_cd") == "IN")

df_org_user_relations = df_org_user_relations.drop("created_at", "created_by", "updated_at", "updated_by", "exclusion_cd")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_org_mark_comm = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_organization_marketing_communications")

df_org_mark_comm = df_org_mark_comm.drop("created_at", "created_by", "updated_at", "updated_by")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_org_extensions = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_organization_extensions")

df_org_extensions = df_org_extensions.filter(col("exclusion_cd") == "IN")

df_org_extensions = df_org_extensions.drop("created_at", "created_by", "updated_at", "updated_by", "exclusion_cd")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_org_final = (
    df_org.select("organization_id")
    .join(df_org_user_relations.drop("data_source_cd"), "organization_id", "left")  
    .join(df_org_mark_comm.drop("data_source_cd"), "organization_id", "left")  
    .join(df_org_extensions.drop("data_source_cd"), "organization_id", "left")  
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_org_final.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_organization_dependencies")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_ref_report = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_ref_reports")

df_affiliation_rel = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_report_affiliation_relations")

df_ref_service_spec = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_ref_service_specialties")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_ref_report = df_ref_report.drop("exclusion_cd")

df_affiliation_rel = df_affiliation_rel.drop("exclusion_cd")

df_ref_service_spec = df_ref_service_spec.drop("exclusion_cd")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
