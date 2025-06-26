# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "2aaca13c-7db2-429b-af27-8213b3ef4b37",
# META       "default_lakehouse_name": "LH_HealthChecker",
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977",
# META       "known_lakehouses": [
# META         {
# META           "id": "f6f49e86-9d3b-492d-a898-53d963a0a525"
# META         },
# META         {
# META           "id": "fd033454-c9c0-47c2-8349-50eb57cb28b9"
# META         },
# META         {
# META           "id": "2aaca13c-7db2-429b-af27-8213b3ef4b37"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

spark.conf.set("spark.sql.parquet.datetimeRebaseModeInRead", "LEGACY")
spark.conf.set("spark.sql.parquet.datetimeRebaseModeInWrite", "LEGACY")

from pyspark.sql import functions as F
from datetime import datetime

current_date = datetime.now().strftime('%Y-%m-%d')
excluded_org_id = 437586

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

file_mapping_subquery = spark.sql(f"""
    SELECT gr.group_id, gs.map
    FROM LH_HealthChecker.allowed_group_relations gr
    JOIN LH_HealthChecker.allowed_group_settings gs
    ON gr.allowed_group_setting_id = gs.allowed_group_setting_id
    AND gr.exclusion_cd = gs.exclusion_cd
    WHERE gs.exclusion_cd = 'IN'
    AND gs.map NOT IN (
        'aetna_si_stagedinclude_group_to_teladoc_group',
        'claims_extract_for_lineco_group',
        'aetna_si_exclusions_group_to_teladoc_group',
        'Brent_Moore_DO_NOT_EXTRACT_for_BD',
        'aetna_vpc_termoff_group_to_teladoc_group',
        'aetna_fi_termoff_group_to_teladoc_group',
        'aetna_si_termoff_group_to_teladoc_group',
        'aetna_si_OutOfOrg_group_to_teladoc_group',
        'ETLD76_split1_group_to_teladoc_group',
        'ETLD76_split2_group_to_teladoc_group'
    )
""")

file_mapping_results = (
    spark.table("LH_HealthChecker.valid_group_sources").alias("vs")
    .join(
        spark.table("LH_HealthChecker.groups").alias("g"),
        ["group_id", "exclusion_cd"],
        "inner"
    )
    .join(
        file_mapping_subquery.alias("agr"),
        "group_id",
        "left"
    )
    .join(
        spark.table("LH_HealthChecker.organizations").alias("o"),
        "group_id",
        "inner"
    )
    .join(
        spark.table("LH_HealthChecker.organizations").alias("p"),
        F.expr("substring(o.sql_path, 3, locate('/', o.sql_path, 3) - 3)").cast("int") == F.col("p.organization_id"),
        "inner"
    )
    .filter(
        (F.col("g.exclusion_cd") == "IN") &
        ((F.col("g.template") == 0) | ((F.col("g.template") == 1) & F.col("agr.map").isNotNull())) &
        (F.coalesce(F.col("g.effective_end_dt"), F.lit(current_date)) >= F.lit(current_date)) &
        (F.col("p.organization_id") != excluded_org_id)
    )
    .groupBy("p.organization_id", "g.group_id", "g.legacy_group_id", "g.group_nm", "p.organization_nm", "g.effective_start_dt")
    .agg(
        F.lit("File Mapping").alias("Validation_Type"),
        F.when(
            (F.countDistinct("agr.map") > 1) |
            (F.max("agr.group_id").isNotNull() & (F.first("g.template") == 1)) |
            (F.max("agr.group_id").isNull() & (F.first("g.template") == 0) & 
             F.first("vs.primary_source_cd").isin(["REGTYPE_APIHYBRID", "REGTYPE_HYBRID", "REGTYPE_STAGEDELIGIBILITY", "REGTYPE_STAGEDREGISTRATION"])) |
            (F.max("agr.group_id").isNotNull() & 
             ~F.first("vs.primary_source_cd").isin(["REGTYPE_APIHYBRID", "REGTYPE_HYBRID", "REGTYPE_STAGEDELIGIBILITY", "REGTYPE_STAGEDREGISTRATION"])),
            F.lit("NO")
        ).otherwise(F.lit("YES")).alias("Good"),
        F.when(
            F.countDistinct("agr.map") > 1, F.lit("Multiple maps found")
        ).when(
            F.max("agr.group_id").isNotNull() & (F.first("g.template") == 1), F.lit("Template group in Map")
        ).when(
            F.max("agr.group_id").isNull() & (F.first("g.template") == 0) & 
            F.first("vs.primary_source_cd").isin(["REGTYPE_APIHYBRID", "REGTYPE_HYBRID", "REGTYPE_STAGEDELIGIBILITY", "REGTYPE_STAGEDREGISTRATION"]),
            F.lit("Map expected No Map")
        ).when(
            F.max("agr.group_id").isNotNull() & 
            ~F.first("vs.primary_source_cd").isin(["REGTYPE_APIHYBRID", "REGTYPE_HYBRID", "REGTYPE_STAGEDELIGIBILITY", "REGTYPE_STAGEDREGISTRATION"]),
            F.lit("RTE ONLY group in Map")
        ).otherwise(F.lit("YES")).alias("Reason"),
        F.lit("").alias("Reason2"),
        F.to_date(F.first("g.effective_start_dt")).alias("Live_Dt"),
        F.to_date(F.first("g.effective_start_dt")).alias("Grp_Start_Dt")
    )
)

display(file_mapping_results.limit(10))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

ccm_feature_subquery = spark.sql(f"""
    SELECT gfr.*, sr.group_id
    FROM LH_HealthChecker.group_service_specialty_feature_relations gfr
    JOIN LH_HealthChecker.group_service_specialty_relations sr
    ON sr.group_service_specialty_relation_id = gfr.group_service_specialty_relation_id
    AND sr.exclusion_cd = gfr.exclusion_cd
    JOIN LH_HealthChecker.ref_service_specialties rss
    ON sr.service_specialty_cd = rss.service_specialty_cd
    WHERE rss.servicing_platform_cd = 'SERVICEPLATFORM_CHRONICCARE'
    AND IFNULL(gfr.termination_dt, '{current_date}') >= '{current_date}'
""")

ccm_config_results = (
    spark.table("LH_HealthChecker.groups").alias("g")
    .join(
        spark.table("LH_HealthChecker.group_service_specialty_relations").alias("sr"),
        ["group_id", "exclusion_cd"],
        "inner"
    )
    .join(
        spark.table("LH_HealthChecker.alt_group_ids").alias("agi"),
        (F.col("g.group_id") == F.col("agi.group_id")) &
        (F.col("g.exclusion_cd") == F.col("agi.exclusion_cd")) &
        (F.col("agi.alt_group_cd") == "ALT_CHRONICCARECLIENTCODE"),
        "left"
    )
    .join(
        ccm_feature_subquery.alias("fr"),
        ["group_service_specialty_relation_id", "exclusion_cd"],
        "left"
    )
    .join(
        spark.table("LH_HealthChecker.organizations").alias("o"),
        "group_id",
        "inner"
    )
    .join(
        spark.table("LH_HealthChecker.organizations").alias("p"),
        F.expr("substring(o.sql_path, 3, locate('/', o.sql_path, 3) - 3)").cast("int") == F.col("p.organization_id"),
        "inner"
    )
    .filter(
        (F.col("g.exclusion_cd") == "IN") &
        (F.col("g.template") == 0) &
        (F.coalesce(F.col("g.effective_end_dt"), F.lit(current_date)) >= F.lit(current_date)) &
        (F.col("p.organization_id") != excluded_org_id)
    )
    .groupBy("p.organization_id", "g.group_id", "g.legacy_group_id", "g.group_nm", "p.organization_nm", "g.effective_start_dt")
    .agg(
        F.lit("CCM Config").alias("Validation_Type"),
        F.when(
            (F.max("fr.group_service_specialty_relation_id").isNull()) |
            (F.max("fr.group_service_specialty_relation_id").isNotNull() & F.max("agi.alt_group_id").isNotNull()),
            F.lit("YES")
        ).otherwise(F.lit("NO")).alias("Good"),
        F.concat(
            F.lit("HasProduct - "),
            F.when(
                F.max("fr.group_service_specialty_relation_id").isNull(),
                F.lit("NO")
            ).otherwise(F.lit("YES"))
        ).alias("Reason"),
        F.concat(
            F.lit("HasClientCd - "),
            F.when(
                F.max("agi.alt_group_id").isNull(),
                F.lit("NO")
            ).otherwise(F.max("agi.alt_group_value"))
        ).alias("Reason2"),
        F.max("fr.live_dt").alias("Live_Dt"),
        F.to_date(F.first("g.effective_start_dt")).alias("Grp_Start_Dt")
    )
)

display(ccm_config_results.limit(10))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

rte_mapping_results = (
    spark.table("LH_HealthChecker.groups").alias("g")
    .join(
        spark.table("LH_HealthChecker.valid_group_sources").alias("vs"),
        ["group_id", "exclusion_cd"],
        "inner"
    )
    .join(
        spark.table("LH_HealthChecker.organizations").alias("o"),
        "group_id",
        "inner"
    )
    .join(
        spark.table("LH_HealthChecker.organizations").alias("p"),
        F.expr("substring(o.sql_path, 3, locate('/', o.sql_path, 3) - 3)").cast("int") == F.col("p.organization_id"),
        "inner"
    )
    .join(
        spark.table("LH_HealthChecker.external_group_relations").alias("er"),
        ["group_id", "exclusion_cd"],
        "left"
    )
    .join(
        spark.table("LH_HealthChecker.payers").alias("pay"),
        F.col("er.payer_id") == F.col("pay.payer_id"),
        "left"
    )
    .filter(
        (F.col("g.exclusion_cd") == "IN") &
        (F.col("g.template") == 0) &
        (F.coalesce(F.col("g.effective_end_dt"), F.lit(current_date)) >= F.lit(current_date)) &
        (F.col("p.organization_id") != excluded_org_id)
    )
    .groupBy(
        "p.organization_id",
        "g.group_id",
        "g.legacy_group_id",
        "g.group_nm",
        "p.organization_nm",
        "g.effective_start_dt"
    )
    .agg(
        F.lit("RTE Mapping").alias("Validation_Type"),
        F.when(
            (F.max("er.external_group_id").isNull() & 
             F.first("vs.primary_source_cd").isin(["REGTYPE_RTE", "REGTYPE_HYBRID"])),
            F.lit("NO")
        ).when(
            (F.max("er.external_group_id").isNotNull() & 
             ~F.first("vs.primary_source_cd").isin(["REGTYPE_RTE", "REGTYPE_HYBRID"])),
            F.lit("NO")
        ).otherwise(F.lit("YES")).alias("Good"),
        F.when(
            (F.max("er.external_group_id").isNull() & 
             F.first("vs.primary_source_cd").isin(["REGTYPE_RTE", "REGTYPE_HYBRID"])),
            F.lit("Not Good - No RTE Map for Group, but RTE is supported")
        ).when(
            (F.max("er.external_group_id").isNotNull() & 
             ~F.first("vs.primary_source_cd").isin(["REGTYPE_RTE", "REGTYPE_HYBRID"])),
            F.lit("??? - RTE Map for Group, but not configured for RTE")
        ).when(
            (F.max("er.external_group_id").isNull() & 
             ~F.first("vs.primary_source_cd").isin(["REGTYPE_RTE", "REGTYPE_HYBRID"])),
            F.lit("Good - No RTE Map for Group and not configured for RTE")
        ).otherwise(F.lit("Good - RTE and Mapped")).alias("Reason"),
        F.concat(
            F.lit("No Turn Away - "),
            F.coalesce(F.first("pay.do_not_turn_away_flg"), F.lit("N")),
            F.lit(" / "),
            F.first("vs.primary_source_cd")
        ).alias("Reason2"),
        F.first("er.effective_start_dt").alias("Live_Dt")  # Use first() instead of grouping by this column
    )
    .withColumn("Grp_Start_Dt", F.to_date(F.col("g.effective_start_dt")))
)

display(rte_mapping_results.limit(10))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

merged_df = file_mapping_results.unionByName(ccm_config_results).unionByName(rte_mapping_results)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

duplicates_df = (
    merged_df.groupBy("group_id")
    .count()
    .filter("count == 3")
)

display(duplicates_df.limit(10))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

display(merged_df.where("group_id = 589395"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

display(merged_df.count())

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

merged_df.write.format("delta").mode("overwrite").saveAsTable("LH_HealthChecker.final_table")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
