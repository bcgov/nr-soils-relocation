from urllib.parse import urlencode
import requests
from requests.auth import HTTPBasicAuth
import json
import csv
import smtplib
from email.message import EmailMessage
import datetime

# arcgis libraries
from arcgis.gis import GIS
from arcgis import features
import pandas as pd
import os
import datetime as dt
import shutil
from arcgis import geometry
from copy import deepcopy
import csv, os, time

# Move these to a configuration file
chefsUrl = 'https://chefs.nrs.gov.bc.ca/app/api/v1'

soilsFormId = 'e6083928-4bff-45b5-a447-2b9b59d61757'
hvsFormId = '83181b39-521b-4b9f-b089-f5c794bdcc80'
subscriptionFormId = '75a33b78-f20a-4d05-8eb6-96986604760b'

authUrl = 'https://dev.oidc.gov.bc.ca' # dev
# authUrl = 'https://test.oidc.gov.bc.ca' # test
# authUrl	= 'https://oidc.gov.bc.ca' # prod

chesUrl = 'https://ches-dev.apps.silver.devops.gov.bc.ca' # dev
# chesUrl = 'https://ches-test.apps.silver.devops.gov.bc.ca' # test
# chesUrl = 'https://ches.nrs.gov.bc.ca' # prod
# chesServiceClient = 'SRIS_SERVICE_CLIENT'

csvLocation = 'C:\GITHUB_REPOS\nr-soils-relocation'

arcgisUrl = 'https://governmentofbc.maps.arcgis.com'
arcgisUsername = 'PX.SRIS.CHEFSTOAGOL'

testSourceLats = ['53.89428','58.0151','57.07397','55.56444']
testSourceLons = ['-122.6543','-115.7708','-119.22593','-125.04611']


regionalDistrictDict = dict(regionalDistrictOfBulkleyNechako='Regional District of Bulkley-Nechako'
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

def send_mail(to_email, subject, message):
  to_email = 'rjeong@vividsolutions.com'
  authPayload = 'grant_type=client_credentials'
  authHaders = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': 'Basic ' + chesEncodedServiceClientKey
  }
  authResponse = requests.request("POST", authUrl + '/auth/realms/jbd6rnxw/protocol/openid-connect/token', headers=authHaders, data=authPayload)
  # print(authResponse.text)
  authResponseJson = json.loads(authResponse.content)
  accessToken = authResponseJson['access_token']

  from_email = "noreply@gov.bc.ca"
  chesPayload = "{\n \"bodyType\": \"html\",\n \"body\": \""+message+"\",\n \"delayTS\": 0,\n \"encoding\": \"utf-8\",\n \"from\": \""+from_email+"\",\n \"priority\": \"normal\",\n  \"subject\": \""+subject+"\",\n  \"to\": [\""+to_email+"\"]\n }\n"
  chesHeaders = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer ' + accessToken
  }
  chesResponse = requests.request("POST", chesUrl + '/api/v1/email', headers=chesHeaders, data=chesPayload)
  print(chesResponse.text)
  chesContent = json.loads(chesResponse.content)
  return chesContent

def is_json(string):
  try:
    json.loads(str(string))
  except ValueError as e:
    return False
  return True

def site_list(formId, formKey):
  request = requests.get(chefsUrl + '/forms/' + formId + '/export?format=json&type=submissions', auth=HTTPBasicAuth(formId, formKey), headers={'Content-type': 'application/json'})
  print('Parsing JSON response')
  content = json.loads(request.content)
  return content

def fetch_columns(formId, formKey):
  request = requests.get(chefsUrl + '/forms/' + formId + '/versions', auth=HTTPBasicAuth(formId, formKey), headers={'Content-type': 'application/json'})
  requestJson = json.loads(request.content)
  version = requestJson[0]['id']

  attributeRequest = requests.get(chefsUrl + '/forms/' + formId + '/versions/' + version + '/fields', auth=HTTPBasicAuth(formId, formKey), headers={'Content-type': 'application/json'})
  attributes = json.loads(attributeRequest.content)
  return attributes

def create_site_relocation_email_msg(regional_district):
  #<p>----------------------------------------------------------------------------------------------------------------------------------------</p>\
  msg = ''
  msg = '<p>This email is to notify you that soil is being relocated in the following Regional District: <span style=font-weight:bold;color:red;>' 
  msg += regional_district 
  msg += '</span></p>\
        <p>The following new submission(s) were received.<p/>\
        <p><a href=https://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=8a6afeae8fdd4960a0ea0df1fa34aa74&find=382011>Link to new submission</a><br/>\
        <a href=http://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=8a6afeae8fdd4960a0ea0df1fa34aa74&find=6810%20Random%20St.>Link to new submission</a></p><br/>\
        <p><hr style=height:1px;border-top:dotted;color:#000000;background-color:#000000;/></p>\
        <p><b>To search the <a href=https://soil-relocation-information-system-governmentofbc.hub.arcgis.com/>Soil Relocation Information System</a> (SRIS):</b></p>\
        <p>Click on the link above to access the web page containing information on soil movement from commercial and industrial sites in BC.</p>\
        Click &#8216;view&#8217; under the Soil Relocation Dashboard and follow the search instructions below:\
        <ul>\
          <li>click on the small arrow on the left of the screen  to open search options</li>\
          <li>Filter by site address, regional district, high volume sites, and more.</li>\
          <li>On the map, you can zoom to the area you interested in and click on a single location. This will bring up information on that site including the address, volume of soil being moved, start date and finish date of the soil movement.</li>\
          <li>On the map, you can also select a rectangular area and view data in csv format for all sites within that rectangle.</li>\
        </ul>\
        <p>You can also search for information on the Soil Relocation Site Map by clicking on &#8216;view&#8217; under the Soil relocation site map on the main page.'
  msg += '<hr style=border-top:dotted;/></p><br/><br/><br/>'
  msg += '<hr style=height:4px;border:none;color:#4da6ff;background-color:#4da6ff;/>'
  msg += '<span style=font-style:italic;color:#4da6ff;>You are receiving this email because you subscribed to receive email notifications of soil relocation or high-volume site registrations in select Regional Districts in BC. If you wish to stop receiving these email notifications, please select &#8216;unsubscribe&#8217; on the subscription <a href=https://chefs.nrs.gov.bc.ca/app/form/submit?f=' + subscriptionFormId + '>form</a></span>.<br/>'
  msg += '<hr style=height:4px;border:none;color:#4da6ff;background-color:#4da6ff;/>'
  return msg

def create_hv_site_email_msg(regional_district, linksToPopup):
  #<p>----------------------------------------------------------------------------------------------------------------------------------------</p>\
  msg = ''
  msg = '<p>This email is to notify you that a registration for a high volume soil receiving site has been received in the following Regional District: <span style=font-weight:bold;color:red;>'
  msg += regional_district
  msg += '</span></p>\
        <p>The following new high volume receiving site registration(s) were received.<p/>\
        <p>'
  msg += linksToPopup
  msg += '</p><br/>\
        <p><hr style=height:1px;border-top:dotted;color:#000000;background-color:#000000;/></p>\
        <p><b>To search the <a href=https://soil-relocation-information-system-governmentofbc.hub.arcgis.com/>Soil Relocation Information System</a> (SRIS):</b></p>\
        <p>Click on the link above to access the web page containing information on soil movement from commercial and industrial sites in BC.</p>\
        Click &#8216;view&#8217; under the Soil Relocation Dashboard and follow the search instructions below:\
        <ul>\
          <li>click on the small arrow on the left of the screen to open search options</li>\
          <li>Filter by site address, regional district, high volume sites, and more.</li>\
          <li>On the map, you can zoom to the area you interested in and click on a single location. This will bring up information on that site including the address, volume of soil being moved, start date and finish date of the soil movement</li>\
          <li>On the map, you can also select a rectangular area and view data in csv format for all sites within that rectangle.</li>\
        </ul>\
        <p>You can also search for information on the Soil Relocation Site Map by clicking on &#8216;view&#8217; under the Soil relocation site map on the main page.'
  msg += '<hr style=border-top:dotted;/></p><br/><br/><br/>'
  msg += '<hr style=height:4px;border:none;color:#4da6ff;background-color:#4da6ff;/>'
  msg += '<span style=font-style:italic;color:#4da6ff;>You are receiving this email because you subscribed to receive email notifications of soil relocation or high-volume site registrations in select Regional Districts in BC. If you wish to stop receiving these email notifications, please select &#8216;unsubscribe&#8217; on the subscription <a href=https://chefs.nrs.gov.bc.ca/app/form/submit?f=' + subscriptionFormId + '>form</a></span>.<br/>'
  msg += '<hr style=height:4px;border:none;color:#4da6ff;background-color:#4da6ff;/>'
  return msg

def convert_regional_district_to_name(id):
  name = regionalDistrictDict.get(id)
  if name is not None:
    return name
  else:
    return id

# high volumn soil receiving sites
def createLinkToPopupOnMapForHV(hv_sites):
  link_prx = '<a href=https://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=8a6afeae8fdd4960a0ea0df1fa34aa74&find='
  link_suf = '>Link to new high volume receiving site registration</a>'
  links = ''
  for hv_site in hv_sites:
    if hv_site[33] is not None : 
      links = addBRToLinks(links) + hv_site[33]  #Site ID
    #PID
    #PIN  
    #Receiver Address
    #Receiver 2 Address    
    #Receiver Zip/Postal Code
    #Receiver 2 Postal Code/Zip
    # Receiver Regional District
    # Receiver Organization  
    #Receiver 2 Organization    
    #Receiver City
    #Receiver 2 City    
    #Receiver Province/State
    #Receiver 2 Province/State    
    #Receiver Country
    #Receiver 2 Country



    #elif 



  return link

def addBRToLinks(links):
  if links is not None and (not links):
    links += '<br/>'
  return links

def convert_deciaml_lat_long(lat_deg, lat_min, lat_sec, lon_deg, lon_min, lon_sec):
  # Convert to DD in mapLatitude and mapLongitude
  data = []
  lat_dd = (float(lat_deg) + float(lat_min)/60 + float(lat_sec)/(60*60))
  lon_dd = - (float(lon_deg) + float(lon_min)/60 + float(lon_sec)/(60*60))

  data.append(lat_dd)
  data.append(lon_dd)

  return data

# Fetch subscribers list
print('Loading submission subscribers list...')
subscribersJson = site_list(subscriptionFormId, subscriptionKey)
# print(subscribersJson)
print('Loading submission subscribers attributes and headers...')
subscribeAttributes = fetch_columns(subscriptionFormId, subscriptionKey)
# print(subscribeAttributes)

print('Loading High Volume Sites list...')
hvsJson = site_list(hvsFormId, hvsKey)
# print(hvsJson)
print('Loading High Volume Sites attributes and headers...')
hvsAttributes = fetch_columns(hvsFormId, hvsKey)
# print(hvsAttributes)

# Fetch all submissions from chefs API
print('Loading Submissions List...')
submissionsJson = site_list(soilsFormId, soilsKey)
print(submissionsJson)
print('Loading Submission attributes and headers...')
soilsAttributes = fetch_columns(soilsFormId, soilsKey)
# print(soilsAttributes)

sourceSiteHeaders = [
  "A1_FIRSTName",
  "A1_LASTName",
  "A1_Company",
  "A1_Address",
  "A1_City",
  "A1_ProvinceState",
  "A1_Country",
  "A1_PostalZipCode",
  "A1_Phone",
  "A1_Email",
  "A1_checkbox_extraowners",
  "A1_additionalownerFIRSTName",
  "A1_additionalownerLASTName1",
  "A1_additionalownerCompany1",
  "A1_additionalownerAddress1",
  "A1_additionalownerCity1",
  "A1_additionalownerPhone1",
  "A1_additionalownerEmail1",
  "areThereMoreThanTwoOwnersIncludeTheirInformationBelow",
  "A1_SourceSiteContact_sameAsAbove",
  "A2_SourceSiteContactFirstName",
  "A2_SourceSiteContactLastName",
  "A2_SourceSiteContactCompany",
  "A2_SourceSiteContactAddress",
  "A2_SourceSiteContactCity",
  "SourceSiteContactphoneNumber",
  "A2_SourceSiteContactEmail",
  "A3_SourcesiteIdentificationNumberSiteIdIfAvailable",
  "A3_SourceSiteLatitude_Degrees",
  "A3_SourceSiteLatitude_Minutes",
  "A3_SourceSiteLatitude_Seconds",
  "A3_SourceSiteLongitude_Degrees",
  "A3_SourceSiteLongitude_Minutes",
  "A3_SourceSiteLongitude_Seconds",
  "SourcelandOwnership_checkbox",
  "A_LegallyTitled_AddressSource",
  "A_LegallyTitled_CitySource",
  "A_LegallyTitled_PostalZipCodeSource",
  "SourceSiteregionalDistrict",
  "dataGrid",
  "FirstAdditionalReceivingsiteuploadLandTitleRecord",
  "dataGrid1",
  "A_UntitledCrownLand_FileNumberColumnSource",
  "A_UntitledMunicipalLand_PIDColumnSource",
  "A4_schedule2ReferenceSourceSite",
  "isTheSourceSiteHighRisk",
  "A5_PurposeOfSoilExcavationSource",
  "B4_currentTypeOfSoilStorageEGStockpiledInSitu1Source",
  "dataGrid9",
  "B2_describeSoilCharacterizationMethod1",
  "uploadSoilAnalyticalData",
  "B3_yesOrNoVapourexemptionsource",
  "B3_ifExemptionsApplyPleaseDescribe",
  "B3_describeVapourCharacterizationMethod",
  "uploadVapourAnalyticalData1",
  "B4_soilRelocationEstimatedStartDateMonthDayYear",
  "B4_soilRelocationEstimatedCompletionDateMonthDayYear",
  "B4_RelocationMethod",
  "D1_FirstNameQualifiedProfessional",
  "LastNameQualifiedProfessional",
  "D1_TypeofQP1",
  "D1_professionalLicenseRegistrationEGPEngRpBio",
  "D1_organization1QualifiedProfessional",
  "D1_streetAddress1QualifiedProfessional",
  "D1_city1QualifiedProfessional",
  "D1_provinceState3QualifiedProfessional",
  "D1_canadaQualifiedProfessional",
  "D1_postalZipCode3QualifiedProfessional",
  "simplephonenumber1QualifiedProfessional",
  "EmailAddressQualifiedProfessional",
  "D2_soilDepositIsInTheAgriculturalLandReserveAlr",
  "D2_soilDepositIsInTheReserveLands",
  "createAt", # not in soilsAttributes, but in submissionsJson
  "confirmationId", # not in soilsAttributes, but in submissionsJson
  "A3_SourceSiteLatitude",
  "A3_SourceSiteLongitude"
]


receivingSiteHeaders = [
  "C1-FirstNameReceivingSiteOwner",
  "C1-LastNameReceivingSiteOwner",
  "C1-CompanyReceivingSiteOwner",
  "C1-AddressReceivingSiteOwner",
  "C1-CityReceivingSiteOwner",
  "C1-PhoneRecevingSiteOwner",
  "C1-EmailReceivingSiteOwner",
  "C1-checkbox-extraownersReceivingSite",
  "C1-FirstName1ReceivingSiteAdditionalOwners",
  "C1-LastName1ReceivingSiteAdditionalOwners",
  "C1-Company1ReceivingSiteAdditionalOwners",
  "C1-Address1ReceivingSiteAdditionalOwners",
  "C1-City1ReceivingSiteAdditionalOwners",
  "C1-Phone1ReceivingSiteAdditionalOwners",
  "C1-Email1ReceivingSiteAdditionalOwners",
  "haveMoreThatTwoOwnersEnterTheirInformationBelow",
  "receivingsitecontact-sameAsAbove",
  "C2-RSC-FirstName",
  "C2-RSC-LastName",
  "C2-RSC-Company",
  "C2-RSC-Address",
  "C2-RSC-City",
  "C2-RSCphoneNumber1",
  "C2-RSC-Email",
  "C2-siteIdentificationNumberSiteIdIfAvailableReceivingSite",
  "C2-Latitude-DegreesReceivingSite",
  "C2-Latitude-MinutesReceivingSite",
  "Section2-Latitude-Seconds1ReceivingSite",
  "C2-Longitude-DegreesReceivingSite",
  "C2-Longitude-MinutesReceivingSite",
  "C2-Longitude-SecondsReceivingSite",
  "ReceivingSiteregionalDistrict",
  "ReceivingSiteLocationMap",
  "C2-receivinglandOwnership-checkbox",
  "C2-LegallyTitled-AddressReceivingSite",
  "C2-LegallyTitled-CityReceivingSite",
  "C2-LegallyTitled-PostalReceivingSite",
  "dataGrid2",
  "ReceivingSiteLandTitleRecord",
  "dataGrid5",
  "A-UntitledCrownLand-FileNumberColumn1",
  "A-UntitledMunicipalLand-PIDColumn1",
  "C3-soilClassification1ReceivingSite",
  "C3-applicableSiteSpecificFactorsForCsrSchedule31ReceivingSite",
  "C3-applicableSiteSpecificFactorsForCsrSchedule32ReceivingSite",
  "C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime",
  "additionalReceivingSites",
  "C1-FirstName2FirstAdditionalReceivingSite",
  "C1-LastName2FirstAdditionalReceivingSite",
  "C1-Company2FirstAdditionalReceivingSite",
  "C1-Address2FirstAdditionalReceivingSite",
  "C1-City2FirstAdditionalReceivingSite",
  "phoneNumber4FirstAdditionalReceivingSite",
  "C1-Email2FirstAdditionalReceivingSite",
  "Firstadditionalreceiving-checkbox-extraowners1",
  "C1-FirstName3AdditionalReceivingSiteOwner",
  "C1-LastName3AdditionalReceivingSiteOwner",
  "C1-Company3AdditionalReceivingSiteOwner",
  "C1-Address3AdditionalReceivingSiteOwner",
  "C1-City3AdditionalReceivingSiteOwner",
  "phoneNumber2AdditionalReceivingSiteOwner",
  "C1-Email3AdditionalReceivingSiteOwner",
  "C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow2ReceivingSite",
  "Firstadditionalcontactperson-sameAsAbove1",
  "C2-RSC-FirstName1AdditionalReceivingSite",
  "C2-RSC-LastName1AdditionalReceivingSite",
  "C2-RSC-Company1AdditionalReceivingSite",
  "C2-RSC-Address1AdditionalReceivingSite",
  "C2-RSC-City1AdditionalReceivingSite",
  "phoneNumber3AdditionalReceivingSite",
  "C2-RSC-Email1AdditionalReceivingSite",
  "C2-siteIdentificationNumberSiteIdIfAvailable1FirstAdditionalReceivingSite",
  "C2-Latitude-Degrees1FirstAdditionalReceivingSite",
  "C2-Latitude-Minutes1FirstAdditionalReceivingSite",
  "Section2-Latitude-Seconds2FirstAdditionalReceivingSite",
  "C2-Longitude-Degrees1FirstAdditionalReceivingSite",
  "C2-Longitude-Minutes1FirstAdditionalReceivingSite",
  "C2-Longitude-Seconds1FirstAdditionalReceivingSite",
  "FirstAdditionalReceivingSiteregionalDistrict1",
  "FirstAdditionalReceivingSiteLocationMap",
  "Firstadditionalreceiving-landOwnership-checkbox1",
  "C2-LegallyTitled-Address1FirstAdditionalReceivingSite",
  "C2-LegallyTitled-City1FirstAdditionalReceivingSite",
  "C2-LegallyTitled-PostalZipCode1FirstAdditionalReceivingSite",
  "dataGrid3",
  "FirstAdditionalReceivingSiteLandTitle",
  "dataGrid6",
  "A-UntitledCrownLand-FileNumberColumn2",
  "A-UntitledMunicipalLand-PIDColumn2",
  "C3-soilClassification2FirstAdditionalReceivingSite",
  "C3-applicableSiteSpecificFactorsForCsrSchedule33FirstAdditionalReceivingSite",
  "C3-applicableSiteSpecificFactorsForCsrSchedule34FirstAdditionalReceivingSite",
  "C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1",
  "secondadditionalReceivingSites1",
  "C1-FirstName6SecondAdditionalreceivingSite",
  "C1-LastName6SecondAdditionalreceivingSite",
  "C1-Company6SecondAdditionalreceivingSite",
  "C1-Address6SecondAdditionalreceivingSite",
  "C1-City6SecondAdditionalreceivingSite",
  "phoneNumber7SecondAdditionalreceivingSite",
  "C1-Email6SecondAdditionalreceivingSite",
  "secondadditionalreceivingsiteC1-checkbox-extraowners3",
  "C1-FirstName7SecondAdditionalreceivingSite",
  "C1-LastName7SecondAdditionalreceivingSite",
  "C1-Company7SecondAdditionalreceivingSite",
  "C1-Address7SecondAdditionalreceivingSite",
  "C1-City7SecondAdditionalreceivingSite",
  "phoneNumber5SecondAdditionalreceivingSite",
  "C1-Email7SecondAdditionalreceivingSite",
  "C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow4SecondAdditionalreceivingSite",
  "secondadditionalreceivingsiteContactperson-sameAsAbove3",
  "C2-RSC-FirstName3SecondAdditionalreceivingSite",
  "C2-RSC-LastName3SecondAdditionalreceivingSite",
  "C2-RSC-Company3SecondAdditionalreceivingSite",
  "C2-RSC-Address3SecondAdditionalreceivingSite",
  "C2-RSC-City3SecondAdditionalreceivingSite",
  "phoneNumber6SecondAdditionalreceivingSite",
  "C2-RSC-Email3SecondAdditionalreceivingSite",
  "C2-siteIdentificationNumberSiteIdIfAvailable3SecondAdditionalreceivingSite",
  "C2-Latitude-Degrees3SecondAdditionalreceivingSite",
  "C2-Latitude-Minutes3SecondAdditionalreceivingSite",
  "Section2-Latitude-Seconds4SecondAdditionalreceivingSite",
  "C2-Longitude-Degrees3SecondAdditionalreceivingSite",
  "C2-Longitude-Minutes3SecondAdditionalreceivingSite",
  "C2-Longitude-Seconds3SecondAdditionalreceivingSite",
  "SecondAdditionalReceivingSiteregionalDistrict",
  "SecondAdditionalReceivingSiteLocationMap",
  "Secondadditionalreceiving-landOwnership-checkbox3",
  "C2-LegallyTitled-Address3SecondAdditionalreceivingSite",
  "C2-LegallyTitled-City3SecondAdditionalreceivingSite",
  "C2-LegallyTitled-PostalZipCode3SecondAdditionalreceivingSite",
  "dataGrid4",
  "SecondAdditionalReceivingSiteLandTitle2",
  "dataGrid7",
  "A-UntitledCrownLand-FileNumberColumn3",
  "A-UntitledMunicipalLand-PIDColumn3",
  "C3-soilClassification4SecondAdditionalreceivingSite",
  "C3-applicableSiteSpecificFactorsForCsrSchedule37SecondAdditionalreceivingSite",
  "C3-applicableSiteSpecificFactorsForCsrSchedule38SecondAdditionalreceivingSite",
  "C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime3",
  "createAt", # not in soilsAttributes, but in submissionsJson
  "confirmationId" # not in soilsAttributes, but in submissionsJson
]

hvSiteHeaders = [
  "Section1-FirstNameReceivingSiteOwner",
  "Section1-LastNameReceivingSiteOwner",
  "Section1-CompanyReceivingSiteOwner",
  "Section1-AddressReceivingSiteOwner",
  "Section1-CityReceivingSiteOwner",
  "Section1-provinceStateReceivingSiteOwner",
  "Section1-countryReceivingSiteOwner",
  "Section1-postalZipCodeReceivingSiteOwner",
  "Section1-PhoneReceivingSiteOwner",
  "Section1-EmailReceivingSiteOwner",
  "Section1-checkbox-extraowners",
  "Section1a-FirstNameAdditionalOwner",
  "Section1A-LastNameAdditionalOwner",
  "Section1A-CompanyAdditionalOwner",
  "Section1A-AddressAdditionalOwner",
  "Section1A-CityAdditionalOwner",
  "Section1A-ProvinceStateAdditionalOwner",
  "Section1A-CountryAdditionalOwner",
  "Section1A-PostalZipCodeAdditionalOwner",
  "Section1A-PhoneAdditionalOwner",
  "Section1A-EmailAdditionalOwner",
  "areThereMoreThanTwoOwnersIncludeTheirInformationBelow",
  "receivingsitecontact",
  "Section2-firstNameRSC",
  "Section2-lastNameRSC",
  "Section2-organizationRSC",
  "Section2-streetAddressRSC",
  "Section2-cityRSC",
  "Section2-provinceStateRSC",
  "Section2-countryRSC",
  "Section2-postalZipCodeRSC",
  "section2phoneNumberRSC",
  "Section2-simpleemailRSC",
  "Section3-siteIdIncludeAllRelatedNumbers",
  "Section3-Latitude-Degrees",
  "Section3-Latitude-Minutes",
  "Section3-Latitude-Seconds",
  "Section3-Longitude-Degrees",
  "Section3-Longitude-Minutes",
  "Section3-Longitude-Seconds",
  "ReceivingSiteregionalDistrict",
  "uploadMapOfHighVolumeSiteLocation",
  "landOwnership-checkbox",
  "Section3-LegallyTitled-Address",
  "Section3-LegallyTitled-City",
  "Section3-LegallyTitled-PostalZipCode",
  "dataGrid",
  "uploadMapOfHighVolumeSiteLocation1",
  "dataGrid1",
  "A-UntitledCrownLand-FileNumberColumn",
  "A-UntitledMunicipalLand-PIDColumn",
  "primarylanduse",
  "highVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime",
  "dateSiteBecameHighVolume",
  "howrelocatedsoilwillbeused",
  "soilDepositIsInTheAgriculturalLandReserveAlr1",
  "receivingSiteIsOnReserveLands1",
  "Section5-FirstNameQualifiedProfessional",
  "Section5-LastName1QualifiedProfessional",
  "Section5-TypeofQP",
  "Section5-organizationQualifiedProfessional",
  "Section5-professionalLicenseRegistrationEGPEngRpBio",
  "Section5-streetAddressQualifiedProfessional",
  "Section5-cityQualifiedProfessional",
  "Section5-provinceStateQualifiedProfessional",
  "Section5-countryQualifiedProfessional",
  "Section5-postalZipCodeQualifiedProfessional",
  "simplephonenumber1QualifiedProfessional",
  "simpleemail1QualifiedProfessional",
  "firstAndLastNameQualifiedProfessional",
  "createAt", # not in hvsAttributes, but in hvsJson
  "confirmationId" # not in hvsAttributes, but in hvsJson
]

sourceSites = [] # [''] * len(submissionsJson)
receivingSites = [] # [''] * len(submissionsJson)
sitesDic = {}
sourceSiteLatLon = []
testingCount = 0
# create source site, destination site records
for submission in submissionsJson:
  # print(submission)

  # Map submission data to the source site
  sourceSiteData = [''] * 76
  if submission.get("A1-FIRSTName") is not None : sourceSiteData[0] = submission["A1-FIRSTName"]
  if submission.get("A1-LASTName") is not None : sourceSiteData[1] = submission["A1-LASTName"]
  if submission.get("A1-Company") is not None : sourceSiteData[2] = submission["A1-Company"]
  if submission.get("A1-Address") is not None : sourceSiteData[3] = submission["A1-Address"]
  if submission.get("A1-City") is not None : sourceSiteData[4] = submission["A1-City"]
  if submission.get("A1-ProvinceState") is not None : sourceSiteData[5] = submission["A1-ProvinceState"]
  if submission.get("A1-Country") is not None : sourceSiteData[6] = submission["A1-Country"]
  if submission.get("A1-PostalZipCode") is not None : sourceSiteData[7] = submission["A1-PostalZipCode"]
  if submission.get("A1-Phone") is not None : sourceSiteData[8] = submission["A1-Phone"]
  if submission.get("A1-Email") is not None : sourceSiteData[9] = submission["A1-Email"]
  if submission.get("A1-checkbox-extraowners") is not None : sourceSiteData[10] = submission["A1-checkbox-extraowners"]
  if submission.get("A1-additionalownerFIRSTName") is not None : sourceSiteData[11] = submission["A1-additionalownerFIRSTName"] #
  if submission.get("A1-additionalownerLASTName1") is not None : sourceSiteData[12] = submission["A1-additionalownerLASTName1"] #
  if submission.get("A1-additionalownerCompany1") is not None : sourceSiteData[13] = submission["A1-additionalownerCompany1"] #
  if submission.get("A1-additionalownerAddress1") is not None : sourceSiteData[14] = submission["A1-additionalownerAddress1"] #
  if submission.get("A1-additionalownerCity1") is not None : sourceSiteData[15] = submission["A1-additionalownerCity1"] #
  if submission.get("A1-additionalownerPhone1") is not None : sourceSiteData[16] = submission["A1-additionalownerPhone1"] #
  if submission.get("A1-additionalownerEmail1") is not None : sourceSiteData[17] = submission["A1-additionalownerEmail1"] #
  if submission.get("areThereMoreThanTwoOwnersIncludeTheirInformationBelow") is not None : sourceSiteData[18] = submission["areThereMoreThanTwoOwnersIncludeTheirInformationBelow"]
  if submission.get("A1-SourceSiteContact-sameAsAbove") is not None : sourceSiteData[19] = submission["A1-SourceSiteContact-sameAsAbove"]
  if submission.get("A2-SourceSiteContactFirstName") is not None : sourceSiteData[20] = submission["A2-SourceSiteContactFirstName"]
  if submission.get("A2-SourceSiteContactLastName") is not None : sourceSiteData[21] = submission["A2-SourceSiteContactLastName"]
  if submission.get("A2-SourceSiteContactCompany") is not None : sourceSiteData[22] = submission["A2-SourceSiteContactCompany"]
  if submission.get("A2-SourceSiteContactAddress") is not None : sourceSiteData[23] = submission["A2-SourceSiteContactAddress"]
  if submission.get("A2-SourceSiteContactCity") is not None : sourceSiteData[24] = submission["A2-SourceSiteContactCity"]
  if submission.get("SourceSiteContactphoneNumber") is not None : sourceSiteData[25] = submission["SourceSiteContactphoneNumber"]
  if submission.get("A2-SourceSiteContactEmail") is not None : sourceSiteData[26] = submission["A2-SourceSiteContactEmail"]
  if submission.get("A3-SourcesiteIdentificationNumberSiteIdIfAvailable") is not None : sourceSiteData[27] = submission["A3-SourcesiteIdentificationNumberSiteIdIfAvailable"]
  if submission.get("A3-SourceSiteLatitude-Degrees") is not None : sourceSiteData[28] = submission["A3-SourceSiteLatitude-Degrees"]
  if submission.get("A3-SourceSiteLatitude-Minutes") is not None : sourceSiteData[29] = submission["A3-SourceSiteLatitude-Minutes"]
  if submission.get("A3-SourceSiteLatitude-Seconds") is not None : sourceSiteData[30] = submission["A3-SourceSiteLatitude-Seconds"]
  if submission.get("A3-SourceSiteLongitude-Degrees") is not None : sourceSiteData[31] = submission["A3-SourceSiteLongitude-Degrees"]
  if submission.get("A3-SourceSiteLongitude-Minutes") is not None : sourceSiteData[32] = submission["A3-SourceSiteLongitude-Minutes"]
  if submission.get("A3-SourceSiteLongitude-Seconds") is not None : sourceSiteData[33] = submission["A3-SourceSiteLongitude-Seconds"]
  if submission.get("SourcelandOwnership-checkbox") is not None : sourceSiteData[34] = submission["SourcelandOwnership-checkbox"]
  if submission.get("A-LegallyTitled-AddressSource") is not None : sourceSiteData[35] = submission["A-LegallyTitled-AddressSource"]
  if submission.get("A-LegallyTitled-CitySource") is not None : sourceSiteData[36] = submission["A-LegallyTitled-CitySource"]
  if submission.get("A-LegallyTitled-PostalZipCodeSource") is not None : sourceSiteData[37] = submission["A-LegallyTitled-PostalZipCodeSource"]
  if submission.get("SourceSiteregionalDistrict") is not None : sourceSiteData[38] = submission["SourceSiteregionalDistrict"]
  #if submission.get("dataGrid") is not None : sourceSiteData[39] = submission["dataGrid"]
  #if submission.get("FirstAdditionalReceivingsiteuploadLandTitleRecord") is not None : sourceSiteData[40] = submission["FirstAdditionalReceivingsiteuploadLandTitleRecord"]
  #if submission.get("dataGrid1") is not None : sourceSiteData[41] = submission["dataGrid1"]
  #if submission.get("A-UntitledCrownLand-FileNumberColumnSource") is not None : sourceSiteData[42] = submission["A-UntitledCrownLand-FileNumberColumnSource"]
  #if submission.get("A-UntitledMunicipalLand-PIDColumnSource") is not None : sourceSiteData[43] = submission["A-UntitledMunicipalLand-PIDColumnSource"]
  #if submission.get("A4-schedule2ReferenceSourceSite") is not None : sourceSiteData[44] = submission["A4-schedule2ReferenceSourceSite"]
  if submission.get("isTheSourceSiteHighRisk") is not None : sourceSiteData[45] = submission["isTheSourceSiteHighRisk"]
  if submission.get("A5-PurposeOfSoilExcavationSource") is not None : sourceSiteData[46] = submission["A5-PurposeOfSoilExcavationSource"]
  if submission.get("B4-currentTypeOfSoilStorageEGStockpiledInSitu1Source") is not None : sourceSiteData[47] = submission["B4-currentTypeOfSoilStorageEGStockpiledInSitu1Source"]
  #if submission.get("dataGrid9") is not None : sourceSiteData[48] = submission["dataGrid9"]
  if submission.get("B2-describeSoilCharacterizationMethod1") is not None : sourceSiteData[49] = submission["B2-describeSoilCharacterizationMethod1"]
  #if submission.get("uploadSoilAnalyticalData") is not None : sourceSiteData[50] = submission["uploadSoilAnalyticalData"]
  if submission.get("B3-yesOrNoVapourexemptionsource") is not None : sourceSiteData[51] = submission["B3-yesOrNoVapourexemptionsource"]
  if submission.get("B3-ifExemptionsApplyPleaseDescribe") is not None : sourceSiteData[52] = submission["B3-ifExemptionsApplyPleaseDescribe"]
  if submission.get("B3-describeVapourCharacterizationMethod") is not None : sourceSiteData[53] = submission["B3-describeVapourCharacterizationMethod"]
  #if submission.get("uploadVapourAnalyticalData1") is not None : sourceSiteData[54] = submission["uploadVapourAnalyticalData1"]
  if submission.get("B4-soilRelocationEstimatedStartDateMonthDayYear") is not None : sourceSiteData[55] = submission["B4-soilRelocationEstimatedStartDateMonthDayYear"]
  if submission.get("B4-soilRelocationEstimatedCompletionDateMonthDayYear") is not None : sourceSiteData[56] = submission["B4-soilRelocationEstimatedCompletionDateMonthDayYear"]
  if submission.get("B4-RelocationMethod") is not None : sourceSiteData[57] = submission["B4-RelocationMethod"]
  if submission.get("D1-FirstNameQualifiedProfessional") is not None : sourceSiteData[58] = submission["D1-FirstNameQualifiedProfessional"]
  if submission.get("LastNameQualifiedProfessional") is not None : sourceSiteData[59] = submission["LastNameQualifiedProfessional"]
  if submission.get("D1-TypeofQP1") is not None : sourceSiteData[60] = submission["D1-TypeofQP1"]
  if submission.get("D1-professionalLicenseRegistrationEGPEngRpBio") is not None : sourceSiteData[61] = submission["D1-professionalLicenseRegistrationEGPEngRpBio"]
  if submission.get("D1-organization1QualifiedProfessional") is not None : sourceSiteData[62] = submission["D1-organization1QualifiedProfessional"]
  if submission.get("D1-streetAddress1QualifiedProfessional") is not None : sourceSiteData[63] = submission["D1-streetAddress1QualifiedProfessional"]
  if submission.get("D1-city1QualifiedProfessional") is not None : sourceSiteData[64] = submission["D1-city1QualifiedProfessional"]
  if submission.get("D1-provinceState3QualifiedProfessional") is not None : sourceSiteData[65] = submission["D1-provinceState3QualifiedProfessional"]
  if submission.get("D1-canadaQualifiedProfessional") is not None : sourceSiteData[66] = submission["D1-canadaQualifiedProfessional"]
  if submission.get("D1-postalZipCode3QualifiedProfessional") is not None : sourceSiteData[67] = submission["D1-postalZipCode3QualifiedProfessional"]
  if submission.get("simplephonenumber1QualifiedProfessional") is not None : sourceSiteData[68] = submission["simplephonenumber1QualifiedProfessional"]
  if submission.get("EmailAddressQualifiedProfessional") is not None : sourceSiteData[69] = submission["EmailAddressQualifiedProfessional"]
  if submission.get("D2-soilDepositIsInTheAgriculturalLandReserveAlr") is not None : sourceSiteData[70] = submission["D2-soilDepositIsInTheAgriculturalLandReserveAlr"]
  if submission.get("D2-soilDepositIsInTheReserveLands") is not None : sourceSiteData[71] = submission["D2-soilDepositIsInTheReserveLands"]
  if submission.get("form") is not None : 
    formStr = json.dumps(submission.get("form"))
    formJson = json.loads(formStr)
    createdAt = datetime.datetime.strptime(formJson['createdAt'], "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo = None, hour = 0, minute = 0, second = 0, microsecond = 0) # remove the timezone awareness
    confirmationId = formJson['confirmationId']
    # not in attributes, but in json
    if createdAt is not None : sourceSiteData[72] = createdAt
    if confirmationId is not None : sourceSiteData[73] = confirmationId

  sourceSiteLatLon = convert_deciaml_lat_long(sourceSiteData[28], sourceSiteData[29], sourceSiteData[30], sourceSiteData[31], sourceSiteData[32], sourceSiteData[33])

  #for testing
  #sourceSiteData[74] = sourceSiteLatLon[0] # source site latitude
  #sourceSiteData[75] = sourceSiteLatLon[1] # source site longitude
  sourceSiteData[74] = testSourceLats[testingCount]
  sourceSiteData[75] = testSourceLons[testingCount]
  testingCount = testingCount +1

  sourceSites.append(sourceSiteData)



  # Map submission data to the receiving site
  receivingSiteData = [''] * 142
  rcvIdx = 0
  if submission.get("C1-FirstNameReceivingSiteOwner") is not None : receivingSiteData[0] = submission["C1-FirstNameReceivingSiteOwner"]
  if submission.get("C1-LastNameReceivingSiteOwner") is not None : receivingSiteData[1] = submission["C1-LastNameReceivingSiteOwner"]
  if submission.get("C1-CompanyReceivingSiteOwner") is not None : receivingSiteData[2] = submission["C1-CompanyReceivingSiteOwner"]
  if submission.get("C1-AddressReceivingSiteOwner") is not None : receivingSiteData[3] = submission["C1-AddressReceivingSiteOwner"]
  if submission.get("C1-CityReceivingSiteOwner") is not None : receivingSiteData[4] = submission["C1-CityReceivingSiteOwner"]
  if submission.get("C1-PhoneRecevingSiteOwner") is not None : receivingSiteData[5] = submission["C1-PhoneRecevingSiteOwner"]
  if submission.get("C1-EmailReceivingSiteOwner") is not None : receivingSiteData[6] = submission["C1-EmailReceivingSiteOwner"]
  if submission.get("C1-checkbox-extraownersReceivingSite") is not None : receivingSiteData[7] = submission["C1-checkbox-extraownersReceivingSite"]
  if submission.get("C1-FirstName1ReceivingSiteAdditionalOwners") is not None : receivingSiteData[8] = submission["C1-FirstName1ReceivingSiteAdditionalOwners"]
  if submission.get("C1-LastName1ReceivingSiteAdditionalOwners") is not None : receivingSiteData[9] = submission["C1-LastName1ReceivingSiteAdditionalOwners"]
  if submission.get("C1-Company1ReceivingSiteAdditionalOwners") is not None : receivingSiteData[10] = submission["C1-Company1ReceivingSiteAdditionalOwners"]
  if submission.get("C1-Address1ReceivingSiteAdditionalOwners") is not None : receivingSiteData[11] = submission["C1-Address1ReceivingSiteAdditionalOwners"]
  if submission.get("C1-City1ReceivingSiteAdditionalOwners") is not None : receivingSiteData[12] = submission["C1-City1ReceivingSiteAdditionalOwners"]
  if submission.get("C1-Phone1ReceivingSiteAdditionalOwners") is not None : receivingSiteData[13] = submission["C1-Phone1ReceivingSiteAdditionalOwners"]
  if submission.get("C1-Email1ReceivingSiteAdditionalOwners") is not None : receivingSiteData[14] = submission["C1-Email1ReceivingSiteAdditionalOwners"]
  if submission.get("haveMoreThatTwoOwnersEnterTheirInformationBelow") is not None : receivingSiteData[15] = submission["haveMoreThatTwoOwnersEnterTheirInformationBelow"]
  if submission.get("receivingsitecontact-sameAsAbove") is not None : receivingSiteData[16] = submission["receivingsitecontact-sameAsAbove"]
  if submission.get("C2-RSC-FirstName") is not None : receivingSiteData[17] = submission["C2-RSC-FirstName"]
  if submission.get("C2-RSC-LastName") is not None : receivingSiteData[18] = submission["C2-RSC-LastName"]
  if submission.get("C2-RSC-Company") is not None : receivingSiteData[19] = submission["C2-RSC-Company"]
  if submission.get("C2-RSC-Address") is not None : receivingSiteData[20] = submission["C2-RSC-Address"]
  if submission.get("C2-RSC-City") is not None : receivingSiteData[21] = submission["C2-RSC-City"]
  if submission.get("C2-RSCphoneNumber1") is not None : receivingSiteData[22] = submission["C2-RSCphoneNumber1"]
  if submission.get("C2-RSC-Email") is not None : receivingSiteData[23] = submission["C2-RSC-Email"]
  if submission.get("C2-siteIdentificationNumberSiteIdIfAvailableReceivingSite") is not None : receivingSiteData[24] = submission["C2-siteIdentificationNumberSiteIdIfAvailableReceivingSite"]
  if submission.get("C2-Latitude-DegreesReceivingSite") is not None : receivingSiteData[25] = submission["C2-Latitude-DegreesReceivingSite"]
  if submission.get("C2-Latitude-MinutesReceivingSite") is not None : receivingSiteData[26] = submission["C2-Latitude-MinutesReceivingSite"]
  if submission.get("Section2-Latitude-Seconds1ReceivingSite") is not None : receivingSiteData[27] = submission["Section2-Latitude-Seconds1ReceivingSite"]
  if submission.get("C2-Longitude-DegreesReceivingSite") is not None : receivingSiteData[28] = submission["C2-Longitude-DegreesReceivingSite"]
  if submission.get("C2-Longitude-MinutesReceivingSite") is not None : receivingSiteData[29] = submission["C2-Longitude-MinutesReceivingSite"]
  if submission.get("C2-Longitude-SecondsReceivingSite") is not None : receivingSiteData[30] = submission["C2-Longitude-SecondsReceivingSite"]
  if submission.get("ReceivingSiteregionalDistrict") is not None : receivingSiteData[31] = submission["ReceivingSiteregionalDistrict"]
  if submission.get("ReceivingSiteLocationMap") is not None : receivingSiteData[32] = submission["ReceivingSiteLocationMap"]
  if submission.get("C2-receivinglandOwnership-checkbox") is not None : receivingSiteData[33] = submission["C2-receivinglandOwnership-checkbox"]
  if submission.get("C2-LegallyTitled-AddressReceivingSite") is not None : receivingSiteData[34] = submission["C2-LegallyTitled-AddressReceivingSite"]
  if submission.get("C2-LegallyTitled-CityReceivingSite") is not None : receivingSiteData[35] = submission["C2-LegallyTitled-CityReceivingSite"]
  if submission.get("C2-LegallyTitled-PostalReceivingSite") is not None : receivingSiteData[36] = submission["C2-LegallyTitled-PostalReceivingSite"]
  if submission.get("dataGrid2") is not None : receivingSiteData[37] = submission["dataGrid2"]
  if submission.get("ReceivingSiteLandTitleRecord") is not None : receivingSiteData[38] = submission["ReceivingSiteLandTitleRecord"]
  if submission.get("dataGrid5") is not None : receivingSiteData[39] = submission["dataGrid5"]
  if submission.get("A-UntitledCrownLand-FileNumberColumn1") is not None : receivingSiteData[40] = submission["A-UntitledCrownLand-FileNumberColumn1"]
  if submission.get("A-UntitledMunicipalLand-PIDColumn1") is not None : receivingSiteData[41] = submission["A-UntitledMunicipalLand-PIDColumn1"]
  if submission.get("C3-soilClassification1ReceivingSite") is not None : receivingSiteData[42] = submission["C3-soilClassification1ReceivingSite"]
  if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule31ReceivingSite") is not None : receivingSiteData[43] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule31ReceivingSite"]
  if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule32ReceivingSite") is not None : receivingSiteData[44] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule32ReceivingSite"]
  if submission.get("C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime") is not None : receivingSiteData[45] = submission["C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime"]
  if submission.get("additionalReceivingSites") is not None : receivingSiteData[46] = submission["additionalReceivingSites"]
  if submission.get("C1-FirstName2FirstAdditionalReceivingSite") is not None : receivingSiteData[47] = submission["C1-FirstName2FirstAdditionalReceivingSite"]
  if submission.get("C1-LastName2FirstAdditionalReceivingSite") is not None : receivingSiteData[48] = submission["C1-LastName2FirstAdditionalReceivingSite"]
  if submission.get("C1-Company2FirstAdditionalReceivingSite") is not None : receivingSiteData[49] = submission["C1-Company2FirstAdditionalReceivingSite"]
  if submission.get("C1-Address2FirstAdditionalReceivingSite") is not None : receivingSiteData[50] = submission["C1-Address2FirstAdditionalReceivingSite"]
  if submission.get("C1-City2FirstAdditionalReceivingSite") is not None : receivingSiteData[51] = submission["C1-City2FirstAdditionalReceivingSite"]
  if submission.get("phoneNumber4FirstAdditionalReceivingSite") is not None : receivingSiteData[52] = submission["phoneNumber4FirstAdditionalReceivingSite"]
  if submission.get("C1-Email2FirstAdditionalReceivingSite") is not None : receivingSiteData[53] = submission["C1-Email2FirstAdditionalReceivingSite"]
  if submission.get("Firstadditionalreceiving-checkbox-extraowners1") is not None : receivingSiteData[54] = submission["Firstadditionalreceiving-checkbox-extraowners1"]
  if submission.get("C1-FirstName3AdditionalReceivingSiteOwner") is not None : receivingSiteData[55] = submission["C1-FirstName3AdditionalReceivingSiteOwner"]
  if submission.get("C1-LastName3AdditionalReceivingSiteOwner") is not None : receivingSiteData[56] = submission["C1-LastName3AdditionalReceivingSiteOwner"]
  if submission.get("C1-Company3AdditionalReceivingSiteOwner") is not None : receivingSiteData[57] = submission["C1-Company3AdditionalReceivingSiteOwner"]
  if submission.get("C1-Address3AdditionalReceivingSiteOwner") is not None : receivingSiteData[58] = submission["C1-Address3AdditionalReceivingSiteOwner"]
  if submission.get("C1-City3AdditionalReceivingSiteOwner") is not None : receivingSiteData[59] = submission["C1-City3AdditionalReceivingSiteOwner"]
  if submission.get("phoneNumber2AdditionalReceivingSiteOwner") is not None : receivingSiteData[60] = submission["phoneNumber2AdditionalReceivingSiteOwner"]
  if submission.get("C1-Email3AdditionalReceivingSiteOwner") is not None : receivingSiteData[61] = submission["C1-Email3AdditionalReceivingSiteOwner"]
  if submission.get("C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow2ReceivingSite") is not None : receivingSiteData[62] = submission["C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow2ReceivingSite"]
  if submission.get("Firstadditionalcontactperson-sameAsAbove1") is not None : receivingSiteData[63] = submission["Firstadditionalcontactperson-sameAsAbove1"]
  if submission.get("C2-RSC-FirstName1AdditionalReceivingSite") is not None : receivingSiteData[64] = submission["C2-RSC-FirstName1AdditionalReceivingSite"]
  if submission.get("C2-RSC-LastName1AdditionalReceivingSite") is not None : receivingSiteData[65] = submission["C2-RSC-LastName1AdditionalReceivingSite"]
  if submission.get("C2-RSC-Company1AdditionalReceivingSite") is not None : receivingSiteData[66] = submission["C2-RSC-Company1AdditionalReceivingSite"]
  if submission.get("C2-RSC-Address1AdditionalReceivingSite") is not None : receivingSiteData[67] = submission["C2-RSC-Address1AdditionalReceivingSite"]
  if submission.get("C2-RSC-City1AdditionalReceivingSite") is not None : receivingSiteData[68] = submission["C2-RSC-City1AdditionalReceivingSite"]
  if submission.get("phoneNumber3AdditionalReceivingSite") is not None : receivingSiteData[69] = submission["phoneNumber3AdditionalReceivingSite"]
  if submission.get("C2-RSC-Email1AdditionalReceivingSite") is not None : receivingSiteData[70] = submission["C2-RSC-Email1AdditionalReceivingSite"]
  if submission.get("C2-siteIdentificationNumberSiteIdIfAvailable1FirstAdditionalReceivingSite") is not None : receivingSiteData[71] = submission["C2-siteIdentificationNumberSiteIdIfAvailable1FirstAdditionalReceivingSite"]
  if submission.get("C2-Latitude-Degrees1FirstAdditionalReceivingSite") is not None : receivingSiteData[72] = submission["C2-Latitude-Degrees1FirstAdditionalReceivingSite"]
  if submission.get("C2-Latitude-Minutes1FirstAdditionalReceivingSite") is not None : receivingSiteData[73] = submission["C2-Latitude-Minutes1FirstAdditionalReceivingSite"]
  if submission.get("Section2-Latitude-Seconds2FirstAdditionalReceivingSite") is not None : receivingSiteData[74] = submission["Section2-Latitude-Seconds2FirstAdditionalReceivingSite"]
  if submission.get("C2-Longitude-Degrees1FirstAdditionalReceivingSite") is not None : receivingSiteData[75] = submission["C2-Longitude-Degrees1FirstAdditionalReceivingSite"]
  if submission.get("C2-Longitude-Minutes1FirstAdditionalReceivingSite") is not None : receivingSiteData[76] = submission["C2-Longitude-Minutes1FirstAdditionalReceivingSite"]
  if submission.get("C2-Longitude-Seconds1FirstAdditionalReceivingSite") is not None : receivingSiteData[77] = submission["C2-Longitude-Seconds1FirstAdditionalReceivingSite"]
  if submission.get("FirstAdditionalReceivingSiteregionalDistrict1") is not None : receivingSiteData[78] = submission["FirstAdditionalReceivingSiteregionalDistrict1"]
  if submission.get("FirstAdditionalReceivingSiteLocationMap") is not None : receivingSiteData[79] = submission["FirstAdditionalReceivingSiteLocationMap"]
  if submission.get("Firstadditionalreceiving-landOwnership-checkbox1") is not None : receivingSiteData[80] = submission["Firstadditionalreceiving-landOwnership-checkbox1"]
  if submission.get("C2-LegallyTitled-Address1FirstAdditionalReceivingSite") is not None : receivingSiteData[81] = submission["C2-LegallyTitled-Address1FirstAdditionalReceivingSite"]
  if submission.get("C2-LegallyTitled-City1FirstAdditionalReceivingSite") is not None : receivingSiteData[82] = submission["C2-LegallyTitled-City1FirstAdditionalReceivingSite"]
  if submission.get("C2-LegallyTitled-PostalZipCode1FirstAdditionalReceivingSite") is not None : receivingSiteData[83] = submission["C2-LegallyTitled-PostalZipCode1FirstAdditionalReceivingSite"]
  if submission.get("dataGrid3") is not None : receivingSiteData[84] = submission["dataGrid3"]
  if submission.get("FirstAdditionalReceivingSiteLandTitle") is not None : receivingSiteData[85] = submission["FirstAdditionalReceivingSiteLandTitle"]
  if submission.get("dataGrid6") is not None : receivingSiteData[86] = submission["dataGrid6"]
  if submission.get("A-UntitledCrownLand-FileNumberColumn2") is not None : receivingSiteData[87] = submission["A-UntitledCrownLand-FileNumberColumn2"]
  if submission.get("A-UntitledMunicipalLand-PIDColumn2") is not None : receivingSiteData[88] = submission["A-UntitledMunicipalLand-PIDColumn2"]
  if submission.get("C3-soilClassification2FirstAdditionalReceivingSite") is not None : receivingSiteData[89] = submission["C3-soilClassification2FirstAdditionalReceivingSite"]
  if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule33FirstAdditionalReceivingSite") is not None : receivingSiteData[90] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule33FirstAdditionalReceivingSite"]
  if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule34FirstAdditionalReceivingSite") is not None : receivingSiteData[91] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule34FirstAdditionalReceivingSite"]
  if submission.get("C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1") is not None : receivingSiteData[92] = submission["C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1"]
  if submission.get("secondadditionalReceivingSites1") is not None : receivingSiteData[93] = submission["secondadditionalReceivingSites1"]
  if submission.get("C1-FirstName6SecondAdditionalreceivingSite") is not None : receivingSiteData[94] = submission["C1-FirstName6SecondAdditionalreceivingSite"]
  if submission.get("C1-LastName6SecondAdditionalreceivingSite") is not None : receivingSiteData[95] = submission["C1-LastName6SecondAdditionalreceivingSite"]
  if submission.get("C1-Company6SecondAdditionalreceivingSite") is not None : receivingSiteData[96] = submission["C1-Company6SecondAdditionalreceivingSite"]
  if submission.get("C1-Address6SecondAdditionalreceivingSite") is not None : receivingSiteData[97] = submission["C1-Address6SecondAdditionalreceivingSite"]
  if submission.get("C1-City6SecondAdditionalreceivingSite") is not None : receivingSiteData[98] = submission["C1-City6SecondAdditionalreceivingSite"]
  if submission.get("phoneNumber7SecondAdditionalreceivingSite") is not None : receivingSiteData[99] = submission["phoneNumber7SecondAdditionalreceivingSite"]
  if submission.get("C1-Email6SecondAdditionalreceivingSite") is not None : receivingSiteData[100] = submission["C1-Email6SecondAdditionalreceivingSite"]
  if submission.get("secondadditionalreceivingsiteC1-checkbox-extraowners3") is not None : receivingSiteData[101] = submission["secondadditionalreceivingsiteC1-checkbox-extraowners3"]
  if submission.get("C1-FirstName7SecondAdditionalreceivingSite") is not None : receivingSiteData[102] = submission["C1-FirstName7SecondAdditionalreceivingSite"]
  if submission.get("C1-LastName7SecondAdditionalreceivingSite") is not None : receivingSiteData[103] = submission["C1-LastName7SecondAdditionalreceivingSite"]
  if submission.get("C1-Company7SecondAdditionalreceivingSite") is not None : receivingSiteData[104] = submission["C1-Company7SecondAdditionalreceivingSite"]
  if submission.get("C1-Address7SecondAdditionalreceivingSite") is not None : receivingSiteData[105] = submission["C1-Address7SecondAdditionalreceivingSite"]
  if submission.get("C1-City7SecondAdditionalreceivingSite") is not None : receivingSiteData[106] = submission["C1-City7SecondAdditionalreceivingSite"]
  if submission.get("phoneNumber5SecondAdditionalreceivingSite") is not None : receivingSiteData[107] = submission["phoneNumber5SecondAdditionalreceivingSite"]
  if submission.get("C1-Email7SecondAdditionalreceivingSite") is not None : receivingSiteData[108] = submission["C1-Email7SecondAdditionalreceivingSite"]
  if submission.get("C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow4SecondAdditionalreceivingSite") is not None : receivingSiteData[109] = submission["C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow4SecondAdditionalreceivingSite"]
  if submission.get("secondadditionalreceivingsiteContactperson-sameAsAbove3") is not None : receivingSiteData[110] = submission["secondadditionalreceivingsiteContactperson-sameAsAbove3"]
  if submission.get("C2-RSC-FirstName3SecondAdditionalreceivingSite") is not None : receivingSiteData[111] = submission["C2-RSC-FirstName3SecondAdditionalreceivingSite"]
  if submission.get("C2-RSC-LastName3SecondAdditionalreceivingSite") is not None : receivingSiteData[112] = submission["C2-RSC-LastName3SecondAdditionalreceivingSite"]
  if submission.get("C2-RSC-Company3SecondAdditionalreceivingSite") is not None : receivingSiteData[113] = submission["C2-RSC-Company3SecondAdditionalreceivingSite"]
  if submission.get("C2-RSC-Address3SecondAdditionalreceivingSite") is not None : receivingSiteData[114] = submission["C2-RSC-Address3SecondAdditionalreceivingSite"]
  if submission.get("C2-RSC-City3SecondAdditionalreceivingSite") is not None : receivingSiteData[115] = submission["C2-RSC-City3SecondAdditionalreceivingSite"]
  if submission.get("phoneNumber6SecondAdditionalreceivingSite") is not None : receivingSiteData[116] = submission["phoneNumber6SecondAdditionalreceivingSite"]
  if submission.get("C2-RSC-Email3SecondAdditionalreceivingSite") is not None : receivingSiteData[117] = submission["C2-RSC-Email3SecondAdditionalreceivingSite"]
  if submission.get("C2-siteIdentificationNumberSiteIdIfAvailable3SecondAdditionalreceivingSite") is not None : receivingSiteData[118] = submission["C2-siteIdentificationNumberSiteIdIfAvailable3SecondAdditionalreceivingSite"]
  if submission.get("C2-Latitude-Degrees3SecondAdditionalreceivingSite") is not None : receivingSiteData[119] = submission["C2-Latitude-Degrees3SecondAdditionalreceivingSite"]
  if submission.get("C2-Latitude-Minutes3SecondAdditionalreceivingSite") is not None : receivingSiteData[120] = submission["C2-Latitude-Minutes3SecondAdditionalreceivingSite"]
  if submission.get("Section2-Latitude-Seconds4SecondAdditionalreceivingSite") is not None : receivingSiteData[121] = submission["Section2-Latitude-Seconds4SecondAdditionalreceivingSite"]
  if submission.get("C2-Longitude-Degrees3SecondAdditionalreceivingSite") is not None : receivingSiteData[122] = submission["C2-Longitude-Degrees3SecondAdditionalreceivingSite"]
  if submission.get("C2-Longitude-Minutes3SecondAdditionalreceivingSite") is not None : receivingSiteData[123] = submission["C2-Longitude-Minutes3SecondAdditionalreceivingSite"]
  if submission.get("C2-Longitude-Seconds3SecondAdditionalreceivingSite") is not None : receivingSiteData[124] = submission["C2-Longitude-Seconds3SecondAdditionalreceivingSite"]
  if submission.get("SecondAdditionalReceivingSiteregionalDistrict") is not None : receivingSiteData[125] = submission["SecondAdditionalReceivingSiteregionalDistrict"]
  if submission.get("SecondAdditionalReceivingSiteLocationMap") is not None : receivingSiteData[126] = submission["SecondAdditionalReceivingSiteLocationMap"]
  if submission.get("Secondadditionalreceiving-landOwnership-checkbox3") is not None : receivingSiteData[127] = submission["Secondadditionalreceiving-landOwnership-checkbox3"]
  if submission.get("C2-LegallyTitled-Address3SecondAdditionalreceivingSite") is not None : receivingSiteData[128] = submission["C2-LegallyTitled-Address3SecondAdditionalreceivingSite"]
  if submission.get("C2-LegallyTitled-City3SecondAdditionalreceivingSite") is not None : receivingSiteData[129] = submission["C2-LegallyTitled-City3SecondAdditionalreceivingSite"]
  if submission.get("C2-LegallyTitled-PostalZipCode3SecondAdditionalreceivingSite") is not None : receivingSiteData[130] = submission["C2-LegallyTitled-PostalZipCode3SecondAdditionalreceivingSite"]
  if submission.get("dataGrid4") is not None : receivingSiteData[131] = submission["dataGrid4"]
  if submission.get("SecondAdditionalReceivingSiteLandTitle2") is not None : receivingSiteData[132] = submission["SecondAdditionalReceivingSiteLandTitle2"]
  if submission.get("dataGrid7") is not None : receivingSiteData[133] = submission["dataGrid7"]
  if submission.get("A-UntitledCrownLand-FileNumberColumn3") is not None : receivingSiteData[134] = submission["A-UntitledCrownLand-FileNumberColumn3"]
  if submission.get("A-UntitledMunicipalLand-PIDColumn3") is not None : receivingSiteData[135] = submission["A-UntitledMunicipalLand-PIDColumn3"]
  if submission.get("C3-soilClassification4SecondAdditionalreceivingSite") is not None : receivingSiteData[136] = submission["C3-soilClassification4SecondAdditionalreceivingSite"]
  if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule37SecondAdditionalreceivingSite") is not None : receivingSiteData[137] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule37SecondAdditionalreceivingSite"]
  if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule38SecondAdditionalreceivingSite") is not None : receivingSiteData[138] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule38SecondAdditionalreceivingSite"]
  if submission.get("C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime3") is not None : receivingSiteData[139] = submission["C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime3"]
  if submission.get("form") is not None : 
    formStr = json.dumps(submission.get("form"))
    formJson = json.loads(formStr)
    createdAt = datetime.datetime.strptime(formJson['createdAt'], "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo = None, hour = 0, minute = 0, second = 0, microsecond = 0) # remove the timezone awareness
    confirmationId = formJson['confirmationId']
     # not in attributes, but in json
    if createdAt is not None : receivingSiteData[140] = createdAt
    if confirmationId is not None : receivingSiteData[141] = confirmationId
  receivingSites.append(receivingSiteData)

  # 'sitesDic' dictionary - key:regionalDistrict / value:hvSiteData
  for rd in receivingSiteData[31]: # could be more than one
    if rd is not None: 
      if rd in sitesDic:
        sitesDic[rd].append(receivingSiteData)
      else:
        sitesDic[rd] = receivingSiteData



hvSites = [] # [''] * len(hvsJson)
hvSitesDic = {}
# create high volumn site records
for hvs in hvsJson:
  # print(hvs)
  # Map hv data to the hv site
  hvSiteData = [''] * 72
  hvIdx = 0
  if hvs.get("Section1-FirstNameReceivingSiteOwner") is not None : hvSiteData[0] = hvs["Section1-FirstNameReceivingSiteOwner"]
  if hvs.get("Section1-LastNameReceivingSiteOwner") is not None : hvSiteData[1] = hvs["Section1-LastNameReceivingSiteOwner"]
  if hvs.get("Section1-CompanyReceivingSiteOwner") is not None : hvSiteData[2] = hvs["Section1-CompanyReceivingSiteOwner"]
  if hvs.get("Section1-AddressReceivingSiteOwner") is not None : hvSiteData[3] = hvs["Section1-AddressReceivingSiteOwner"]
  if hvs.get("Section1-CityReceivingSiteOwner") is not None : hvSiteData[4] = hvs["Section1-CityReceivingSiteOwner"]
  if hvs.get("Section1-provinceStateReceivingSiteOwner") is not None : hvSiteData[5] = hvs["Section1-provinceStateReceivingSiteOwner"]
  if hvs.get("Section1-countryReceivingSiteOwner") is not None : hvSiteData[6] = hvs["Section1-countryReceivingSiteOwner"]
  if hvs.get("Section1-postalZipCodeReceivingSiteOwner") is not None : hvSiteData[7] = hvs["Section1-postalZipCodeReceivingSiteOwner"]
  if hvs.get("Section1-PhoneReceivingSiteOwner") is not None : hvSiteData[8] = hvs["Section1-PhoneReceivingSiteOwner"]
  if hvs.get("Section1-EmailReceivingSiteOwner") is not None : hvSiteData[9] = hvs["Section1-EmailReceivingSiteOwner"]
  if hvs.get("Section1-checkbox-extraowners") is not None : hvSiteData[10] = hvs["Section1-checkbox-extraowners"]
  if hvs.get("Section1a-FirstNameAdditionalOwner") is not None : hvSiteData[11] = hvs["Section1a-FirstNameAdditionalOwner"]
  if hvs.get("Section1A-LastNameAdditionalOwner") is not None : hvSiteData[12] = hvs["Section1A-LastNameAdditionalOwner"]
  if hvs.get("Section1A-CompanyAdditionalOwner") is not None : hvSiteData[13] = hvs["Section1A-CompanyAdditionalOwner"]
  if hvs.get("Section1A-AddressAdditionalOwner") is not None : hvSiteData[14] = hvs["Section1A-AddressAdditionalOwner"]
  if hvs.get("Section1A-CityAdditionalOwner") is not None : hvSiteData[15] = hvs["Section1A-CityAdditionalOwner"]
  if hvs.get("Section1A-ProvinceStateAdditionalOwner") is not None : hvSiteData[16] = hvs["Section1A-ProvinceStateAdditionalOwner"]
  if hvs.get("Section1A-CountryAdditionalOwner") is not None : hvSiteData[17] = hvs["Section1A-CountryAdditionalOwner"]
  if hvs.get("Section1A-PostalZipCodeAdditionalOwner") is not None : hvSiteData[18] = hvs["Section1A-PostalZipCodeAdditionalOwner"]
  if hvs.get("Section1A-PhoneAdditionalOwner") is not None : hvSiteData[19] = hvs["Section1A-PhoneAdditionalOwner"]
  if hvs.get("Section1A-EmailAdditionalOwner") is not None : hvSiteData[20] = hvs["Section1A-EmailAdditionalOwner"]
  if hvs.get("areThereMoreThanTwoOwnersIncludeTheirInformationBelow") is not None : hvSiteData[21] = hvs["areThereMoreThanTwoOwnersIncludeTheirInformationBelow"]
  if hvs.get("receivingsitecontact") is not None : hvSiteData[22] = hvs["receivingsitecontact"]
  if hvs.get("Section2-firstNameRSC") is not None : hvSiteData[23] = hvs["Section2-firstNameRSC"]
  if hvs.get("Section2-lastNameRSC") is not None : hvSiteData[24] = hvs["Section2-lastNameRSC"]
  if hvs.get("Section2-organizationRSC") is not None : hvSiteData[25] = hvs["Section2-organizationRSC"]
  if hvs.get("Section2-streetAddressRSC") is not None : hvSiteData[26] = hvs["Section2-streetAddressRSC"]
  if hvs.get("Section2-cityRSC") is not None : hvSiteData[27] = hvs["Section2-cityRSC"]
  if hvs.get("Section2-provinceStateRSC") is not None : hvSiteData[28] = hvs["Section2-provinceStateRSC"]
  if hvs.get("Section2-countryRSC") is not None : hvSiteData[29] = hvs["Section2-countryRSC"]
  if hvs.get("Section2-postalZipCodeRSC") is not None : hvSiteData[30] = hvs["Section2-postalZipCodeRSC"]
  if hvs.get("section2phoneNumberRSC") is not None : hvSiteData[31] = hvs["section2phoneNumberRSC"]
  if hvs.get("Section2-simpleemailRSC") is not None : hvSiteData[32] = hvs["Section2-simpleemailRSC"]
  if hvs.get("Section3-siteIdIncludeAllRelatedNumbers") is not None : hvSiteData[33] = hvs["Section3-siteIdIncludeAllRelatedNumbers"]
  if hvs.get("Section3-Latitude-Degrees") is not None : hvSiteData[34] = hvs["Section3-Latitude-Degrees"]
  if hvs.get("Section3-Latitude-Minutes") is not None : hvSiteData[35] = hvs["Section3-Latitude-Minutes"]
  if hvs.get("Section3-Latitude-Seconds") is not None : hvSiteData[36] = hvs["Section3-Latitude-Seconds"]
  if hvs.get("Section3-Longitude-Degrees") is not None : hvSiteData[37] = hvs["Section3-Longitude-Degrees"]
  if hvs.get("Section3-Longitude-Minutes") is not None : hvSiteData[38] = hvs["Section3-Longitude-Minutes"]
  if hvs.get("Section3-Longitude-Seconds") is not None : hvSiteData[39] = hvs["Section3-Longitude-Seconds"]
  if hvs.get("ReceivingSiteregionalDistrict") is not None : hvSiteData[40] = hvs["ReceivingSiteregionalDistrict"]
  if hvs.get("uploadMapOfHighVolumeSiteLocation") is not None : hvSiteData[41] = hvs["uploadMapOfHighVolumeSiteLocation"]
  if hvs.get("landOwnership-checkbox") is not None : hvSiteData[42] = hvs["landOwnership-checkbox"]
  if hvs.get("Section3-LegallyTitled-Address") is not None : hvSiteData[43] = hvs["Section3-LegallyTitled-Address"]
  if hvs.get("Section3-LegallyTitled-City") is not None : hvSiteData[44] = hvs["Section3-LegallyTitled-City"]
  if hvs.get("Section3-LegallyTitled-PostalZipCode") is not None : hvSiteData[45] = hvs["Section3-LegallyTitled-PostalZipCode"]
  if hvs.get("dataGrid") is not None : hvSiteData[46] = hvs["dataGrid"]
  if hvs.get("uploadMapOfHighVolumeSiteLocation1") is not None : hvSiteData[47] = hvs["uploadMapOfHighVolumeSiteLocation1"]
  if hvs.get("dataGrid1") is not None : hvSiteData[48] = hvs["dataGrid1"]
  if hvs.get("A-UntitledCrownLand-FileNumberColumn") is not None : hvSiteData[49] = hvs["A-UntitledCrownLand-FileNumberColumn"]
  if hvs.get("A-UntitledMunicipalLand-PIDColumn") is not None : hvSiteData[50] = hvs["A-UntitledMunicipalLand-PIDColumn"]
  if hvs.get("primarylanduse") is not None : hvSiteData[51] = hvs["primarylanduse"]
  if hvs.get("highVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime") is not None : hvSiteData[52] = hvs["highVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime"]
  if hvs.get("dateSiteBecameHighVolume") is not None : hvSiteData[53] = hvs["dateSiteBecameHighVolume"]
  if hvs.get("howrelocatedsoilwillbeused") is not None : hvSiteData[54] = hvs["howrelocatedsoilwillbeused"]
  if hvs.get("soilDepositIsInTheAgriculturalLandReserveAlr1") is not None : hvSiteData[55] = hvs["soilDepositIsInTheAgriculturalLandReserveAlr1"]
  if hvs.get("receivingSiteIsOnReserveLands1") is not None : hvSiteData[56] = hvs["receivingSiteIsOnReserveLands1"]
  if hvs.get("Section5-FirstNameQualifiedProfessional") is not None : hvSiteData[57] = hvs["Section5-FirstNameQualifiedProfessional"]
  if hvs.get("Section5-LastName1QualifiedProfessional") is not None : hvSiteData[58] = hvs["Section5-LastName1QualifiedProfessional"]
  if hvs.get("Section5-TypeofQP") is not None : hvSiteData[59] = hvs["Section5-TypeofQP"]
  if hvs.get("Section5-organizationQualifiedProfessional") is not None : hvSiteData[60] = hvs["Section5-organizationQualifiedProfessional"]
  if hvs.get("Section5-professionalLicenseRegistrationEGPEngRpBio") is not None : hvSiteData[61] = hvs["Section5-professionalLicenseRegistrationEGPEngRpBio"]
  if hvs.get("Section5-streetAddressQualifiedProfessional") is not None : hvSiteData[62] = hvs["Section5-streetAddressQualifiedProfessional"]
  if hvs.get("Section5-cityQualifiedProfessional") is not None : hvSiteData[63] = hvs["Section5-cityQualifiedProfessional"]
  if hvs.get("Section5-provinceStateQualifiedProfessional") is not None : hvSiteData[64] = hvs["Section5-provinceStateQualifiedProfessional"]
  if hvs.get("Section5-countryQualifiedProfessional") is not None : hvSiteData[65] = hvs["Section5-countryQualifiedProfessional"]
  if hvs.get("Section5-postalZipCodeQualifiedProfessional") is not None : hvSiteData[66] = hvs["Section5-postalZipCodeQualifiedProfessional"]
  if hvs.get("simplephonenumber1QualifiedProfessional") is not None : hvSiteData[67] = hvs["simplephonenumber1QualifiedProfessional"]
  if hvs.get("simpleemail1QualifiedProfessional") is not None : hvSiteData[68] = hvs["simpleemail1QualifiedProfessional"]
  if hvs.get("firstAndLastNameQualifiedProfessional") is not None : hvSiteData[69] = hvs["firstAndLastNameQualifiedProfessional"]
  if submission.get("form") is not None : 
    formStr = json.dumps(submission.get("form"))
    formJson = json.loads(formStr)
    createdAt = datetime.datetime.strptime(formJson['createdAt'], "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo = None, hour = 0, minute = 0, second = 0, microsecond = 0) # remove the timezone awareness
    confirmationId = formJson['confirmationId']
    # not in attributes, but in json
    if createdAt is not None : hvSiteData[70] = createdAt 
    if confirmationId is not None : hvSiteData[71] = confirmationId
  hvSites.append(hvSiteData)

  # 'hvSitesDic' dictionary - key:regionalDistrict / value:hvSiteData
  for rd in hvSiteData[40]: # could be more than one
    if rd is not None: 
      if rd in hvSitesDic:
        hvSitesDic[rd].append(hvSiteData)
      else:
        hvSitesDic[rd] = hvSiteData

  # Map hv data to the hv site
  # for col in hvsAttributes: 
  #   if hvs.get(col) is not None : hvSiteData.append(hvs[col])


print('Creating soil source site CSV...')
# with open(csvLocation, 'w', encoding='UTF8', newline='') as f:
with open('soil_source_site.csv', 'w', encoding='UTF8', newline='') as f:  
  #print('Creating CSV @ ' + csvLocation)
  writer = csv.writer(f)
  writer.writerow(sourceSiteHeaders)

  print('Parsing ' + str(len(submissionsJson)) + ' submission forms.')
  # print(sourceSites)
  for ss in sourceSites:
    # print(ss)
    data = [] # the source data to inject into the csv    
    for ssData in ss:
      data.append(ssData)
    writer.writerow(data)      

print('Creating soil destination site CSV...')
# with open(csvLocation, 'w', encoding='UTF8', newline='') as f:
with open('soil_destination_site.csv', 'w', encoding='UTF8', newline='') as f:  
  print('Creating CSV @ ' + csvLocation)
  writer = csv.writer(f)
  writer.writerow(receivingSiteHeaders)

  print('Parsing ' + str(len(submissionsJson)) + ' submission forms.')
  # print(receivingSites)
  for rs in receivingSites:
    # print(rs)
    data = [] # the receiving data to inject into the csv
    for rsData in rs:
      data.append(rsData)
    writer.writerow(data)          

print('Creating soil high volume site CSV...')
# with open(csvLocation, 'w', encoding='UTF8', newline='') as f:
with open('soil_high_volume_site.csv', 'w', encoding='UTF8', newline='') as f:  
  print('Creating CSV @ ' + csvLocation)
  writer = csv.writer(f)
  writer.writerow(hvSiteHeaders)

  print('Parsing ' + str(len(hvsJson)) + ' Sites forms.')
  # print(hvSites)
  for hvs in hvSites:
    # print(hvs)
    data = [] # the hv data to inject into the csv
    for hvsData in hvs:
      data.append(hvsData)
    writer.writerow(data)



start_time = time.time()

# Connect to GIS
gis = GIS(arcgisUrl, arcgisUsername, arcgisPwd)


# read the second csv set
csv2 = 'soil_source_site_test.csv'
cities_df_2 = pd.read_csv(csv2)
cities_df_2.head()
#print(cities_df_2.head())

sourceFLayerItemID = 'ebd6b75fa5b44b62ab13014674250f3f' # Soil Relocation Source Site - feature layer Item Id

featureLayerCollectionItem = gis.content.get(sourceFLayerItemID)

cities_flayer = featureLayerCollectionItem.layers[0]
cities_fset = cities_flayer.query() #querying without any conditions returns all the features
print(cities_fset.sdf.head())





overlap_rows = pd.merge(left=cities_fset.sdf, right=cities_df_2, how='inner', on='confirmationId')

print(overlap_rows)

features_for_update = [] #list containing corrected features
all_features = cities_fset.features
print(all_features[0])
print(cities_fset.spatial_reference)

for confirmationId in overlap_rows['confirmationId']:
    # get the feature to be updated
    original_feature = [f for f in all_features if f.attributes['confirmationId'] == confirmationId][0]

    feature_to_be_updated = deepcopy(original_feature)
    
    print(str(original_feature))
    
    # get the matching row from csv
    matching_row = cities_df_2.where(cities_df_2["confirmationId"] == confirmationId).dropna()


    #get geometries in the destination coordinate system
    #input_geometry = {'y':float(matching_row['A3-SourceSiteLatitude']),
    #                   'x':float(matching_row['A3-SourceSiteLongitude'])}
    #output_geometry = geometry.project(geometries = [input_geometry],
    #                                   in_sr = 4326, 
    #                                   out_sr = cities_fset.spatial_reference['latestWkid'],
    #                                  gis = gis)
    
    # assign the updated values
    #feature_to_be_updated.geometry = output_geometry[0]
    print(matching_row['A1_FIRSTName'])

    feature_to_be_updated.attributes['A1_FIRSTName'] = str(matching_row['A1_FIRSTName'])

    #feature_to_be_updated.attributes['confirmationId'] = (matching_row['confirmationId'])
    
    #add this to the list of features to be updated
    features_for_update.append(feature_to_be_updated)
    print(features_for_update)
    
    #print(str(feature_to_be_updated))
    #print("========================================================================")

#cities_flayer.edit_features(updates=features_for_update)


elapsed_time = time.time() - start_time
totaltime = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
print("Total processing time: "+ totaltime)



# add new feature
#select those rows in the capitals_2.csv that do not overlap with those in capitals_1.csv

new_rows = cities_df_2[~cities_df_2['confirmationId'].isin(overlap_rows['confirmationId'])]
print(new_rows.shape)


features_to_be_added = []
# get a template feature object
template_feature = deepcopy(features_for_update[0])
print(template_feature)

# loop through each row and add to the list of features to be added
for row in new_rows.iterrows():
  new_feature = deepcopy(template_feature)
    
  #print
  print("Creating " + row[1]['A1_FIRSTName'])
  
  #get geometries in the destination coordinate system
  #input_geometry = {'y':float(row[1]['latitude']),
  #                    'x':float(row[1]['longitude'])}
  #output_geometry = geometry.project(geometries = [input_geometry],
  #                                    in_sr = 4326, 
  #                                    out_sr = cities_fset.spatial_reference['latestWkid'],
  #                                  gis = gis)
  
  # assign the updated values
  #new_feature.geometry = output_geometry[0]
  new_feature.attributes['A1_FIRSTName'] = row[1]['A1_FIRSTName']
  new_feature.attributes['A1_LASTName'] = row[1]['A1_LASTName']
  new_feature.attributes['A1_Company'] = row[1]['A1_Company']
  new_feature.attributes['A1_Address'] = row[1]['A1_Address']
  new_feature.attributes['A1_City'] = row[1]['A1_City']
  new_feature.attributes['A1_ProvinceState'] = row[1]['A1_ProvinceState']
  new_feature.attributes['A1_Country'] = row[1]['A1_Country']
  new_feature.attributes['A1_PostalZipCode'] = row[1]['A1_PostalZipCode']
  new_feature.attributes['A1_Phone'] = row[1]['A1_Phone']
  new_feature.attributes['A1_Email'] = row[1]['A1_Email']
  new_feature.attributes['A1_checkbox_extraowners'] = row[1]['A1_checkbox_extraowners']
  new_feature.attributes['A1_additionalownerFIRSTName'] = row[1]['A1_additionalownerFIRSTName']
  new_feature.attributes['A1_additionalownerLASTName1'] = row[1]['A1_additionalownerLASTName1']
  new_feature.attributes['A1_additionalownerCompany1'] = row[1]['A1_additionalownerCompany1']
  new_feature.attributes['A1_additionalownerAddress1'] = row[1]['A1_additionalownerAddress1']
  new_feature.attributes['A1_additionalownerCity1'] = row[1]['A1_additionalownerCity1']
  new_feature.attributes['A1_additionalownerPhone1'] = row[1]['A1_additionalownerPhone1']
  new_feature.attributes['A1_additionalownerEmail1'] = row[1]['A1_additionalownerEmail1']
  new_feature.attributes['areThereMoreThanTwoOwnersIncludeTheirInformationBelow'] = row[1]['areThereMoreThanTwoOwnersIncludeTheirInformationBelow']
  new_feature.attributes['A1_SourceSiteContact_sameAsAbove'] = row[1]['A1_SourceSiteContact_sameAsAbove']
  new_feature.attributes['A2_SourceSiteContactFirstName'] = row[1]['A2_SourceSiteContactFirstName']
  new_feature.attributes['A2_SourceSiteContactLastName'] = row[1]['A2_SourceSiteContactLastName']
  new_feature.attributes['A2_SourceSiteContactCompany'] = row[1]['A2_SourceSiteContactCompany']
  new_feature.attributes['A2_SourceSiteContactAddress'] = row[1]['A2_SourceSiteContactAddress']
  new_feature.attributes['A2_SourceSiteContactCity'] = row[1]['A2_SourceSiteContactCity']
  new_feature.attributes['SourceSiteContactphoneNumber'] = row[1]['SourceSiteContactphoneNumber']
  new_feature.attributes['A2_SourceSiteContactEmail'] = row[1]['A2_SourceSiteContactEmail']
  new_feature.attributes['A3_SourcesiteIdentificationNumberSiteIdIfAvailable'] = row[1]['A3_SourcesiteIdentificationNumberSiteIdIfAvailable']
  new_feature.attributes['A3_SourceSiteLatitude_Degrees'] = row[1]['A3_SourceSiteLatitude_Degrees']
  new_feature.attributes['A3_SourceSiteLatitude_Minutes'] = row[1]['A3_SourceSiteLatitude_Minutes']
  new_feature.attributes['A3_SourceSiteLatitude_Seconds'] = row[1]['A3_SourceSiteLatitude_Seconds']
  new_feature.attributes['A3_SourceSiteLongitude_Degrees'] = row[1]['A3_SourceSiteLongitude_Degrees']
  new_feature.attributes['A3_SourceSiteLongitude_Minutes'] = row[1]['A3_SourceSiteLongitude_Minutes']
  new_feature.attributes['A3_SourceSiteLongitude_Seconds'] = row[1]['A3_SourceSiteLongitude_Seconds']
  new_feature.attributes['SourcelandOwnership_checkbox'] = row[1]['SourcelandOwnership_checkbox']
  new_feature.attributes['A_LegallyTitled_AddressSource'] = row[1]['A_LegallyTitled_AddressSource']
  new_feature.attributes['A_LegallyTitled_CitySource'] = row[1]['A_LegallyTitled_CitySource']
  new_feature.attributes['A_LegallyTitled_PostalZipCodeSource'] = row[1]['A_LegallyTitled_PostalZipCodeSource']
  new_feature.attributes['SourceSiteregionalDistrict'] = row[1]['SourceSiteregionalDistrict']
  new_feature.attributes['dataGrid'] = row[1]['dataGrid']
  new_feature.attributes['FirstAdditionalReceivingsiteuploadLandTitleRecord'] = row[1]['FirstAdditionalReceivingsiteuploadLandTitleRecord']
  new_feature.attributes['dataGrid1'] = row[1]['dataGrid1']
  new_feature.attributes['A_UntitledCrownLand_FileNumberColumnSource'] = row[1]['A_UntitledCrownLand_FileNumberColumnSource']
  new_feature.attributes['A_UntitledMunicipalLand_PIDColumnSource'] = row[1]['A_UntitledMunicipalLand_PIDColumnSource']
  new_feature.attributes['A4_schedule2ReferenceSourceSite'] = row[1]['A4_schedule2ReferenceSourceSite']
  new_feature.attributes['isTheSourceSiteHighRisk'] = row[1]['isTheSourceSiteHighRisk']
  new_feature.attributes['A5_PurposeOfSoilExcavationSource'] = row[1]['A5_PurposeOfSoilExcavationSource']
  new_feature.attributes['B4_currentTypeOfSoilStorageEGStockpiledInSitu1Source'] = row[1]['B4_currentTypeOfSoilStorageEGStockpiledInSitu1Source']
  new_feature.attributes['dataGrid9'] = row[1]['dataGrid9']
  new_feature.attributes['B2_describeSoilCharacterizationMethod1'] = row[1]['B2_describeSoilCharacterizationMethod1']
  new_feature.attributes['uploadSoilAnalyticalData'] = row[1]['uploadSoilAnalyticalData']
  new_feature.attributes['B3_yesOrNoVapourexemptionsource'] = row[1]['B3_yesOrNoVapourexemptionsource']
  new_feature.attributes['B3_ifExemptionsApplyPleaseDescribe'] = row[1]['B3_ifExemptionsApplyPleaseDescribe']
  new_feature.attributes['B3_describeVapourCharacterizationMethod'] = row[1]['B3_describeVapourCharacterizationMethod']
  new_feature.attributes['uploadVapourAnalyticalData1'] = row[1]['uploadVapourAnalyticalData1']
  new_feature.attributes['B4_soilRelocationEstimatedStartDateMonthDayYear'] = row[1]['B4_soilRelocationEstimatedStartDateMonthDayYear']
  new_feature.attributes['B4_soilRelocationEstimatedCompletionDateMonthDayYear'] = row[1]['B4_soilRelocationEstimatedCompletionDateMonthDayYear']
  new_feature.attributes['B4_RelocationMethod'] = row[1]['B4_RelocationMethod']
  new_feature.attributes['D1_FirstNameQualifiedProfessional'] = row[1]['D1_FirstNameQualifiedProfessional']
  new_feature.attributes['LastNameQualifiedProfessional'] = row[1]['LastNameQualifiedProfessional']
  new_feature.attributes['D1_TypeofQP1'] = row[1]['D1_TypeofQP1']
  new_feature.attributes['D1_professionalLicenseRegistrationEGPEngRpBio'] = row[1]['D1_professionalLicenseRegistrationEGPEngRpBio']
  new_feature.attributes['D1_organization1QualifiedProfessional'] = row[1]['D1_organization1QualifiedProfessional']
  new_feature.attributes['D1_streetAddress1QualifiedProfessional'] = row[1]['D1_streetAddress1QualifiedProfessional']
  new_feature.attributes['D1_city1QualifiedProfessional'] = row[1]['D1_city1QualifiedProfessional']
  new_feature.attributes['D1_provinceState3QualifiedProfessional'] = row[1]['D1_provinceState3QualifiedProfessional']
  new_feature.attributes['D1_canadaQualifiedProfessional'] = row[1]['D1_canadaQualifiedProfessional']
  new_feature.attributes['D1_postalZipCode3QualifiedProfessional'] = row[1]['D1_postalZipCode3QualifiedProfessional']
  new_feature.attributes['simplephonenumber1QualifiedProfessional'] = row[1]['simplephonenumber1QualifiedProfessional']
  new_feature.attributes['EmailAddressQualifiedProfessional'] = row[1]['EmailAddressQualifiedProfessional']
  new_feature.attributes['D2_soilDepositIsInTheAgriculturalLandReserveAlr'] = row[1]['D2_soilDepositIsInTheAgriculturalLandReserveAlr']
  new_feature.attributes['D2_soilDepositIsInTheReserveLands'] = row[1]['D2_soilDepositIsInTheReserveLands']
  new_feature.attributes['createAt'] = row[1]['createAt']
  new_feature.attributes['confirmationId'] = row[1]['confirmationId']
  new_feature.attributes['A3_SourceSiteLatitude'] = row[1]['A3_SourceSiteLatitude']
  new_feature.attributes['A3_SourceSiteLongitude'] = row[1]['A3_SourceSiteLongitude']

  #add this to the list of features to be updated
  features_to_be_added.append(new_feature)

# take a look at one of the features we created
#print(features_to_be_added[0])
cities_flayer.edit_features(adds = features_to_be_added)



"""
# read the initial csv
#soil_source_site_csv_file = 'soil_source_site.csv' #testing
soil_source_site_csv_file = 'Contaminated_Soils_Site_upt.csv'
soil_source_site_df = pd.read_csv(soil_source_site_csv_file)
soil_source_site_df.head()

# print the number of records in this csv
soil_source_site_df.shape

# assign variables to locations on the file system 
cwd = os.path.abspath(os.getcwd())
#data_pth = os.path.join(cwd, r'data/updating_gis_content/')
data_pth = cwd

# create a unique timestamp string to append to the file name
now_ts = str(int(dt.datetime.now().timestamp()))

# copy the file, appending the unique string and assign it to a variable
soil_source_site_csv_data = shutil.copyfile(os.path.abspath(soil_source_site_csv_file),
                       os.path.join(data_pth, 'Contaminated_Soils_Site' + now_ts + '.csv'))


# add the initial csv file and publish that as a web layer
item_prop = {'title':'Contaminated Soils Sites ' + now_ts,'tags':'Contaminated Soils, Contaminated Soils Sites, BC','description':'Contaminated Soils Sites',"commentsEnabled" : False}
#item_prop = {'type':'Feature Collection','title':'Contaminated Soils Sites ' + now_ts,'tags':'Contaminated Soils, Contaminated Soils Sites, BC','description':'Contaminated Soils Sites',"commentsEnabled" : False}
csv_item = gis.content.add(item_properties=item_prop, data=soil_source_site_csv_data, owner = arcgisUsername)

# publish the csv item into a feature layer
#publishParameters = 

analyzed = gis.content.analyze(item=csv_item)
publish_parameters = analyzed['publishParameters']
#publish_parameters['name'] = 'AVeryUniqueName' # this needs to be updated
publish_parameters['locationType'] = 'coordinates' # this makes it a hosted table

#pitem = csv_item.publish(publish_parameters=publish_parameters, file_type='csv')
pitem = csv_item.publish(publish_parameters=publish_parameters, file_type='csv')
print(pitem.tables)
"""


"""
publish_parameters = {
  "type": "CSV",
  "name": "Soil Relocation Source Sites",
  "sourceUrl": "",
  "locationType": "coordinates",
  "latitudeFieldName":"",
  "longitudeFieldName":"",
  "coordinateFieldType":"LatitudeAndLongitude",
  "coordinateFieldName":"",
  "maxRecordCount": 2000,
  #"geocodeServiceUrl": "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer",
  "sourceCountry": "ca",
  "sourceLocale": "en",
  "addressFields": {
    "Address": "A1-Address",
    "City": "A1-City",
    "Region": "A1-ProvinceState",
    "Postal": "A1-PostalZipCode"
  },
  "standardizedFieldNames": {
    "Address": "A1-Address",
    "City": "A1-City",
    "Region": "A1-ProvinceState",
    "Postal": "A1-PostalZipCode",
    "PostalExt": "A1-PostalZipCode",
    "CountryCode": "A1-Country"
  },
  "columnDelimiter": ",",
  "qualifier": "\"",
  "targetSR": {
    "wkid": 102100,
    "latestWkid": 3857
  },
  "editorTrackingInfo": {
    "enableEditorTracking": False,
    "enableOwnershipAccessControl": False,
    "allowOthersToQuery": True,
    "allowOthersToUpdate": True,
    "allowOthersToDelete": False,
    "allowAnonymousToUpdate": True,
    "allowAnonymousToDelete": True
  },
  "layerInfo": {
    "currentVersion": 10.8,
    "id": 0,
    "name": "Soil Relocation Source Sites",
    "type": "Table",
    "displayField": "",
    "description": "",
    "copyrightText": "",
    "defaultVisibility": True,
    "relationships": [],
    "isDataVersioned": False,
    "supportsCalculate": True,
    "supportsTruncate": False,
    "supportsAttachmentsByUploadId": True,
    "supportsRollbackOnFailureParameter": True,
    "supportsStatistics": True,
    "supportsAdvancedQueries": True,
    "supportsValidateSql": True,
    "supportsCoordinatesQuantization": True,
    "supportsApplyEditsWithGlobalIds": False,
    "advancedQueryCapabilities": {
    "supportsPagination": True,
    "supportsPaginationOnAggregatedQueries": True,
    "supportsQueryRelatedPagination": True,
    "supportsQueryWithDistance": True,
    "supportsReturningQueryExtent": True,
    "supportsStatistics": True,
    "supportsOrderBy": True,
    "supportsDistinct": True,
    "supportsQueryWithResultType": True,
    "supportsSqlExpression": True,
    "supportsAdvancedQueryRelated": True,
    "supportsReturningGeometryCentroid": False,
    "supportsQueryWithDatumTransformation": True
    },
    "useStandardizedQueries": False,
    "geometryType": "esriGeometryPoint",
    "drawingInfo": {
      "renderer": {
        "type": "simple",
        "symbol": {
          "type": "esriPMS",
          "url": "RedSphere.png",
          "imageData": "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAABGdBTUEAALGPASUVORK5CYII=",
          "contentType": "image/png",
          "width": 15,
          "height": 15
        }
      }
    },
    "allowGeometryUpdates": True,
    "hasAttachments": False,
    "htmlPopupType": "",
    "hasM": False,
    "hasZ": False,
    "globalIdField": "",
    "typeIdField": "",
    "fields": [
      {
        "name": "A1-FIRSTName",
        "type": "esriFieldTypeString",
        "alias": "A1-FIRSTName",
        "sqlType": "sqlTypeNVarchar",
        "length": 256,
        "nullable": True,
        "editable": True,
        "domain": None,
        "defaultValue": None,
        "locationType": "unknown"
      },
      {
        "name": "A1-LASTName",
        "type": "esriFieldTypeString",
        "alias": "A1-LASTName",
        "sqlType": "sqlTypeNVarchar",
        "length": 256,
        "nullable": True,
        "editable": True,
        "domain": None,
        "defaultValue": None,
        "locationType": "unknown"
      },
      {
        "name": "A1-Company",
        "type": "esriFieldTypeString",
        "alias": "A1-Company",
        "sqlType": "sqlTypeNVarchar",
        "length": 256,
        "nullable": True,
        "editable": True,
        "domain": None,
        "defaultValue": None,
        "locationType": "unknown"
      },
      {
        "name": "A1-Address",
        "type": "esriFieldTypeString",
        "alias": "A1-Address",
        "sqlType": "sqlTypeNVarchar",
        "length": 256,
        "nullable": True,
        "editable": True,
        "domain": None,
        "defaultValue": None,
        "locationType": "Address"
      },
      {
        "name": "A1-City",
        "type": "esriFieldTypeString",
        "alias": "A1-City",
        "sqlType": "sqlTypeNVarchar",
        "length": 256,
        "nullable": True,
        "editable": True,
        "domain": None,
        "defaultValue": None,
        "locationType": "City"
      }
    ],
    "indexes": [],
    "types": [],
    "templates": [
      {
        "name": "New Feature",
        "description": "",
        "drawingTool": "esriFeatureEditToolPoint",
        "prototype": {
          "attributes": {
            "Name": None,
            "Street": None,
            "City": None,
            "State": None,
            "Zip": None
          }
        }
      }
    ],
    "supportedQueryFormats": "JSON, geoJSON",
    "hasStaticData": False,
    "maxRecordCount": -1,
    "standardMaxRecordCount": 32000,
    "tileMaxRecordCount": 8000,
    "maxRecordCountFactor": 1,
    "capabilities": "Querys"
  },
  "sourceCountryHint": "",
  "hasStaticData": True,
  "persistErrorRecordsForReview": True,
  "candidateFieldsType": "AllFields",
  "dateFieldsTimeReference": {
    "timeZone": "Pacific Standard Time"
  }
}

address_fields= { "CountryCode" : "Country"}
soil_source_site_item = csv_item.publish(
  publish_parameters=publish_parameters,
  address_fields=address_fields,
  overwrite=False,
  file_type="CSV")
"""





# update the item metadata
#item_prop = {'title':'USA Capitals'}
#cities_item.update(item_properties = item_prop, thumbnail='data/updating_gis_content/capital_cities.png')




"""
# Remove if same csv is already added to AGOL
tempCSV_to_delete = gis.content.search('title: update_features type: CSV')
for item in tempCSV_to_delete:
  if item:
    item.delete()

# Add the csv into a folder called Smartsheets in AGOL
item_prop = {'title':'update_features', 'description':'This csv has been created from Smartsheets', 'tags':'Smartsheet, csv, Python API'}
csv_item = gis.content.add(item_properties=item_prop, data=output_csv, folder='SmartSheets')

# Get the hosted feature layer
feature_layer_item = gis.content.get(hosted_feature.id)
fLyr = feature_layer_item.layers[0]

# Truncate the hosted feature layer
fLyr.manager.truncate()

# append the newly added csv to the hosted feature layer
param1 = gis.content.analyze(item.csv_item.id)
fLyr.append(item_id=csv_item.id, upload_format='csv', source_info=param1['publishParameters'])
"""





# Find a location or feature to open the map
# https://doc.arcgis.com/en/web-appbuilder/latest/manage-apps/app-url-parameters.htm
# example: (1) using site addrees: http://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=8a6afeae8fdd4960a0ea0df1fa34aa74&find=6810%20Random%20St.
#          (2) using siteIdentificationNumber: https://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=8a6afeae8fdd4960a0ea0df1fa34aa74&find=382011



"""
print('Sending subscriber emails...')

#Email sending testing
#emailMsg = '<a href=&quot;http://www.google.com&quot;>asdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfaasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdsdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasfasdfaasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfasdfassssssssssssssssssssssssssssssssssssssssssssssasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasd-end</a>'
#send_mail('rjeong@vividsolutions.com', '5153 char-Soil Relocations Notification', emailMsg)

# iterate through the submissions and send an email
# Only send emails for sites that are new (don't resend for old sites)

emailSubjSR = 'Soil Relocations Notification'
emailSubjHV = 'High Volume Site Registrations Notification'

today = datetime.datetime.now().replace(hour = 0, minute = 0, second = 0, microsecond = 0)
# print(today)
counterTesting = 0
counterTesting2 = 0

for subscriber in subscribersJson:
  print(subscriber)

  if counterTesting == 1:
    break
  counterTesting = 1

  subscriberEmail = ''
  regionalDistrict = [] # could be more than one
  notifyOnHighVolumeSiteRegistrations = False
  notifyOnSoilRelocationsInSelectedDistrict = False
  unsubscribe = False

  if subscriber.get("emailAddress") is not None : subscriberEmail = subscriber["emailAddress"]
  if subscriber.get("regionalDistrict") is not None : regionalDistrict = subscriber["regionalDistrict"] 
  if subscriber.get("notificationSelection") is not None : 
    notificationSelectionStr = json.dumps(subscriber["notificationSelection"])
    notificationSelectionJson = json.loads(notificationSelectionStr)
    notifyOnHighVolumeSiteRegistrations = notificationSelectionJson['notifyOnHighVolumeSiteRegistrations']
    notifyOnSoilRelocationsInSelectedDistrict = notificationSelectionJson['notifyOnSoilRelocationsInSelectedDistrict']
  if subscriber.get("notificationSelection1") is not None : 
    notificationSelection1Str = json.dumps(subscriber["notificationSelection1"])
    notificationSelection1Json = json.loads(notificationSelection1Str)
    unsubscribe = notificationSelection1Json['unsubscribe']

  # print('subscriberEmail:' + subscriberEmail)
  # print(regionalDistrict)
  # print(notifyOnHighVolumeSiteRegistrations)
  # print(notifyOnSoilRelocationsInSelectedDistrict)
  # print(unsubscribe)

  if subscriberEmail is not None and regionalDistrict is not None and unsubscribe == False:
    ""
    # Notification of soil relocation in selected Regional District(s)
    if notifyOnSoilRelocationsInSelectedDistrict == True:
      for receivingSiteData in receivingSites:

        if counterTesting2 == 1:
          break
        counterTesting2 = 1

        # For new/old submissions, you'll have to compare the submission create date against the current script runtime. 
        # This may require finding a way to store a "last run time" for the script, or running the script once per day, 
        # and only sending submissions for where a create-date is within the last 24 hours.
        # d1 = datetime.datetime.utcfromtimestamp(receivingSiteData[140])
        createdAt = receivingSiteData[140]
        # print(createdAt)
        daysDiff = (today - createdAt).days
        # print(daysDiff)
        if (daysDiff >= 1):
          
          #for testing the following condition line commented out, SHOULD BE UNCOMMENT OUT after testing!!!!
          #if receivingSiteData[31] == regionalDistrict: # ReceivingSiteregionalDistrict
            regDis = convert_regional_district_to_name(regionalDistrict[0])
            emailMsg = create_site_relocation_email_msg(regDis)
            subscriberEmail = 'rjeong@vividsolutions.com'
            send_mail(subscriberEmail, emailSubjSR, emailMsg)
    ""
    # Notification of high volume site registration in selected Regional District(s)        
    
    #for testing the following condition line commented out, SHOULD BE UNCOMMENT OUT after testing!!!!
    #if notifyOnHighVolumeSiteRegistrations == True:
    for hvSiteData in hvSites:

      if counterTesting2 == 1:
        break
      counterTesting2 = 1

      createdAt = hvSiteData[70]
      # print(createdAt)
      daysDiff = (today - createdAt).days
      # print(daysDiff)

      if (daysDiff >= 1):
        for rd in regionalDistrict:
          # finding if subscriber's regional district in high volumn receiving site registration
          hvSitesInRD = hvSitesDic.get(rd)
          createLinkToPopupOnMap(hvSitesInRD)


          if hvSitesInRD is not None:
            hvRegDis = convert_regional_district_to_name(rd)
            hvSiteEmailMsg = create_hv_site_email_msg(hvRegDis)
            subscriberEmail = 'rjeong@vividsolutions.com'
            send_mail(subscriberEmail, emailSubjHV, hvSiteEmailMsg)
    
"""


print('Completed Soils data publishing')