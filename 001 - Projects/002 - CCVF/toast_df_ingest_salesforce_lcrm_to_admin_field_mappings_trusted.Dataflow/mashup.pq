[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Table1_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared Table1 = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa-my.sharepoint.com/personal/rmontero_teladochealth_com/Documents/Power_Automate/Client_Configuration_Validation_Framework/salesforce_lcrm_to_admin_field_mappings.xlsx"), null, true),
  Navigation = Source{[Item = "Table1", Kind = "Table"]}[Data],
  #"Changed column type" = Table.TransformColumnTypes(Navigation, {{"id", Int64.Type}, {"salesforce_lcrm_object", type text}, {"salesforce_lcrm_field_name", type text}, {"salesforce_lcrm_field_friendly_name", type text}, {"admin_field_name", type text}, {"admin_field_friendly_name", type text}})
in
  #"Changed column type";
shared Table1_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false]),
  Navigation_1 = Pattern{[workspaceId = "b08d383a-b8cc-4b8e-b189-d9d696a01977"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "e29a63e5-b594-4b3c-a005-d9dd6019942a"]}[Data],
  TableNavigation = Navigation_2{[Id = "salesforce_lcrm_to_admin_field_mappings_trusted", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
