[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Payers Admin Salesforce Match_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared #"Payers Admin Salesforce Match" = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalImplementation/Shared%20Documents/Documents/Flow%201B/GAB%20-%20Processing/Payers%20-%20Admin%20Salesforce%20Match.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "Payers Admin Salesforce Match", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ADMIN Payer ID", Int64.Type}, {"ADMIN Payer Name", type text}, {"SALESFORCE Account ID", type text}, {"SALESFORCE Account Name", type text}, {"Column5", type text}, {"Column6", type text}, {"Column7", type text}, {"Column8", type text}}),
  #"Renamed columns" = Table.RenameColumns(#"Changed column type", {{"ADMIN Payer ID", "admin_payer_id"}, {"ADMIN Payer Name", "admin_payer_name"}, {"SALESFORCE Account ID", "salesforce_account_id"}, {"SALESFORCE Account Name", "salesforce_account_name"}}),
  #"Filtered rows" = Table.SelectRows(#"Renamed columns", each ([salesforce_account_id] <> null and [salesforce_account_id] <> "N/A")),
  #"Extracted first characters" = Table.TransformColumns(#"Filtered rows", {{"salesforce_account_id", each Text.Start(_, 15), type text}}),
  #"Removed columns" = Table.RemoveColumns(#"Extracted first characters", {"Column5", "Column6", "Column7", "Column8"})
in
  #"Removed columns";
shared #"Payers Admin Salesforce Match_DataDestination" = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false]),
  Navigation_1 = Pattern{[workspaceId = "b08d383a-b8cc-4b8e-b189-d9d696a01977"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "5c03804a-6817-4f61-bdd3-d666573c958a"]}[Data],
  TableNavigation = Navigation_2{[Id = "sp_excel_gab_admin_payers_to_salesforce", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
