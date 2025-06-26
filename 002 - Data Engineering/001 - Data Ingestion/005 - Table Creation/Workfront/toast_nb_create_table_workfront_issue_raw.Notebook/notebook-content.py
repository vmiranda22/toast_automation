# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "858ad52b-f017-4d74-9957-17175dd47103",
# META       "default_lakehouse_name": "toast_lh_workfront_raw",
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977",
# META       "known_lakehouses": [
# META         {
# META           "id": "858ad52b-f017-4d74-9957-17175dd47103"
# META         }
# META       ]
# META     },
# META     "warehouse": {
# META       "default_warehouse": "0d50be10-2e1a-4c74-a4e8-d8819668d36b",
# META       "known_warehouses": [
# META         {
# META           "id": "0d50be10-2e1a-4c74-a4e8-d8819668d36b",
# META           "type": "Lakewarehouse"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql.functions import sha2, concat_ws, col
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, ArrayType
from collections import defaultdict
import re

spark = SparkSession.builder.getOrCreate()

timestamp_columns_raw = {
    "actualCompletionDate", "actualStartDate", "approvalCompletionDate", "approvalStartDate",
    "autoClosureDate", "commitDate", "entryDate", "lastUpdateDate", "plannedCompletionDate", 
    "plannedStartDate"
}

array_columns_raw = {"auditTypes"}

def sanitize_column(name, used_names, suffix_counter):
    sanitized = re.sub(r"[^\w]", "_", name).lower()
    base = sanitized
    while sanitized in used_names:
        suffix_counter[base] += 1
        sanitized = f"{base}_{suffix_counter[base]}"
    used_names.add(sanitized)
    return sanitized

base_columns_raw = [
    "ID", "name", "objCode", "actualCompletionDate", "actualCost", "actualStartDate", "actualWorkRequired",
    "approvalCompletionDate", "approvalProcessID", "approvalStartDate", "assignedToID", "auditTypes",
    "autoClosureDate", "backlogOrder", "categoryID", "color", "commitDate", "condition",
    "currentApprovalStepID", "customerID", "description", "enteredByID", "entryDate", "extRefID",
    "hasDocuments", "hasMessages", "hasNotes", "hasResolvables", "hasTimedNotifications", "isComplete",
    "isHelpDesk", "isReady", "iterationID", "kanbanBoardID", "lastConditionNoteID", "lastNoteID",
    "lastUpdateDate", "lastUpdatedByID", "opTaskType", "ownerID", "percentComplete", "plannedCompletionDate",
    "plannedDurationMinutes", "plannedStartDate", "previousStatus", "priority", "projectID",
    "projectedDurationMinutes", "queueTopicID", "referenceNumber", "remainingDurationMinutes",
    "resolveOpTaskID", "resolveProjectID", "resolveTaskID", "resolvingObjCode", "resolvingObjID",
    "roleID", "securityRootID", "securityRootObjCode", "severity", "sourceObjCode", "sourceObjID",
    "sourceTaskID", "status", "statusUpdate", "storyBoardOrder", "storyPoints", "submittedByID",
    "teamID", "url", "version", "work", "workRequired"
]

parameter_columns_raw = [
    "parameterValues.DE:BT - Regulatory Score",
    "parameterValues.DE:Ready to be Evaluated?",
    "parameterValues.DE:BT - Number of Systems Impacted",
    "parameterValues.DE:BT - Total Systems",
    "parameterValues.DE:BT - OKR 1 Score",
    "parameterValues.DE:BT - What Work If Any Has Been Completed to Date?",
    "parameterValues.DE:BT - Systems Impacted Score",
    "parameterValues.DE:BT - Business Continuity Score",
    "parameterValues.DE:BT - Total Benefit Score",
    "parameterValues.DE:Which channels will this ad appear in?",
    "parameterValues.DE:Will  you need copy to go with this asset?",
    "parameterValues.DE:Channel Deliverable - Display",
    "parameterValues.DE:Channel Deliverables - LinkedIn",
    "parameterValues.DE:If other, please note below",
    "parameterValues.DE:BT - Team Name",
    "parameterValues.DE:Who will be impacted by this project?",
    "parameterValues.DE:What areas may be impacted by this project?",
    "parameterValues.DE:BT - Project Executive Sponsor - SVP/ELT Level",
    "parameterValues.DE:BT - Level of Change Score",
    "parameterValues.DE:BT - Region",
    "parameterValues.DE:BT - Background and Current State Challenges",
    "parameterValues.DE:BT - OKR 4 Score",
    "parameterValues.DE:BT - Total Score",
    "parameterValues.DE:BT - Total Complexity Score",
    "parameterValues.DE:BT - Area of Business",
    "parameterValues.DE:BT - Is this request confidential?",
    "parameterValues.DE:BT - Timeline/Urgency",
    "parameterValues.DE:BT - Project Type",
    "parameterValues.DE:BT - Project Team's experience Score",
    "parameterValues.DE:BT - OKR 2 Score",
    "parameterValues.DE:BT - Urgency Score",
    "parameterValues.DE:BT - OKR 3 Score",
    "parameterValues.DE:BT - Number of Other Systems",
    "parameterValues.DE:BT - Number of Teams Score",
    "parameterValues.DE:BT - Project Prioritization Recommendation",
    "parameterValues.DE:BT - OKR 5 Score",
    "parameterValues.DE:BT - Duration Score",
    "parameterValues.DE:BT - Business Impact Score",
    "parameterValues.DE:BT - Project Sponsor - Director/VP Level",
    "parameterValues.DE:BT - Cost Score",
    "parameterValues.DE:Brand",
    "parameterValues.DE:Is this Landing Page using an existing template?",
    "parameterValues.DE:Will speakers be highlighted on this landing page?",
    "parameterValues.DE:If yes, provide asset or job number or description",
    "parameterValues.DE:Asset size",    
    "parameterValues.DE:Will this route to Propel for legal review?",
    "parameterValues.DE:Will your project need a creative strategist?",
    "parameterValues.DE:Where will files be delivered?",
    "parameterValues.DE:Project Notes",
    "parameterValues.DE:Will this piece require translations?",
    "parameterValues.DE:Please provide # of rounds and # of days per round for client reviews",
    "parameterValues.DE:If other or notes are needed please provide below",
    "parameterValues.DE:If other collateral asset type, please note here",
    "parameterValues.DE:Is there an existing Workfront project?",
    "parameterValues.DE:What makes up the cultural and market context?",
    "parameterValues.DE:If change to existing video provide link to the video",
    "parameterValues.DE:Provide creative thought starters",
    "parameterValues.DE:Project notes",
    "parameterValues.DE:If video is net new, please provide style direction or example of styles you like",
    "parameterValues.DE:What devices will this video highlight?",
    "parameterValues.DE:How can we support this?",
    "parameterValues.DE:DM asset type",
    "parameterValues.DE:Description of changes needed",
    "parameterValues.DE:Projected Launch Date",
    "parameterValues.DE:Will this piece need to be AODA compliant?",
    "parameterValues.DE:What day does your Landing Page need to go live?",
    "parameterValues.DE:The Ask",
    "parameterValues.DE:What type of social ad is this?",
    "parameterValues.DE:What does success look like?",
    "parameterValues.DE:If other, please provide channel information",
    "parameterValues.DE:Provide where final video will live",
    "parameterValues.DE:Planned Duration",
    "parameterValues.DE:What day does your email need to deploy?",
    "parameterValues.DE:Channel Deliverables - Meta - FB + Instagram",
    "parameterValues.DE:Channel Deliverables - Twitter",
    "parameterValues.DE:Is video net new?",
    "parameterValues.DE:Are you linking to a Teladoc Health Web page or landing page?",
    "parameterValues.DE:What is the most important insight about the customer?",
    "parameterValues.DE:Please Select Line of Business",
    "parameterValues.DE:If other, provide notes below",
    "parameterValues.DE:Are we using an existing approved format?",
    "parameterValues.DE:If yes, outline your testing request below; or upload your test hypothesis at the end of this brief",
    "parameterValues.DE:If 2+ versions are chosen, please upload a version matrix at the end of this brief",
    "parameterValues.DE:Provide any related assets at the end of this brief",
    "parameterValues.DE:Where will this video be used?",
    "parameterValues.DE:Provide official video title",
    "parameterValues.DE:Will blog live on Teladoc.com HealthTalk?",
    "parameterValues.DE:Channel Deliverables - Banner",
    "parameterValues.DE:What size is your asset?",
    "parameterValues.DE:which template will we use?",
    "parameterValues.DE:Has your executive sponsor reviewed and approved this brief?",
    "parameterValues.DE:B2B - Which Services will this project feature?",
    "parameterValues.DE:Is this piece being created for a client?",
    "parameterValues.DE:How will the final assets be delivered?",
    "parameterValues.DE:Are interviews required for this blog?",
    "parameterValues.DE:How will contact list be built?",
    "parameterValues.DE:Provide file format for asset delivery",
    "parameterValues.DE:New Asset Type",
    "parameterValues.DE:Will testing be requested on this project?",
    "parameterValues.DE:Related Project",
    "parameterValues.DE:Chose your collateral asset type",
    "parameterValues.DE:Requested due date",
    "parameterValues.DE:Are any marketing materials driving to this blog?",
    "parameterValues.DE:Which Services will this project feature?",
    "parameterValues.DE:If other is chosen, provide file specifications below",
    "parameterValues.DE:What is your billing code?",
    "parameterValues.DE:Which PPT template will be used as the base?",
    "parameterValues.DE:Who will be approving the SOW?",
    "parameterValues.DE:CM- Where will files be delivered?",
    "parameterValues.DE:If routing to Propel, please provide PM codes here",
    "parameterValues.DE:Please provide existing Landing page  URL",
    "parameterValues.DE:Estimated length of requested video",
    "parameterValues.DE:Does this video have a budget?",
    "parameterValues.DE:Provide privacy settings on Vimeo/Other",
    "parameterValues.DE:What is the most important thing we want our audience to take away?",
    "parameterValues.DE:Provide the name of the client",
    "parameterValues.DE:if content is provided, by whom and when will it be delivered?",
    "parameterValues.DE:Tracking requirements",
    "parameterValues.DE:Will this piece need to route to an external client for review?",
    "parameterValues.DE:Provide the CTA for the video",
    "parameterValues.DE:Are external sources needed to support creative development?",
    "parameterValues.DE:What are the core campaign elements?.0",
    "parameterValues.DE:What are the core campaign elements?.1",
    "parameterValues.DE:UTM code for any asset that links to a TDH webpage.",
    "parameterValues.DE:How many versions of this piece will be delivered?",
    "parameterValues.DE:What enhancements/work do you want done?",
    "parameterValues.DE:Your requested due date",
    "parameterValues.DE:Line of Business",
    "parameterValues.DE:List of people to add to your proof as a reviewer",
    "parameterValues.DE:Executive Sponsor",
    "parameterValues.DE:On which system will the content asset be stored?",
    "parameterValues.DE:Has your executive sponsor approved this request?",
    "parameterValues.DE:Provide any overall information the creative team may need to execute",
    "parameterValues.DE:Will any content be provided?"
]

all_columns_raw = base_columns_raw + parameter_columns_raw + ["row_hash"]

suffix_counter = defaultdict(int)
used_names = set()
raw_to_sanitized = {
    raw: sanitize_column(raw, used_names, suffix_counter)
    for raw in all_columns_raw
}
timestamp_columns_sanitized = {
    raw_to_sanitized[f] for f in timestamp_columns_raw if f in raw_to_sanitized
}
array_columns_sanitized = {
    raw_to_sanitized[f] for f in array_columns_raw if f in raw_to_sanitized
}

schema = StructType([
    StructField(
        raw_to_sanitized[raw],
        ArrayType(StringType()) if raw_to_sanitized[raw] in array_columns_sanitized
        else TimestampType() if raw_to_sanitized[raw] in timestamp_columns_sanitized
        else StringType(),
        False if raw == "ID" else True
    )
    for raw in all_columns_raw
])

empty_df = spark.createDataFrame([], schema)
empty_df.write.format("delta").mode("ignore").saveAsTable("workfront_issue_raw")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
