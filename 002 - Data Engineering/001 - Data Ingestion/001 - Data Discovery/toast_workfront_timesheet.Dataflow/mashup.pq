[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
shared Query = let
  Source = Json.Document(Web.Contents("https://teladochealth.my.workfront.com/attask/api/v19.0/timesheet/search?apiKey=al7s4u94ggluu08vnh7atni3p5sagebm&fields=*")),
  #"Converted to table" = Table.FromRecords({Source}),
  #"Expanded data" = Table.ExpandListColumn(#"Converted to table", "data"),
  #"Expanded data1" = Table.ExpandRecordColumn(#"Expanded data", "data", {"ID", "displayName", "objCode", "approverCanEditHours", "approverID", "customerID", "endDate", "extRefID", "hasNotes", "hoursDuration", "isOvertimeDisabled", "lastNoteID", "lastUpdateDate", "lastUpdatedByID", "overtimeHours", "regularHours", "startDate", "status", "timesheetProfileID", "totalDays", "totalHours", "userID"}, {"data.ID", "data.displayName", "data.objCode", "data.approverCanEditHours", "data.approverID", "data.customerID", "data.endDate", "data.extRefID", "data.hasNotes", "data.hoursDuration", "data.isOvertimeDisabled", "data.lastNoteID", "data.lastUpdateDate", "data.lastUpdatedByID", "data.overtimeHours", "data.regularHours", "data.startDate", "data.status", "data.timesheetProfileID", "data.totalDays", "data.totalHours", "data.userID"}),
  #"Changed column type" = Table.TransformColumnTypes(#"Expanded data1", {{"data.ID", type text}, {"data.displayName", type text}, {"data.objCode", type text}, {"data.approverCanEditHours", type logical}, {"data.approverID", type text}, {"data.customerID", type text}, {"data.endDate", type date}, {"data.hasNotes", type logical}, {"data.hoursDuration", Int64.Type}, {"data.isOvertimeDisabled", type logical}, {"data.lastUpdateDate", type text}, {"data.lastUpdatedByID", type text}, {"data.overtimeHours", Int64.Type}, {"data.regularHours", type number}, {"data.startDate", type date}, {"data.status", type text}, {"data.timesheetProfileID", type text}, {"data.totalDays", type number}, {"data.totalHours", type number}, {"data.userID", type text}})
in
  #"Changed column type";
