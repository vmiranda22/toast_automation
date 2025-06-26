# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "858ad52b-f017-4d74-9957-17175dd47103",
# META       "default_lakehouse_name": "toast_lh_dev_raw",
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977",
# META       "known_lakehouses": [
# META         {
# META           "id": "858ad52b-f017-4d74-9957-17175dd47103"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

%run ./toast_nb_utils_sanitize_column_name

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

%run ./toast_nb_utils_build_schema

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

%run ./toast_nb_utils_fetch_data

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

%run ./toast_nb_utils_flatten_records

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import pandas as pd
import numpy as np
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sha2, concat_ws
from pyspark.sql.types import StringType

spark = SparkSession.builder.getOrCreate()

default_start_date = datetime(2025, 5, 5)
delta_table = "workfront_prod_project_raw"

timestamp_columns = {
    "actualCompletionDate", "actualStartDate", "approvalCompletionDate", "approvalStartDate",
    "budgetedCompletionDate", "budgetedStartDate", "convertedOpTaskEntryDate", "entryDate",
    "estCompletionDate", "estStartDate", "financeLastUpdateDate", "fixedEndDate",
    "fixedStartDate", "lastCalcDate", "lastUpdateDate", "nextAutoBaselineDate"
}

array_columns = {"auditTypes"}

base_columns_raw = [
    "ID", "name", "objCode", "BCCompletionState", "URL", "actualBenefit", "actualBillableExpenseCost",
    "actualCompletionDate", "actualCost", "actualDurationMinutes", "actualExpenseCost",
    "actualLaborCost", "actualNonBillableExpenseCost", "actualRevenue", "actualRiskCost",
    "actualStartDate", "actualValue", "actualWorkRequired", "alignment", "alignmentScoreCardID",
    "approvalCompletionDate", "approvalProcessID", "approvalStartDate", "auditTypes",
    "autoBaselineRecurOn", "autoBaselineRecurrenceType", "bcwp", "bcws", "billedRevenue",
    "budget", "budgetStatus", "budgetedCompletionDate", "budgetedCost", "budgetedHours",
    "budgetedLaborCost", "budgetedStartDate", "categoryID", "companyID", "completionType",
    "condition", "conditionType", "convertedOpTaskEntryDate", "convertedOpTaskName",
    "convertedOpTaskOriginatorID", "cpi", "csi", "currency", "currentApprovalStepID",
    "customerID", "deliverableScoreCardID", "deliverableSuccessScore", "description",
    "displayOrder", "durationMinutes", "eac", "eacCalculationMethod", "enableAutoBaselines",
    "enteredByID", "entryDate", "estCompletionDate", "estStartDate", "extRefID", "filterHourTypes",
    "financeLastUpdateDate", "fixedCost", "fixedEndDate", "fixedRevenue", "fixedStartDate",
    "groupID", "hasBudgetConflict", "hasCalcError", "hasDocuments", "hasExpenses", "hasMessages",
    "hasNotes", "hasRateOverride", "hasResolvables", "hasTimedNotifications", "hasTimelineException",
    "isOriginalPlannedHoursSet", "isStatusComplete", "lastCalcDate", "lastConditionNoteID",
    "lastNoteID", "lastUpdateDate", "lastUpdatedByID", "levelingMode", "milestonePathID",
    "nextAutoBaselineDate", "numberOpenOpTasks", "optimizationScore", "originalWorkRequired",
    "ownerID", "ownerPrivileges", "pendingCalculation", "pendingUpdateMethods", "percentComplete",
    "performanceIndexMethod", "personal", "plannedBenefit"
]

parameter_columns_raw = [
    "data.parameterValues.DE:Brand",
    "data.parameterValues.DE:Will your project need a creative strategist?",
    "data.parameterValues.DE:Will speakers be highlighted on this landing page?",
    "data.parameterValues.DE:Asset size",
    "data.parameterValues.DE:Will this route to Propel for legal review?",
    "data.parameterValues.DE:Note the approved/estimated format below",
    "data.parameterValues.DE:Project Notes",
    "data.parameterValues.DE:Where will files be delivered?",
    "data.parameterValues.DE:Will this piece require translations?",
    "data.parameterValues.DE:If other or notes are needed please provide below",
    "data.parameterValues.DE:Please provide # of rounds and # of days per round for client reviews",
    "data.parameterValues.DE:Is there an existing Workfront project?",
    "data.parameterValues.DE:Description of changes needed",
    "data.parameterValues.DE:DM asset type",
    "data.parameterValues.DE:if yes, which language is needed?",
    "data.parameterValues.DE:If video is net new, please provide style direction or example of styles you like",
    "data.parameterValues.DE:What devices will this video highlight?",
    "data.parameterValues.DE:How can we support this?",
    "data.parameterValues.DE:Will you need a vanity URL?",
    "data.parameterValues.DE:Will this piece need to be AODA compliant?",
    "data.parameterValues.DE:What makes up the cultural and market context?",
    "data.parameterValues.DE:B2B - Which Services will this project feature?",
    "data.parameterValues.DE:Provide creative thought starters",
    "data.parameterValues.DE:Project notes",
    "data.parameterValues.DE:Engagement Center",
    "data.parameterValues.DE:How will contact list be built?",
    "data.parameterValues.DE:What type of social ad is this?",
    "data.parameterValues.DE:Is this piece being created for a client?",
    "data.parameterValues.DE:Executive Creative Director",
    "data.parameterValues.DE:What does success look like?",
    "data.parameterValues.DE:Provide file format for asset delivery",
    "data.parameterValues.DE:Provide where final video will live",
    "data.parameterValues.DE:If other, provide asset type here",
    "data.parameterValues.DE:Content Director",
    "data.parameterValues.DE:New Asset Type",
    "data.parameterValues.DE:Planned Duration",
    "data.parameterValues.DE:Will testing be requested on this project?",
    "data.parameterValues.DE:What day does your Landing Page need to go live?",
    "data.parameterValues.DE:Creative Director",
    "data.parameterValues.DE:The Ask",
    "data.parameterValues.DE:Is client \"sell in\" required?",
    "data.parameterValues.DE:Custom Job Number",
    "data.parameterValues.DE:Where in the navigation structure of the site do we need to repair?",
    "data.parameterValues.DE:How will the final assets be delivered?",
    "data.parameterValues.DE:Which channels will this ad appear in?",
    "data.parameterValues.DE:Will  you need copy to go with this asset?",
    "data.parameterValues.DE:Channel Deliverables - LinkedIn",
    "data.parameterValues.DE:If other, please note below",
    "data.parameterValues.DE:Related Project",
    "data.parameterValues.DE:Chose your collateral asset type",
    "data.parameterValues.DE:Estimated length of requested video",
    "data.parameterValues.DE:Requested due date",
    "data.parameterValues.DE:What day does your email need to deploy?",
    "data.parameterValues.DE:If other  please provide below",
    "data.parameterValues.DE:Are you linking to a Teladoc Health Web page or landing page?",
    "data.parameterValues.DE:Is video net new?",
    "data.parameterValues.DE:Channel Deliverables - Meta - FB + Instagram",
    "data.parameterValues.DE:What is the most important insight about the customer?",
    "data.parameterValues.DE:Which Services will this project feature?",
    "data.parameterValues.DE:Which Website has the error/defect?",
    "data.parameterValues.DE:Please Select Line of Business",
    "data.parameterValues.DE:Are we using an existing approved format?",
    "data.parameterValues.DE:What size is your asset?",
    "data.parameterValues.DE:Where will this video be used?",
    "data.parameterValues.DE:Provide official video title",
    "data.parameterValues.DE:Has your executive sponsor reviewed and approved this brief?",
    "data.parameterValues.DE:Please provide existing Landing page  URL",
    "data.parameterValues.DE:Tracking requirements",
    "data.parameterValues.DE:Provide the name of the client",
    "data.parameterValues.DE:Will this piece need to route to an external client for review?",
    "data.parameterValues.DE:Is this a client Landing Page",
    "data.parameterValues.DE:CM- Where will files be delivered?",
    "data.parameterValues.DE:If routing to Propel, please provide PM codes here",
    "data.parameterValues.DE:If other, provide notes below",
    "data.parameterValues.DE:Does this video have a budget?",
    "data.parameterValues.DE:Provide privacy settings on Vimeo/Other",
    "data.parameterValues.DE:What is the most important thing we want our audience to take away?",
    "data.parameterValues.DE:UTM code for any asset that links to a TDH webpage.",
    "data.parameterValues.DE:Provide the CTA for the video",
    "data.parameterValues.DE:How many versions of this piece will be delivered?",
    "data.parameterValues.DE:Is there an existing legacy page in place?",
    "data.parameterValues.DE:Who has approved this request?",
    "data.parameterValues.DE:Problem",
    "data.parameterValues.DE:On which system will the content asset be stored?",
    "data.parameterValues.DE:Line of Business",
    "data.parameterValues.DE:List of people to add to your proof as a reviewer",
    "data.parameterValues.DE:Executive Sponsor",
    "data.parameterValues.DE:CRM Data Updates",
    "data.parameterValues.DE:HealthiestYou Client",
    "data.parameterValues.DE:Total # of Open Transactions Ending",
    "data.parameterValues.DE:Total # of Open Transactions Beginning",
    "data.parameterValues.DE:Account Status Beginning",
    "data.parameterValues.DE:Contract Contracting Account",
    "data.parameterValues.DE:Project Template",
    "data.parameterValues.DE:Client Management Action Status",
    "data.parameterValues.DE:% of groups in Admin Termed",
    "data.parameterValues.DE:# of Conga Agreement Records Ending",
    "data.parameterValues.DE:Status Notes",
    "data.parameterValues.DE:Octiv RPA Agreements",
    "data.parameterValues.DE:Sales Ops Action Required",
    "data.parameterValues.DE:Total # of Contracts Ending",
    "data.parameterValues.DE:Prioritization Notes",
    "data.parameterValues.DE:Client Sub-Type",
    "data.parameterValues.DE:Admin Sold To",
    "data.parameterValues.DE:# of Conga Agreement Records Beginning",
    "data.parameterValues.DE:Client Management Actions",
    "data.parameterValues.DE:Account GUID GCRM",
    "data.parameterValues.DE:# of Archived Contracts Ending",
    "data.parameterValues.DE:# of Activated Contracts Ending",
    "data.parameterValues.DE:Client Management Action Required",
    "data.parameterValues.DE:HealthiestYou Termed",
    "data.parameterValues.DE:Contract Contract Path",
    "data.parameterValues.DE:CPQ Clean-up Notes",
    "data.parameterValues.DE:Total # of Contracts Beginning",
    "data.parameterValues.DE:CM Last Action Date",
    "data.parameterValues.DE:Account Owner",
    "data.parameterValues.DE:Virtual Care Revenue",
    "data.parameterValues.DE:# of Amendments to Recreate",
    "data.parameterValues.DE:Account Health Score",
    "data.parameterValues.DE:Client Type",
    "data.parameterValues.DE:Post Kick Off Email",
    "data.parameterValues.DE:Client Enrollment JIRA Ticket Needed?",
    "data.parameterValues.DE:Eligibility Account Structure and/or File link posted in Salesforce?",
    "data.parameterValues.DE:Naming Convention - DOPS",
    "data.parameterValues.DE:Billing Risk Details",
    "data.parameterValues.DE:Client Line of Business",
    "data.parameterValues.DE:CCM Initial Targeted Marketing Date",
    "data.parameterValues.DE:Request Type - Client Reporting",
    "data.parameterValues.DE:NPS Satisfaction Survey Sent?",
    "data.parameterValues.DE:Sub-Channel",
    "data.parameterValues.DE:Email File",
    "data.parameterValues.DE:Actual Kickoff Date",
    "data.parameterValues.DE:Tech Ops CMC created on backend Date",
    "data.parameterValues.DE:Legacy ID",
    "data.parameterValues.DE:Client Code - DOPS",
    "data.parameterValues.DE:Billing Status",
    "data.parameterValues.DE:Number of Clients - ASO Cohort Projects",
    "data.parameterValues.DE:CCM Targeted Marketed Status",
    "data.parameterValues.DE:Canceled Products",
    "data.parameterValues.DE:Elig Email Sent Status",
    "data.parameterValues.DE:AE Email Address",
    "data.parameterValues.DE:Pre-Launch Validation Status",
    "data.parameterValues.DE:Rx Claims Readiness",
    "data.parameterValues.DE:Medical Claims File",
    "data.parameterValues.DE:Escalation Needed?",
    "data.parameterValues.DE:CIM Support",
    "data.parameterValues.DE:Date of Acknowledgement Form Approval",
    "data.parameterValues.DE:Closed Won Override",
    "data.parameterValues.DE:Implementation Acknowledgement Form Status",
    "data.parameterValues.DE:Eligibility Type - Dependents",
    "data.parameterValues.DE:Marketing Automation Bug?",
    "data.parameterValues.DE:Billing Contact Name",
    "data.parameterValues.DE:Group Number",
    "data.parameterValues.DE:Cohort Name",
    "data.parameterValues.DE:Transition to Client Services Made?",
    "data.parameterValues.DE:Admin Org Created?",
    "data.parameterValues.DE:Transition to Client Services",
    "data.parameterValues.DE:Jira Ticket Type",
    "data.parameterValues.DE:Name of Elig File Source",
    "data.parameterValues.DE:New Opportunity Sub Type",
    "data.parameterValues.DE:Mapping Details - DOPS",
    "data.parameterValues.DE:Programs - CCS",
    "data.parameterValues.DE:Predefined List Processed",
    "data.parameterValues.DE:Data Readiness",
    "data.parameterValues.DE:Medical Claims File Processed",
    "data.parameterValues.DE:Launch Day Validation Status",
    "data.parameterValues.DE:Salesforce Opportunity URL",
    "data.parameterValues.DE:Estimated Launch Date",
    "data.parameterValues.DE:New Group or Product Add",
    "data.parameterValues.DE:Marketing Status",
    "data.parameterValues.DE:CCM Marketing Type",
    "data.parameterValues.DE:Key Client?",
    "data.parameterValues.DE:Is Client Utilizing Flow1b?",
    "data.parameterValues.DE:Dependents included in Elig",
    "data.parameterValues.DE:Opportunity Type",
    "data.parameterValues.DE:Marketing Readiness",
    "data.parameterValues.DE:Post Launch Mkt HR announcement sent?",
    "data.parameterValues.DE:Care Coordination",
    "data.parameterValues.DE:Account Name",
    "data.parameterValues.DE:# of Activated Contracts Beginning",
    "data.parameterValues.DE:# of Archived Contracts Beginning",
    "data.parameterValues.DE:Data Extraction Status",
    "data.parameterValues.DE:Data Operations Escalation Notes",
    "data.parameterValues.DE:Combined Eligibility?",
    "data.parameterValues.DE:Existing Opportunity Sub Type",
    "data.parameterValues.DE:Data Readiness Total Score",
    "data.parameterValues.DE:Email File Readiness _Data",
    "data.parameterValues.DE:Contracting Account",
    "data.parameterValues.DE:Actual Launch Date",
    "data.parameterValues.DE:Rx Claims File",
    "data.parameterValues.DE:Predefined List Readiness",
    "data.parameterValues.DE:Salesforce Opportunity GUID",
    "data.parameterValues.DE:TM Registration Marketing Journey",
    "data.parameterValues.DE:Client Overview #",
    "data.parameterValues.DE:TM Welcome Letter Status",
    "data.parameterValues.DE:Elig Email Sent",
    "data.parameterValues.DE:Medical Claims Readiness",
    "data.parameterValues.DE:Billing Jira Tickets Needed",
    "data.parameterValues.DE:DOPS Summary",
    "data.parameterValues.DE:Data Readiness Check",
    "data.parameterValues.DE:Sub-Type Detail",
    "data.parameterValues.DE:DOPS Lead",
    "data.parameterValues.DE:Sales Stage",
    "data.parameterValues.DE:Client Enrollment Marketing Escalation Notes",
    "data.parameterValues.DE:Request Type - DOPS",
    "data.parameterValues.DE:Partnership Lead",
    "data.parameterValues.DE:Tech Ops CMC created on backend Date Status",
    "data.parameterValues.DE:Technical Integrations JIRA Tickets needed",
    "data.parameterValues.DE:Pre-Launch Validation Date",
    "data.parameterValues.DE:Opportunity Notes/Special Terms",
    "data.parameterValues.DE:Net ARR",
    "data.parameterValues.DE:Opportunity Owner",
    "data.parameterValues.DE:Referrals?",
    "data.parameterValues.DE:Predefined List",
    "data.parameterValues.DE:Scorecard Recipient – Email address",
    "data.parameterValues.DE:DOPS Eligibility Ingested Status",
    "data.parameterValues.DE:Contract Path or Partnership Name",
    "data.parameterValues.DE:Frequency - DOPS",
    "data.parameterValues.DE:Use Case - DOPS",
    "data.parameterValues.DE:Link to SF Record - DOPS",
    "data.parameterValues.DE:Number of Lives",
    "data.parameterValues.DE:Group ID",
    "data.parameterValues.DE:Teladoc Salesforce Account Link",
    "data.parameterValues.DE:Time of Validation Review 4 Days or Less",
    "data.parameterValues.DE:TM Welcome Letter Mail Date",
    "data.parameterValues.DE:Email File Processed",
    "data.parameterValues.DE:Pre-Launch Reviewer",
    "data.parameterValues.DE:Client Name",
    "data.parameterValues.DE:Change Request Status - Details",
    "data.parameterValues.DE:Change Request Sub-Type - Eligibility Type Change",
    "data.parameterValues.DE:Manual Final Validation Review - Overall",
    "data.parameterValues.DE:Average Time to Complete or Convert",
    "data.parameterValues.DE:Group",
    "data.parameterValues.DE:Eligibility Type - Primaries",
    "data.parameterValues.DE:Are Plan Specific Fees in SF",
    "data.parameterValues.DE:PS Channel",
    "data.parameterValues.DE:Client Enrollment Lead",
    "data.parameterValues.DE:Billing Address City, State, Zip",
    "data.parameterValues.DE:Employee Email File Link",
    "data.parameterValues.DE:Link - DOPS",
    "data.parameterValues.DE:DOPS Claims Ingested Status",
    "data.parameterValues.DE:Multitenant? - DOPS",
    "data.parameterValues.DE:File Type - DOPS",
    "data.parameterValues.DE:P360 Clinical Questionnaire Status",
    "data.parameterValues.DE:Historical Record Import",
    "data.parameterValues.DE:Exclusions, Eligibility Rules, or necessary notes",
    "data.parameterValues.DE:Number of Programs",
    "data.parameterValues.DE:Eligibility File",
    "data.parameterValues.DE:DOPS Eligibility Ingested",
    "data.parameterValues.DE:CMC- Client Member Codes",
    "data.parameterValues.DE:Client ID",
    "data.parameterValues.DE:Eligibility File Readiness",
    "data.parameterValues.DE:CIM Notes",
    "data.parameterValues.DE:Revenue Effective Date",
    "data.parameterValues.DE:Overall Launch Status",
    "data.parameterValues.DE:Link to Implementation Acknowledgement Form Approval",
    "data.parameterValues.DE:Client Allows Targeted Marketing?",
    "data.parameterValues.DE:Total US Employees Benefits Enrolled",
    "data.parameterValues.DE:Eligibility File Processed",
    "data.parameterValues.DE:What is Launching?",
    "data.parameterValues.DE:Registration Codes",
    "data.parameterValues.DE:Safe Sender Contact",
    "data.parameterValues.DE:Ready to Go?",
    "data.parameterValues.DE:Estimated Close Date",
    "data.parameterValues.DE:Billing Method",
    "data.parameterValues.DE:Contract Path Change?",
    "data.parameterValues.DE:OneApp Client?",
    "data.parameterValues.DE:Total US Employees",
    "data.parameterValues.DE:Delay Targeted Marketing?",
    "data.parameterValues.DE:Project ready for pre-Launch Validation?",
    "data.parameterValues.DE:Billing Type",
    "data.parameterValues.DE:Partner Name - DOPS",
    "data.parameterValues.DE:Number of Groups Impacted",
    "data.parameterValues.DE:Change Effective Date",
    "data.parameterValues.DE:Manual Initial Validation Review - Overall",
    "data.parameterValues.DE:Total Change Request Completion Time",
    "data.parameterValues.DE:Final Validation Review - SF",
    "data.parameterValues.DE:Is this a multiple day fair?",
    "data.parameterValues.DE:Initial Validation Review - Overall",
    "data.parameterValues.DE:Passed Final Validation Review",
    "data.parameterValues.DE:Previous CR Status - Details",
    "data.parameterValues.DE:USGH - Type of Change",
    "data.parameterValues.DE:Is Shipping Address the same as Event Location?",
    "data.parameterValues.DE:Average Time to Complete",
    "data.parameterValues.DE:Initial Validation Review - Jira",
    "data.parameterValues.DE:Final Validation Review - Jira",
    "data.parameterValues.DE:Initial Requester",
    "data.parameterValues.DE:Account Number",
    "data.parameterValues.DE:Assigned Client Manager",
    "data.parameterValues.DE:Telemed Admin Org ID",
    "data.parameterValues.DE:Internal Notes for Eligibility Team",
    "data.parameterValues.DE:HHS Project Type",
    "data.parameterValues.DE:What team are you from?",
    "data.parameterValues.DE:Initial Validation Review - SF",
    "data.parameterValues.DE:Program Selection - Chronic Care and Telemedicine",
    "data.parameterValues.DE:CI Director/Manager Notes",
    "data.parameterValues.DE:Opportunity Name",
    "data.parameterValues.DE:Sales Channel",
    "data.parameterValues.DE:CM, CCM Services",
    "data.parameterValues.DE:CM, Assets",
    "data.parameterValues.DE:CM, OneApp",
    "data.parameterValues.DE:CM, Data Team",
    "data.parameterValues.DE:CM, Volume",
    "data.parameterValues.DE:CM, Formats",
    "data.parameterValues.DE:CM, Brand",
    "data.parameterValues.DE:CM, CCM MA",
    "data.parameterValues.DE:CM, Incentive",
    "data.parameterValues.DE:CM, Campaign Type",
    "data.parameterValues.DE:CA, Date - Addt'l",
    "data.parameterValues.DE:CM, Budget",
    "data.parameterValues.DE:CM, MA No",
    "data.parameterValues.DE:CM, Creative",
    "data.parameterValues.DE:CM, Telemed Services",
    "data.parameterValues.DE:CM, Creative Project",
    "data.parameterValues.DE:CM, Create - Int/Ext",
    "data.parameterValues.DE:CM, Mail Date",
    "data.parameterValues.DE:CM, Sell-In",
    "data.parameterValues.DE:CM, Budget Line Item",
    "data.parameterValues.DE:Data Update Root Cause",
    "data.parameterValues.DE:Integration Inbox Request?",
    "data.parameterValues.DE:Final Validation Review - Overall"
]

all_columns_raw = base_columns_raw + parameter_columns_raw + ["row_hash"]

try:
    df_existing = spark.read.format("delta").table(delta_table)
    last_update = df_existing.agg({"lastUpdateDate": "max"}).collect()[0][0]
    if last_update is None:
        last_update = default_start_date
except Exception:
    last_update = default_start_date

print("Fetching projects updated since:", last_update)

api_key = "al7s4u94ggluu08vnh7atni3p5sagebm"
formatted_date = last_update.strftime('%Y-%m-%dT%H:%M:%S.000Z')
params = {
    "apiKey": api_key,
    "fields": "*,parameterValues",
    "lastUpdateDate": formatted_date,
    "lastUpdateDate_Mod": "gt"
}
url = "https://teladochealth.my.workfront.com/attask/api/v19.0/project/search"
data = fetch_data(url, params)

if not data:
    print("No new data. Exiting.")
    exit(0)

schema, raw_to_sanitized, timestamp_sanitized = build_schema(
    all_columns_raw, timestamp_columns, array_columns
)
datetime_columns = list(timestamp_sanitized)

records = flatten_records(data, raw_to_sanitized)
df_new = pd.DataFrame(records).replace({np.nan: None, "": None})

for col_name in datetime_columns:
    if col_name in df_new:
        df_new[col_name] = (
            df_new[col_name].astype(str)
            .str.replace(r'(?<=\d{2}):(?=\d{3}-\d{4}$)', '.', regex=True)
            .pipe(pd.to_datetime, format="%Y-%m-%dT%H:%M:%S.%f%z", errors="coerce", utc=True)
            .dt.tz_localize(None)
            .apply(lambda x: x.to_pydatetime() if pd.notnull(x) else None)
        )

for field in schema.fields:
    if isinstance(field.dataType, StringType) and field.name in df_new:
        df_new[field.name] = df_new[field.name].astype(str).where(df_new[field.name].notnull(), None)

df_new = df_new.reindex(columns=[f.name for f in schema.fields])

for dt_col in datetime_columns:
    if dt_col in df_new.columns:
        df_new[dt_col] = df_new[dt_col].apply(lambda x: x if isinstance(x, datetime) else None)

df_spark = spark.createDataFrame(df_new, schema=schema).dropDuplicates(["ID"])
valid_cols = [c for c in df_spark.columns if c != "row_hash"]
df_spark = df_spark.withColumn("row_hash", sha2(concat_ws("|", *[col(c) for c in valid_cols]), 256))
df_spark.createOrReplaceTempView("workfront_project_staging")

update_set = ",\n    ".join([f"target.{c} = source.{c}" for c in valid_cols if c != "ID"])
insert_cols = ", ".join(valid_cols)
insert_vals = ", ".join([f"source.{c}" for c in valid_cols])

merge_sql = f"""
MERGE INTO {delta_table} AS target
USING workfront_project_staging AS source
ON target.ID = source.ID
WHEN MATCHED AND target.row_hash != source.row_hash THEN
  UPDATE SET
    {update_set}
WHEN NOT MATCHED THEN
  INSERT ({insert_cols})
  VALUES ({insert_vals})
"""

spark.sql(merge_sql)
spark.sql(f"REFRESH TABLE {delta_table}")
print("Merge complete.")

summary = spark.sql(f"SELECT COUNT(*) AS total, COUNT(DISTINCT ID) AS unique_IDs FROM {delta_table}").collect()[0]
print(f"Total records: {summary['total']}, Unique IDs: {summary['unique_IDs']}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
