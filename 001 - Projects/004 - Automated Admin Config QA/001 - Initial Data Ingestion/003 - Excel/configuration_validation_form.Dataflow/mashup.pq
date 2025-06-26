[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Sheet1_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared Sheet1 = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa-my.sharepoint.com/personal/rmontero_teladochealth_com/Documents/Configuration%20Validation%20Form.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "Sheet1", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"Id", type text}, {"Start time", type text}, {"Completion time", type text}, {"Email", type text}, {"Name", type text}, {"Case ID", type text}, {"Tech Analyst/Owner", type text}, {"Have you found errors in the configuration?", type text}, {"Number of groups with errors (please add NASF count to Salesforce if not available)", type text}, {"Errors Detected ", type text}, {"Admin Error", type text}, {"Error Detail", type text}, {"Admin Error1", type text}, {"Error Detail1", type text}, {"Admin Error2", type text}, {"Error Detail2", type text}, {"Admin Error3", type text}, {"Error Detail3", type text}, {"Admin Error4", type text}, {"Error Detail4", type text}, {"Admin Error5", type text}, {"Error Detail5", type text}, {"Admin Error6", type text}, {"Error Detail6", type text}, {"Admin Error7", type text}, {"Error Detail7", type text}, {"Admin Error8", type text}, {"Error Detail8", type text}, {"Admin Error9", type text}, {"Error Detail9", type text}, {"For incorrect pricing, please indicate Product (copy/paste from Admin)", type text}, {"For incorrect pricing, please indicate Product incorrect fee", type text}, {"For incorrect pricing, please select the product's effective date in Admin at the time of the review", type text}, {"For incorrect pricing, please select the correct pricing in accordance with the NASF", type text}, {"For incorrect pricing, please select the effective date since price correction", type text}, {"Error Detail10", type text}, {"Salesforce", type text}, {"Admin Error10", type text}, {"Error Detail11", type text}})
in
  #"Changed column type";
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "OfficeForms Table_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared #"OfficeForms Table" = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa-my.sharepoint.com/personal/rmontero_teladochealth_com/Documents/Configuration%20Validation%20Form.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "OfficeForms.Table", Kind = "Table"]}[Data],
  #"Changed column type" = Table.TransformColumnTypes(#"Navigation 1", {{"Id", Int64.Type}, {"Start time", type datetime}, {"Completion time", type datetime}, {"Email", type text}, {"Name", type text}, {"Case ID", Int64.Type}, {"Tech Analyst/Owner", type text}, {"Have you found errors in the configuration?", type text}, {"Number of groups with errors (please add NASF count to Salesforce if not available)", Int64.Type}, {"Errors Detected ", type text}, {"Admin Error", type text}, {"Error Detail", type text}, {"Admin Error2", type text}, {"Error Detail2", type text}, {"Admin Error3", type text}, {"Error Detail3", type text}, {"Admin Error4", type text}, {"Error Detail4", type text}, {"Admin Error5", type text}, {"Error Detail5", type text}, {"Admin Error6", type text}, {"Error Detail6", type text}, {"Admin Error7", type text}, {"Error Detail7", type text}, {"Admin Error9", type text}, {"Error Detail9", type text}, {"For incorrect pricing, please indicate Product (copy/paste from Admin)", type text}, {"For incorrect pricing, please indicate Product incorrect fee", Int64.Type}, {"For incorrect pricing, please select the product's effective date in Admin at the time of the review", type date}, {"For incorrect pricing, please select the correct pricing in accordance with the NASF", Int64.Type}, {"For incorrect pricing, please select the effective date since price correction", type date}})
in
  #"Changed column type";
shared #"OfficeForms Table_DataDestination" = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false]),
  Navigation_1 = Pattern{[workspaceId = "b08d383a-b8cc-4b8e-b189-d9d696a01977"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "4b9a8e2d-64db-464e-b218-053f22ac13b1"]}[Data],
  TableNavigation = Navigation_2{[Id = "OfficeForms Table", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
shared Sheet1_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false]),
  Navigation_1 = Pattern{[workspaceId = "b08d383a-b8cc-4b8e-b189-d9d696a01977"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "4b9a8e2d-64db-464e-b218-053f22ac13b1"]}[Data],
  TableNavigation = Navigation_2{[Id = "configuration_validation_form", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
