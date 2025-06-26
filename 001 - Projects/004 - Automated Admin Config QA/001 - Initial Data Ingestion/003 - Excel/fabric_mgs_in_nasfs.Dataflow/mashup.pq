[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "_table_mgs_in_nasfs_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared _table_mgs_in_nasfs = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/ToolsAndAutomation/Documentation/Automated%20QA%20on%20Fabric/Fabric_MGs_in_NASFs.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "_table_mgs_in_nasfs", Kind = "Table"]}[Data],
  #"Changed column type" = Table.TransformColumnTypes(#"Navigation 1", {{"Case Link", type text}, {"Case ID", type text}, {"Case Number", Int64.Type}, {"NASF Title", type text}, {"NASF Group Count", Int64.Type}, {"Member Group Link", type text}, {"Member Group ID", type text}, {"Member Group Number", type text}, {"Member Group Name", type text}, {"Legacy Group ID", Int64.Type}, {"Flow Run Date", type datetime}, {"Flow Run Link", type text}, {"Processed", type text}, {"Status", type text}, {"Primary Request Type", type text}})
in
  #"Changed column type";
shared _table_mgs_in_nasfs_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false]),
  Navigation_1 = Pattern{[workspaceId = "b08d383a-b8cc-4b8e-b189-d9d696a01977"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "4b9a8e2d-64db-464e-b218-053f22ac13b1"]}[Data],
  TableNavigation = Navigation_2{[Id = "excel_member_groups_in_nasfs", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
