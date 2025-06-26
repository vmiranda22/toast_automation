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

# # Gold Data Model Table - Admin Organization Information

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

# # Organizations (RELATION WITH GOLD GROUPS MUST BE ORG ID = PARENT ID)

# CELL ********************

organizations_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organizations")

organizations_df = organizations_df.select("organization_id", "organization_nm", "party_id", "ancestry", "created_at", "updated_at")

display(organizations_df)

# Print row count

row_count = organizations_df.count()

print(f"Total Rows: {row_count}")

# Print unique group_id

unique_count = organizations_df.select("organization_id").distinct().count()

print(f"Unique values in organization_id: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Organization Extensions to Organizations

# CELL ********************

# Load tables

organization_extensions_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organization_extensions")

organization_extensions_df = organization_extensions_df.select("organization_id", "employer", "print_url", "print_phone", "additional_url")

# Add web_url column
organization_extensions_df = organization_extensions_df.withColumn("web_url", lower(concat(lit("www."), col("print_url"))))

# Join groups with organizations (INNER)

organization_extensions_to_organizations_df = organizations_df.join(organization_extensions_df, "organization_id", "left")

final_df = organization_extensions_to_organizations_df

display(final_df)

# Print row count

row_count = final_df.count()

print(f"Total Rows: {row_count}")

# Print unique group_id

unique_count = final_df.select("organization_id").distinct().count()

print(f"Unique values in organization_id: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Organization Marketing Communications to Organizations

# CELL ********************

# Load tables

organization_marketing_communications_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_organization_marketing_communications")

organization_marketing_communications_df = organization_marketing_communications_df.select("organization_id", "direct_mail", "email", "incentive", "outbound_calls", "sms_text")

# Join groups with organizations (left)

organization_marketing_communications_to_organizations_df = organizations_df.join(organization_marketing_communications_df, "organization_id", "left")

display(organization_marketing_communications_to_organizations_df)

final_df = final_df.join(organization_marketing_communications_df, "organization_id", "left")

display(final_df)

# Print row count

row_count = final_df.count()

print(f"Total Rows: {row_count}")

# Print unique group_id

unique_count = final_df.select("organization_id").distinct().count()

print(f"Unique values in organization_id: {unique_count}")

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

# ## Party Addresses to Organizations

# CELL ********************

# Load tables

party_addresses_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_party_addresses")

party_addresses_df = party_addresses_df.drop("party_address_id", "preferred", "alert", "batch_id", "temporary")

party_addresses_to_organizations_df = organizations_df.join(party_addresses_df, "party_id", "left")

display(party_addresses_to_organizations_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Load tables

party_addresses_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_party_addresses")

party_addresses_df = party_addresses_df.select("payer_id", "group_id")

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
    concat_ws(", ", collect_list("cc_payers")).alias("cc_payers_combined")
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

# ## Save Admin Organization Information Gold Table

# CELL ********************

# Save back to Lakehouse
final_df.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_admin_organization_information")

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

# CELL ********************

df_ref_report = df_ref_report.join(df_affiliation_rel, "report_cd", "left").join(df_ref_service_spec, "service_specialty_cd", "left")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
