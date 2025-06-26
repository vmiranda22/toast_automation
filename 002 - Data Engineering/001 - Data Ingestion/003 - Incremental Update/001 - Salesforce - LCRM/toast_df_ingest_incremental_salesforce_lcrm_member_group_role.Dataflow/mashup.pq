[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Member Group Role_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared #"Member Group Role" = let
  Source = Salesforce.Data("https://login.salesforce.com/", [ApiVersion = 48]),
  Navigation = Source{[Name = "Mbr_Group_Role__c"]}[Data],
  #"Filtered rows" = Table.SelectRows(Navigation, each DateTime.IsInPreviousNMinutes([SystemModstamp], 10080))
in
  #"Filtered rows";
shared #"Member Group Role_DataDestination" = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false]),
  Navigation_1 = Pattern{[workspaceId = "b08d383a-b8cc-4b8e-b189-d9d696a01977"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "a852188b-a853-4fd2-b6fb-541fa5469293"]}[Data],
  TableNavigation = Navigation_2{[Id = "salesforce_lcrm_member_group_role_raw_recent", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
