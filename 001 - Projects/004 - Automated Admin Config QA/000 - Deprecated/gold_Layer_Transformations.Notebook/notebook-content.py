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

# CELL ********************

from pyspark.sql.functions import col

spark.conf.set("spark.sql.parquet.datetimeRebaseModeInRead", "LEGACY")

spark.conf.set("spark.sql.parquet.datetimeRebaseModeInWrite", "LEGACY")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Groups

# MARKDOWN ********************

# ## Billing Relations

# CELL ********************

df_billing = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_billings")

df_billing = df_billing.filter(col("exclusion_cd") == "IN")

df_billing = df_billing.drop("created_at", "created_by", "updated_at", "updated_by", "exclusion_cd",  "data_source_cd")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_billing_relations = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_group_billing_relations")

df_billing_relations = df_billing_relations.filter(col("exclusion_cd") == "IN")

df_billing_relations = df_billing_relations.drop("group_billing_relation_id", "created_at", "created_by", "updated_at", "updated_by", "exclusion_cd", "data_source_cd")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_billing_relations = df_billing_relations.dropDuplicates()

df_billing = df_billing.dropDuplicates()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_billing_relations = df_billing_relations.join(df_billing, on="billing_id", how="left")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_billing_relations.describe()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Payer Relations

# CELL ********************

df_payer = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_payers")

df_payer = df_payer.drop("created_at", "created_by", "updated_at", "updated_by")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_payer_relations = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_group_payer_relations")

df_payer_relations = df_payer_relations.filter(col("exclusion_cd") == "IN")

df_payer_relations = df_payer_relations.drop("group_payer_relation_id", "created_at", "created_by", "updated_at", "updated_by", "exclusion_cd")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_payer_relations = df_payer_relations.dropDuplicates()

df_payer = df_payer.dropDuplicates()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_payer_relations.describe()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Group Relations

# CELL ********************

df_group_relations = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_group_relations")

df_group_relations = df_group_relations.filter(col("exclusion_cd") == "IN")

df_group_relations = df_group_relations.drop("group_relation_id", "created_at", "created_by", "updated_at", "updated_by", "exclusion_cd")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_group_relations = df_group_relations.dropDuplicates()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_group_relations.describe()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Group settings

# CELL ********************

df_ref_countries = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_ref_countries")

df_ref_countries = df_ref_countries.drop("created_at", "created_by", "updated_at", "updated_by", "country_nm")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_group_settings = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_group_settings")

df_group_settings = df_group_settings.filter(col("exclusion_cd") == "IN")

df_group_settings = df_group_settings.drop("group_setting_id", "created_at", "created_by", "updated_at", "updated_by", "exclusion_cd")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_group_settings = df_group_settings.dropDuplicates()

df_ref_countries = df_ref_countries.dropDuplicates()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_group_settings = df_group_settings.withColumn("country_cd", col("domestic_country")).join(df_ref_countries, on="country_cd", how="left").drop("ref_country_id")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Valid Group Sources

# CELL ********************

df_valid_group = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_valid_group_sources")

df_valid_group = df_valid_group.filter(col("exclusion_cd") == "IN")

df_valid_group = df_valid_group.drop("valid_group_source_id", "created_at", "created_by", "updated_at", "updated_by", "exclusion_cd", "data_source_cd")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_valid_group = df_valid_group.dropDuplicates()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_valid_group.describe()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Empi Namespace Relations

# CELL ********************

df_empi_namespace = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_group_empi_namespace_relations ")

df_empi_namespace = df_empi_namespace.filter(col("exclusion_cd") == "IN")

df_empi_namespace = df_empi_namespace.drop("group_empi_namespace_relation_id", "created_at", "created_by", "updated_at", "updated_by", "exclusion_cd")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_empi_namespace = df_empi_namespace.dropDuplicates()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_empi_namespace.describe()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Group Service Level Relations

# CELL ********************

df_ref_service_level = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_ref_service_levels")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_service_level_rel = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_group_service_level_relations")

df_service_level_rel = df_service_level_rel.filter(col("exclusion_cd") == "IN")

df_service_level_rel = df_service_level_rel.drop("group_service_level_relation_id", "created_at", "created_by", "updated_at", "updated_by", "exclusion_cd")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_service_level_rel = df_service_level_rel.dropDuplicates()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_service_level_rel.describe()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Groups Merge

# CELL ********************

df_groups = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_groups")

df_groups = df_groups.filter(col("exclusion_cd") == "IN")

df_groups = df_groups.drop("created_at", "created_by", "updated_at", "updated_by", "exclusion_cd")

df_groups = df_groups.withColumnsRenamed({'effective_end_dt': 'effective_end_dt_grps', 'effective_start_dt' : 'effective_start_dt_grps'})

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_final = df_groups.select("group_id") \
    .join(df_service_level_rel, on="group_id", how="left") \
    .join(df_empi_namespace, on="group_id", how="left") \
    .join(df_valid_group, on="group_id", how="left") \
    .join(df_group_settings, on="group_id", how="left") \
    .join(df_group_relations, on="group_id", how="left") \
    .join(df_billing_relations, on="group_id", how="left")
    #.join(df_payer_relations, on="group_id", how="left") \


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Tables dropped: 
#     - df_service_level_rel, 
#     - . df_empi_namespace, df_valid_group, 
#     - df_group_settings, 
#     - df_group_relations, 
#     - df_billing_relations, 
#     - df_billing, 
#     - df_countries

# CELL ********************

df_final.describe()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_final.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_group_dependenciesyy")

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

# MARKDOWN ********************

# # Group service specialty relations

# CELL ********************

df_specialty_rel = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_group_service_specialty_relations")

df_specialty_rel = df_specialty_rel.dropDuplicates()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_specialty_rel_det = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_group_service_specialty_relation_details")

df_specialty_rel_det = df_specialty_rel_det.dropDuplicates()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_specialty_feat_sett = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_group_service_specialty_feature_settings")

df_specialty_feat_sett = df_specialty_feat_sett.dropDuplicates()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_group_relation_pricing = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_group_relation_pricings")

df_group_relation_pricing = df_group_relation_pricing.dropDuplicates()

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

# CELL ********************

df_specialty_feature = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_ref_service_specialty_features")

df_feature_rel = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_group_service_specialty_feature_relations")

df_features = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_ref_features")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_specialty_feature = df_specialty_feature.drop("exclusion_cd")

df_feature_rel = df_feature_rel.drop("exclusion_cd")

df_features = df_features.drop("exclusion_cd")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_specialty_feature = df_specialty_feature.join(df_features, "feature_cd", "left")

df_specialty_feature = df_specialty_feature.drop("service_specialty_cd", "exclusion_cd")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_feature_rel = df_feature_rel.join(df_specialty_feature, "service_specialty_feature_cd", "left")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_geographic_regions = spark.sql("SELECT * FROM fabrictest_lakehouse.teladoc_eds_dev_200_silver_ref_geographic_regions")

df_geographic_regions = df_geographic_regions.drop("exclusion_cd")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_specialty_rel = df_specialty_rel.withColumnsRenamed({"geographic_region_coverage_cd" : "geographic_region_cd", "group_service_specialty_relation_id" : "group_service_specialty_feature_relation_id"}).join(df_geographic_regions, "geographic_region_cd").join(df_feature_rel, "group_service_specialty_feature_relation_id", "left")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_specialty_rel.describe()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_specialty_rel.dropDuplicates()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Saves

# CELL ********************

df_specialty_rel.write.format("delta").mode("overwrite").option("mergeSchema", "true").save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_specialty_relations")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_ref_report.write.format("delta").mode("overwrite").option("mergeSchema", "true").save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_ref_reports")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
