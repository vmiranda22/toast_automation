[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "flattened_hours_DataDestination", IsNewTarget = true], Settings = [Kind = "Manual", AllowCreation = true, ColumnSettings = [Mappings = {[SourceColumnName = "Date", DestinationColumnName = "Date"], [SourceColumnName = "Year", DestinationColumnName = "Year"], [SourceColumnName = "Month", DestinationColumnName = "Month"], [SourceColumnName = "MonthName", DestinationColumnName = "MonthName"], [SourceColumnName = "Day", DestinationColumnName = "Day"], [SourceColumnName = "Weekday", DestinationColumnName = "Weekday"], [SourceColumnName = "WeekdayName", DestinationColumnName = "WeekdayName"], [SourceColumnName = "Quarter", DestinationColumnName = "Quarter"]}], DynamicSchema = true, UpdateMethod = [Kind = "Replace"], TypeSettings = [Kind = "Table"]]]}]
shared flattened_hours = let
  Source = Lakehouse.Contents([]),
  Navigation1 = Source{[workspaceId = "b08d383a-b8cc-4b8e-b189-d9d696a01977"]}[Data],
  Navigation2 = Navigation1{[lakehouseId = "fd91a974-12de-4aed-9135-cd6bfb991855"]}[Data],
  FlattenedHours = Navigation2{[Id = "flattened_hours", ItemKind = "Table"]}[Data],
  #"Changed column type" = Table.TransformColumnTypes(FlattenedHours, {{"entryDate", type date}}),

  LatestDate = List.Max(#"Changed column type"[entryDate]),

  StartDate = Date.AddYears(LatestDate, -5),

  DateList = List.Dates(StartDate, Duration.Days(LatestDate - StartDate) + 1, #duration(1, 0, 0, 0)),
  CalendarTable = Table.FromList(DateList, Splitter.SplitByNothing(), {"Date"}),

  AddYear = Table.AddColumn(CalendarTable, "Year", each Date.Year([Date]), Int64.Type),
  AddMonth = Table.AddColumn(AddYear, "Month", each Date.Month([Date]), Int64.Type),
  AddMonthName = Table.AddColumn(AddMonth, "MonthName", each Date.ToText([Date], "MMMM"), type text),
  AddDay = Table.AddColumn(AddMonthName, "Day", each Date.Day([Date]), Int64.Type),
  AddWeekday = Table.AddColumn(AddDay, "Weekday", each Date.DayOfWeek([Date]) + 1, Int64.Type),
  AddWeekdayName = Table.AddColumn(AddWeekday, "WeekdayName", each Date.ToText([Date], "dddd"), type text),
  AddQuarter = Table.AddColumn(AddWeekdayName, "Quarter", each Date.QuarterOfYear([Date]), Int64.Type),
  #"Sorted rows" = Table.Sort(AddQuarter, {{"Date", Order.Descending}}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Sorted rows", {{"Date", type date}})
in
  #"Changed column type 1";
shared flattened_hours_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false]),
  Navigation_1 = Pattern{[workspaceId = "b08d383a-b8cc-4b8e-b189-d9d696a01977"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "fd91a974-12de-4aed-9135-cd6bfb991855"]}[Data],
  TableNavigation = Navigation_2{[Id = "calendar", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
