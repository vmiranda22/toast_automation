[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "TOP_25_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared TOP_25 = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa-my.sharepoint.com/personal/rmontero_teladochealth_com/Documents/top_25_clients.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "TOP_25", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"Org ID", type text}, {"Client Name", type text}, {"Org Name", type text}})
in
  #"Changed column type";
shared TOP_25_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false]),
  Navigation_1 = Pattern{[workspaceId = "b08d383a-b8cc-4b8e-b189-d9d696a01977"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "4b9a8e2d-64db-464e-b218-053f22ac13b1"]}[Data],
  TableNavigation = Navigation_2{[Id = "top_25_clients", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
