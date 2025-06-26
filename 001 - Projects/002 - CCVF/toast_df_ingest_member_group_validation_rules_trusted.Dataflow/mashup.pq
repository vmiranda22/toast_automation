[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Table1_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared Table1 = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa-my.sharepoint.com/personal/rmontero_teladochealth_com/Documents/Power_Automate/Client_Configuration_Validation_Framework/validation_rules.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "Table1", Kind = "Table"]}[Data],
  #"Changed column type" = Table.TransformColumnTypes(#"Navigation 1", {{"id", Int64.Type}, {"rule_name", type text}, {"admin_organization_id", type text}, {"field_name", type text}, {"expected_value", type text}, {"comparison_operator", type text}, {"condition_expression", type text}, {"priority", Int64.Type}, {"active", type logical}, {"created_at", type datetime}, {"created_by", type text}, {"is_dependent", type logical}, {"system", type text}, {"rule_scope", type text}, {"salesforce_lcrm_account_id", type text}})
in
  #"Changed column type";
shared Table1_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false]),
  Navigation_1 = Pattern{[workspaceId = "b08d383a-b8cc-4b8e-b189-d9d696a01977"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "e29a63e5-b594-4b3c-a005-d9dd6019942a"]}[Data],
  TableNavigation = Navigation_2{[Id = "memger_group_validation_rules_trusted", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
