# pylint: disable=line-too-long
"""
strings, dictionaries, arrays Constant
"""
EXP_EXTRACT_FLOATING = r'[-+]?\d*\.\d+|\d+'
VALUE_ERROR_EXCEPTION_RAISED = r'ValueError Raised:'
EMAIL_SUBJECT_SOIL_RELOCATION = r'SRIS Subscription Service - New Notification(s) Received (Soil Relocation)'
EMAIL_SUBJECT_HIGH_VOLUME = r'SRIS Subscription Service - New Registration(s) Received (High Volume Receiving Site)'
SOURCE_CSV_FILE = r'soil_relocation_source_sites.csv'
RECEIVE_CSV_FILE = r'soil_relocation_receiving_sites.csv'
HIGH_VOLUME_CSV_FILE = r'high_volume_receiving_sites.csv'
EMAIL_SENDER_ADDRESS = r'donotreplySRIS@gov.bc.ca'
CHES_HEALTH_200_STATUS = r'The status of CHES returned the healthy.'
CHES_HEALTH_401_STATUS = r'Access token is mission or invalid.'
CHES_HEALTH_403_STATUS = r'Lack required role to perform action.'
REGIONAL_DISTRICT_NAME_DIC = dict(regionalDistrictOfBulkleyNechako='Regional District of Bulkley-Nechako'
                                , caribooRegionalDistrict='Cariboo Regional District'
                                , regionalDistrictOfFraserFortGeorge='Regional District of Fraser-Fort George'
                                , regionalDistrictOfKitimatStikine='Regional District of Kitimat-Stikine'
                                , peaceRiverRegionalDistrict='Peace River Regional District'
                                , northCoastRegionalDistrict='North Coast Regional District'
                                , regionalDistrictOfCentralOkanagan='Regional District of Central Okanagan'
                                , fraserValleyRegionalDistrict='Fraser Valley Regional District'
                                , metroVancouverRegionalDistrict='Metro Vancouver Regional District'
                                , regionalDistrictOfOkanaganSimilkameen='Regional District of Okanagan-Similkameen'
                                , squamishLillooetRegionalDistrict='Squamish-Lillooet Regional District'
                                , thompsonNicolaRegionalDistrict='Thompson-Nicola Regional District'
                                , regionalDistrictOfCentralKootenay='Regional District of Central Kootenay'
                                , columbiaShuswapRegionalDistrict='Columbia-Shuswap Regional District'
                                , regionalDistrictOfEastKootenay='Regional District of East Kootenay'
                                , regionalDistrictOfKootenayBoundary='Regional District of Kootenay Boundary'
                                , regionalDistrictOfNorthOkanagan='Regional District of North Okanagan'
                                , regionalDistrictOfAlberniClayoquot='Regional District of Alberni-Clayoquot'
                                , capitalRegionalDistrict='Capital Regional District'
                                , centralCoastRegionalDistrict='Central Coast Regional District'
                                , comoxValleyRegionalDistrict='Comox Valley Regional District'
                                , cowichanValleyRegionalDistrict='Cowichan Valley Regional District'
                                , regionalDistrictOfNanaimo='Regional District of Nanaimo'
                                , regionalDistrictOfMountWaddington='Regional District of Mount Waddington'
                                , qathetRegionalDistrict='qathet Regional District'
                                , sunshineCoastRegionalDistrict='Sunshine Coast Regional District'
                                , strathconaRegionalDistrict='Strathcona Regional District'
                                , stikineRegionUnincorporated='Stikine Region (Unincorporated)')
SOURCE_SITE_USE_NAME_DIC = dict(a1='A1. adhesives manufacturing or bulk storage'
                                , a2='A2. chemical manufacturing or bulk storage'
                                , a3='A3. explosives or ammunition manufacturing or bulk storage'
                                , a4='A4. fire retardant manufacturing, bulk storage or shipping'
                                , a5='A5. fertilizer manufacturing, bulk storage or shipping'
                                , a6='A6. ink or dye manufacturing or bulk storage'
                                , a7='A7. leather or hides tanning'
                                , a8='A8. paint, lacquer or varnish manufacturing, formulation, recycling or bulk storage'
                                , a9='A9. pharmaceutical products, or controlled substances as defined in the Controlled Drugs and Substances Act (Canada), manufacturing or operations'
                                , a10='A10. plastic products (foam or expanded plastic) manufacturing or repurposing'
                                , none='None'
                                , a11='A11. textile dyeing'
                                , a12='A12. pesticide manufacturing, formulation, bulk storage or shipping'
                                , a13='A13. resin or plastic monomer manufacturing, formulation or bulk storage'
                                , b1='B1. battery manufacturing, recycling or bulk storage'
                                , b2='B2. facilities using equipment that contains PCBs greater than or equal to 50 ppm'
                                , b3='B3. electrical equipment manufacturing, refurbishing or bulk storage'
                                , b4='B4. electrical transmission or distribution substations'
                                , b5='B5. electronic equipment manufacturing'
                                , b6='B6. transformer oil manufacturing, processing or bulk storage'
                                , b7='B7. electrical power generating operations fueled by coal or petroleum hydrocarbons that supply electricity to a community or commercial or industrial operation, excluding emergency generators'
                                , c1='C1. foundries'
                                , c2='C2. galvanizing'
                                , c3='C3. metal plating or finishing'
                                , c4='C4. metal salvage operations'
                                , c5='C5. metal smelting or refining'
                                , c6='C6. welding or machine shops (repair or fabrication)'
                                , d1='D1. asbestos mining, milling, bulk storage or shipping'
                                , d2='D2. coal coke manufacture, bulk storage or shipping'
                                , d3='D3. coal or lignite mining, milling, bulk storage or shipping'
                                , d4='D4. milling reagent manufacture, bulk storage or shipping'
                                , d5='D5. metal concentrate bulk storage or shipping'
                                , d6='D6. metal ore mining or milling'
                                , e1='E1. appliance, equipment or engine maintenance, repair, reconditioning, cleaning or salvage'
                                , e2='E2. ash deposit from boilers, incinerators or other thermal facilities'
                                , e3='E3. asphalt and asphalt tar manufacture, storage and distribution, including stationary asphalt batch plants'
                                , e4='E4. coal gasification (manufactured gas production)'
                                , e5='E5. medical, chemical, radiological or biological laboratories'
                                , e6='E6. outdoor firearm shooting ranges'
                                , e7='E7. road salt or brine storage'
                                , e8='E8. measuring instruments (containing mercury) manufacture, repair or bulk storage'
                                , e9='E9. dry cleaning facilities or operations and dry cleaning chemical storage, excluding locations at which clothing is deposited but no dry cleaning process occurs'
                                # , e10='E10. contamination or likely contamination of land by substances migrating from an industrial or commercial site'
                                , e11='E11. fire training facilities at which fire retardants are used'
                                # , e12='E12. single or cumulative spills to the environment greater than the reportable quantities of substances listed in the Spill Reporting Regulation'
                                , f1='F1. petroleum or natural gas drilling'
                                , f2='F2. petroleum or natural gas production facilities'
                                , f3='F3. natural gas processing'
                                , f4='F4. petroleum coke manufacture, bulk storage or shipping'
                                , f5='F5. petroleum product, other than compressed gas, dispensing facilities, including service stations and card locks'
                                , f6='F6. petroleum, natural gas or sulfur pipeline rights of way excluding rights of way for pipelines used to distribute natural gas to consumers in a community'
                                , f7='F7. petroleum product (other than compressed gas), or produced water storage in non-mobile above ground or underground tanks, except tanks associated with emergency generators or with secondary containment'
                                , f8='F8. petroleum product, other than compressed gas, bulk storage or distribution'
                                , f9='F9. petroleum refining'
                                , f10='F10. solvent manufacturing or bulk storage'
                                , f11='F11. sulfur handling, processing or bulk storage and distribution'
                                , g1='G1. aircraft maintenance, cleaning or salvage'
                                , g2='G2. automotive, truck, bus, subway or other motor vehicle maintenance, repair, salvage or wrecking'
                                , g3='G3. dry docks, marinas, ship building or boat repair and maintenance, including paint removal from hulls'
                                , g4='G4. marine equipment salvage'
                                , g5='G5. rail car or locomotive maintenance, cleaning, salvage or related uses, including railyards'
                                , h1='H1. antifreeze bulk storage, recycling or shipping'
                                , h2='H2. barrel, drum or tank reconditioning or salvage'
                                , h3='H3. biomedical waste disposal'
                                , h4='H4. bulk manure stockpiling and high rate land application or disposal (nonfarm applications only)'
                                , h5='H5. landfilling of construction demolition material, including without limitation asphalt and concrete'
                                , h6='H6. contaminated soil or sediment storage, treatment, deposit or disposal'
                                , h7l='H7. dry cleaning waste disposal'
                                , h8='H8. electrical equipment recycling'
                                , h9='H9. industrial waste lagoons or impoundments'
                                , h10='H10. industrial waste storage, recycling or landfilling'
                                , h11='H11. industrial woodwaste (log yard waste, hogfuel) disposal'
                                , h12='H12. mine tailings waste disposal'
                                , h13='H13. municipal waste storage, recycling, composting or landfilling'
                                , h14='H14. organic or petroleum material landspreading (landfarming)'
                                , h15='H15. sandblasting operations or sandblasting waste disposal'
                                , h16='H16. septic tank pumpage storage or disposal'
                                , h7='H17. sewage lagoons or impoundments'
                                , h18='H18. hazardous waste storage, treatment or disposal'
                                , h19='H19. sludge drying or composting'
                                , h20='H20. municipal or provincial road or yard snow removal dumping'
                                , h21='H21. waste oil reprocessing, recycling or bulk storage'
                                , h22='H22. wire reclaiming operations'
                                , i1='I1. particle or wafer board manufacturing'
                                , i2='I2. pulp mill operations'
                                , i3='I3. pulp and paper manufacturing'
                                , i4='I4. treated wood storage at the site of treatment'
                                , i5='I5. veneer or plywood manufacturing'
                                , i6='I6. wood treatment (antisapstain or preservation)'
                                , i7='I7. wood treatment chemical manufacturing or bulk storage')
RECEIVING_SITE_USE_NAME_DIC = dict(industrialLandUseIl='Industrial Land Use (IL)'
                                  , commercialLandUseCl='Commercial Land Use (CL)'
                                  , residentialLandUseHighDensityRlhd='Residential Land Use High Density (RLHD)'
                                  , residentialLandUseLowDensityRlld='Residential Land Use Low Density (RLLD)'
                                  , urbanParkLandUsePl='Urban Park Land Use (PL)'
                                  , agriculturalLandUseAl='Agricultural Land Use (AL)'
                                  , wildlandsNaturalLandUseWln='Wildlands Natural Land Use (WLN)'
                                  , wildlandsRevertedLandUseWlr='Wildlands Reverted Land Use (WLR)'
                                  , potentialToCauseMetalsLeachingAcidRockDrainageMlArd='Without potential for Metals Leaching/Acid Rock Drainage (ML/ARD) as evaluated under Protocol 19')
SOIL_QUALITY_NAME_DIC = dict(industrialLandUseIl='Industrial (IL)'
                            , commercialLandUseCl='Commercial (CL)'
                            , residentialLandUseHighDensityRlhd='Residential high density (RLHD)'
                            , residentialLandUseLowDensityRlld='Residential low density (RLLD)'
                            , urbanParkLandUsePl='Urban park (PL)'
                            , agriculturalLandUseAl='Agricultural (AL)'
                            , wildlandsNaturalLandUseWln='Wildlands natural (WLN)'
                            , wildlandsRevertedLandUseWlr='Wildlands reverted (WLR)'
                            , potentialToCauseMetalsLeachingAcidRockDrainageMlArd='Without potential for Metals Leaching/Acid Rock Drainage (ML/ARD) as evaluated under Protocol 19')
LAND_OWNERSHIP_NAME_DIC = dict(titled='Legally Titled, registered property'
                            , untitled='Untitled Crown Land'
                            , untitledMunicipalLand='Untitled Municipal Land'
                            , reserveLand='Reserve land')
SOIL_EXEMPTION_NAME_DIC = dict(eligibleForExemption1='Exemption 1- site with a Final Determination the site is not contaminated or a numerical-based Certificate of Compliance'
                            , eligibleForExemption2='Exemption 2- soil treatment facilities with an Environmental Management Act waste discharge authorization'
                            , eligibleForExemption3='Exemption 3- quarries with a Mines Act Permit'
                            , eligibleForExemption4='Exemption 4- transitory sites')
CHEFS_SOURCE_PARAM_DIC = dict(latitudeDegrees='A3-SourceSiteLatitude-Degrees'
                            , latitudeMinutes='A3-SourceSiteLatitude-Minutes'
                            , latitudeSeconds='A3-SourceSiteLatitude-Seconds'
                            , longitudeDegrees='A3-SourceSiteLongitude-Degrees'
                            , longitudeMinutes='A3-SourceSiteLongitude-Minutes'
                            , longitudeSeconds='A3-SourceSiteLongitude-Seconds'
                            , landOwnership='SourcelandOwnership-checkbox'
                            , regionalDistrict='SourceSiteregionalDistrict'
                            , updateToPreviousForm='Intro-New_form_or_update'
                            , previousConfirmCode='ifThisIsAnUpdatePleaseEnterTheConfirmationCodeOfThePreviousSubmission'
                            , ownerCompany='A1-Company'
                            , owner2Company='A1-additionalownerCompany1'
                            , contactCompany='A2-SourceSiteContactCompany'
                            , SID='A3-SourcesiteIdentificationNumberSiteIdIfAvailable'
                            , legallyTitledSiteAddress='A-LegallyTitled-AddressSource'
                            , legallyTitledSiteCity='A-LegallyTitled-CitySource'
                            , legallyTitledSitePostalCode='A-LegallyTitled-PostalZipCodeSource'
                            , crownLandFileNumbers='A-UntitledCrownLand-FileNumberColumnSource'
                            , reserveNameAndNumber='SourceReserveNameAndNumber'
                            , pidDataGrid='dataGrid'
                            , pid='A-LegallyTitled-PID'
                            , pidDesc='legalLandDescriptionSource'
                            , pinDataGrid='dataGrid1'
                            , pin='A-UntitledPINSource'
                            , pinDesc='legalLandDescriptionUntitledSource'
                            , untitledMunicipalLand='A-UntitledMunicipalLand-PIDColumnSource'
                            , untitledMunicipalLandDesc='legalLandDescriptionUntitledMunicipalSource'
                            , sourceSiteLandUse='A4-schedule2ReferenceSourceSite'
                            , highVolumeSite='isTheSourceSiteHighRisk'
                            , soilRelocationPurpose='A5-PurposeOfSoilExcavationSource'
                            , soilStorageType='B4-currentTypeOfSoilStorageEGStockpiledInSitu1Source'
                            , exemptionFromProtocol19Apply='A6_DoesexemptionfromProtocol19apply' # Do exemptions from Protocol 19 apply?
                            , protocol19AppliedExemptions='ifAnExemptionFromProtocol19AppliesPleaseSelectBelow' # Exemption check boxes - If yes, please choose below. - Under Source Site Protocol 19 Exemptions                            
                            , soilVolumeDataGrid='dataGrid9'
                            , soilVolume='B1-soilVolumeToBeRelocationedInCubicMetresM3Source'
                            , soilClassificationSource='B1-soilClassificationSource'
                            , soilUnderProtocol19Exemptions='doAllOfTheSoilsListedAboveFallUnderProtocol19Exemptions' # "Do all of the soils listed above fall under Protocol 19 exemptions?" yes or no radio box
                            , vapourExemption='B3-yesOrNoVapourexemptionsource'
                            , vapourExemptionDesc='B3-ifExemptionsApplyPleaseDescribe'
                            , soilRelocationStartDate='B4-soilRelocationEstimatedStartDateMonthDayYear'
                            , soilRelocationCompletionDate='B4-soilRelocationEstimatedCompletionDateMonthDayYear'
                            , relocationMethod='B4-RelocationMethod'
                            , qualifiedProfessionalOrganization='D1-organization1QualifiedProfessional'
                            , form='form'
                            , createdAt='createdAt'
                            , confirmationId='confirmationId')
CHEFS_RCV1_PARAM_DIC = dict(latitudeDegrees='C2-Latitude-DegreesReceivingSite'
                            , latitudeMinutes='C2-Latitude-MinutesReceivingSite'
                            , latitudeSeconds='Section2-Latitude-Seconds1ReceivingSite'
                            , longitudeDegrees='C2-Longitude-DegreesReceivingSite'
                            , longitudeMinutes='C2-Longitude-MinutesReceivingSite'
                            , longitudeSeconds='C2-Longitude-SecondsReceivingSite'
                            , landOwnership='C2-receivinglandOwnership-checkbox'
                            , regionalDistrict='ReceivingSiteregionalDistrict'
                            , previousConfirmCode='ifThisIsAnUpdatePleaseEnterTheConfirmationCodeOfThePreviousSubmission'
                            , ownerCompany='C1-CompanyReceivingSiteOwner'
                            , owner2Company='C1-Company1ReceivingSiteAdditionalOwners'
                            , contactCompany='C2-RSC-Company'
                            , SID='C2-siteIdentificationNumberSiteIdIfAvailableReceivingSite'
                            , legallyTitledSiteAddress='C2-LegallyTitled-AddressReceivingSite'
                            , legallyTitledSiteCity='C2-LegallyTitled-CityReceivingSite'
                            , legallyTitledSitePostalCode='C2-LegallyTitled-PostalReceivingSite'
                            , crownLandFileNumbers='A-UntitledCrownLand-FileNumberColumn1'
                            , reserveNameAndNumber='ReceivingReserveNameAndNumber'
                            , soilVolumeDataGrid='ReceivingSiteVolumeAndLandUse'
                            , soilVolume='B1-soilVolumeToBeRelocationedInCubicMetresM3Source'
                            , soilClassificationSource='B1-soilClassificationSource'
							, receivingSiteLandUse='C3-soilClassification1ReceivingSite'
							, CSRFactors='C3-applicableSiteSpecificFactorsForCsrSchedule31ReceivingSite'
							, relocatedSoilUse='C3-applicableSiteSpecificFactorsForCsrSchedule32ReceivingSite'
                            , pidDataGrid='dataGrid2'
                            , pid='A-LegallyTitled-PIDReceivingSite'
                            , pidDesc='legalLandDescriptionReceivingSite'
                            , pinDataGrid='dataGrid5'
                            , pin='A-LegallyTitled-PID'
                            , pinDesc='legalLandDescriptionUntitledCrownLandReceivingSite'
                            , untitledMunicipalLand='A-UntitledMunicipalLand-PIDColumn1'
                            , untitledMunicipalLandDesc='legalLandDescription'
                            , highVolumeSite='C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime'
							, soilDepositIsALR='D2-receivingsitesoilDepositIsInTheAgriculturalLandReserveAlr1'
							, soilDepositIsReserveLands='D2-receivingsitesoilDepositIsInTheReserveLands1'
                            , soilRelocationStartDate='B4-soilRelocationEstimatedStartDateMonthDayYear'
                            , soilRelocationCompletionDate='B4-soilRelocationEstimatedCompletionDateMonthDayYear'
                            , form='form'
                            , createdAt='createdAt'
                            , confirmationId='confirmationId'
                            , receivingSiteClass='receivingSiteClass')
CHEFS_RCV2_PARAM_DIC = dict(latitudeDegrees='C2-Latitude-Degrees1FirstAdditionalReceivingSite'
                            , latitudeMinutes='C2-Latitude-Minutes1FirstAdditionalReceivingSite'
                            , latitudeSeconds='Section2-Latitude-Seconds2FirstAdditionalReceivingSite'
                            , longitudeDegrees='C2-Longitude-Degrees1FirstAdditionalReceivingSite'
                            , longitudeMinutes='C2-Longitude-Minutes1FirstAdditionalReceivingSite'
                            , longitudeSeconds='C2-Longitude-Seconds1FirstAdditionalReceivingSite'
							, additionalRcvSite='additionalReceivingSites'
							, additionalRcvInformation='firstAdditionalReceivingSiteInformation'
                            , landOwnership='Firstadditionalreceiving-landOwnership-checkbox1'
                            , regionalDistrict='FirstAdditionalReceivingSiteregionalDistrict1'
                            , previousConfirmCode='ifThisIsAnUpdatePleaseEnterTheConfirmationCodeOfThePreviousSubmission'
                            , ownerCompany='C1-Company2FirstAdditionalReceivingSite'
                            , owner2Company='C1-Company3AdditionalReceivingSiteOwner'
                            , contactCompany='C2-RSC-Company1AdditionalReceivingSite'
                            , SID='C2-siteIdentificationNumberSiteIdIfAvailable1FirstAdditionalReceivingSite'
                            , legallyTitledSiteAddress='C2-LegallyTitled-Address1FirstAdditionalReceivingSite'
                            , legallyTitledSiteCity='C2-LegallyTitled-City1FirstAdditionalReceivingSite'
                            , legallyTitledSitePostalCode='C2-LegallyTitled-PostalZipCode1FirstAdditionalReceivingSite'
                            , crownLandFileNumbers='A-UntitledCrownLand-FileNumberColumn2'
                            , reserveNameAndNumber='reserveNameAndNumberfirstadditionalreceiving'
                            , soilVolumeDataGrid='FirstAdditionalReceivingSiteVolumeAndLandUse'
                            , soilVolume='B1-soilVolumeToBeRelocationedInCubicMetresM3Source'
                            , soilClassificationSource='B1-soilClassificationSource'
							, receivingSiteLandUse='C3-soilClassification2FirstAdditionalReceivingSite'
							, CSRFactors='C3-applicableSiteSpecificFactorsForCsrSchedule33FirstAdditionalReceivingSite'
							, relocatedSoilUse='C3-applicableSiteSpecificFactorsForCsrSchedule34FirstAdditionalReceivingSite'
                            , pidDataGrid='dataGrid3'
                            , pid='A-LegallyTitled-PIDFirstAdditionalReceivingSite'
                            , pidDesc='legalLandDescriptionFirstAdditionalReceivingSite'
                            , pinDataGrid='dataGrid6'
                            , pin='A-UntitledCrown-PINFirstAdditionalReceivingSite'
                            , pinDesc='legalLandDescriptionUntitledCrownFirstAdditionalReceivingSite'
                            , untitledMunicipalLand='A-UntitledMunicipalLand-PIDColumn2'
                            , untitledMunicipalLandDesc='legalLandDescriptionUntitledMunicipalFirstAdditionalReceivingSite'
                            , highVolumeSite='C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1'
							, soilDepositIsALR='D2-firstaddtlreceivingsitesoilDepositIsInTheAgriculturalLandReserveAlr2'
							, soilDepositIsReserveLands='D2-firstaddtlreceivingsitesoilDepositIsInTheReserveLands2'
                            , soilRelocationStartDate='B4-soilRelocationEstimatedStartDateMonthDayYear'
                            , soilRelocationCompletionDate='B4-soilRelocationEstimatedCompletionDateMonthDayYear'
                            , form='form'
                            , createdAt='createdAt'
                            , confirmationId='confirmationId'
                            , receivingSiteClass='receivingSiteClass')
CHEFS_RCV3_PARAM_DIC = dict(latitudeDegrees='C2-Latitude-Degrees3SecondAdditionalreceivingSite'
                            , latitudeMinutes='C2-Latitude-Minutes3SecondAdditionalreceivingSite'
                            , latitudeSeconds='Section2-Latitude-Seconds4SecondAdditionalreceivingSite'
                            , longitudeDegrees='C2-Longitude-Degrees3SecondAdditionalreceivingSite'
                            , longitudeMinutes='C2-Longitude-Minutes3SecondAdditionalreceivingSite'
                            , longitudeSeconds='C2-Longitude-Seconds3SecondAdditionalreceivingSite'
							, additionalRcvSite='secondadditionalReceivingSites1'
							, additionalRcvInformation='secondAdditionalReceivingSiteInformation'
                            , landOwnership='Secondadditionalreceiving-landOwnership-checkbox3'
                            , regionalDistrict='SecondAdditionalReceivingSiteregionalDistrict'
                            , previousConfirmCode='ifThisIsAnUpdatePleaseEnterTheConfirmationCodeOfThePreviousSubmission'
                            , ownerCompany='C1-Company6SecondAdditionalreceivingSite'
                            , owner2Company='C1-Company7SecondAdditionalreceivingSite'
                            , contactCompany='C2-RSC-Company3SecondAdditionalreceivingSite'
                            , SID='C2-siteIdentificationNumberSiteIdIfAvailable3SecondAdditionalreceivingSite'
                            , legallyTitledSiteAddress='C2-LegallyTitled-Address3SecondAdditionalreceivingSite'
                            , legallyTitledSiteCity='C2-LegallyTitled-City3SecondAdditionalreceivingSite'
                            , legallyTitledSitePostalCode='C2-LegallyTitled-PostalZipCode3SecondAdditionalreceivingSite'
                            , crownLandFileNumbers='A-UntitledCrownLand-FileNumberColumn2'
                            , reserveNameAndNumber='reserveNameAndNumbersecondadditionalreceiving'
                            , soilVolumeDataGrid='SecondAdditionalReceivingSiteVolumeAndLandUse'
                            , soilVolume='B1-soilVolumeToBeRelocationedInCubicMetresM3Source'
                            , soilClassificationSource='B1-soilClassificationSource'
							, receivingSiteLandUse='C3-soilClassification4SecondAdditionalreceivingSite'
							, CSRFactors='C3-applicableSiteSpecificFactorsForCsrSchedule37SecondAdditionalreceivingSite'
							, relocatedSoilUse='C3-applicableSiteSpecificFactorsForCsrSchedule38SecondAdditionalreceivingSite'
                            , pidDataGrid='dataGrid4'
                            , pid='A-LegallyTitled-PIDSecondAdditionalreceivingSite'
                            , pidDesc='legalLandDescriptionSecondAdditionalreceivingSite'
                            , pinDataGrid='dataGrid7'
                            , pin='A-UntitledCrownLand-PINSecondAdditionalreceivingSite'
                            , pinDesc='UntitledCrownLandLegalLandDescriptionSecondAdditionalreceivingSite'
                            , untitledMunicipalLand='A-UntitledMunicipalLand-PIDColumn3'
                            , untitledMunicipalLandDesc='legalLandDescriptionUntitledMunicipalSecondAdditionalreceivingSite'
                            , highVolumeSite='C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime3'
							, soilDepositIsALR='D2-secondaddtlreceivingsitesoilDepositIsInTheAgriculturalLandReserveAlr3'
							, soilDepositIsReserveLands='D2-secondaddtlreceivingsitesoilDepositIsInTheReserveLands3'
                            , soilRelocationStartDate='B4-soilRelocationEstimatedStartDateMonthDayYear'
                            , soilRelocationCompletionDate='B4-soilRelocationEstimatedCompletionDateMonthDayYear'
                            , form='form'
                            , createdAt='createdAt'
                            , confirmationId='confirmationId'
                            , receivingSiteClass='receivingSiteClass')
CHEFS_HV_PARAM_DIC = dict(latitudeDegrees='Section3-Latitude-Degrees'
                            , latitudeMinutes='Section3-Latitude-Minutes'
                            , latitudeSeconds='Section3-Latitude-Seconds'
                            , longitudeDegrees='Section3-Longitude-Degrees'
                            , longitudeMinutes='Section3-Longitude-Minutes'
                            , longitudeSeconds='Section3-Longitude-Seconds'
                            , landOwnership='landOwnership-checkbox'
                            , regionalDistrict='ReceivingSiteregionalDistrict'
                            , ownerCompany='Section1-CompanyReceivingSiteOwner'
                            , owner2Company='Section1A-CompanyAdditionalOwner'
                            , contactCompany='Section2-organizationRSC'
                            , SID='Section3-siteIdIncludeAllRelatedNumbers'
                            , legallyTitledSiteAddress='Section3-LegallyTitled-Address'
                            , legallyTitledSiteCity='Section3-LegallyTitled-City'
                            , legallyTitledSitePostalCode='Section3-LegallyTitled-PostalZipCode'
                            , crownLandFileNumbers='A-UntitledCrownLand-FileNumberColumn'
                            , reserveNameAndNumber='nameOfReserveAndNumberIfAvailable'
                            , pidDataGrid='dataGrid'
                            , pid='A-LegallyTitled-PID'
                            , pidDesc='legalLandDescription'
                            , pinDataGrid='dataGrid1'
                            , pin='A-LegallyTitled-PID'
                            , pinDesc='legalLandDescription'
                            , untitledMunicipalLand='A-UntitledMunicipalLand-PIDColumn'
                            , untitledMunicipalLandDesc='legalLandDescription'
							, receivingSiteLandUse='primarylanduse'
							, hvsConfirmation='highVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime'
							, dateSiteBecameHighVolume='dateSiteBecameHighVolume'
							, howRelocatedSoilWillBeUsed='howrelocatedsoilwillbeused'
							, soilDepositIsALR='soilDepositIsInTheAgriculturalLandReserveAlr1'
							, soilDepositIsReserveLands='receivingSiteIsOnReserveLands1'
                            , qualifiedProfessionalOrganization='Section5-organizationQualifiedProfessional'
                            , form='form'
                            , createdAt='createdAt'
                            , confirmationId='confirmationId')
SOURCE_SITE_HEADERS = ["confirmationId",
                       "updateToPreviousForm",
                       "previousConfirmCode",
                       "ownerCompany",
                       "owner2Company",
                       "contactCompany",
                       "SID",
                       "latitude",
                       "longitude",
                       "landOwnership",
                       "legallyTitledSiteAddress",
                       "legallyTitledSiteCity",
                       "legallyTitledSitePostalCode",
                       "regionalDistrict",
                       "PID",
                       "PIN",
                       "legalLandDescription",
                       "crownLandFileNumbers",
                       "reserveNameAndNumber",
                       "sourceSiteLandUse",
                       "highVolumeSite",
                       "soilRelocationPurpose",
                       "soilStorageType",
                       "exemptionFromProtocol19Apply", # Do exemptions from Protocol 19 apply?
                       "protocol19AppliedExemptions", # Exemption check boxes - If yes, please choose below. - Under Source Site Protocol 19 Exemptions
                       "industrialSoilVol",
                       "commercialSoilVol",
                       "residentHighDensitySoilVol",
                       "residentLowDensitySoilVol",
                       "urbanParkSoilVol",
                       "agriculturalSoilVol",
                       "wildlandsNaturalSoilVol",
                       "wildlandsRevertedSoilVol",
                       "mdardSoilVol",
                       "totalSoilVolume",
                       "soilUnderProtocol19Exemptions", # "Do all of the soils listed above fall under Protocol 19 exemptions?" yes or no radio box
                       "vapourExemption",
                       "vapourExemptionDesc",
                       "soilRelocationStartDate",
                       "soilRelocationCompletionDate",
                       "relocationMethod",
                       "qualifiedProfessionalOrganization",
                       "receivingSite1Address",
                       "receivingSite1City",
                       "receivingSite1RegionalDistrict",
                       "receivingSite2Address",
                       "receivingSite2City",
                       "receivingSite2RegionalDistrict",
                       "receivingSite3Address",
                       "receivingSite3City",
                       "receivingSite3RegionalDistrict"
                       ]
RECEIVING_SITE_HEADERS = ["confirmationId",
                          "previousConfirmCode",
                          "ownerCompany",
                          "owner2Company",
                          "contactCompany",
                          "SID",
                          "latitude",
                          "longitude",
                          "regionalDistrict",
                          "landOwnership",
                          "legallyTitledSiteAddress",
                          "legallyTitledSiteCity",
                          "legallyTitledSitePostalCode",
                          "PID",
                          "PIN",
                          "legalLandDescription",
                          "crownLandFileNumbers",
                          "reserveNameAndNumber",
                          "industrialSoilVol",
                          "commercialSoilVol",
                          "residentHighDensitySoilVol",
                          "residentLowDensitySoilVol",
                          "urbanParkSoilVol",
                          "agriculturalSoilVol",
                          "wildlandsNaturalSoilVol",
                          "wildlandsRevertedSoilVol",
                          "mdardSoilVol",
                          "totalSoilVolume",
                          "receivingSiteLandUse",
                          "CSRFactors",
                          "relocatedSoilUse",
                          "highVolumeSite",
                          "soilDepositIsALR",
                          "soilDepositIsReserveLands",
                          "soilRelocationStartDate",
                          "soilRelocationCompletionDate",
                          "sourceSiteAddress",
                          "sourceSiteCity",
                          "sourceSiteRegionalDistrict"
                          ]
HV_SITE_HEADERS = ["confirmationId",
                   "ownerCompany",
                   "owner2Company",
                   "contactCompany",
                   "SID",
                   "latitude",
                   "longitude",
                   "regionalDistrict",
                   "landOwnership",
                   "legallyTitledSiteAddress",
                   "legallyTitledSiteCity",
                   "legallyTitledSitePostalCode",
                   "PID",
                   "PIN",
                   "legalLandDescription",
                   "crownLandFileNumbers",
                   "reserveNameAndNumber",
                   "receivingSiteLandUse",
                   "hvsConfirmation",
                   "dateSiteBecameHighVolume",
                   "howRelocatedSoilWillBeUsed",
                   "soilDepositIsALR",
                   "soilDepositIsReserveLands",
                   "qualifiedProfessionalOrganization"
                   ]
