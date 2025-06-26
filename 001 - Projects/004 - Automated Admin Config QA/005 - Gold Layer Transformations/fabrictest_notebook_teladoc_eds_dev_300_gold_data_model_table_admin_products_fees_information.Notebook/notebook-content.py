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

# # Product Fees - Not Product Settings


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


# CELL ********************

# TABLE USED FOR OPPS UUID AND THEIR DATES
# group_service_specialty_relation_details_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_service_specialty_relation_details")


# TABLE USED FOR PRODUCT SETTINGS LIKE PRINT OR LESS, FAMILY EXTENDED BENEFITS, ETC.
# group_service_specialty_feature_settings_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_service_specialty_feature_settings")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Import required resources.

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, collect_list, concat, contains, expr, first, lit, regexp_extract, sum, when
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

group_service_specialty_relations_df = group_service_specialty_relations_df.select("group_service_specialty_relation_id", "group_id", "service_specialty_cd")

# Group Service Specialty Feature Relations

group_service_specialty_feature_relations_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_service_specialty_feature_relations")

group_service_specialty_feature_relations_df = group_service_specialty_feature_relations_df.select("group_service_specialty_feature_relation_id", "group_service_specialty_relation_id", "service_specialty_feature_cd")

# Group Relation Pricings

group_relation_pricings_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_relation_pricings")

group_relation_pricings_df = group_relation_pricings_df.orderBy("relation_id")

# Group Offers

group_offers_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_group_offers")

group_offers_df = group_offers_df.select("group_offer_id", "group_id", "promotion_cd", "dependent_promotion_cd", "promotion_type_cd")

# Offer Service Specialty Feature Relations

offer_service_specialty_feature_relations_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_offer_service_specialty_feature_relations")

offer_service_specialty_feature_relations_df = offer_service_specialty_feature_relations_df.drop("offer_service_specialty_feature_relation_id")

offer_service_specialty_feature_relations_df = offer_service_specialty_feature_relations_df.withColumnRenamed("service_specialty_feature_cd", "offer_service_specialty_feature_cd")

# Ref Service Specialties

ref_service_specialties_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_ref_service_specialties")

ref_service_specialties_df = ref_service_specialties_df.select("service_specialty_cd", "service_specialty_nm", "service_specialty_uft", "service_offering_cd", "servicing_platform_cd")

# Ref Service Specialty Features

ref_service_specialty_features_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_ref_service_specialty_features")

ref_service_specialty_features_df = ref_service_specialty_features_df.select("service_specialty_feature_cd", "service_specialty_feature_nm", "service_specialty_cd", "feature_cd")

# Ref Features

ref_features_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_ref_features")

ref_features_df = ref_features_df.select("feature_cd", "feature_nm", "feature_family_cd")

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

# # Create lists of Products that do not need Membership Fee or Visit Fees.


# CELL ********************

no_membership_fees_products = [
    "SECONDOPINION",
    "BHPATHOLOGY",
    "GMPATHOLOGY",
    "STDPATHOLOGY",
    "VPCPATHOLOGY"
]

no_visit_fees_products = [
    "ADVANCEWEIGHTMANAGEMENT",
    "ADVNCDIABETESPRVNTNPRGRM",
    "BHPATHOLOGY",
    "CHRONICKIDNEYDISEASE",
    "CMPRHNSVDIABETESPRVNTNCARE",
    "COMPREHENSIVEWEIGHTCARE",
    "DIABETESCKDVARIANT",
    "DIABETESFLEX",
    "DIABETES",
    "GMPATHOLOGY",
    "HEARTFAILURE",
    "HYPERTENSIONCKDVARIANT",
    "HYPERTENSION",
    "MYMENTALHEALTH1",
    "MYMENTALHEALTH2",
    "MYMENTALHEALTHCOMP",
    "MYMENTALHEALTH",
    "MYSTRENGTHPLUS",
    "PREDIABETES",
    "SECONDOPINION",
    "STDPATHOLOGY",
    "VPCPATHOLOGY",
    "WEIGHTMANAGEMENT"
]

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

products_and_features_df = group_service_specialty_relations_df.join(group_service_specialty_feature_relations_df, "group_service_specialty_relation_id", "inner")

products_and_features_df = products_and_features_df.join(final_ref_df.alias("ref"), "service_specialty_feature_cd", "left")

products_and_features_df = products_and_features_df.select("group_id", "group_service_specialty_relation_id", "ref.service_specialty_cd", "service_specialty_nm",
                                                            "group_service_specialty_feature_relation_id", "ref.service_specialty_feature_cd", "service_specialty_feature_nm",
                                                            "feature_cd", "feature_nm", "feature_family_cd")

products_and_features_df = products_and_features_df.filter((col("feature_cd") != "PHONE") & (col("feature_cd") != "VIDEO") & (col("feature_cd") != "MESSAGING"))

products_and_features_df = products_and_features_df.orderBy("group_id", "service_specialty_feature_cd")

# display(products_and_features_df)

display(products_and_features_df.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Create product_fees_raw tables.
# - product_fees_raw_1
# - product_fees_raw_2
# - product_fees_raw_3

# MARKDOWN ********************

# ### product_fees_raw_1

# CELL ********************

# The Join is performed on "group_service_specialty_FEATURE_relation_id" 

product_fees_raw_1 = products_and_features_df.join(group_relation_pricings_df,
                                                    (col("group_service_specialty_feature_relation_id") == col("relation_id"))
                                                    & (col("relation_type") == "GroupServiceSpecialtyFeatureRelation"),
                                                    "left")

product_fees_raw_1 = product_fees_raw_1.orderBy("group_id", "service_specialty_feature_cd")

# display(product_fees_raw_1)

display(product_fees_raw_1.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### product_fees_raw_2

# CELL ********************

# The Join is performed on "group_offer_id" 

product_fees_raw_2 = products_and_features_df.join(group_offers_df, "group_id", "inner")
                                    
product_fees_raw_2 = product_fees_raw_2.join(group_relation_pricings_df, col("group_offer_id") == col("relation_id"), "inner")

product_fees_raw_2 = product_fees_raw_2.join(offer_service_specialty_feature_relations_df, col("group_offer_id") == col("offer_id"), "inner")

product_fees_raw_2 = product_fees_raw_2.orderBy("group_id", "service_specialty_feature_cd")

# display(product_fees_raw_2)

display(product_fees_raw_2.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### product_fees_raw_3

# CELL ********************

# The Join is performed on "group_service_SPECIALTY_relation_id" 

product_fees_raw_3 = products_and_features_df.join(group_relation_pricings_df,
                                                    (col("group_service_specialty_relation_id") == col("relation_id"))
                                                    & (col("relation_type") == "GroupServiceSpecialtyFeatureRelation"),
                                                    "inner")

product_fees_raw_3 = product_fees_raw_3.filter(col("service_specialty_feature_cd").isin("VPC_DM", "VPC_DPP", "VPC_HTN", "VPC_WM"))

product_fees_raw_3 = product_fees_raw_3.orderBy("group_id", "service_specialty_feature_cd")

# display(product_fees_raw_3)

display(product_fees_raw_3.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Create a DF with Pathology Products only

# CELL ********************

pathology_products_df = products_and_features_df.filter(col("service_specialty_feature_cd").contains("PATHOLOGY"))

pathology_fees = pathology_products_df.withColumn(
    "fee_name",
    when(col("feature_cd") == "BASE", "Pathology Base - No Fee")
    .when(col("feature_cd") == "ATHOMELAB", "Pathology At Home Lab - No Fee")
    .when(col("feature_cd") == "COVID19PCRLAB", "Pathology COVID-19 At Home Lab - No Fee")
    .when(col("feature_cd") == "LAB", "Pathology Standard Lab - No Fee")
    .when(col("feature_cd") == "MD", "Pathology MD Lab - No Fee")
    .when(col("feature_cd") == "NONSTANDARDLAB", "Pathology Non Standard Lab - No Fee")
    .otherwise(None)
)

pathology_fees = pathology_fees.withColumn(
    "amount",
    lit(0.0)
)

pathology_fees = pathology_fees.filter(
    (col("fee_name").isNotNull())
)

pathology_fees = pathology_fees.select(
    "group_id",
    "service_specialty_cd",
    "service_specialty_nm",
    "service_specialty_feature_cd",
    "service_specialty_feature_nm",
    "fee_name",
    "amount"
).orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(pathology_fees)

display(pathology_fees.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # No Aggregation Fees.
# The following Fees are obtained directly without aggregations:
# - Membership Fees.
# - Base Service Specialty Features Visit Fees (Client & Member).
# - Therapy Visit Fees (Client & Member).
# - Primary Care Visit Fees (Client & Member).
# - Primary Care Follow-up Visit Fees (Client & Member).

# CELL ********************

# With product_fees_raw_1

no_aggregation_fees = product_fees_raw_1.withColumn(
    "fee_name",
    when(
        (col("pricing_type_cd") == "PRICINGTYPE_BILLING") &
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("invoice_submethod_cd") == "INVOICESUBMETHOD_BILLEDAMOUNT") &
        (col("feature_cd") == "BASE") &
        ~(col("service_specialty_cd").isin(no_membership_fees_products)),
        "Membership Fee"
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("feature_cd") == "BASE") &
        (col("service_specialty_cd") != "BEHAVHEALTH") &
        (col("service_specialty_cd") != "VPC") &
        ~(col("service_specialty_cd").isin(no_visit_fees_products)),
        "Visit Fee - Client"
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("feature_cd") == "BASE") &
        (col("service_specialty_cd") != "BEHAVHEALTH") &
        (col("service_specialty_cd") != "VPC") &
        ~(col("service_specialty_cd").isin(no_visit_fees_products)),
        "Visit Fee - Member"
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("service_specialty_feature_cd") == "BEHAVHEALTH_BASE"),
        "Therapy Visit Fee - Client"
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("service_specialty_feature_cd") == "BEHAVHEALTH_BASE"),
        "Therapy Visit Fee - Member"
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("service_specialty_feature_cd") == "VPC_BASE"),
        "Primary Care Visit Fee - Client" # New
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("service_specialty_feature_cd") == "VPC_BASE"),
        "Primary Care Visit Fee - Member" # New
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Client"
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Member"
    ).otherwise(None)
)

no_aggregation_fees = no_aggregation_fees.filter(
    (col("fee_name").isNotNull())
)

no_aggregation_fees = no_aggregation_fees.select(
    "group_id",
    "service_specialty_cd",
    "service_specialty_nm",
    "service_specialty_feature_cd",
    "service_specialty_feature_nm",
    "fee_name",
    "amount"
).orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(no_aggregation_fees)

# display(no_aggregation_fees.filter(col("service_specialty_cd") == "BEHAVHEALTH"))

# display(no_aggregation_fees.filter(col("service_specialty_cd") == "VPC"))

display(no_aggregation_fees.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Aggregated Fees.

# MARKDOWN ********************

# ### **aggregated_fees_part_1**
# **aggregated_fees_part_1** and **aggregated_fees_part_2** are needed to get the following Fees:
# - Psychiatry Initial Visit Fees.
# - Primary Care Annual Checkup Visit Fees.

# CELL ********************

# aggregated_fees_part_1 with product_fees_raw_1

aggregated_fees_part_1 = product_fees_raw_1.withColumn(
    "fee_name",
    when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("service_specialty_feature_cd") == "BEHAVHEALTH_BASE"),
        "Therapy Visit Fee - Client"
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("service_specialty_feature_cd") == "BEHAVHEALTH_BASE"),
        "Therapy Visit Fee - Member"
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("service_specialty_feature_cd") == "BEHAVHEALTH_MD"),
        "Psychiatry Ongoing Visit Fee - Member"
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("service_specialty_feature_cd") == "BEHAVHEALTH_MD"),
        "Psychiatry Ongoing Visit Fee - Client"
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("service_specialty_feature_cd") == "VPC_BASE"),
        "Primary Care Visit Fee - Client"
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("service_specialty_feature_cd") == "VPC_BASE"),
        "Primary Care Visit Fee - Member"
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Client"
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Member"
    ).otherwise(None)
)

aggregated_fees_part_1 = aggregated_fees_part_1.filter(
    (col("fee_name").isNotNull())
)

aggregated_fees_part_1 = aggregated_fees_part_1.select(
    "group_id",
    "service_specialty_cd",
    "service_specialty_nm",
    "service_specialty_feature_cd",
    "service_specialty_feature_nm",
    "fee_name",
    "amount"
).orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_part_1)

display(aggregated_fees_part_1.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### **aggregated_fees_part_2**
# **aggregated_fees_part_1** and **aggregated_fees_part_2** are needed to get the following Fees:
# - Psychiatry Initial Visit Fees.
# - Primary Care Annual Checkup Visit Fees.

# CELL ********************

# aggregated_fees_part_2 with product_fees_raw_2

aggregated_fees_part_2 = product_fees_raw_2.withColumn(
    "fee_name",
    when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("service_specialty_feature_cd") == "BEHAVHEALTH_MD") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM"),
        "Psychiatry Initial Visit Fee - Client"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("service_specialty_feature_cd") == "BEHAVHEALTH_MD") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM"),
        "Psychiatry Initial Visit Fee - Member"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("service_specialty_feature_cd") == "VPC_MD") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
        (col("promotion_cd") == "PREMIUM_ANNUALWITHSPECIALTYFEATURE"),
        "Primary Care Annual Checkup Visit Fee - Client"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("service_specialty_feature_cd") == "VPC_MD") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
        (col("promotion_cd") == "PREMIUM_ANNUALWITHSPECIALTYFEATURE"),
        "Primary Care Annual Checkup Visit Fee - Member"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("service_specialty_feature_cd") == "VPC_MD") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
        (col("promotion_cd") == "PREMIUM_FIRSTWITHSPECIALTYFEATURE"),
        "Primary Care New Patient Visit Fee - Client"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("service_specialty_feature_cd") == "VPC_MD") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
        (col("promotion_cd") == "PREMIUM_FIRSTWITHSPECIALTYFEATURE"),
        "Primary Care New Patient Visit Fee - Member"
    # ).when(
    #    (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
    #    (col("feature_cd") == "MD") &
    #    (col("service_specialty_feature_cd") == "VPC_MD") &
    #    (col("service_specialty_cd") == "VPC") &
    #    (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
    #    (col("promotion_cd") == "PREMIUM_INTLFLEXSWITHSPECIALTYFEATURE"),
    #    "Primary Care Initial Flex Visit Fee - Client" # New
    #).when(
    #    (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
    #    (col("feature_cd") == "MD") &
    #    (col("service_specialty_feature_cd") == "VPC_MD") &
    #    (col("service_specialty_cd") == "VPC") &
    #    (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
    #    (col("promotion_cd") == "PREMIUM_INTLFLEXSWITHSPECIALTYFEATURE"),
    #    "Primary Care Initial Flex Visit Fee - Member" # New
    ).otherwise(None)
)

aggregated_fees_part_2 = aggregated_fees_part_2.filter(
    (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
    (col("relation_type") == "GroupOffer") &
    (col("service_specialty_feature_cd") == col("offer_service_specialty_feature_cd"))
)

aggregated_fees_part_2 = aggregated_fees_part_2.filter(
    (col("fee_name").isNotNull())
)

aggregated_fees_part_2 = aggregated_fees_part_2.select(
    "group_id",
    "service_specialty_cd",
    "service_specialty_nm",
    "service_specialty_feature_cd",
    "service_specialty_feature_nm",
    "fee_name",
    "amount"
).orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_part_2)

display(aggregated_fees_part_2.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### **aggregated_fees_final_part_1**
# Needed to get the following Fees:
# - Psychiatry Initial Visit Fees.
# - Primary Care Annual Checkup Visit Fees.

# CELL ********************

# Union aggregated_fees_part_1 with aggregated_fees_part_2

aggregated_fees_final_part_1 = aggregated_fees_part_1.unionByName(aggregated_fees_part_2)

aggregated_fees_final_part_1 = aggregated_fees_final_part_1.withColumn(
    "fee_name",
    when(
        col("fee_name").isin(
            "Psychiatry Initial Visit Fee - Member",
            "Psychiatry Ongoing Visit Fee - Member",
            "Therapy Visit Fee - Member"
        ),
        "Psychiatry Initial Visit Fee - Member"
    ).when(
        col("fee_name").isin(
            "Psychiatry Initial Visit Fee - Client",
            "Psychiatry Ongoing Visit Fee - Client",
            "Therapy Visit Fee - Client"
        ),
        "Psychiatry Initial Visit Fee - Client"
    ).when(
        col("fee_name").isin(
            "Primary Care Annual Checkup Visit Fee - Member",
            "Primary Care Follow-up Visit Fee - Member",
            "Primary Care Visit Fee - Member"
        ),
        "Primary Care Annual Checkup Visit Fee - Member"
    ).when(
        col("fee_name").isin(
            "Primary Care Annual Checkup Visit Fee - Client",
            "Primary Care Follow-up Visit Fee - Client",
            "Primary Care Visit Fee - Client"
        ),
        "Primary Care Annual Checkup Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_final_part_1 = aggregated_fees_final_part_1.filter(
    (col("fee_name").isNotNull())
)

aggregated_fees_final_part_1 = aggregated_fees_final_part_1.withColumn(
    "amount", col("amount").cast("double")
)

aggregated_fees_final_part_1 = aggregated_fees_final_part_1 \
    .groupBy("group_id", "fee_name") \
    .agg(
        sum("amount").alias("amount"),
        first("service_specialty_cd").alias("service_specialty_cd"),
        first("service_specialty_nm").alias("service_specialty_nm"), 
        first("service_specialty_feature_cd").alias("service_specialty_feature_cd"),
        first("service_specialty_feature_nm").alias("service_specialty_feature_nm")
    ) \
    .select("group_id", "service_specialty_cd", "service_specialty_nm", "service_specialty_feature_cd", "service_specialty_feature_nm", "fee_name", "amount") \
    .orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_final_part_1)

# display(aggregated_fees_final_part_1.filter(col("service_specialty_cd") == "BEHAVHEALTH"))

# display(aggregated_fees_final_part_1.filter(col("service_specialty_cd") == "VPC"))

display(aggregated_fees_final_part_1.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Union **aggregated_fees_final_part_1** and **no_aggregation_fees**.

# CELL ********************

aggregated_fees_final_part_1 = aggregated_fees_final_part_1.unionByName(no_aggregation_fees)

aggregated_fees_final_part_1 = aggregated_fees_final_part_1.orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_final_part_1)

display(aggregated_fees_final_part_1.filter(col("group_id") == "12282"))

# UP TO HERE I AM GETTING THE CORRECT VALUES FOR VPC FEES: MEMBERSHIP FEE, PRIMARY CARE VISIT FEES, FOLLOW UP VISIT FEES, AND ANNUAL CHECKUP VISIT FEES
# UP TO HERE I AM GETTING THE CORRECT VALUES FOR MH FEES: MEMBERSHIP FEE, THERAPY VISIT FEES, AND PSYCHIATRY INITIAL VISIT FEES

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### **aggregated_fees_part_3**
# **aggregated_fees_part_3** and **aggregated_fees_part_4** are needed to get the following Fees:
# - Psychiatry Ongoing Visit Fees.
# - Primary Care New Patient Visit Fees.

# CELL ********************

aggregated_fees_part_3 = product_fees_raw_1.withColumn(
    "fee_name",
    when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "BEHAVHEALTH_BASE"),
        "Therapy Visit Fee - Client"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "BEHAVHEALTH_BASE"),
        "Therapy Visit Fee - Member"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "BEHAVHEALTH_MD"),
        "Psychiatry Ongoing Visit Fee - Member"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "BEHAVHEALTH_MD"),
        "Psychiatry Ongoing Visit Fee - Client"
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("service_specialty_feature_cd") == "VPC_BASE"),
        "Primary Care Visit Fee - Client"
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("service_specialty_feature_cd") == "VPC_BASE"),
        "Primary Care Visit Fee - Member"
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Client"
    ).when(
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Member"
    ).otherwise(None)
)

aggregated_fees_part_3 = aggregated_fees_part_3.filter(
    (col("fee_name").isNotNull())
)

aggregated_fees_part_3 = aggregated_fees_part_3.select(
    "group_id",
    "service_specialty_cd",
    "service_specialty_nm",
    "service_specialty_feature_cd",
    "service_specialty_feature_nm",
    "fee_name",
    "amount"
).orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_part_3)

display(aggregated_fees_part_3.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### **aggregated_fees_part_4**
# **aggregated_fees_part_3** and **aggregated_fees_part_4** are needed to get the following Fees:
# - Psychiatry Ongoing Visit Fees.
# - Primary Care New Patient Visit Fees.

# CELL ********************

aggregated_fees_part_4 = product_fees_raw_2.withColumn(
    "fee_name",
    when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("feature_cd") == "MD") &
        (col("service_specialty_feature_cd") == "VPC_MD") &
        (col("service_specialty_cd") == "VPC") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
        (col("promotion_cd") == "PREMIUM_ANNUALWITHSPECIALTYFEATURE"),
        "Primary Care Annual Checkup Visit Fee - Member"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("feature_cd") == "MD") &
        (col("service_specialty_feature_cd") == "VPC_MD") &
        (col("service_specialty_cd") == "VPC") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
        (col("promotion_cd") == "PREMIUM_ANNUALWITHSPECIALTYFEATURE"),
        "Primary Care Annual Checkup Visit Fee - Client"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("feature_cd") == "MD") &
        (col("service_specialty_feature_cd") == "VPC_MD") &
        (col("service_specialty_cd") == "VPC") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
        (col("promotion_cd") == "PREMIUM_FIRSTWITHSPECIALTYFEATURE"),
        "Primary Care New Patient Visit Fee - Member"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("feature_cd") == "MD") &
        (col("service_specialty_feature_cd") == "VPC_MD") &
        (col("service_specialty_cd") == "VPC") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
        (col("promotion_cd") == "PREMIUM_FIRSTWITHSPECIALTYFEATURE"),
        "Primary Care New Patient Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_part_4 = aggregated_fees_part_4.filter(
    (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
    (col("relation_type") == "GroupOffer") &
    (col("service_specialty_feature_cd") == col("offer_service_specialty_feature_cd"))
)

aggregated_fees_part_4 = aggregated_fees_part_4.filter(
    (col("fee_name").isNotNull())
)

aggregated_fees_part_4 = aggregated_fees_part_4.select(
    "group_id",
    "service_specialty_cd",
    "service_specialty_nm",
    "service_specialty_feature_cd",
    "service_specialty_feature_nm",
    "fee_name",
    "amount"
).orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_part_4)

display(aggregated_fees_part_4.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### **aggregated_fees_final_part_2**
# Needed to get the following Fees:
# - Psychiatry Ongoing Visit Fees.
# - Primary Care New Patient Visit Fees.

# CELL ********************

# Union aggregated_fees_part_3 with aggregated_fees_part_4

aggregated_fees_final_part_2 = aggregated_fees_part_3.unionByName(aggregated_fees_part_4)

aggregated_fees_final_part_2 = aggregated_fees_final_part_2.withColumn(
    "fee_name",
    when(
        col("fee_name").isin(
            "Psychiatry Ongoing Visit Fee - Member",
            "Therapy Visit Fee - Member"
        ),
        "Psychiatry Ongoing Visit Fee - Member"
    ).when(
        col("fee_name").isin(
            "Psychiatry Ongoing Visit Fee - Client",
            "Therapy Visit Fee - Client"
        ),
        "Psychiatry Ongoing Visit Fee - Client"
    ).when(
        col("fee_name").isin(
            "Primary Care New Patient Visit Fee - Member",
            "Primary Care Follow-up Visit Fee - Member",
            "Primary Care Visit Fee - Member"
        ),
        "Primary Care New Patient Visit Fee - Member"
    ).when(
        col("fee_name").isin(
            "Primary Care New Patient Visit Fee - Client",
            "Primary Care Follow-up Visit Fee - Client",
            "Primary Care Visit Fee - Client"
        ),
        "Primary Care New Patient Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_final_part_2 = aggregated_fees_final_part_2.filter(
    (col("fee_name").isNotNull())
)

aggregated_fees_final_part_2 = aggregated_fees_final_part_2.withColumn(
    "amount", col("amount").cast("double")
)

aggregated_fees_final_part_2 = aggregated_fees_final_part_2 \
    .groupBy("group_id", "fee_name") \
    .agg(
        sum("amount").alias("amount"),
        first("service_specialty_cd").alias("service_specialty_cd"),
        first("service_specialty_nm").alias("service_specialty_nm"), 
        first("service_specialty_feature_cd").alias("service_specialty_feature_cd"),
        first("service_specialty_feature_nm").alias("service_specialty_feature_nm")
    ) \
    .select("group_id", "service_specialty_cd", "service_specialty_nm", "service_specialty_feature_cd", "service_specialty_feature_nm", "fee_name", "amount") \
    .orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_final_part_2)

display(aggregated_fees_final_part_2.filter(col("group_id") == "12282"))

# UP TO HERE I AM GETTING THE CORRECT VALUES FOR VPC FEES: NEW PATIENT VISIT FEES
# UP TO HERE I AM GETTING THE CORRECT VALUES FOR MH FEES: PSYCHIATRY ONGOING VISIT FEES

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # VPC CCM Care Products Visit Fees

# MARKDOWN ********************

# ### Diabetes Care
# - Diabetes Care New Patient Visit Fee
# - Diabetes Care Follow-up Visit Fee

# CELL ********************

# aggregated_fees_part_5 is used to get Diabetes Care Follow-up Visit Fees

aggregated_fees_part_5 = product_fees_raw_3.withColumn(
    "fee_name",
    when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "VPC_DM"),
        "Diabetes Care Follow-up Visit Fee - Client"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "VPC_DM"),
        "Diabetes Care Follow-up Visit Fee - Member"
    ).otherwise(None)
)

aggregated_fees_part_5 = aggregated_fees_part_5.filter(col("fee_name").isNotNull())

diabetes_care_group_ids = [row["group_id"] for row in aggregated_fees_part_5.select("group_id").dropDuplicates().collect()]

# aggregated_fees_part_5_vpc_follow_up is used to get Primary Care Follow-up Visit Fees

aggregated_fees_part_5_vpc_follow_up = product_fees_raw_1.withColumn(
    "fee_name",
    when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Client"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Member"
    ).otherwise(None)
)

aggregated_fees_part_5_vpc_follow_up = aggregated_fees_part_5_vpc_follow_up.filter((col("fee_name").isNotNull()) & (col("group_id").isin(diabetes_care_group_ids)))

# aggregated_fees_diabetes_care_follow_up_visit_fees
### If aggregated_fees_part_5 IS NOT empty, it means the Group has Diabetes Care, so we should do the Union

if aggregated_fees_part_5.isEmpty() != True:

    aggregated_fees_diabetes_care_follow_up_visit_fees = aggregated_fees_part_5.unionByName(aggregated_fees_part_5_vpc_follow_up)

    aggregated_fees_diabetes_care_follow_up_visit_fees = aggregated_fees_diabetes_care_follow_up_visit_fees.orderBy("group_id", "service_specialty_feature_cd", "fee_name")

    # display(aggregated_fees_diabetes_care_follow_up_visit_fees)

    # display(aggregated_fees_diabetes_care_follow_up_visit_fees.filter(col("group_id") == "12282"))
    
else:

    print("There are no Groups with service_specialty_feature_cd == VPC_DM")

aggregated_fees_diabetes_care_follow_up_visit_fees = aggregated_fees_diabetes_care_follow_up_visit_fees.filter(col("fee_name").isNotNull())

aggregated_fees_diabetes_care_follow_up_visit_fees = aggregated_fees_diabetes_care_follow_up_visit_fees.select(
    "group_id",
    "service_specialty_cd",
    "service_specialty_nm",
    "service_specialty_feature_cd",
    "service_specialty_feature_nm",
    "fee_name",
    "amount"
).orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_diabetes_care_follow_up_visit_fees)

# display(aggregated_fees_diabetes_care_follow_up_visit_fees.filter(col("group_id") == "12282"))

# aggregated_fees_part_6 to get Diabetes Care New Patient Visit Fees

aggregated_fees_part_6 = product_fees_raw_2.withColumn(
    "fee_name",
    when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("service_specialty_feature_cd") == "VPC_DM") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM"),
        "Diabetes Care New Patient Visit Fee - Member"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("service_specialty_feature_cd") == "VPC_DM") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM"),
        "Diabetes Care New Patient Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_part_6 = aggregated_fees_part_6.filter(
    (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
    (col("promotion_cd") == "PREMIUM_FIRSTWITHSPECIALTYFEATURE") &
    (col("relation_type") == "GroupOffer") &
    (col("offer_service_specialty_feature_cd") == "VPC_MD"))

aggregated_fees_part_6 = aggregated_fees_part_6.filter(col("fee_name").isNotNull())

aggregated_fees_part_6 = aggregated_fees_part_6.select(
    "group_id",
    "service_specialty_cd",
    "service_specialty_nm",
    "service_specialty_feature_cd",
    "service_specialty_feature_nm",
    "fee_name",
    "amount"
).orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_part_6)

# display(aggregated_fees_part_6.filter(col("group_id") == "12282"))



# aggregated_fees_final_part_3 to get FINAL Diabetes Care New Patient Visit Fees

aggregated_fees_final_part_3 = aggregated_fees_diabetes_care_follow_up_visit_fees.unionByName(aggregated_fees_part_6)

aggregated_fees_final_part_3 = aggregated_fees_final_part_3.withColumn(
    "fee_name",
    when(
        col("fee_name").isin(
            "Diabetes Care Follow-up Visit Fee - Member",
            "Diabetes Care New Patient Visit Fee - Member",
            "Primary Care Follow-up Visit Fee - Member"
            # "Diabetes Care Visit Fee - Member"
        ),
        "Diabetes Care New Patient Visit Fee - Member"
    ).when(
        col("fee_name").isin(
            "Diabetes Care Follow-up Visit Fee - Client",
            "Diabetes Care New Patient Visit Fee - Client",
            "Primary Care Follow-up Visit Fee - Client"
            # "Diabetes Care Visit Fee - Client"
        ),
        "Diabetes Care New Patient Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_final_part_3 = aggregated_fees_final_part_3.filter(
    (col("fee_name").isNotNull())
)

aggregated_fees_final_part_3 = aggregated_fees_final_part_3.withColumn(
    "amount", col("amount").cast("double")
)

aggregated_fees_final_part_3 = aggregated_fees_final_part_3 \
    .groupBy("group_id", "fee_name") \
    .agg(
        sum("amount").alias("amount"),
        first("service_specialty_cd").alias("service_specialty_cd"),
        first("service_specialty_nm").alias("service_specialty_nm"), 
        first("service_specialty_feature_cd").alias("service_specialty_feature_cd"),
        first("service_specialty_feature_nm").alias("service_specialty_feature_nm")
    ) \
    .select("group_id", "service_specialty_cd", "service_specialty_nm", "service_specialty_feature_cd", "service_specialty_feature_nm", "fee_name", "amount") \
    .orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_final_part_3)

display(aggregated_fees_final_part_3.filter(col("group_id") == "12282"))



# aggregated_fees_final_part_4 to get FINAL Diabetes Care Follow-up Visit Fees

aggregated_fees_final_part_4 = aggregated_fees_diabetes_care_follow_up_visit_fees.withColumn(
    "fee_name",
    when(
        col("fee_name").isin(
            "Diabetes Care Follow-up Visit Fee - Member",
            "Primary Care Follow-up Visit Fee - Member"
            # "Diabetes Care Visit Fee - Member"
        ),
        "Diabetes Care Follow-up Visit Fee - Member"
    ).when(
        col("fee_name").isin(
            "Diabetes Care Follow-up Visit Fee - Client",
            "Primary Care Follow-up Visit Fee - Client"
            # "Diabetes Care Visit Fee - Client"
        ),
        "Diabetes Care Follow-up Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_final_part_4 = aggregated_fees_final_part_4.filter(
    (col("fee_name").isNotNull())
)

aggregated_fees_final_part_4 = aggregated_fees_final_part_4.withColumn(
    "amount", col("amount").cast("double")
)

aggregated_fees_final_part_4 = aggregated_fees_final_part_4 \
    .groupBy("group_id", "fee_name") \
    .agg(
        sum("amount").alias("amount"),
        first("service_specialty_cd").alias("service_specialty_cd"),
        first("service_specialty_nm").alias("service_specialty_nm"), 
        first("service_specialty_feature_cd").alias("service_specialty_feature_cd"),
        first("service_specialty_feature_nm").alias("service_specialty_feature_nm")
    ) \
    .select("group_id", "service_specialty_cd", "service_specialty_nm", "service_specialty_feature_cd", "service_specialty_feature_nm", "fee_name", "amount") \
    .orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_final_part_4)

display(aggregated_fees_final_part_4.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Prediabetes Care
# - Prediabetes Care New Patient Visit Fee
# - Prediabetes Care Follow-up Visit Fee

# CELL ********************

# aggregated_fees_part_6 is used to get Prediabetes Care Follow-up Visit Fees

aggregated_fees_part_6 = product_fees_raw_3.withColumn(
    "fee_name",
    when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "VPC_DPP"),
        "Prediabetes Care Follow-up Visit Fee - Client"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "VPC_DPP"),
        "Prediabetes Care Follow-up Visit Fee - Member"
    ).otherwise(None)
)

aggregated_fees_part_6 = aggregated_fees_part_6.filter(col("fee_name").isNotNull())

prediabetes_care_group_ids = [row["group_id"] for row in aggregated_fees_part_6.select("group_id").dropDuplicates().collect()]

# display(aggregated_fees_part_6)

# display(prediabetes_care_group_ids)

# aggregated_fees_part_6_vpc_follow_up is used to get Primary Care Follow-up Visit Fees



aggregated_fees_part_6_vpc_follow_up = product_fees_raw_1.withColumn(
    "fee_name",
    when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Client"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Member"
    ).otherwise(None)
)

aggregated_fees_part_6_vpc_follow_up = aggregated_fees_part_6_vpc_follow_up.filter((col("fee_name").isNotNull()) & (col("group_id").isin(prediabetes_care_group_ids)))

# aggregated_fees_prediabetes_care_follow_up_visit_fees
### If aggregated_fees_part_6 IS NOT empty, it means the Group has Prediabetes Care, so we should do the Union

if aggregated_fees_part_6.isEmpty() != True:

    aggregated_fees_prediabetes_care_follow_up_visit_fees = aggregated_fees_part_6.unionByName(aggregated_fees_part_6_vpc_follow_up)

    aggregated_fees_prediabetes_care_follow_up_visit_fees = aggregated_fees_prediabetes_care_follow_up_visit_fees.orderBy("group_id", "service_specialty_feature_cd", "fee_name")

    # display(aggregated_fees_prediabetes_care_follow_up_visit_fees)

    display(aggregated_fees_prediabetes_care_follow_up_visit_fees.filter(col("group_id") == "12282"))
    
else:

    print("There are no Groups with service_specialty_feature_cd == VPC_DPP")

aggregated_fees_prediabetes_care_follow_up_visit_fees = aggregated_fees_prediabetes_care_follow_up_visit_fees.filter(col("fee_name").isNotNull())

aggregated_fees_prediabetes_care_follow_up_visit_fees = aggregated_fees_prediabetes_care_follow_up_visit_fees.select(
    "group_id",
    "service_specialty_cd",
    "service_specialty_nm",
    "service_specialty_feature_cd",
    "service_specialty_feature_nm",
    "fee_name",
    "amount"
).orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_prediabetes_care_follow_up_visit_fees)

# display(aggregated_fees_prediabetes_care_follow_up_visit_fees.filter(col("group_id") == "12282"))

# aggregated_fees_part_6 to get Prediabetes Care New Patient Visit Fees

aggregated_fees_part_7 = product_fees_raw_2.withColumn(
    "fee_name",
    when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("service_specialty_feature_cd") == "VPC_DPP") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM"),
        "Prediabetes Care New Patient Visit Fee - Member"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("service_specialty_feature_cd") == "VPC_DPP") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM"),
        "Prediabetes Care New Patient Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_part_7 = aggregated_fees_part_7.filter(
    (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
    (col("promotion_cd") == "PREMIUM_FIRSTWITHSPECIALTYFEATURE") &
    (col("relation_type") == "GroupOffer") &
    (col("offer_service_specialty_feature_cd") == "VPC_MD"))

aggregated_fees_part_7 = aggregated_fees_part_7.filter(col("fee_name").isNotNull())

aggregated_fees_part_7 = aggregated_fees_part_7.select(
    "group_id",
    "service_specialty_cd",
    "service_specialty_nm",
    "service_specialty_feature_cd",
    "service_specialty_feature_nm",
    "fee_name",
    "amount"
).orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_part_7)

# display(aggregated_fees_part_7.filter(col("group_id") == "12282"))



# aggregated_fees_final_part_5 to get FINAL Prediabetes Care New Patient Visit Fees

aggregated_fees_final_part_5 = aggregated_fees_prediabetes_care_follow_up_visit_fees.unionByName(aggregated_fees_part_7)

aggregated_fees_final_part_5 = aggregated_fees_final_part_5.withColumn(
    "fee_name",
    when(
        col("fee_name").isin(
            "Prediabetes Care Follow-up Visit Fee - Member",
            "Prediabetes Care New Patient Visit Fee - Member",
            "Primary Care Follow-up Visit Fee - Member"
            # "Prediabetes Care Visit Fee - Member"
        ),
        "Prediabetes Care New Patient Visit Fee - Member"
    ).when(
        col("fee_name").isin(
            "Prediabetes Care Follow-up Visit Fee - Client",
            "Prediabetes Care New Patient Visit Fee - Client",
            "Primary Care Follow-up Visit Fee - Client"
            # "Prediabetes Care Visit Fee - Client"
        ),
        "Prediabetes Care New Patient Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_final_part_5 = aggregated_fees_final_part_5.filter(
    (col("fee_name").isNotNull())
)

aggregated_fees_final_part_5 = aggregated_fees_final_part_5.withColumn(
    "amount", col("amount").cast("double")
)

aggregated_fees_final_part_5 = aggregated_fees_final_part_5 \
    .groupBy("group_id", "fee_name") \
    .agg(
        sum("amount").alias("amount"),
        first("service_specialty_cd").alias("service_specialty_cd"),
        first("service_specialty_nm").alias("service_specialty_nm"), 
        first("service_specialty_feature_cd").alias("service_specialty_feature_cd"),
        first("service_specialty_feature_nm").alias("service_specialty_feature_nm")
    ) \
    .select("group_id", "service_specialty_cd", "service_specialty_nm", "service_specialty_feature_cd", "service_specialty_feature_nm", "fee_name", "amount") \
    .orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_final_part_5)

display(aggregated_fees_final_part_5.filter(col("group_id") == "12282"))



# aggregated_fees_final_part_6 to get FINAL Prediabetes Care Follow-up Visit Fees

aggregated_fees_final_part_6 = aggregated_fees_prediabetes_care_follow_up_visit_fees.withColumn(
    "fee_name",
    when(
        col("fee_name").isin(
            "Prediabetes Care Follow-up Visit Fee - Member",
            "Primary Care Follow-up Visit Fee - Member"
            # "Prediabetes Care Visit Fee - Member"
        ),
        "Prediabetes Care Follow-up Visit Fee - Member"
    ).when(
        col("fee_name").isin(
            "Prediabetes Care Follow-up Visit Fee - Client",
            "Primary Care Follow-up Visit Fee - Client"
            # "Prediabetes Care Visit Fee - Client"
        ),
        "Prediabetes Care Follow-up Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_final_part_6 = aggregated_fees_final_part_6.filter(
    (col("fee_name").isNotNull())
)

aggregated_fees_final_part_6 = aggregated_fees_final_part_6.withColumn(
    "amount", col("amount").cast("double")
)

aggregated_fees_final_part_6 = aggregated_fees_final_part_6 \
    .groupBy("group_id", "fee_name") \
    .agg(
        sum("amount").alias("amount"),
        first("service_specialty_cd").alias("service_specialty_cd"),
        first("service_specialty_nm").alias("service_specialty_nm"), 
        first("service_specialty_feature_cd").alias("service_specialty_feature_cd"),
        first("service_specialty_feature_nm").alias("service_specialty_feature_nm")
    ) \
    .select("group_id", "service_specialty_cd", "service_specialty_nm", "service_specialty_feature_cd", "service_specialty_feature_nm", "fee_name", "amount") \
    .orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_final_part_6)

display(aggregated_fees_final_part_6.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Hypertension Care
# - Hypertension Care New Patient Visit Fee
# - Hypertension Care Follow-up Visit Fee

# CELL ********************

# aggregated_fees_part_8 is used to get Hypertension Care Follow-up Visit Fees

aggregated_fees_part_8 = product_fees_raw_3.withColumn(
    "fee_name",
    when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "VPC_HTN"),
        "Hypertension Care Follow-up Visit Fee - Client"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "VPC_HTN"),
        "Hypertension Care Follow-up Visit Fee - Member"
    ).otherwise(None)
)

aggregated_fees_part_8 = aggregated_fees_part_8.filter(col("fee_name").isNotNull())

hypertension_care_group_ids = [row["group_id"] for row in aggregated_fees_part_8.select("group_id").dropDuplicates().collect()]

# display(aggregated_fees_part_8)

# display(hypertension_care_group_ids)

# aggregated_fees_part_8_vpc_follow_up is used to get Primary Care Follow-up Visit Fees



aggregated_fees_part_8_vpc_follow_up = product_fees_raw_1.withColumn(
    "fee_name",
    when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Client"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Member"
    ).otherwise(None)
)

aggregated_fees_part_8_vpc_follow_up = aggregated_fees_part_8_vpc_follow_up.filter((col("fee_name").isNotNull()) & (col("group_id").isin(hypertension_care_group_ids)))

# aggregated_fees_hypertension_care_follow_up_visit_fees
### If aggregated_fees_part_8 IS NOT empty, it means the Group has Hypertension Care, so we should do the Union

if aggregated_fees_part_8.isEmpty() != True:

    aggregated_fees_hypertension_care_follow_up_visit_fees = aggregated_fees_part_8.unionByName(aggregated_fees_part_8_vpc_follow_up)

    aggregated_fees_hypertension_care_follow_up_visit_fees = aggregated_fees_hypertension_care_follow_up_visit_fees.orderBy("group_id", "service_specialty_feature_cd", "fee_name")

    # display(aggregated_fees_hypertension_care_follow_up_visit_fees)

    display(aggregated_fees_hypertension_care_follow_up_visit_fees.filter(col("group_id") == "12282"))
    
else:

    print("There are no Groups with service_specialty_feature_cd == VPC_HTN")

aggregated_fees_hypertension_care_follow_up_visit_fees = aggregated_fees_hypertension_care_follow_up_visit_fees.filter(col("fee_name").isNotNull())

aggregated_fees_hypertension_care_follow_up_visit_fees = aggregated_fees_hypertension_care_follow_up_visit_fees.select(
    "group_id",
    "service_specialty_cd",
    "service_specialty_nm",
    "service_specialty_feature_cd",
    "service_specialty_feature_nm",
    "fee_name",
    "amount"
).orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_hypertension_care_follow_up_visit_fees)

# display(aggregated_fees_hypertension_care_follow_up_visit_fees.filter(col("group_id") == "12282"))

# aggregated_fees_part_8 to get Hypertension Care New Patient Visit Fees

aggregated_fees_part_9 = product_fees_raw_2.withColumn(
    "fee_name",
    when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("service_specialty_feature_cd") == "VPC_HTN") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM"),
        "Hypertension Care New Patient Visit Fee - Member"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("service_specialty_feature_cd") == "VPC_HTN") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM"),
        "Hypertension Care New Patient Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_part_9 = aggregated_fees_part_9.filter(
    (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
    (col("promotion_cd") == "PREMIUM_FIRSTWITHSPECIALTYFEATURE") &
    (col("relation_type") == "GroupOffer") &
    (col("offer_service_specialty_feature_cd") == "VPC_MD"))

aggregated_fees_part_9 = aggregated_fees_part_9.filter(col("fee_name").isNotNull())

aggregated_fees_part_9 = aggregated_fees_part_9.select(
    "group_id",
    "service_specialty_cd",
    "service_specialty_nm",
    "service_specialty_feature_cd",
    "service_specialty_feature_nm",
    "fee_name",
    "amount"
).orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_part_9)

# display(aggregated_fees_part_9.filter(col("group_id") == "12282"))



# aggregated_fees_final_part_7 to get FINAL Hypertension Care New Patient Visit Fees

aggregated_fees_final_part_7 = aggregated_fees_hypertension_care_follow_up_visit_fees.unionByName(aggregated_fees_part_9)

aggregated_fees_final_part_7 = aggregated_fees_final_part_7.withColumn(
    "fee_name",
    when(
        col("fee_name").isin(
            "Hypertension Care Follow-up Visit Fee - Member",
            "Hypertension Care New Patient Visit Fee - Member",
            "Primary Care Follow-up Visit Fee - Member"
            # "Hypertension Care Visit Fee - Member"
        ),
        "Hypertension Care New Patient Visit Fee - Member"
    ).when(
        col("fee_name").isin(
            "Hypertension Care Follow-up Visit Fee - Client",
            "Hypertension Care New Patient Visit Fee - Client",
            "Primary Care Follow-up Visit Fee - Client"
            # "Hypertension Care Visit Fee - Client"
        ),
        "Hypertension Care New Patient Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_final_part_7 = aggregated_fees_final_part_7.filter(
    (col("fee_name").isNotNull())
)

aggregated_fees_final_part_7 = aggregated_fees_final_part_7.withColumn(
    "amount", col("amount").cast("double")
)

aggregated_fees_final_part_7 = aggregated_fees_final_part_7 \
    .groupBy("group_id", "fee_name") \
    .agg(
        sum("amount").alias("amount"),
        first("service_specialty_cd").alias("service_specialty_cd"),
        first("service_specialty_nm").alias("service_specialty_nm"), 
        first("service_specialty_feature_cd").alias("service_specialty_feature_cd"),
        first("service_specialty_feature_nm").alias("service_specialty_feature_nm")
    ) \
    .select("group_id", "service_specialty_cd", "service_specialty_nm", "service_specialty_feature_cd", "service_specialty_feature_nm", "fee_name", "amount") \
    .orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_final_part_7)

display(aggregated_fees_final_part_7.filter(col("group_id") == "12282"))



# aggregated_fees_final_part_8 to get FINAL Hypertension Care Follow-up Visit Fees

aggregated_fees_final_part_8 = aggregated_fees_hypertension_care_follow_up_visit_fees.withColumn(
    "fee_name",
    when(
        col("fee_name").isin(
            "Hypertension Care Follow-up Visit Fee - Member",
            "Primary Care Follow-up Visit Fee - Member"
            # "Hypertension Care Visit Fee - Member"
        ),
        "Hypertension Care Follow-up Visit Fee - Member"
    ).when(
        col("fee_name").isin(
            "Hypertension Care Follow-up Visit Fee - Client",
            "Primary Care Follow-up Visit Fee - Client"
            # "Hypertension Care Visit Fee - Client"
        ),
        "Hypertension Care Follow-up Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_final_part_8 = aggregated_fees_final_part_8.filter(
    (col("fee_name").isNotNull())
)

aggregated_fees_final_part_8 = aggregated_fees_final_part_8.withColumn(
    "amount", col("amount").cast("double")
)

aggregated_fees_final_part_8 = aggregated_fees_final_part_8 \
    .groupBy("group_id", "fee_name") \
    .agg(
        sum("amount").alias("amount"),
        first("service_specialty_cd").alias("service_specialty_cd"),
        first("service_specialty_nm").alias("service_specialty_nm"), 
        first("service_specialty_feature_cd").alias("service_specialty_feature_cd"),
        first("service_specialty_feature_nm").alias("service_specialty_feature_nm")
    ) \
    .select("group_id", "service_specialty_cd", "service_specialty_nm", "service_specialty_feature_cd", "service_specialty_feature_nm", "fee_name", "amount") \
    .orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_final_part_8)

display(aggregated_fees_final_part_8.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Weight Management Care
# - Weight Management Care New Patient Visit Fee
# - Weight Management Care Follow-up Visit Fee

# CELL ********************

# aggregated_fees_part_10 is used to get Weight Management Care Follow-up Visit Fees

aggregated_fees_part_10 = product_fees_raw_3.withColumn(
    "fee_name",
    when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "VPC_WM"),
        "Weight Management Care Follow-up Visit Fee - Client"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "VPC_WM"),
        "Weight Management Care Follow-up Visit Fee - Member"
    ).otherwise(None)
)

aggregated_fees_part_10 = aggregated_fees_part_10.filter(col("fee_name").isNotNull())

weight_management_care_group_ids = [row["group_id"] for row in aggregated_fees_part_10.select("group_id").dropDuplicates().collect()]

# display(aggregated_fees_part_10)

# display(Weight Management_care_group_ids)

# aggregated_fees_part_10_vpc_follow_up is used to get Primary Care Follow-up Visit Fees



aggregated_fees_part_10_vpc_follow_up = product_fees_raw_1.withColumn(
    "fee_name",
    when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Client"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("pricing_type_cd") == "PRICINGTYPE_EVENT") &
        (col("service_specialty_feature_cd") == "VPC_MD"),
        "Primary Care Follow-up Visit Fee - Member"
    ).otherwise(None)
)

aggregated_fees_part_10_vpc_follow_up = aggregated_fees_part_10_vpc_follow_up.filter((col("fee_name").isNotNull()) & (col("group_id").isin(weight_management_care_group_ids)))

# aggregated_fees_weight_management_care_follow_up_visit_fees
### If aggregated_fees_part_10 IS NOT empty, it means the Group has Weight Management Care, so we should do the Union

if aggregated_fees_part_10.isEmpty() != True:

    aggregated_fees_weight_management_care_follow_up_visit_fees = aggregated_fees_part_10.unionByName(aggregated_fees_part_10_vpc_follow_up)

    aggregated_fees_weight_management_care_follow_up_visit_fees = aggregated_fees_weight_management_care_follow_up_visit_fees.orderBy("group_id", "service_specialty_feature_cd", "fee_name")

    # display(aggregated_fees_weight_management_care_follow_up_visit_fees)

    display(aggregated_fees_weight_management_care_follow_up_visit_fees.filter(col("group_id") == "12282"))
    
else:

    print("There are no Groups with service_specialty_feature_cd == VPC_WM")

aggregated_fees_weight_management_care_follow_up_visit_fees = aggregated_fees_weight_management_care_follow_up_visit_fees.filter(col("fee_name").isNotNull())

aggregated_fees_weight_management_care_follow_up_visit_fees = aggregated_fees_weight_management_care_follow_up_visit_fees.select(
    "group_id",
    "service_specialty_cd",
    "service_specialty_nm",
    "service_specialty_feature_cd",
    "service_specialty_feature_nm",
    "fee_name",
    "amount"
).orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_weight_management_care_follow_up_visit_fees)

# display(aggregated_fees_weight_management_care_follow_up_visit_fees.filter(col("group_id") == "12282"))

# aggregated_fees_part_11 to get Weight Management Care New Patient Visit Fees

aggregated_fees_part_11 = product_fees_raw_2.withColumn(
    "fee_name",
    when(
        (col("invoice_method_cd") == "INVOICEMETHOD_MEM") &
        (col("service_specialty_feature_cd") == "VPC_WM") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM"),
        "Weight Management Care New Patient Visit Fee - Member"
    ).when(
        (col("invoice_method_cd") == "INVOICEMETHOD_COMP") &
        (col("service_specialty_feature_cd") == "VPC_WM") &
        (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM"),
        "Weight Management Care New Patient Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_part_11 = aggregated_fees_part_11.filter(
    (col("pricing_type_cd") == "PRICINGTYPE_PREMIUM") &
    (col("promotion_cd") == "PREMIUM_FIRSTWITHSPECIALTYFEATURE") &
    (col("relation_type") == "GroupOffer") &
    (col("offer_service_specialty_feature_cd") == "VPC_MD"))

aggregated_fees_part_11 = aggregated_fees_part_11.filter(col("fee_name").isNotNull())

aggregated_fees_part_11 = aggregated_fees_part_11.select(
    "group_id",
    "service_specialty_cd",
    "service_specialty_nm",
    "service_specialty_feature_cd",
    "service_specialty_feature_nm",
    "fee_name",
    "amount"
).orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_part_11)

# display(aggregated_fees_part_11.filter(col("group_id") == "12282"))



# aggregated_fees_final_part_9 to get FINAL Weight Management Care New Patient Visit Fees

aggregated_fees_final_part_9 = aggregated_fees_weight_management_care_follow_up_visit_fees.unionByName(aggregated_fees_part_11)

aggregated_fees_final_part_9 = aggregated_fees_final_part_9.withColumn(
    "fee_name",
    when(
        col("fee_name").isin(
            "Weight Management Care Follow-up Visit Fee - Member",
            "Weight Management Care New Patient Visit Fee - Member",
            "Primary Care Follow-up Visit Fee - Member"
            # "Weight Management Care Visit Fee - Member"
        ),
        "Weight Management Care New Patient Visit Fee - Member"
    ).when(
        col("fee_name").isin(
            "Weight Management Care Follow-up Visit Fee - Client",
            "Weight Management Care New Patient Visit Fee - Client",
            "Primary Care Follow-up Visit Fee - Client"
            # "Weight Management Care Visit Fee - Client"
        ),
        "Weight Management Care New Patient Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_final_part_9 = aggregated_fees_final_part_9.filter(
    (col("fee_name").isNotNull())
)

aggregated_fees_final_part_9 = aggregated_fees_final_part_9.withColumn(
    "amount", col("amount").cast("double")
)

aggregated_fees_final_part_9 = aggregated_fees_final_part_9 \
    .groupBy("group_id", "fee_name") \
    .agg(
        sum("amount").alias("amount"),
        first("service_specialty_cd").alias("service_specialty_cd"),
        first("service_specialty_nm").alias("service_specialty_nm"), 
        first("service_specialty_feature_cd").alias("service_specialty_feature_cd"),
        first("service_specialty_feature_nm").alias("service_specialty_feature_nm")
    ) \
    .select("group_id", "service_specialty_cd", "service_specialty_nm", "service_specialty_feature_cd", "service_specialty_feature_nm", "fee_name", "amount") \
    .orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_final_part_9)

display(aggregated_fees_final_part_9.filter(col("group_id") == "12282"))



# aggregated_fees_final_part_10 to get FINAL Weight Management Care Follow-up Visit Fees

aggregated_fees_final_part_10 = aggregated_fees_weight_management_care_follow_up_visit_fees.withColumn(
    "fee_name",
    when(
        col("fee_name").isin(
            "Weight Management Care Follow-up Visit Fee - Member",
            "Primary Care Follow-up Visit Fee - Member"
            # "Weight Management Care Visit Fee - Member"
        ),
        "Weight Management Care Follow-up Visit Fee - Member"
    ).when(
        col("fee_name").isin(
            "Weight Management Care Follow-up Visit Fee - Client",
            "Primary Care Follow-up Visit Fee - Client"
            # "Weight Management Care Visit Fee - Client"
        ),
        "Weight Management Care Follow-up Visit Fee - Client"
    ).otherwise(None)
)

aggregated_fees_final_part_10 = aggregated_fees_final_part_10.filter(
    (col("fee_name").isNotNull())
)

aggregated_fees_final_part_10 = aggregated_fees_final_part_10.withColumn(
    "amount", col("amount").cast("double")
)

aggregated_fees_final_part_10 = aggregated_fees_final_part_10 \
    .groupBy("group_id", "fee_name") \
    .agg(
        sum("amount").alias("amount"),
        first("service_specialty_cd").alias("service_specialty_cd"),
        first("service_specialty_nm").alias("service_specialty_nm"), 
        first("service_specialty_feature_cd").alias("service_specialty_feature_cd"),
        first("service_specialty_feature_nm").alias("service_specialty_feature_nm")
    ) \
    .select("group_id", "service_specialty_cd", "service_specialty_nm", "service_specialty_feature_cd", "service_specialty_feature_nm", "fee_name", "amount") \
    .orderBy("group_id", "service_specialty_feature_cd", "fee_name")

# display(aggregated_fees_final_part_10)

display(aggregated_fees_final_part_10.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Final union.

# CELL ********************

aggregated_fees_final = aggregated_fees_final_part_1.unionByName(aggregated_fees_final_part_2) \
                                                    .unionByName(aggregated_fees_final_part_3) \
                                                    .unionByName(aggregated_fees_final_part_4) \
                                                    .unionByName(aggregated_fees_final_part_5) \
                                                    .unionByName(aggregated_fees_final_part_6) \
                                                    .unionByName(aggregated_fees_final_part_7) \
                                                    .unionByName(aggregated_fees_final_part_8) \
                                                    .unionByName(aggregated_fees_final_part_9) \
                                                    .unionByName(aggregated_fees_final_part_10) \
                                                    .unionByName(pathology_fees)

aggregated_fees_final = aggregated_fees_final.dropDuplicates()

# display(aggregated_fees_final.filter(col("service_specialty_feature_cd") == "VPC_DM"))

display(aggregated_fees_final.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Set correct Service Specialty Feature Codes and Names

# CELL ********************

# Mental Health

aggregated_fees_final = aggregated_fees_final.withColumn("service_specialty_feature_cd",
                            when(col("fee_name").contains("Psychiatry"), "BEHAVHEALTH_MD")
                            .otherwise(col("service_specialty_feature_cd")))

aggregated_fees_final = aggregated_fees_final.withColumn("service_specialty_feature_nm",
                            when(col("fee_name").contains("Psychiatry"), "Mental Health MD")
                            .otherwise(col("service_specialty_feature_nm")))

# Primary Care

aggregated_fees_final = aggregated_fees_final.withColumn("service_specialty_feature_cd",
                            when((col("fee_name").contains("Annual")) | (col("fee_name").contains("New Patient")), "VPC_MD")
                            .otherwise(col("service_specialty_feature_cd")))

aggregated_fees_final = aggregated_fees_final.withColumn("service_specialty_feature_nm",
                            when((col("fee_name").contains("Annual")) | (col("fee_name").contains("New Patient")), "Primary Care MD Feature")
                            .otherwise(col("service_specialty_feature_nm")))

# Diabetes Care

aggregated_fees_final = aggregated_fees_final.withColumn("service_specialty_feature_cd",
                            when(col("fee_name").contains("Diabetes Care"), "VPC_DM")
                            .otherwise(col("service_specialty_feature_cd")))

aggregated_fees_final = aggregated_fees_final.withColumn("service_specialty_feature_nm",
                            when(col("fee_name").contains("Diabetes Care"), "Diabetes Management Feature")
                            .otherwise(col("service_specialty_feature_nm")))

# Prediabetes Care

aggregated_fees_final = aggregated_fees_final.withColumn("service_specialty_feature_cd",
                            when(col("fee_name").contains("Prediabetes Care"), "VPC_DPP")
                            .otherwise(col("service_specialty_feature_cd")))

aggregated_fees_final = aggregated_fees_final.withColumn("service_specialty_feature_nm",
                            when(col("fee_name").contains("Prediabetes Care"), "Prediabetes Management Feature")
                            .otherwise(col("service_specialty_feature_nm")))

# Hypertension Care

aggregated_fees_final = aggregated_fees_final.withColumn("service_specialty_feature_cd",
                            when(col("fee_name").contains("Hypertension Care"), "VPC_HTN")
                            .otherwise(col("service_specialty_feature_cd")))

aggregated_fees_final = aggregated_fees_final.withColumn("service_specialty_feature_nm",
                            when(col("fee_name").contains("Hypertension Care"), "Hypertension Management Feature")
                            .otherwise(col("service_specialty_feature_nm")))

# Weight Management Care

aggregated_fees_final = aggregated_fees_final.withColumn("service_specialty_feature_cd",
                            when(col("fee_name").contains("Weight Management Care"), "VPC_WM")
                            .otherwise(col("service_specialty_feature_cd")))

aggregated_fees_final = aggregated_fees_final.withColumn("service_specialty_feature_nm",
                            when(col("fee_name").contains("Weight Management Care"), "Weight Management Feature")
                            .otherwise(col("service_specialty_feature_nm")))

aggregated_fees_final = aggregated_fees_final.orderBy("group_id", "service_specialty_feature_nm", "fee_name")

display(aggregated_fees_final.filter(col("group_id") == "12282"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Add Visit Fee Total row.

# CELL ********************

# Extract the common prefix of each "Visit Fee" (e.g., "Psychiatry Initial Visit Fee")
visit_fees_df = aggregated_fees_final.filter(col("fee_name").contains("Visit Fee"))

visit_fees_df = visit_fees_df.withColumn("fee_prefix", regexp_extract(col("fee_name"), r"(.+) - (Client|Member)", 1))

visit_fees_df = visit_fees_df.withColumn("fee_prefix", col("fee_prefix").cast(StringType()))

# display(visit_fees_df)

# Identify grouping columns (all except 'fee_name' and 'amount')
grouping_columns = [c for c in visit_fees_df.columns if c not in ["fee_name", "amount"]]

# Aggregate data by fee_prefix and grouping columns
visit_fees_totals_df = visit_fees_df.groupBy(grouping_columns).agg(sum("amount").alias("amount"))

visit_fees_totals_df = visit_fees_totals_df.withColumn("fee_name", concat(col("fee_prefix"), lit(" - Total")))

visit_fees_totals_df = visit_fees_totals_df.drop("fee_prefix")

visit_fees_totals_df = visit_fees_totals_df.orderBy("group_id", "service_specialty_feature_nm", "fee_name")

display(visit_fees_totals_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Union to add Total rows.

# CELL ********************

final_df = aggregated_fees_final.unionByName(visit_fees_totals_df)

final_df = final_df.orderBy("group_id", "service_specialty_feature_nm", "fee_name")

display(final_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Check Group count.

# CELL ********************

### Print row count

row_count = final_df.count()

print(f"Total rows in final Products table: {row_count}")

### Print unique group_id

unique_count = final_df.select("group_id").distinct().count()

print(f"Unique values in group_id column in final Products table: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Save to Lakehouse with new Schema.

# CELL ********************

final_df.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_admin_products_fees_information")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
