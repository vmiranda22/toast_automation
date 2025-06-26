[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
shared Allied = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "Allied", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Organization ID", Int64.Type}, {"Livongo Client Code Check", type text}, {"Livongo Registration Code Check", type text}, {"Enable Chronic Care Referrals", type text}, {"Enable Livongo Combined Eligibility", type text}, {"SLA Waive Visit Fee", type text}, {"OneApp Access", type text}, {"Cross Billing", type text}, {"Primary Registration", type text}, {"Dependent Registration", type text}, {"Consult Reimbursement Method 1", type text}, {"Consult Reimbursement Method 2", type text}, {"Card Name", type text}, {"Bill To", type text}, {"Group (Billing) Membership Fee Type", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Amount", type number}, {"Membership Fee Type", type text}, {"Payer", type text}, {"Min Age", Int64.Type}, {"Max Age", Int64.Type}, {"Bundle Type", type text}, {"Notes", type text}, {"Consult Reimbursement Method additional details:", type text}})
in
  #"Changed column type";
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Empire Life of Canada_DataDestination", IsNewTarget = true], Settings = [Kind = "Manual", AllowCreation = true, ColumnSettings = [Mappings = {[SourceColumnName = "ID", DestinationColumnName = "ID"], [SourceColumnName = "Organization ID", DestinationColumnName = "Organization_ID"], [SourceColumnName = "Bill To", DestinationColumnName = "Bill_To"], [SourceColumnName = "Service Specialty Feature", DestinationColumnName = "Service_Specialty_Feature"], [SourceColumnName = "Fee Name", DestinationColumnName = "Fee_Name"], [SourceColumnName = "Amount", DestinationColumnName = "Amount"], [SourceColumnName = "Membership Fee Type", DestinationColumnName = "Membership_Fee_Type"], [SourceColumnName = "Reference", DestinationColumnName = "Reference"]}], DynamicSchema = true, UpdateMethod = [Kind = "Replace"], TypeSettings = [Kind = "Table"]]]}]
shared #"Empire Life of Canada" = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "Empire Life of Canada", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Organization ID", type text}, {"Bill To", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Amount", type number}, {"Membership Fee Type", type text}, {"Reference", type text}})
in
  #"Changed column type";
shared Meritain = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "Meritain", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Organization ID", Int64.Type}, {"Livongo Client Code Check", type text}, {"Livongo Registration Code Check", type text}, {"Enable Chronic Care Referrals", type text}, {"Enable Livongo Combined Eligibility", type text}, {"SLA Waive Visit Fee", type text}, {"OneApp Access", type text}, {"Cross Billing", type text}, {"Consult Reimbursement Method", type text}, {"Card Name", type text}, {"Bill To", type text}, {"Group (Billing) Membership Fee Type", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Amount", type number}, {"Membership Fee Type", type text}, {"Payer", type text}, {"Min Age", Int64.Type}, {"Max Age", Int64.Type}, {"Bundle Type", type text}, {"Notes", type text}})
in
  #"Changed column type";
shared #"BCBSNC ASO" = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "BCBSNC ASO", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Organization ID", Int64.Type}, {"Livongo Client Code Check", type text}, {"Livongo Registration Code Check", type text}, {"Enable Chronic Care Referrals", type text}, {"Enable Livongo Combined Eligibility", type text}, {"SLA Waive Visit Fee", type text}, {"OneApp Access", type text}, {"Cross Billing", type text}, {"Primary Registration", type text}, {"Dependent Registration", type text}, {"Consult Reimbursement Method", type text}, {"Card Name", type text}, {"Bill To", type text}, {"Group (Billing) Membership Fee Type", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Membership Fee Type", type text}, {"Payer", type text}, {"Min Age", Int64.Type}, {"Max Age", Int64.Type}, {"Bundle Type", type text}, {"Notes", type text}})
in
  #"Changed column type";
shared #"BCBSNC FI" = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "BCBSNC FI", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Livongo Client Code Check", type text}, {"Livongo Registration Code Check", type text}, {"Enable Chronic Care Referrals", type text}, {"Enable Livongo Combined Eligibility", type text}, {"SLA Waive Visit Fee", type text}, {"OneApp Access", type text}, {"Cross Billing", type text}, {"Primary Registration", type text}, {"Dependent Registration", type text}, {"Consult Reimbursement Method", type text}, {"Card Name", type text}, {"Bill To", type text}, {"Group (Billing) Membership Fee Type", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Membership Fee Type", type text}, {"Payer", type text}, {"Min Age", Int64.Type}, {"Max Age", Int64.Type}, {"Bundle Type", type text}, {"Notes", type text}})
in
  #"Changed column type";
shared BRMS = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "BRMS", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Organization ID", Int64.Type}, {"Livongo Client Code Check", type text}, {"Livongo Registration Code Check", type text}, {"Enable Chronic Care Referrals", type text}, {"Enable Livongo Combined Eligibility", type text}, {"SLA Waive Visit Fee", type text}, {"OneApp Access", type text}, {"Cross Billing", type text}, {"Primary Registration", type text}, {"Dependent Registration", type text}, {"Consult Reimbursement Method 1", type text}, {"Consult Reimbursement Method 2", type text}, {"allow_advanced_practitioner", Int64.Type}, {"Card Name", type text}, {"Bill To", type text}, {"Group (Billing) Membership Fee Type", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Amount", type number}, {"Membership Fee Type", type text}, {"Payer", type text}, {"Max Age", Int64.Type}, {"Bundle Type", type text}, {"Notes", type text}, {"Column28", type text}})
in
  #"Changed column type";
shared #"IBC ASO" = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "IBC ASO", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Organization ID", Int64.Type}, {"Livongo Client Code Check", type text}, {"Livongo Registration Code Check", type text}, {"Enable Chronic Care Referrals", type text}, {"Enable Livongo Combined Eligibility", type text}, {"SLA Waive Visit Fee", type text}, {"OneApp Access", type text}, {"Cross Billing", type text}, {"Primary Registration", type text}, {"Dependent Registration", type text}, {"Consult Reimbursement Method", type text}, {"allow_advanced_practitioner", Int64.Type}, {"Line of Business", type text}, {"Card Name", type text}, {"Bill To", type text}, {"Group (Billing) Membership Fee Type", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Amount", type number}, {"Membership Fee Type", type text}, {"Min Age", Int64.Type}, {"Max Age", Int64.Type}, {"Bundle Type", type text}, {"Payer", type text}, {"PAYERS", type text}})
in
  #"Changed column type";
shared #"IBC Medicare" = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "IBC Medicare", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Organization ID", Int64.Type}, {"Livongo Client Code Check", type text}, {"Livongo Registration Code Check", type text}, {"Card Name", type text}, {"Bill To", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Amount", type number}, {"Membership Fee Type", type text}, {"Min Age", Int64.Type}, {"Max Age", Int64.Type}, {"Bundle Type", type text}})
in
  #"Changed column type";
shared HealthJoy = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "HealthJoy", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Organization ID", Int64.Type}, {"Livongo Client Code Check", type text}, {"Livongo Registration Code Check", type text}, {"Enable Chronic Care Referrals", type text}, {"Enable Livongo Combined Eligibility", type text}, {"SLA Waive Visit Fee", type text}, {"OneApp Access", type text}, {"Cross Billing", type text}, {"Primary Registration", type text}, {"Dependent Registration", type text}, {"Consult Reimbursement Method", type text}, {"Card Name", type text}, {"Bill To", type text}, {"Group (Billing) Membership Fee Type", type text}, {"Dual Access", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Amount", type number}, {"Membership Fee Type", type text}, {"Payer", type text}, {"Min Age", Int64.Type}, {"Max Age", Int64.Type}, {"Bundle Type", type text}, {"Notes", type text}, {"Payer (original Liz)", type text}, {"Payers", type text}})
in
  #"Changed column type";
shared #"G&A" = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "G&A", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Organization ID", Int64.Type}, {"Livongo Client Code Check", type text}, {"Livongo Registration Code Check", type text}, {"Enable Chronic Care Referrals", type text}, {"Enable Livongo Combined Eligibility", type text}, {"SLA Waive Visit Fee", type text}, {"OneApp Access", type text}, {"Cross Billing", type text}, {"Primary Registration", type text}, {"Dependent Registration", type text}, {"Consult Reimbursement Method", type text}, {"allow_advanced_practitioner", Int64.Type}, {"Card Name", type text}, {"Bill To", type text}, {"Group (Billing) Membership Fee Type", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Amount", type number}, {"Membership Fee Type", type text}, {"Payer", type text}, {"Min Age", Int64.Type}, {"Max Age", Int64.Type}, {"Bundle Type", type text}})
in
  #"Changed column type";
shared HealthEZ = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "HealthEZ", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Organization ID", Int64.Type}, {"Livongo Client Code Check", type text}, {"Livongo Registration Code Check", type text}, {"Enable Chronic Care Referrals", type text}, {"Enable Livongo Combined Eligibility", type text}, {"SLA Waive Visit Fee", type text}, {"OneApp Access", type text}, {"Cross Billing", type text}, {"Primary Registration", type text}, {"Dependent Registration", type text}, {"Consult Reimbursement Method", type text}, {"allow_advanced_practitioner", Int64.Type}, {"Card Name", type text}, {"Bill To", type text}, {"Group (Billing) Membership Fee Type", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Amount", type number}, {"Membership Fee Type", type text}, {"Payer 1", type text}, {"Payer 2", type text}, {"Min Age", Int64.Type}, {"Max Age", Int64.Type}, {"Bundle Type", type text}, {"Notes", type text}})
in
  #"Changed column type";
shared Nippon = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "Nippon", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Organization ID", Int64.Type}, {"Livongo Client Code Check", type text}, {"Livongo Registration Code Check", type text}, {"Enable Chronic Care Referrals", type text}, {"Enable Livongo Combined Eligibility", type text}, {"OneApp Access", type text}, {"SLA Waive Visit Fee", type text}, {"Cross Billing", type text}, {"Primary Registration", type text}, {"Dependent Registration", type text}, {"Consult Reimbursement Method", type text}, {"allow_advanced_practitioner", Int64.Type}, {"Card Name", type text}, {"Bill To", type text}, {"Group (Billing) Membership Fee Type", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Amount", type number}, {"Membership Fee Type", type text}, {"Payer", type text}, {"Min Age", Int64.Type}, {"Max Age", Int64.Type}, {"Bundle Type", type text}, {"Notes", type text}})
in
  #"Changed column type";
shared Nextep = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "Nextep", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Organization ID", Int64.Type}, {"Livongo Client Code Check", type text}, {"Livongo Registration Code Check", type text}, {"Enable Chronic Care Referrals", type text}, {"Enable Livongo Combined Eligibility", type text}, {"OneApp Access", type text}, {"SLA Waive Visit Fee", type text}, {"Cross Billing", type text}, {"Primary Registration", type text}, {"Dependent Registration", type text}, {"Consult Reimbursement Method", type text}, {"allow_advanced_practitioner", Int64.Type}, {"Card Name", type text}, {"Bill To", type text}, {"Group (Billing) Membership Fee Type", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Amount", type number}, {"Membership Fee Type", type text}, {"Min Age", Int64.Type}, {"Max Age", Int64.Type}, {"Bundle Type", type text}, {"Notes", type text}})
in
  #"Changed column type";
shared #"Ben Intel" = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "Ben Intel", Kind = "Sheet"]}[Data]
in
  #"Navigation 1";
shared GMS = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "GMS", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Organization ID", Int64.Type}, {"Livongo Client Code Check", type text}, {"Livongo Registration Code Check", type text}, {"Enable Chronic Care Referrals", type text}, {"Enable Livongo Combined Eligibility", type text}, {"SLA Waive Visit Fee", type text}, {"OneApp Access", type text}, {"Cross Billing", type text}, {"Primary Registration", type text}, {"Dependent Registration", type text}, {"Consult Reimbursement Method", type text}, {"allow_advanced_practitioner", Int64.Type}, {"Card Name", type text}, {"Bill To", type text}, {"Group (Billing) Membership Fee Type", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Amount", type number}, {"Membership Fee Type", type text}, {"Payer", type text}, {"Min Age", Int64.Type}, {"Max Age", Int64.Type}, {"Bundle Type", type text}})
in
  #"Changed column type";
shared #"Lucent NAA" = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "Lucent NAA", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Organization ID", Int64.Type}, {"Livongo Client Code Check", type text}, {"Livongo Registration Code Check", type text}, {"Enable Chronic Care Referrals", type text}, {"Enable Livongo Combined Eligibility", type text}, {"SLA Waive Visit Fee", type text}, {"OneApp Access", type text}, {"Cross Billing", type text}, {"Primary Registration", type text}, {"Dependent Registration", type text}, {"Consult Reimbursement Method 1", type text}, {"Consult Reimbursement Method 2", type text}, {"allow_advanced_practitioner", Int64.Type}, {"Card Name", type text}, {"Bill To", type text}, {"Group (Billing) Membership Fee Type", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Amount", type number}, {"Membership Fee Type", type text}, {"Payer", type text}, {"Min Age", Int64.Type}, {"Max Age", Int64.Type}, {"Bundle Type", type text}, {"Notes", type text}, {"Column28", type text}})
in
  #"Changed column type";
shared Elan = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "Elan", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Organization ID", Int64.Type}, {"Livongo Client Code Check", type text}, {"Livongo Registration Code Check", type text}, {"Enable Chronic Care Referrals", type text}, {"Enable Livongo Combined Eligibility", type text}, {"SLA Waive Visit Fee", type text}, {"OneApp Access", type text}, {"Cross Billing", type text}, {"Primary Registration", type text}, {"Dependent Registration", type text}, {"Consult Reimbursement Method", type text}, {"allow_advanced_practitioner", Int64.Type}, {"Card Name", type text}, {"Bill To", type text}, {"Group (Billing) Membership Fee Type", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Amount", type number}, {"Membership Fee Type", type text}, {"Payer", type text}, {"Min Age", Int64.Type}, {"Max Age", Int64.Type}, {"Bundle Type", type text}, {"Notes", type text}})
in
  #"Changed column type";
shared Humania = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "Humania", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Organization ID", Int64.Type}, {"Livongo Client Code Check", type text}, {"Livongo Registration Code Check", type text}, {"Enable Chronic Care Referrals", type text}, {"Enable Livongo Combined Eligibility", type text}, {"SLA Waive Visit Fee", type text}, {"OneApp Access", type text}, {"Cross Billing", type text}, {"Primary Registration", type text}, {"Dependent Registration", type text}, {"Consult Reimbursement Method", type text}, {"allow_advanced_practitioner", Int64.Type}, {"Card Name", type text}, {"Bill To", type text}, {"Group (Billing) Membership Fee Type", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Amount", type number}, {"Membership Fee Type", type text}, {"Payer", type text}, {"Min Age", Int64.Type}, {"Max Age", Int64.Type}, {"Bundle Type", type text}})
in
  #"Changed column type";
shared #"IBC original" = let
  Source = Excel.Workbook(Web.Contents("https://teladocpa.sharepoint.com/sites/TechnicalBenefitsAdministrationEligibilityImplementation/Shared%20Documents/Flow%201B/SOT%20-%20Reports.xlsx"), null, true),
  #"Navigation 1" = Source{[Item = "IBC original", Kind = "Sheet"]}[Data],
  #"Promoted headers" = Table.PromoteHeaders(#"Navigation 1", [PromoteAllScalars = true]),
  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"ID", Int64.Type}, {"Organization ID", Int64.Type}, {"Livongo Client Code Check", type text}, {"Livongo Registration Code Check", type text}, {"Card Name", type text}, {"Bill To", type text}, {"Service Specialty Feature", type text}, {"Fee Name", type text}, {"Amount", type number}, {"Membership Fee Type", type text}, {"Min Age", Int64.Type}, {"Max Age", Int64.Type}, {"Bundle Type", type text}})
in
  #"Changed column type";
shared #"Empire Life of Canada_DataDestination" = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false]),
  Navigation_1 = Pattern{[workspaceId = "b08d383a-b8cc-4b8e-b189-d9d696a01977"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "4b9a8e2d-64db-464e-b218-053f22ac13b1"]}[Data],
  TableNavigation = Navigation_2{[Id = "excel_sot_empire_life_of_canada", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
