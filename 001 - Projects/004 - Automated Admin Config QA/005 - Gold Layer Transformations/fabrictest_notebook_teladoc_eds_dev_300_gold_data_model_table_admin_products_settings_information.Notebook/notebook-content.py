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

# # Product Settings - Not Product Fees


# MARKDOWN ********************

# ### Import required resources.

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, collect_list, concat, contains, expr, first, lit, max, regexp_extract, sum, when
from pyspark.sql.types import BooleanType, DateType, DoubleType, IntegerType, StringType, TimestampType
from pyspark.sql.window import Window

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Initialize SparkSession.

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

# # Load required tables.

# MARKDOWN ********************

# ### Groups table.

# CELL ********************

groups_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_groups")

groups_df = groups_df.select("group_id", "legacy_group_id")

### Print row count

row_count = groups_df.count()

print(f"Total rows in Groups table: {row_count}")

### Print unique group_id

unique_count = groups_df.select("group_id").distinct().count()

print(f"Unique values in group_id column in Groups table: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Product-related tables.

# CELL ********************

# Group Service Specialty Relations

group_service_specialty_relations_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_service_specialty_relations")

group_service_specialty_relations_df = group_service_specialty_relations_df.drop("primary_contract", "claim_billing_method_cd", "payer_fee_schedule_relation_id", "condition")

# Group Service Specialty Relation Details (TABLE USED FOR OPPS UUID AND THEIR DATES)

group_service_specialty_relation_details_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_service_specialty_relation_details")

# Group Payer Service Specialty Relations (TABLE TO GET PRODUCT PAYER)

group_payer_service_specialty_relations_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_payer_service_specialty_relations")

# Payers

payers_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_payers")

payers_df = payers_df.select("payer_id", "payer_nm", "payer_cd")

# Group Service Specialty Feature Relations (TABLE TO GET PRODUCT DATES AND COMMUNICATION METHODS)

group_service_specialty_feature_relations_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_service_specialty_feature_relations")

# Group Service Specialty Feature Settings (TABLE USED FOR PRODUCT SETTINGS LIKE PRINT OR LESS, FAMILY EXTENDED BENEFITS, ETC.)

group_service_specialty_feature_settings_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_service_specialty_feature_settings")

# Ref Service Specialties

ref_service_specialties_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_ref_service_specialties")

ref_service_specialties_df = ref_service_specialties_df.select("service_specialty_cd", "service_specialty_nm", "service_specialty_uft", "service_offering_cd", "servicing_platform_cd")

# Ref Service Specialty Features

ref_service_specialty_features_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_ref_service_specialty_features")

ref_service_specialty_features_df = ref_service_specialty_features_df.select("service_specialty_feature_cd", "service_specialty_feature_nm", "service_specialty_cd", "feature_cd")

# Ref Features

ref_features_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_ref_features")

ref_features_df = ref_features_df.select("feature_cd", "feature_nm", "feature_family_cd")

# Ref Geographic Regions

ref_geographic_regions_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_ref_geographic_regions")

ref_geographic_regions_df = ref_geographic_regions_df.drop("ref_geographic_region_id")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }

# MARKDOWN ********************

# # Create a complete Service Specialty and Service Specialty Feature References table.

# CELL ********************

final_ref_df = ref_service_specialty_features_df.join(ref_features_df, "feature_cd", "left")

final_ref_df = final_ref_df.join(ref_service_specialties_df, "service_specialty_cd", "left")

final_ref_df = final_ref_df.select("service_specialty_feature_cd", "service_specialty_feature_nm", "service_specialty_cd", "service_specialty_nm",
                                    "service_specialty_uft", "service_offering_cd", "servicing_platform_cd", "feature_cd", "feature_nm", "feature_family_cd")

display(final_ref_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Create Product Payers table.

# CELL ********************

product_payers_df = group_payer_service_specialty_relations_df.join(payers_df, "payer_id", "inner")

product_payers_df = product_payers_df.withColumn("product_payer", concat(col("payer_nm"), lit(" ("), col("payer_cd"), lit(")")))

product_payers_df = product_payers_df.select("group_payer_service_specialty_relation_id", "group_service_specialty_relation_id", "payer_id", "payer_nm",
                                            "payer_cd", "product_payer", "default_payer", "claim_payer_id")

display(product_payers_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Create Product Communication Methods DF

# CELL ********************

product_communication_methods_df = group_service_specialty_relations_df.join(group_service_specialty_feature_relations_df, "group_service_specialty_relation_id", "inner")

product_communication_methods_df = product_communication_methods_df.select("group_id", "service_specialty_cd", "service_specialty_feature_cd")

product_communication_methods_df = product_communication_methods_df.filter((col("service_specialty_feature_cd").contains("PHONE")) | (col("service_specialty_feature_cd").contains("VIDEO")) | (col("service_specialty_feature_cd").contains("MESSAGING")))

product_communication_methods_df = product_communication_methods_df.orderBy("group_id", "service_specialty_feature_cd")

display(product_communication_methods_df)

# Add Boolean Columns
product_communication_methods_df = product_communication_methods_df.withColumn("phone_communication_method", when(col("service_specialty_feature_cd").endswith("_PHONE"), True).otherwise(False)) \
                                                                    .withColumn("video_communication_method", when(col("service_specialty_feature_cd").endswith("_VIDEO"), True).otherwise(False)) \
                                                                    .withColumn("message_center_communication_method", when(col("service_specialty_feature_cd").endswith("_MESSAGING"), True).otherwise(False))

# Aggregate by group_id and service_specialty_cd
product_communication_methods_df_pivoted = product_communication_methods_df.groupBy("group_id", "service_specialty_cd").agg(
    max("phone_communication_method").alias("phone_communication_method"),
    max("video_communication_method").alias("video_communication_method"),
    max("message_center_communication_method").alias("message_center_communication_method")
)

product_communication_methods_df_pivoted = product_communication_methods_df_pivoted.withColumnsRenamed({"group_id": "comm_group_id", "service_specialty_cd": "comm_service_specialty_cd"})

product_communication_methods_df_pivoted = product_communication_methods_df_pivoted.orderBy("comm_group_id", "comm_service_specialty_cd")

display(product_communication_methods_df_pivoted)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Create products_and_features table.
# - Starting from group_service_specialty_relations and joining it with group_service_specialty_feature_relations.
# - Then join with the final_ref_df.

# CELL ********************

products_and_features_df = group_service_specialty_relations_df.join(group_service_specialty_relation_details_df, "group_service_specialty_relation_id", "inner")

products_and_features_df = products_and_features_df.join(ref_geographic_regions_df, col("geographic_region_coverage_cd") == col("geographic_region_cd"), "inner")

products_and_features_df = products_and_features_df.drop("geographic_region_coverage_cd", "geographic_region_cd", "group_service_specialty_relation_detail_id")

products_and_features_df = products_and_features_df.withColumnsRenamed({"effective_start_dt": "opportunity_effective_start_dt", "effective_end_dt": "opportunity_effective_end_dt"})

products_and_features_df = products_and_features_df.select("group_service_specialty_relation_id", "group_id", "service_specialty_cd", "billing_fee_type_cd", "geographic_region_nm",
                                                            "min_age", "max_age", "bundle_type_cd", "override_billing_id", "tpn_rule_id", "opportunity_uuid", "contract_num",
                                                            "opportunity_effective_start_dt", "opportunity_effective_end_dt")

products_and_features_df = products_and_features_df.join(group_service_specialty_feature_relations_df, "group_service_specialty_relation_id", "inner")

products_and_features_df = products_and_features_df.join(group_service_specialty_feature_settings_df, "group_service_specialty_feature_relation_id", "inner")

products_and_features_df = products_and_features_df.drop("group_service_specialty_feature_setting_id")

products_and_features_df = products_and_features_df.withColumnsRenamed({"effective_start_dt": "product_effective_start_dt", "effective_end_dt": "product_effective_end_dt"})

products_and_features_df = products_and_features_df.join(product_payers_df, "group_service_specialty_relation_id", "left")

products_and_features_df = products_and_features_df.drop("group_payer_service_specialty_relation_id")

products_and_features_df = products_and_features_df.join(final_ref_df.alias("ref"), "service_specialty_feature_cd", "left")

products_and_features_df = products_and_features_df.join(product_communication_methods_df_pivoted,
                                                        (col("group_id") == col("comm_group_id")) & (col("ref.service_specialty_cd") == col("comm_service_specialty_cd")),
                                                        "left")

products_and_features_df = products_and_features_df.drop("comm_group_id", "comm_service_specialty_cd") 

products_and_features_df = products_and_features_df.select("group_id", "group_service_specialty_relation_id", "ref.service_specialty_cd", "service_specialty_nm",
                                                            "group_service_specialty_feature_relation_id", "ref.service_specialty_feature_cd", "service_specialty_feature_nm",
                                                            "print_or_less", "product_payer", "payer_id", "payer_nm", "payer_cd", "default_payer", "claim_payer_id",
                                                            "billing_fee_type_cd", "product_effective_start_dt", "product_effective_end_dt", "geographic_region_nm", "min_age",
                                                            "max_age", "extended_family_benefit_cd", "bundle_type_cd", "phone_communication_method", "video_communication_method",
                                                            "message_center_communication_method", "on_demand_consult", "scheduled_consult", "allow_consult_guest",
                                                            "provider_selection_cd", "allow_preselected_provider", "allow_first_available_provider", "allow_searchable_provider",
                                                            "override_billing_id", "tpn_rule_id", "opportunity_uuid", "contract_num", "opportunity_effective_start_dt", "opportunity_effective_end_dt")

products_and_features_df = products_and_features_df.orderBy("group_id", "service_specialty_feature_cd")

display(products_and_features_df)

display(products_and_features_df.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Check Group count.

# CELL ********************

### Print row count

row_count = products_and_features_df.count()

print(f"Total rows in final Products table: {row_count}")

### Print unique group_id

unique_count = products_and_features_df.select("group_id").distinct().count()

print(f"Unique values in group_id column in final Products Settings table: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Save to Lakehouse with new Schema.

# CELL ********************

products_and_features_df.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_admin_products_settings_information")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
