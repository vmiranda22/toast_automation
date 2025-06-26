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
    "actualCompletionDate", "actualStartDate", "approvalCompletionDate",
    "approvalEstStartDate", "approvalPlannedStartDate", "approvalProjectedStartDate",
    "approvalStartDate", "commitDate", "completionPendingDate", "constraintDate",
    "convertedOpTaskEntryDate", "entryDate", "estCompletionDate", "estStartDate",
    "fixedEndDate", "fixedStartDate", "handoffDate", "lastUpdateDate",
    "nextAutoBaselineDate", "plannedCompletionDate", "plannedStartDate",
    "projectedCompletionDate", "projectedStartDate", "slackDate"
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
    "ID", "name", "objCode", "URL", "actualBillableExpenseCost", "actualCompletionDate", "actualCost",
    "actualDuration", "actualDurationMinutes", "actualExpenseCost", "actualLaborCost", "actualNonBillableExpenseCost",
    "actualRevenue", "actualRiskCost", "actualStartDate", "actualValue", "actualWork", "actualWorkRequired",
    "approvalCompletionDate", "approvalEstStartDate", "approvalPlannedStartDate", "approvalProcessID",
    "approvalProjectedStartDate", "approvalStartDate", "assignedToID", "auditTypes", "autoBaselineRecurrenceType",
    "autoBaselineRecurOn", "bcwp", "bcws", "billingAmount", "billingRecordID", "canStart", "categoryID", "color",
    "commitDate", "completionPendingDate", "condition", "conditionType", "constraintDate", "convertedOpTaskEntryDate",
    "convertedOpTaskName", "convertedOpTaskOriginatorID", "costAmount", "costType", "cpi", "csi", "currency",
    "currentApprovalStepID", "customerID", "description", "displayOrder", "duration", "durationType", "durationUnit",
    "eac", "eacCalculationMethod", "enteredByID", "entryDate", "estCompletionDate", "estStartDate", "extRefID",
    "filterHourTypes", "fixedCost", "fixedEndDate", "fixedRevenue", "fixedStartDate", "groupID", "handoffDate",
    "hasBudgetConflict", "hasCalcError", "hasCompletionConstraint", "hasDocuments", "hasExpenses", "hasMessages",
    "hasNotes", "hasRateOverride", "hasResolvables", "hasStartConstraint", "hasTimedNotifications",
    "hasTimelineException", "hoursPerPoint", "indent", "isAgile", "isCritical", "isDurationLocked",
    "isLevelingExcluded", "isOriginalPlannedHoursSet", "isReady", "isStatusComplete", "isWorkRequiredLocked",
    "iterationID", "kanbanBoardID", "kanbanFlag", "lastConditionNoteID", "lastNoteID", "lastUpdateDate",
    "lastUpdatedByID", "levelingMode", "levelingStartDelay", "levelingStartDelayMinutes", "milestoneID",
    "milestonePathID", "nextAutoBaselineDate", "numberOfChildren", "numberOpenOpTasks", "optimizationScore",
    "originalDuration", "originalWorkRequired", "ownerID", "ownerPrivileges", "pendingCalculation",
    "pendingUpdateMethods", "percentComplete", "performanceIndexMethod", "personal", "plannedBenefit",
    "plannedBillableExpenseCost", "plannedCompletionDate", "plannedCost", "plannedDuration",
    "plannedDurationMinutes", "plannedExpenseCost", "plannedLaborCost", "plannedNonBillableExpenseCost",
    "plannedRevenue", "plannedRiskCost", "plannedStartDate", "plannedValue", "popAccountID", "portfolioID",
    "portfolioPriority", "previousStatus", "priority", "programID", "progressStatus", "projectID",
    "projectedCompletionDate", "projectedDurationMinutes", "projectedStartDate", "queueDefID", "referenceNumber",
    "rejectionIssueID", "remainingDurationMinutes", "resourceScope", "revenueType", "roleID", "securityRootID",
    "securityRootObjCode", "slackDate", "spi", "status", "statusUpdate", "storyPoints", "submittedByID",
    "taskConstraint", "taskNumber", "teamID", "templateTaskID", "trackingMode", "version", "wbs", "work",
    "workEffort", "workRequired"
]

parameter_columns_raw = [
    "parameterValues.DE:Change Timeline", "parameterValues.DE:Client Facing",
    "parameterValues.DE:On Time Status", "parameterValues.DE:Current Due Date",
    "parameterValues.DE:Planned Completion No Time", "parameterValues.DE:Partner Contract Path",
    "parameterValues.DE:Disqualifiers & Concerns", "parameterValues.DE:Client Eligibility Type",
    "parameterValues.DE:Client Manager", "parameterValues.DE:Migration Category at Migration",
    "parameterValues.DE:TPM Lead", "parameterValues.DE:Client or Access Code",
    "parameterValues.DE:Invited to Migrate", "parameterValues.DE:Client Agreed For Migration",
    "parameterValues.DE:Migration Category", "parameterValues.DE:MyS Guage Count As",
    "parameterValues.DE:Date Preference For Migration"
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
empty_df.write.format("delta").mode("ignore").saveAsTable("workfront_task_raw")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
