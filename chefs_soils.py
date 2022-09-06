import requests
from requests.auth import HTTPBasicAuth
import json, csv, datetime, copy
import urllib.parse
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection


# CSV file names
srcCSV = 'soil_relocation_source_sites.csv'
rcvCSV = 'soil_relocation_receiving_sites.csv'
hvCSV = 'high_volumn_receiving_sites.csv'

# Soil Relocation Source Sites Item Id
srcCSVId = 'c34c998c1feb4796a61d7e0aef256c12'
srcLayerId = '4a35bb807eec41af9000e9d12b45b06e'

# Soil Relocation Receiving Sites Item Id
rcvCSVId = '2dcbe99f7ea04da19319e0f398b74310'
rcvLayerId = '7cf27ebd5078431394ad4aa7fe1d7f4f'

# High Volume Receiving Sites Item Id
hvCSVId = '90fea595e88549018e9ecd37ef90b9fc'
hvLayerId = 'a5e6db91a855410f9dd5b6ccdb4a6857'

# WEB Mapping Application Itme Id
webMapAppId = '8a6afeae8fdd4960a0ea0df1fa34aa74' #should be changed


maphubUrl = r'https://governmentofbc.maps.arcgis.com'



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



testSrcLats = ['53.89428','58.0151','57.07397','55.56444']
testSrcLons = ['-122.6543','-115.7708','-119.22593','-125.04611']

testRcvLats = ['54.046489','53.317749','52.462704','51.788232']
testRcvLons = ['-127.023798','-124.95887','-126.265493','-123.377022']

testHVLats = ['51.590723','51.672555','52.153714','52.321911']
testHVLons = ['-121.805686','-124.65016','-125.738196','-123.519695']


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
  # print(chesResponse.text)
  chesContent = json.loads(chesResponse.content)
  return chesContent

def is_json(string):
  try:
    json.loads(str(string))
  except ValueError as e:
    return False
  return True

def site_list(form_id, form_key):
  request = requests.get(chefsUrl + '/forms/' + form_id + '/export?format=json&type=submissions', auth=HTTPBasicAuth(form_id, form_key), headers={'Content-type': 'application/json'})
  # print('Parsing JSON response')
  content = json.loads(request.content)
  return content

def fetch_columns(form_id, form_key):
  request = requests.get(chefsUrl + '/forms/' + form_id + '/versions', auth=HTTPBasicAuth(form_id, form_key), headers={'Content-type': 'application/json'})
  request_json = json.loads(request.content)
  version = request_json[0]['id']

  attribute_request = requests.get(chefsUrl + '/forms/' + form_id + '/versions/' + version + '/fields', auth=HTTPBasicAuth(form_id, form_key), headers={'Content-type': 'application/json'})
  attributes = json.loads(attribute_request.content)
  return attributes

def create_site_relocation_email_msg(regional_district, popup_links):
  msg = '<p>Soil Relocation Notifications are received by the ministry under section 55 of the <i>Environmental Management Act</i>. For more information on soil relocation from commercial and industrial sites in BC, please visit our <a href=https://soil-relocation-information-system-governmentofbc.hub.arcgis.com/>webpage</a>.</p>'
  msg += '<p>This email is to notify you that soil is being relocated in the Regional District: <span style=font-weight:bold;color:red;>' 
  msg += regional_district
  msg += '</span></p>\
        <p>The following new submission(s) were received.<p/>\
        <p font-style:italic>'
  msg += popup_links
  msg += '</p><br/>\
        <p><hr style=height:1px;border-top:dotted;color:#1c1b1b;background-color:#1c1b1b;/></p>\
        <p><b>To search the <a href=https://soil-relocation-information-system-governmentofbc.hub.arcgis.com/>Soil Relocation Information System</a> (SRIS):</b></p>\
        <p>Click on the link above to access the web page containing information on soil movement from commercial and industrial sites in BC.</p>\
        Click &#8216;view&#8217; under the <b>Soil Relocation Dashboard</b> and follow the search instructions below:\
        <ul>\
          <li>click on the small arrow on the left of the screen  to open search options</li>\
          <li>Filter by site address, regional district, high volume sites, and more.</li>\
          <li>On the map, you can zoom to the area you interested in and click on a single location. This will bring up information on that site including the address, volume of soil being moved, start date and finish date of the soil movement.</li>\
          <li>On the map, you can also select a rectangular area and view data in csv format for all sites within that rectangle.</li>\
        </ul>\
        <p>You can also search for information on the <b>Soil Relocation Site Map</b> by clicking on &#8216;view&#8217; under the Soil relocation site map on the main page.'

  msg += '<hr style=height:1px;border:none;color:#1c1b1b;background-color:#1c1b1b;/></p><br/><br/><br/>'
  msg += '<hr style=height:4px;border:none;color:#4da6ff;background-color:#4da6ff;/>'
  msg += '<span style=font-style:italic;color:#4da6ff;>You are receiving this email because you subscribed to receive email notifications of soil relocation or high-volume site registrations in select Regional Districts in BC.  If you wish to stop receiving these email notifications, please select &#8216;unsubscribe&#8217; on the subscription <a href=https://chefs.nrs.gov.bc.ca/app/form/submit?f=' + subscriptionFormId + '>form</a></span>.<br/>'
  msg += '<hr style=height:4px;border:none;color:#4da6ff;background-color:#4da6ff;/>'
  return msg

def create_hv_site_email_msg(regional_district, popup_links):
  msg = '<p>High Volume Receiving Site Registrations are received by the ministry under section 55.1 of the <i>Environmental Management Act</i>.  For more information on soil relocation from commercial and industrial sites in BC, please visit our <a href=https://soil-relocation-information-system-governmentofbc.hub.arcgis.com/>webpage</a>.</p>'
  msg += '<p>This email is to notify you that a registration for a high volume site has been received in Regional District: <span style=font-weight:bold;color:red;>'
  msg += regional_district
  msg += '</span></p>\
        <p>The following new high volume receiving site registration(s) were received.<p/>\
        <p font-style:italic>'
  msg += popup_links
  msg += '</p><br/>\
        <p><hr style=height:1px;border-top:dotted;color:#1c1b1b;background-color:#1c1b1b;/></p>\
        <p><b>To search the <a href=https://soil-relocation-information-system-governmentofbc.hub.arcgis.com/>Soil Relocation Information System</a> (SRIS):</b></p>\
        <p>Click on the link above to access the web page containing information on soil movement from commercial and industrial sites in BC.</p>\
        Click &#8216;view&#8217; under the <b>Soil Relocation Dashboard</b> and follow the search instructions below:\
        <ul>\
          <li>click on the small arrow on the left of the screen to open search options</li>\
          <li>Filter by site address, regional district, high volume sites, and more.</li>\
          <li>On the map, you can zoom to the area you interested in and click on a single location. This will bring up information on that site including the address, volume of soil being moved, start date and finish date of the soil movement</li>\
          <li>On the map, you can also select a rectangular area and view data in csv format for all sites within that rectangle.</li>\
        </ul>\
        <p>You can also search for information on the <b>Soil Relocation Site Map</b> by clicking on &#8216;view&#8217; under the Soil relocation site map on the main page.'
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

# create links to popup on Map using receiving sites searching keywords
def create_popup_links(rcv_sites):
    #PID
    #PIN    
  links = ''  
  link_prx = '<a href=https://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=' + webMapAppId + '&find='
  link_suf = '>Link to new submission</a><br/>'

  if rcv_sites is not None:
    for rcv_site in rcv_sites:
      links += link_prx

      if rcv_site[24] is not None and rcv_site[24].strip() != '':
        links += urllib.parse.quote(rcv_site[24]) #Site ID
      elif rcv_site[3] is not None and rcv_site[3].strip() != '':
        links += urllib.parse.quote(rcv_site[3]) #Receiving Site Owner Address
      elif rcv_site[11] is not None and rcv_site[11].strip() != '':
        links += urllib.parse.quote(rcv_site[11])  #Additional Owner Address
      #elif rcv_site[7] is not None and rcv_site[7].strip() != '':
      #  links += rcv_site[7]  #Receiving Site Owner postal Code
      #elif rcv_site[18] is not None and rcv_site[18].strip() != '':
      #  links += rcv_site[18]  #Receiving Site Owner Address
      elif rcv_site[2] is not None and rcv_site[2].strip() != '':
        links += urllib.parse.quote(rcv_site[2])  #Receiving Site Owner Company
      elif rcv_site[10] is not None and rcv_site[10].strip() != '':
        links += urllib.parse.quote(rcv_site[10])  #Additional Owner Company

      links += link_suf
  return links

# high volumn soil receiving sites
def create_hv_popup_links(hv_sites):
    #PID
    #PIN    
  links = ''  
  link_prx = '<a href=https://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=' + webMapAppId + '&find='
  link_suf = '>Link to new high volume receiving site registration</a><br/>'
  if hv_sites is not None:
    for hv_site in hv_sites:
      links += link_prx
      if hv_site[33] is not None and hv_site[33].strip() != '':
        links += urllib.parse.quote(hv_site[33]) #Site ID
      elif hv_site[3] is not None and hv_site[3].strip() != '':
        links += urllib.parse.quote(hv_site[3]) #Receiving Site Owner Address
      elif hv_site[14] is not None and hv_site[14].strip() != '':
        links += urllib.parse.quote(hv_site[14])  #Additional Owner Address
      elif hv_site[7] is not None and hv_site[7].strip() != '':
        links += urllib.parse.quote(hv_site[7])  #Receiving Site Owner postal Code
      elif hv_site[18] is not None and hv_site[18].strip() != '':
        links += urllib.parse.quote(hv_site[18])  #Receiving Site Owner Address
      elif hv_site[2] is not None and hv_site[2].strip() != '':
        links += urllib.parse.quote(hv_site[2])  #Receiving Site Owner Company
      elif hv_site[13] is not None and hv_site[13].strip() != '':
        links += urllib.parse.quote(hv_site[13])  #Additional Owner Company

      links += link_suf
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
# print(submissionsJson)
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
  "confirmationId", # not in soilsAttributes, but in submissionsJson
  "Latitude",
  "Longitude"  
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
  "confirmationId", # not in hvsAttributes, but in hvsJson
  "Latitude",
  "Longitude"
]

sourceSites = [] # [''] * len(submissionsJson)
receivingSites = [] # [''] * len(submissionsJson)
rcvSitesDic = {}
sourceSiteLatLon = []
testingCount1 = 0
testingCount2 = 0
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
  sourceSiteData[74] = testSrcLats[testingCount1]
  sourceSiteData[75] = testSrcLons[testingCount1]
  testingCount1 = testingCount1 +1

  sourceSites.append(sourceSiteData)



  # Map submission data to the receiving site
  receivingSiteData = [''] * 144
  receivingSiteDataCopy = [''] * 144
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
  #if submission.get("ReceivingSiteLocationMap") is not None : receivingSiteData[32] = submission["ReceivingSiteLocationMap"]
  if submission.get("C2-receivinglandOwnership-checkbox") is not None : receivingSiteData[33] = submission["C2-receivinglandOwnership-checkbox"]
  if submission.get("C2-LegallyTitled-AddressReceivingSite") is not None : receivingSiteData[34] = submission["C2-LegallyTitled-AddressReceivingSite"]
  if submission.get("C2-LegallyTitled-CityReceivingSite") is not None : receivingSiteData[35] = submission["C2-LegallyTitled-CityReceivingSite"]
  if submission.get("C2-LegallyTitled-PostalReceivingSite") is not None : receivingSiteData[36] = submission["C2-LegallyTitled-PostalReceivingSite"]
  #if submission.get("dataGrid2") is not None : receivingSiteData[37] = submission["dataGrid2"]
  #if submission.get("ReceivingSiteLandTitleRecord") is not None : receivingSiteData[38] = submission["ReceivingSiteLandTitleRecord"]
  #if submission.get("dataGrid5") is not None : receivingSiteData[39] = submission["dataGrid5"]
  #if submission.get("A-UntitledCrownLand-FileNumberColumn1") is not None : receivingSiteData[40] = submission["A-UntitledCrownLand-FileNumberColumn1"]
  #if submission.get("A-UntitledMunicipalLand-PIDColumn1") is not None : receivingSiteData[41] = submission["A-UntitledMunicipalLand-PIDColumn1"]
  #if submission.get("C3-soilClassification1ReceivingSite") is not None : receivingSiteData[42] = submission["C3-soilClassification1ReceivingSite"]
  if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule31ReceivingSite") is not None : receivingSiteData[43] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule31ReceivingSite"]
  if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule32ReceivingSite") is not None : receivingSiteData[44] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule32ReceivingSite"]
  if submission.get("C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime") is not None : receivingSiteData[45] = submission["C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime"]
  #if submission.get("additionalReceivingSites") is not None : receivingSiteData[46] = submission["additionalReceivingSites"]
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
  #if submission.get("dataGrid3") is not None : receivingSiteData[84] = submission["dataGrid3"]
  if submission.get("FirstAdditionalReceivingSiteLandTitle") is not None : receivingSiteData[85] = submission["FirstAdditionalReceivingSiteLandTitle"]
  #if submission.get("dataGrid6") is not None : receivingSiteData[86] = submission["dataGrid6"]
  #if submission.get("A-UntitledCrownLand-FileNumberColumn2") is not None : receivingSiteData[87] = submission["A-UntitledCrownLand-FileNumberColumn2"]
  #if submission.get("A-UntitledMunicipalLand-PIDColumn2") is not None : receivingSiteData[88] = submission["A-UntitledMunicipalLand-PIDColumn2"]
  if submission.get("C3-soilClassification2FirstAdditionalReceivingSite") is not None : receivingSiteData[89] = submission["C3-soilClassification2FirstAdditionalReceivingSite"]
  if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule33FirstAdditionalReceivingSite") is not None : receivingSiteData[90] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule33FirstAdditionalReceivingSite"]
  if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule34FirstAdditionalReceivingSite") is not None : receivingSiteData[91] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule34FirstAdditionalReceivingSite"]
  if submission.get("C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1") is not None : receivingSiteData[92] = submission["C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1"]
  #if submission.get("secondadditionalReceivingSites1") is not None : receivingSiteData[93] = submission["secondadditionalReceivingSites1"]
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
  #if submission.get("dataGrid4") is not None : receivingSiteData[131] = submission["dataGrid4"]
  if submission.get("SecondAdditionalReceivingSiteLandTitle2") is not None : receivingSiteData[132] = submission["SecondAdditionalReceivingSiteLandTitle2"]
  #if submission.get("dataGrid7") is not None : receivingSiteData[133] = submission["dataGrid7"]
  #if submission.get("A-UntitledCrownLand-FileNumberColumn3") is not None : receivingSiteData[134] = submission["A-UntitledCrownLand-FileNumberColumn3"]
  #if submission.get("A-UntitledMunicipalLand-PIDColumn3") is not None : receivingSiteData[135] = submission["A-UntitledMunicipalLand-PIDColumn3"]
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

  # convert lat/lon
  receivingSiteLatLon = convert_deciaml_lat_long(receivingSiteData[25], receivingSiteData[26], receivingSiteData[27], receivingSiteData[28], receivingSiteData[29], receivingSiteData[30])
  #for testing
  #receivingSiteData[142] = receivingSiteLatLon[0] # receiving site latitude
  #receivingSiteData[143] = receivingSiteLatLon[1] # receiving site longitude
  receivingSiteData[142] = testRcvLats[testingCount2]
  receivingSiteData[143] = testRcvLons[testingCount2]
  testingCount2 = testingCount2 +1

  receivingSites.append(receivingSiteData)

  # 'sitesDic' dictionary - key:regionalDistrict / value:receivingSiteData
  receivingSiteDataCopy = copy.deepcopy(receivingSiteData)
  for rd in receivingSiteData[31]: # could be more than one
    if rd is not None: 

      #for testing
      rd = 'metroVancouverRegionalDistrict' 

      if rd in rcvSitesDic:
        rcvSitesDic[rd].append(receivingSiteDataCopy)
      else:
        rcvSitesDic[rd] = [receivingSiteDataCopy]



hvSites = [] # [''] * len(hvsJson)
hvSitesDic = {}
testingCount3 = 0
# create high volumn site records
for hvs in hvsJson:
  # print(hvs)
  # Map hv data to the hv site
  hvSiteData = [''] * 74
  hvSiteDataCopy = [''] * 74
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
  #if hvs.get("uploadMapOfHighVolumeSiteLocation") is not None : hvSiteData[41] = hvs["uploadMapOfHighVolumeSiteLocation"]
  if hvs.get("landOwnership-checkbox") is not None : hvSiteData[42] = hvs["landOwnership-checkbox"]
  if hvs.get("Section3-LegallyTitled-Address") is not None : hvSiteData[43] = hvs["Section3-LegallyTitled-Address"]
  if hvs.get("Section3-LegallyTitled-City") is not None : hvSiteData[44] = hvs["Section3-LegallyTitled-City"]
  if hvs.get("Section3-LegallyTitled-PostalZipCode") is not None : hvSiteData[45] = hvs["Section3-LegallyTitled-PostalZipCode"]
  #if hvs.get("dataGrid") is not None : hvSiteData[46] = hvs["dataGrid"]
  #if hvs.get("uploadMapOfHighVolumeSiteLocation1") is not None : hvSiteData[47] = hvs["uploadMapOfHighVolumeSiteLocation1"]
  #if hvs.get("dataGrid1") is not None : hvSiteData[48] = hvs["dataGrid1"]
  #if hvs.get("A-UntitledCrownLand-FileNumberColumn") is not None : hvSiteData[49] = hvs["A-UntitledCrownLand-FileNumberColumn"]
  #if hvs.get("A-UntitledMunicipalLand-PIDColumn") is not None : hvSiteData[50] = hvs["A-UntitledMunicipalLand-PIDColumn"]
  #if hvs.get("primarylanduse") is not None : hvSiteData[51] = hvs["primarylanduse"]
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

  # convert to lat/lon
  hvSiteLatLon = convert_deciaml_lat_long(hvSiteData[34], hvSiteData[35], hvSiteData[36], hvSiteData[37], hvSiteData[38], hvSiteData[39])
  #for testing
  #hvSiteData[72] = hvSiteLatLon[0] # High Volume Site latitude
  #hvSiteData[73] = hvSiteLatLon[1] # High Volume Site longitude
  hvSiteData[72] = testHVLats[testingCount3]
  hvSiteData[73] = testHVLons[testingCount3]
  testingCount3 = testingCount3 +1

  hvSites.append(hvSiteData)

  # 'hvSitesDic' dictionary - key:regionalDistrict / value:hvSiteData
  hvSiteDataCopy = copy.deepcopy(hvSiteData)
  for rd in hvSiteData[40]: # could be more than one
    if rd is not None: 

      #for testing
      rd = 'metroVancouverRegionalDistrict' 

      if rd in hvSitesDic:
        hvSitesDic[rd].append(hvSiteDataCopy)
      else:
        hvSitesDic[rd] = [hvSiteDataCopy]




print('Creating soil source site CSV...')
with open(srcCSV, 'w', encoding='UTF8', newline='') as f:  
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
with open(rcvCSV, 'w', encoding='UTF8', newline='') as f:  
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
with open(hvCSV, 'w', encoding='UTF8', newline='') as f:  
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



"""
print('Connecting to AGOL GIS...')
# connect to GIS
gis = GIS(maphubUrl, username=maphubUser, password=maphubPass)

print('Updating Soil Relocation Soruce Site CSV...')
srcCsvItem = gis.content.get(srcCSVId)
srcCsvUpdateResult = srcCsvItem.update({}, srcCSV)
print('Updating Soil Relocation Soruce Site Feature Layer...')
srcLyrItem = gis.content.get(srcLayerId)
srcFlc = FeatureLayerCollection.fromitem(srcLyrItem)
srcLyrOverwriteResult = srcFlc.manager.overwrite(srcCSV)

print('Updating Soil Relocation Soruce Site CSV...')
rcvCsvItem = gis.content.get(rcvCSVId)
rcvCsvUpdateResult = rcvCsvItem.update({}, rcvCSV)
print('Updating Soil Relocation Receiving Site Feature Layer...')
rcvLyrItem = gis.content.get(rcvLayerId)
rcvFlc = FeatureLayerCollection.fromitem(rcvLyrItem)
rcvLyrOverwriteResult = rcvFlc.manager.overwrite(rcvCSV)

print('Updating High Volume Receiving Site CSV...')
hvCsvItem = gis.content.get(hvCSVId)
hvCsvUpdateResult = hvCsvItem.update({}, hvCSV)
print('Updating High Volume Receiving Site Feature Layer...')
hvLyrItem = gis.content.get(hvLayerId)
hvFlc = FeatureLayerCollection.fromitem(hvLyrItem)
hvLyrOverwriteResult = hvFlc.manager.overwrite(hvCSV)
"""




# Find a location or feature to open the map
# https://doc.arcgis.com/en/web-appbuilder/latest/manage-apps/app-url-parameters.htm
# example: (1) using site addrees: http://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=8a6afeae8fdd4960a0ea0df1fa34aa74&find=6810%20Random%20St.
#          (2) using siteIdentificationNumber: https://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=8a6afeae8fdd4960a0ea0df1fa34aa74&find=382011


print('Sending subscriber emails...')

#Email sending testing
#emailMsg = '<a href=&quot;http://www.google.com&quot;>asdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfaasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdsdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasfasdfaasdfasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfasdfassssssssssssssssssssssssssssssssssssssssssssssasdfaasdfasdfasdfaasdfasdfasdfaasdfasdfasdfaasdfasd-end</a>'
#send_mail('rjeong@vividsolutions.com', '5153 char-Soil Relocations Notification', emailMsg)

# iterate through the submissions and send an email
# Only send emails for sites that are new (don't resend for old sites)

emailSubjectSR = 'SRIS Subscription Service - New Notification(s) Received (Soil Relocation)'
emailSubjectHV = 'SRIS Subscription Service - New Registration(s) Received (High Volume Receiving Site)'

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
          for rd in regionalDistrict:
            # finding if subscriber's regional district in receiving site registration
            sitesInRD = rcvSitesDic.get(rd)
            popupLinks = create_popup_links(sitesInRD)

            #for testing the following condition line commented out, SHOULD BE UNCOMMENT OUT after testing!!!!
            #if receivingSiteData[31] == regionalDistrict: # ReceivingSiteregionalDistrict
            if sitesInRD is not None:
              regDis = convert_regional_district_to_name(rd)
              emailMsg = create_site_relocation_email_msg(regDis, popupLinks)
              send_mail('rjeong@vividsolutions.com', emailSubjectSR, emailMsg)
    

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
          hvPopupLinks = create_hv_popup_links(hvSitesInRD)

          if hvSitesInRD is not None:
            hvRegDis = convert_regional_district_to_name(rd)
            hvEmailMsg = create_hv_site_email_msg(hvRegDis, hvPopupLinks)
            send_mail('rjeong@vividsolutions.com', emailSubjectHV, hvEmailMsg)


print('Completed Soils data publishing')