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
SOURCE_SITE_USE_NAME_DIC = dict(a1='A1. adhesives manufacturing, bulk storage, shipping or handling'
                                , a2='A2. chemical manufacturing, bulk storage, shipping or handling'
                                , a3='A3. explosives or ammunition manufacturing, bulk storage, shipping or handling'
                                , a4='A4. fire retardant manufacturing, bulk storage, shipping or handling'
                                , a5='A5. fertilizer manufacturing, bulk storage, shipping or handling'
                                , a6='A6. ink or dye manufacturing, bulk storage, shipping or handling'
                                , a7='A7. leather or hides tanning'
                                , a8='A8. paint, lacquer or varnish manufacturing, formulation, recycling, bulk storage, shipping or handling, not including retail stores'
                                , a9='A9. pharmaceutical products, or controlled substances as defined in the Controlled Drugs and Substances Act (Canada), manufacturing or operations'
                                , a10='A10. plastic products (foam or expanded plastic) manufacturing or repurposing'
                                , none='None'
                                , a11='A11. textile dyeing'
                                , a12='A12. pesticide manufacturing, formulation, bulk storage, shipping or handling'
                                , a13='A13. resin or plastic monomer manufacturing, formulation, bulk storage, shipping or handling'
                                , b1='B1. battery manufacturing, recycling, bulk storage, shipping or handling'
                                , b2='B2. facilities using equipment that contains PCBs greater than or equal to 50 ppm'
                                , b3='B3. electrical equipment manufacturing, refurbishing, bulk storage, shipping or handling'
                                , b4='B4. electrical transmission or distribution substations'
                                , b5='B5. electronic equipment manufacturing'
                                , b6='B6. transformer oil manufacturing, processing, bulk storage, shipping or handling'
                                , b7='B7. electrical power generating operations fuelled by coal or petroleum hydrocarbons that supply electricity to a community or commercial or industrial operation, excluding emergency generators'
                                , c1='C1. foundries'
                                , c2='C2. galvanizing'
                                , c3='C3. metal plating or finishing'
                                , c4='C4. metal salvage operations'
                                , c5='C5. metal smelting or refining'
                                , c6='C6. welding or machine shops (repair or fabrication)'
                                , d1='D1. asbestos mining, milling, bulk storage, shipping or handling'
                                , d2='D2. coal coke manufacture, bulk storage, shipping or handling'
                                , d3='D3. coal or lignite mining, milling, bulk storage, shipping or handling'
                                , d4='D4. milling reagent manufacture, bulk storage, shipping or handling'
                                , d5='D5. metal concentrate bulk storage, shipping or handling'
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
                                , e10='E10. contamination or likely contamination of land by substances migrating from an industrial or commercial site'
                                , e11='E11. fire training facilities at which fire retardants are used'
                                , e12='E12. single or cumulative spills to the environment greater than the reportable quantities of substances listed in the Spill Reporting Regulation'
                                , f1='F1. petroleum or natural gas drilling'
                                , f2='F2. petroleum or natural gas production facilities'
                                , f3='F3. natural gas processing'
                                , f4='F4. petroleum coke manufacture, bulk storage, shipping or handling'
                                , f5='F5. petroleum product, other than compressed gas, dispensing facilities, including service stations and card locks'
                                , f6='F6. petroleum, natural gas or sulfur pipeline rights of way excluding rights of way for pipelines used to distribute natural gas to consumers in a community'
                                , f7='F7. petroleum product (other than compressed gas), or produced water storage in non-mobile above ground or underground tanks, except tanks associated with emergency generators or with secondary containment'
                                , f8='F8. petroleum product, other than compressed gas, bulk storage or distribution'
                                , f9='F9. petroleum refining'
                                , f10='F10. solvent manufacturing, bulk storage, shipping or handling'
                                , f11='F11. sulfur handling, processing or bulk storage and distribution'
                                , g1='G1. aircraft maintenance, cleaning or salvage'
                                , g2='G2. automotive, truck, bus, subway or other motor vehicle maintenance, repair, salvage or wrecking'
                                , g3='G3. dry docks, marinas, ship building or boat repair and maintenance, including paint removal from hulls'
                                , g4='G4. marine equipment salvage'
                                , g5='G5. rail car or locomotive maintenance, cleaning, salvage or related uses, including railyards'
                                , h1='H1. antifreeze bulk storage, recycling, shipping or handling'
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
                                , h20='H20. municipal or provincial road snow removal dumping or yard snow removal dumping'
                                , h21='H21. waste oil reprocessing, recycling or bulk storage'
                                , h22='H22. wire reclaiming operations'
                                , i1='I1. particle or wafer board manufacturing'
                                , i2='I2. pulp mill operations'
                                , i3='I3. pulp and paper manufacturing'
                                , i4='I4. treated wood storage at the site of treatment'
                                , i5='I5. veneer or plywood manufacturing'
                                , i6='I6. wood treatment (antisapstain or preservation)'
                                , i7='I7. wood treatment chemical manufacturing, bulk storage')
RECEIVING_SITE_USE_NAME_DIC = dict(industrialLandUseIl='Industrial Land Use (IL)'
                                  , commercialLandUseCl='Commercial Land Use (CL)'
                                  , residentialLandUseHighDensityRlhd='Residential Land Use High Density (RLHD)'
                                  , residentialLandUseLowDensityRlld='Residential Land Use Low Density (RLLD)'
                                  , urbanParkLandUsePl='Urban Park Land Use (PL)'
                                  , agriculturalLandUseAl='Agricultural Land Use (AL)'
                                  , wildlandsNaturalLandUseWln='Wildlands Natural Land Use (WLN)'
                                  , wildlandsRevertedLandUseWlr='Wildlands Reverted Land Use (WLR)')
SOIL_QUALITY_NAME_DIC = dict(industrialLandUseIl='Industrial Land Use (IL)'
                            , commercialLandUseCl='Commercial Land Use (CL)'
                            , residentialLandUseHighDensityRlhd='Residential Land Use High Density (RLHD)'
                            , residentialLandUseLowDensityRlld='Residential Land Use Low Density (RLLD)'
                            , urbanParkLandUsePl='Urban Park Land Use (PL)'
                            , agriculturalLandUseAl='Agricultural Land Use (AL)'
                            , wildlandsNaturalLandUseWln='Wildlands Natural Land Use (WLN)'
                            , wildlandsRevertedLandUseWlr='Wildlands Reverted Land Use (WLR)')
LAND_OWNERSHIP_NAME_DIC = dict(titled='Legally Titled, registered property'
                            , untitled='Untitled Crown Land'
                            , untitledMunicipalLand='Untitled Municipal Land')
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
                            , industrialOrCommercialUses='Intro-hasthesitebeenusedfor-INDUSTRIALorCOMMERICAL-YESorNO'
                            , ownerFirstName='A1-FIRSTName'
                            , ownerLastName='A1-LASTName'
                            , ownerCompany='A1-Company'
                            , ownerAddress='A1-Address'
                            , ownerCity='A1-City'
                            , ownerProvince='A1-ProvinceState'
                            , ownerCountry='A1-Country'
                            , ownerPostalCode='A1-PostalZipCode'
                            , ownerPhoneNumber='A1-Phone'
                            , ownerEmail='A1-Email'
                            , owner2FirstName='A1-additionalownerFIRSTName'
                            , owner2LastName='A1-additionalownerLASTName1'
                            , owner2Company='A1-additionalownerCompany1'
                            , owner2Address='A1-additionalownerAddress1'
                            , owner2City='A1-additionalownerCity1'
                            , owner2Province='A1-additionalownerProvinceState2'
                            , owner2Country='A1-additionalownerCountry2'
                            , owner2PostalCode='A1-additionalownerPostalZipCode1'
                            , owner2PhoneNumber='A1-additionalownerPhone1'
                            , owner2Email='A1-additionalownerEmail1'
                            , additionalOwners='areThereMoreThanTwoOwnersIncludeTheirInformationBelow'
                            , contactFirstName='A2-SourceSiteContactFirstName'
                            , contactLastName='A2-SourceSiteContactLastName'
                            , contactCompany='A2-SourceSiteContactCompany'
                            , contactAddress='A2-SourceSiteContactAddress'
                            , contactCity='A2-SourceSiteContactCity'
                            , contactProvince='A1-sourcesitecontactProvinceState3'
                            , contactCountry='A1-sourcesitecontactpersonCountry3'
                            , contactPostalCode='A1-sourcesitecontactpersonPostalZipCode2'
                            , contactPhoneNumber='SourceSiteContactphoneNumber'
                            , contactEmail='A2-SourceSiteContactEmail'
                            , SID='A3-SourcesiteIdentificationNumberSiteIdIfAvailable'
                            , legallyTitledSiteAddress='A-LegallyTitled-AddressSource'
                            , legallyTitledSiteCity='A-LegallyTitled-CitySource'
                            , legallyTitledSitePostalCode='A-LegallyTitled-PostalZipCodeSource'
                            , crownLandFileNumbers='A-UntitledCrownLand-FileNumberColumnSource'
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
                            , soilVolumeDataGrid='dataGrid9'
                            , soilVolume='B1-soilVolumeToBeRelocationedInCubicMetresM3Source'
                            , soilClassificationSource='B1-soilClassificationSource'
                            , soilCharacterMethod='B2-describeSoilCharacterizationMethod1'
                            , vapourExemption='B3-yesOrNoVapourexemptionsource'
                            , vapourExemptionDesc='B3-ifExemptionsApplyPleaseDescribe'
                            , vapourCharacterMethodDesc='B3-describeVapourCharacterizationMethod'
                            , soilRelocationStartDate='B4-soilRelocationEstimatedStartDateMonthDayYear'
                            , soilRelocationCompletionDate='B4-soilRelocationEstimatedCompletionDateMonthDayYear'
                            , relocationMethod='B4-RelocationMethod'
                            , qualifiedProfessionalFirstName='D1-FirstNameQualifiedProfessional'
                            , qualifiedProfessionalLastName='LastNameQualifiedProfessional'
                            , qualifiedProfessionalType='D1-TypeofQP1'
                            , professionalLicenceRegistration='D1-professionalLicenseRegistrationEGPEngRpBio'
                            , qualifiedProfessionalOrganization='D1-organization1QualifiedProfessional'
                            , qualifiedProfessionalAddress='D1-streetAddress1QualifiedProfessional'
                            , qualifiedProfessionalCity='D1-city1QualifiedProfessional'
                            , qualifiedProfessionalProvince='D1-provinceState3QualifiedProfessional'
                            , qualifiedProfessionalCountry='D1-canadaQualifiedProfessional'
                            , qualifiedProfessionalPostalCode='D1-postalZipCode3QualifiedProfessional'
                            , qualifiedProfessionalPhoneNumber='simplephonenumber1QualifiedProfessional'
                            , qualifiedProfessionalEmail='EmailAddressQualifiedProfessional'
                            , signaturerFirstAndLastName='sig-firstAndLastNameQualifiedProfessional'
                            , dateSigned='simpledatetime'
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
                            , ownerFirstName='C1-FirstNameReceivingSiteOwner'
                            , ownerLastName='C1-LastNameReceivingSiteOwner'
                            , ownerCompany='C1-CompanyReceivingSiteOwner'
                            , ownerAddress='C1-AddressReceivingSiteOwner'
                            , ownerCity='C1-CityReceivingSiteOwner'
                            , ownerProvince='A1-receivingsiteownerProvinceState4'
                            , ownerCountry='A1-receivingsiteownerCountry4'
                            , ownerPostalCode='A1-receivingsiteownerPostalCode3'
                            , ownerPhoneNumber='C1-PhoneRecevingSiteOwner'
                            , ownerEmail='C1-EmailReceivingSiteOwner'
                            , owner2FirstName='C1-FirstName1ReceivingSiteAdditionalOwners'
                            , owner2LastName='C1-LastName1ReceivingSiteAdditionalOwners'
                            , owner2Company='C1-Company1ReceivingSiteAdditionalOwners'
                            , owner2Address='C1-Address1ReceivingSiteAdditionalOwners'
                            , owner2City='C1-City1ReceivingSiteAdditionalOwners'
                            , owner2Province='A1-additionareceivingsiteownerProvinceState5'
                            , owner2Country='A1-additionareceivingsiteownerCountry5'
                            , owner2PostalCode='A1-additionalreceivingsiteownerPostalCode4'
                            , owner2PhoneNumber='C1-Phone1ReceivingSiteAdditionalOwners'
                            , owner2Email='C1-Email1ReceivingSiteAdditionalOwners'
                            , additionalOwners='haveMoreThatTwoOwnersEnterTheirInformationBelow'
                            , contactFirstName='C2-RSC-FirstName'
                            , contactLastName='C2-RSC-LastName'
                            , contactCompany='C2-RSC-Company'
                            , contactAddress='C2-RSC-Address'
                            , contactCity='C2-RSC-City'
                            , contactProvince='A1-additionareceivingsitecontactpersonProvinceState6'
                            , contactCountry='A1-additionareceivingsitecontactpersonCountry6'
                            , contactPostalCode='A1-additionalreceivingsitecontactpersonPostalCode5'
                            , contactPhoneNumber='C2-RSCphoneNumber1'
                            , contactEmail='C2-RSC-Email'
                            , SID='C2-siteIdentificationNumberSiteIdIfAvailableReceivingSite'
                            , legallyTitledSiteAddress='C2-LegallyTitled-AddressReceivingSite'
                            , legallyTitledSiteCity='C2-LegallyTitled-CityReceivingSite'
                            , legallyTitledSitePostalCode='C2-LegallyTitled-PostalReceivingSite'
                            , crownLandFileNumbers='A-UntitledCrownLand-FileNumberColumn1'
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
                            , dateSigned='simpledatetime'
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
                            , ownerFirstName='C1-FirstName2FirstAdditionalReceivingSite'
                            , ownerLastName='C1-LastName2FirstAdditionalReceivingSite'
                            , ownerCompany='C1-Company2FirstAdditionalReceivingSite'
                            , ownerAddress='C1-Address2FirstAdditionalReceivingSite'
                            , ownerCity='C1-City2FirstAdditionalReceivingSite'
                            , ownerProvince='A1-firstadditionalreceivingsiteownerProvinceState7'
                            , ownerCountry='A1-firstadditionalreceivingsiteownerCountry7'
                            , ownerPostalCode='A1-firstadditionalreceivingsiteownerPostalCode6'
                            , ownerPhoneNumber='phoneNumber4FirstAdditionalReceivingSite'
                            , ownerEmail='C1-Email2FirstAdditionalReceivingSite'
                            , owner2FirstName='C1-FirstName3AdditionalReceivingSiteOwner'
                            , owner2LastName='C1-LastName3AdditionalReceivingSiteOwner'
                            , owner2Company='C1-Company3AdditionalReceivingSiteOwner'
                            , owner2Address='C1-Address3AdditionalReceivingSiteOwner'
                            , owner2City='C1-City3AdditionalReceivingSiteOwner'
                            , owner2Province='A1-additionareceivingsiteownerProvinceState5'
                            , owner2Country='A1-firstadditionalreceivingmoreownersCountry8'
                            , owner2PostalCode='A1-firstadditionalreceivingmoreownersPostalCode7'
                            , owner2PhoneNumber='phoneNumber2AdditionalReceivingSiteOwner'
                            , owner2Email='C1-Email3AdditionalReceivingSiteOwner'
                            , additionalOwners='C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow2ReceivingSite'
                            , contactFirstName='C2-RSC-FirstName1AdditionalReceivingSite'
                            , contactLastName='C2-RSC-LastName1AdditionalReceivingSite'
                            , contactCompany='C2-RSC-Company1AdditionalReceivingSite'
                            , contactAddress='C2-RSC-Address1AdditionalReceivingSite'
                            , contactCity='C2-RSC-City1AdditionalReceivingSite'
                            , contactProvince='A1-firstadditionalreceivingsitecontactProvinceState9'
                            , contactCountry='A1-firstadditionalreceivingsitecontactCountry9'
                            , contactPostalCode='A1-firstadditionalreceivingsitecontactPostalCode8'
                            , contactPhoneNumber='phoneNumber3AdditionalReceivingSite'
                            , contactEmail='C2-RSC-Email1AdditionalReceivingSite'
                            , SID='C2-siteIdentificationNumberSiteIdIfAvailable1FirstAdditionalReceivingSite'
                            , legallyTitledSiteAddress='C2-LegallyTitled-Address1FirstAdditionalReceivingSite'
                            , legallyTitledSiteCity='C2-LegallyTitled-City1FirstAdditionalReceivingSite'
                            , legallyTitledSitePostalCode='C2-LegallyTitled-PostalZipCode1FirstAdditionalReceivingSite'
                            , crownLandFileNumbers='A-UntitledCrownLand-FileNumberColumn2'
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
                            , dateSigned='simpledatetime'
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
                            , ownerFirstName='C1-FirstName6SecondAdditionalreceivingSite'
                            , ownerLastName='C1-LastName6SecondAdditionalreceivingSite'
                            , ownerCompany='C1-Company6SecondAdditionalreceivingSite'
                            , ownerAddress='C1-Address6SecondAdditionalreceivingSite'
                            , ownerCity='C1-City6SecondAdditionalreceivingSite'
                            , ownerProvince='A1-secondadditionalreceivingsiteownerProvinceState10'
                            , ownerCountry='A1-secondadditionalreceivingsiteownerCountry10'
                            , ownerPostalCode='A1-secondadditionalreceivingsiteownerPostalCode9'
                            , ownerPhoneNumber='phoneNumber7SecondAdditionalreceivingSite'
                            , ownerEmail='C1-Email6SecondAdditionalreceivingSite'
                            , owner2FirstName='C1-FirstName7SecondAdditionalreceivingSite'
                            , owner2LastName='C1-LastName7SecondAdditionalreceivingSite'
                            , owner2Company='C1-Company7SecondAdditionalreceivingSite'
                            , owner2Address='C1-Address7SecondAdditionalreceivingSite'
                            , owner2City='C1-City7SecondAdditionalreceivingSite'
                            , owner2Province='A1-secondadditionalreceivingsiteadditionalownerProvinceState11'
                            , owner2Country='A1-secondadditionalreceivingsiteadditionalownerCountry11'
                            , owner2PostalCode='A1-secondadditionalreceivingsiteadditionalownerPostalCode10'
                            , owner2PhoneNumber='phoneNumber5SecondAdditionalreceivingSite'
                            , owner2Email='C1-Email7SecondAdditionalreceivingSite'
                            , additionalOwners='C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow4SecondAdditionalreceivingSite'
                            , contactFirstName='C2-RSC-FirstName3SecondAdditionalreceivingSite'
                            , contactLastName='C2-RSC-LastName3SecondAdditionalreceivingSite'
                            , contactCompany='C2-RSC-Company3SecondAdditionalreceivingSite'
                            , contactAddress='C2-RSC-Address3SecondAdditionalreceivingSite'
                            , contactCity='C2-RSC-City3SecondAdditionalreceivingSite'
                            , contactProvince='A1-firstadditionalreceivingsitecontactProvinceState9'
                            , contactCountry='A1-secondadditionalreceivingsitecontactrCountry12'
                            , contactPostalCode='A1-secondadditionalreceivingsitecontactPostalCode11'
                            , contactPhoneNumber='phoneNumber6SecondAdditionalreceivingSite'
                            , contactEmail='C2-RSC-Email3SecondAdditionalreceivingSite'
                            , SID='C2-siteIdentificationNumberSiteIdIfAvailable3SecondAdditionalreceivingSite'
                            , legallyTitledSiteAddress='C2-LegallyTitled-Address3SecondAdditionalreceivingSite'
                            , legallyTitledSiteCity='C2-LegallyTitled-City3SecondAdditionalreceivingSite'
                            , legallyTitledSitePostalCode='C2-LegallyTitled-PostalZipCode3SecondAdditionalreceivingSite'
                            , crownLandFileNumbers='A-UntitledCrownLand-FileNumberColumn2'
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
                            , dateSigned='simpledatetime'
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
                            , ownerFirstName='Section1-FirstNameReceivingSiteOwner'
                            , ownerLastName='Section1-LastNameReceivingSiteOwner'
                            , ownerCompany='Section1-CompanyReceivingSiteOwner'
                            , ownerAddress='Section1-AddressReceivingSiteOwner'
                            , ownerCity='Section1-CityReceivingSiteOwner'
                            , ownerProvince='Section1-provinceStateReceivingSiteOwner'
                            , ownerCountry='Section1-countryReceivingSiteOwner'
                            , ownerPostalCode='Section1-postalZipCodeReceivingSiteOwner'
                            , ownerPhoneNumber='Section1-PhoneReceivingSiteOwner'
                            , ownerEmail='Section1-EmailReceivingSiteOwner'
                            , owner2FirstName='Section1a-FirstNameAdditionalOwner'
                            , owner2LastName='Section1A-LastNameAdditionalOwner'
                            , owner2Company='Section1A-CompanyAdditionalOwner'
                            , owner2Address='Section1A-AddressAdditionalOwner'
                            , owner2City='Section1A-CityAdditionalOwner'
                            , owner2Province='Section1A-ProvinceStateAdditionalOwner'
                            , owner2Country='Section1A-CountryAdditionalOwner'
                            , owner2PostalCode='Section1A-PostalZipCodeAdditionalOwner'
                            , owner2PhoneNumber='Section1A-PhoneAdditionalOwner'
                            , owner2Email='Section1A-EmailAdditionalOwner'
                            , additionalOwners='areThereMoreThanTwoOwnersIncludeTheirInformationBelow'
                            , contactFirstName='Section2-firstNameRSC'
                            , contactLastName='Section2-lastNameRSC'
                            , contactCompany='Section2-organizationRSC'
                            , contactAddress='Section2-streetAddressRSC'
                            , contactCity='Section2-cityRSC'
                            , contactProvince='Section2-provinceStateRSC'
                            , contactCountry='Section2-countryRSC'
                            , contactPostalCode='Section2-postalZipCodeRSC'
                            , contactPhoneNumber='section2phoneNumberRSC'
                            , contactEmail='Section2-simpleemailRSC'
                            , SID='Section3-siteIdIncludeAllRelatedNumbers'
                            , legallyTitledSiteAddress='Section3-LegallyTitled-Address'
                            , legallyTitledSiteCity='Section3-LegallyTitled-City'
                            , legallyTitledSitePostalCode='Section3-LegallyTitled-PostalZipCode'
                            , crownLandFileNumbers='A-UntitledCrownLand-FileNumberColumn'
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
                            , qualifiedProfessionalFirstName='Section5-FirstNameQualifiedProfessional'
                            , qualifiedProfessionalLastName='Section5-LastName1QualifiedProfessional'
                            , qualifiedProfessionalType='Section5-TypeofQP'
                            , professionalLicenceRegistration='Section5-professionalLicenseRegistrationEGPEngRpBio'
                            , qualifiedProfessionalOrganization='Section5-organizationQualifiedProfessional'
                            , qualifiedProfessionalAddress='Section5-streetAddressQualifiedProfessional'
                            , qualifiedProfessionalCity='Section5-cityQualifiedProfessional'
                            , qualifiedProfessionalProvince='Section5-provinceStateQualifiedProfessional'
                            , qualifiedProfessionalCountry='Section5-countryQualifiedProfessional'
                            , qualifiedProfessionalPostalCode='Section5-postalZipCodeQualifiedProfessional'
                            , qualifiedProfessionalPhoneNumber='simplephonenumber1QualifiedProfessional'
                            , qualifiedProfessionalEmail='simpleemail1QualifiedProfessional'
                            , signaturerFirstAndLastName='firstAndLastNameQualifiedProfessional'
                            , dateSigned='simpledatetime'
                            , form='form'
                            , createdAt='createdAt'
                            , confirmationId='confirmationId')
SOURCE_SITE_HEADERS = ["updateToPreviousForm",
                       "previousConfirmCode",
                       "industrialOrCommercialUses",
                       "ownerFirstName",
                       "ownerLastName",
                       "ownerCompany",
                       "ownerAddress",
                       "ownerCity",
                       "ownerProvince",
                       "ownerCountry",
                       "ownerPostalCode",
                       "ownerPhoneNumber",
                       "ownerEmail",
                       "owner2FirstName",
                       "owner2LastName",
                       "owner2Company",
                       "owner2Address",
                       "owner2City",
                       "owner2Province",
                       "owner2Country",
                       "owner2PostalCode",
                       "owner2PhoneNumber",
                       "owner2Email",
                       "additionalOwners",
                       "contactFirstName",
                       "contactLastName",
                       "contactCompany",
                       "contactAddress",
                       "contactCity",
                       "contactProvince",
                       "contactCountry",
                       "contactPostalCode",
                       "contactPhoneNumber",
                       "contactEmail",
                       "SID",
                       "latitude",
                       "longitude",
                       "latitudeDegrees",
                       "latitudeMinutes",
                       "latitudeSeconds",
                       "longitudeDegrees",
                       "longitudeMinutes",
                       "longitudeSeconds",
                       "regionalDistrict",
                       "landOwnership",
                       "legallyTitledSiteAddress",
                       "legallyTitledSiteCity",
                       "legallyTitledSitePostalCode",
                       "PID",
                       "legalLandDescription",
                       "PIN",
                       "crownLandFileNumbers",
                       "receivingSite1Address",
                       "receivingSite1City",
                       "receivingSite2Address",
                       "receivingSite2City",
                       "receivingSite3Address",
                       "receivingSite3City",
                       "sourceSiteLandUse",
                       "highVolumeSite",
                       "soilRelocationPurpose",
                       "soilStorageType",
                       "industrialLandUseSoilVolume",
                       "commercialLandUseSoilVolume",
                       "residentialLandUseHighDensitySoilVolume",
                       "residentialLandUseLowDensitySoilVolume",
                       "urbanParkLandUseSoilVolume",
                       "agriculturalLandUseSoilVolume",
                       "wildlandsNaturalLandUseSoilVolume",
                       "wildlandsRevertedLandUseSoilVolume",
                       "totalSoilVolme",
                       "soilCharacterMethod",
                       "vapourExemption",
                       "vapourExemptionDesc",
                       "vapourCharacterMethodDesc",
                       "soilRelocationStartDate",
                       "soilRelocationCompletionDate",
                       "relocationMethod",
                       "qualifiedProfessionalFirstName",
                       "qualifiedProfessionalLastName",
                       "qualifiedProfessionalType",
                       "professionalLicenceRegistration",
                       "qualifiedProfessionalOrganization",
                       "qualifiedProfessionalAddress",
                       "qualifiedProfessionalCity",
                       "qualifiedProfessionalProvince",
                       "qualifiedProfessionalCountry",
                       "qualifiedProfessionalPostalCode",
                       "qualifiedProfessionalPhoneNumber",
                       "qualifiedProfessionalEmail",
                       "signaturerFirstAndLastName",
                       "dateSigned",
                       "createAt",
                       "confirmationId"]
RECEIVING_SITE_HEADERS = ["ownerFirstName",
                          "ownerLastName",
                          "ownerCompany",
                          "ownerAddress",
                          "ownerCity",
                          "ownerProvince",
                          "ownerCountry",
                          "ownerPostalCode",
                          "ownerPhoneNumber",
                          "ownerEmail",
                          "owner2FirstName",
                          "owner2LastName",
                          "owner2Company",
                          "owner2Address",
                          "owner2City",
                          "owner2Province",
                          "owner2Country",
                          "owner2PostalCode",
                          "owner2PhoneNumber",
                          "owner2Email",
                          "additionalOwners",
                          "contactFirstName",
                          "contactLastName",
                          "contactCompany",
                          "contactAddress",
                          "contactCity",
                          "contactProvince",
                          "contactCountry",
                          "contactPostalCode",
                          "contactPhoneNumber",
                          "contactEmail",
                          "SID",
                          "latitude",
                          "longitude",
                          "latitudeDegrees",
                          "latitudeMinutes",
                          "latitudeSeconds",
                          "longitudeDegrees",
                          "longitudeMinutes",
                          "longitudeSeconds",
                          "regionalDistrict",
                          "landOwnership",
                          "legallyTitledSiteAddress",
                          "legallyTitledSiteCity",
                          "legallyTitledSitePostalCode",
                          "PID",
                          "legalLandDescription",
                          "PIN",
                          "crownLandFileNumbers",
                          "sourceSiteAddress",
                          "sourceSiteCity",
                          "receivingSiteLandUse",
                          "industrialLandUseSoilVolume",
                          "commercialLandUseSoilVolume",
                          "residentialLandUseHighDensitySoilVolume",
                          "residentialLandUseLowDensitySoilVolume",
                          "urbanParkLandUseSoilVolume",
                          "agriculturalLandUseSoilVolume",
                          "wildlandsNaturalLandUseSoilVolume",
                          "wildlandsRevertedLandUseSoilVolume",
                          "totalSoilVolme",
                          "CSRFactors",
                          "relocatedSoilUse",
                          "highVolumeSite",
                          "soilDepositIsALR",
                          "soilDepositIsReserveLands",
                          "dateSigned",
                          "createAt",
                          "confirmationId",
                          "receivingSiteClass"]
HV_SITE_HEADERS = ["ownerFirstName",
                   "ownerLastName",
                   "ownerCompany",
                   "ownerAddress",
                   "ownerCity",
                   "ownerProvince",
                   "ownerCountry",
                   "ownerPostalCode",
                   "ownerPhoneNumber",
                   "ownerEmail",
                   "owner2FirstName",
                   "owner2LastName",
                   "owner2Company",
                   "owner2Address",
                   "owner2City",
                   "owner2Province",
                   "owner2Country",
                   "owner2PostalCode",
                   "owner2PhoneNumber",
                   "owner2Email",
                   "additionalOwners",
                   "contactFirstName",
                   "contactLastName",
                   "contactCompany",
                   "contactAddress",
                   "contactCity",
                   "contactProvince",
                   "contactCountry",
                   "contactPostalCode",
                   "contactPhoneNumber",
                   "contactEmail",
                   "SID",
                   "latitude",
                   "longitude",
                   "latitudeDegrees",
                   "latitudeMinutes",
                   "latitudeSeconds",
                   "longitudeDegrees",
                   "longitudeMinutes",
                   "longitudeSeconds",
                   "regionalDistrict",
                   "landOwnership",
                   "legallyTitledSiteAddress",
                   "legallyTitledSiteCity",
                   "legallyTitledSitePostalCode",
                   "PID",
                   "legalLandDescription",
                   "PIN",
                   "crownLandFileNumbers",
                   "receivingSiteLandUse",
                   "hvsConfirmation",
                   "dateSiteBecameHighVolume",
                   "howRelocatedSoilWillBeUsed",
                   "soilDepositIsALR",
                   "soilDepositIsReserveLands",
                   "qualifiedProfessionalFirstName",
                   "qualifiedProfessionalLastName",
                   "qualifiedProfessionalType",
                   "professionalLicenceRegistration",
                   "qualifiedProfessionalOrganization",
                   "qualifiedProfessionalAddress",
                   "qualifiedProfessionalCity",
                   "qualifiedProfessionalProvince",
                   "qualifiedProfessionalCountry",
                   "qualifiedProfessionalPostalCode",
                   "qualifiedProfessionalPhoneNumber",
                   "qualifiedProfessionalEmail",
                   "signaturerFirstAndLastName",
                   "dateSigned",
                   "createAt",
                   "confirmationId"]
