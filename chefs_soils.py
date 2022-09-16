import requests
from requests.auth import HTTPBasicAuth
import json, csv, datetime, copy
import urllib.parse
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection


# CSV file names
SOURCE_CSV_FILE = 'soil_relocation_source_sites.csv'
RECEIVE_CSV_FILE = 'soil_relocation_receiving_sites.csv'
HIGH_VOLUME_CSV_FILE = 'high_volumn_receiving_sites.csv'

# Soil Relocation Source Sites Item Id
srcCSVId = '4bfbda4fd22f4ab68fc548b3cfdf41cf'
srcLayerId = 'f99012760e9e4f4394e54abdbfd1f1f8'

# Soil Relocation Receiving Sites Item Id
rcvCSVId = '426e40d6525747bb801c698357dea3b5'
rcvLayerId = 'af9724382684495cbbc8aeeb6e20ea26'

# High Volume Receiving Sites Item Id
hvCSVId = '90fea595e88549018e9ecd37ef90b9fc'
hvLayerId = 'a5e6db91a855410f9dd5b6ccdb4a6857'

# WEB Mapping Application Itme Id
webMapAppId = '8a6afeae8fdd4960a0ea0df1fa34aa74' #should be changed


maphubUrl = r'https://governmentofbc.maps.arcgis.com'


# Move these to a configuration file
chefsUrl = 'https://submit.digital.gov.bc.ca/app/api/v1'

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

DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'
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

def send_mail(to_email, subject, message):
  to_email = 'rjeong@vividsolutions.com'
  auth_pay_load = 'grant_type=client_credentials'
  auth_haders = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': 'Basic ' + chesEncodedServiceClientKey
  }
  auth_response = requests.request("POST", authUrl + '/auth/realms/jbd6rnxw/protocol/openid-connect/token', headers=auth_haders, data=auth_pay_load)
  # print(authResponse.text)
  auth_response_json = json.loads(auth_response.content)
  access_token = auth_response_json['access_token']

  from_email = "noreply@gov.bc.ca"
  ches_pay_load = "{\n \"bodyType\": \"html\",\n \"body\": \""+message+"\",\n \"delayTS\": 0,\n \"encoding\": \"utf-8\",\n \"from\": \""+from_email+"\",\n \"priority\": \"normal\",\n  \"subject\": \""+subject+"\",\n  \"to\": [\""+to_email+"\"]\n }\n"
  ches_headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer ' + access_token
  }
  ches_response = requests.request("POST", chesUrl + '/api/v1/email', headers=ches_headers, data=ches_pay_load)
  # print(chesResponse.text)
  ches_content = json.loads(ches_response.content)
  return ches_content

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
  msg += '</span></p>'

  if popup_links != "" and popup_links is not None:
    msg += '<p>The following new submission(s) were received.<p/>\
            <p font-style:italic>'
    msg += popup_links
    msg += '</p><br/>'

  msg += '<p><hr style=height:1px;border-top:dotted;color:#1c1b1b;background-color:#1c1b1b;/></p>\
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
  msg += '</span></p>'

  if popup_links != "" and popup_links is not None:  
    msg += '<p>The following new high volume receiving site registration(s) were received.<p/>\
            <p font-style:italic>'
    msg += popup_links
    msg += '</p><br/>'

  msg += '<p><hr style=height:1px;border-top:dotted;color:#1c1b1b;background-color:#1c1b1b;/></p>\
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
  name = REGIONAL_DISTRICT_NAME_DIC.get(id)
  if name is not None:
    return name
  else:
    return id

# create links to popup on Map using receiving sites searching keywords
def create_rcv_popup_links(rcv_sites):
  links = ''  
  link_prx = '<a href=https://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=' + webMapAppId + '&find='
  link_suf = '>Link to new submission</a><br/>'

  if rcv_sites is not None:
    for _rcv_site_dic in rcv_sites:
      links += link_prx

      if _rcv_site_dic['SID'] is not None and _rcv_site_dic['SID'].strip() != '':
        links += urllib.parse.quote(_rcv_site_dic['SID']) #Site ID
      elif _rcv_site_dic['PID'] is not None and _rcv_site_dic['PID'].strip() != '':
        links += urllib.parse.quote(_rcv_site_dic['PID']) #PID
      elif _rcv_site_dic['PIN'] is not None and _rcv_site_dic['PIN'].strip() != '':
        links += urllib.parse.quote(_rcv_site_dic['PIN']) #PIN
      elif _rcv_site_dic['latitude'] is not None and _rcv_site_dic['latitude'].strip() != '' and _rcv_site_dic['longitude'] is not None and _rcv_site_dic['longitude'].strip() != '':
        links += urllib.parse.quote(_rcv_site_dic['latitude']+','+_rcv_site_dic['latitude']) #Receiving Site lat/lon
      elif _rcv_site_dic['ownerAddress'] is not None and _rcv_site_dic['ownerAddress'].strip() != '':
        links += urllib.parse.quote(_rcv_site_dic['ownerAddress']) #Receiving Site Owner Address
      elif _rcv_site_dic['ownerCompany'] is not None and _rcv_site_dic['ownerCompany'].strip() != '':
        links += urllib.parse.quote(_rcv_site_dic['ownerCompany'])  #Receiving Site Owner Company

      links += link_suf
  return links

# high volumn soil receiving sites
def create_hv_popup_links(hv_sites):
  links = ''  
  link_prx = '<a href=https://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=' + webMapAppId + '&find='
  link_suf = '>Link to new high volume receiving site registration</a><br/>'
  if hv_sites is not None:
    for hv_site in hv_sites:
      links += link_prx
      if hv_site[33] is not None and hv_site[33].strip() != '':
        links += urllib.parse.quote(hv_site[33]) #Site ID
      elif hv_site[76] is not None and hv_site[76].strip() != '':
        links += urllib.parse.quote(hv_site[76]) #PID
      elif hv_site[77] is not None and hv_site[77].strip() != '':
        links += urllib.parse.quote(hv_site[77]) #PIN
      elif hv_site[72] is not None and hv_site[72].strip() != '' and hv_site[73] is not None and hv_site[73].strip() != '':
        links += urllib.parse.quote(hv_site[72]+','+hv_site[73]) #Receiving Site lat/lon
      elif hv_site[3] is not None and hv_site[3].strip() != '':
        links += urllib.parse.quote(hv_site[3]) #Receiving Site Owner Address
      elif hv_site[2] is not None and hv_site[2].strip() != '':
        links += urllib.parse.quote(hv_site[2])  #Receiving Site Owner Company

      links += link_suf
  return links

def convert_deciaml_lat_long(lat_deg, lat_min, lat_sec, lon_deg, lon_min, lon_sec):
  # Convert to DD in mapLatitude and mapLongitude
  data = []
  if (lat_deg is not None and lat_deg != '' and
      lat_min is not None and lat_min != '' and
      lat_sec is not None and lat_sec != '' and
      lon_deg is not None and lon_deg != '' and
      lon_min is not None and lon_min != '' and
      lon_sec is not None and lon_sec != ''
  ):
    lat_dd = (float(lat_deg) + float(lat_min)/60 + float(lat_sec)/(60*60))
    lon_dd = - (float(lon_deg) + float(lon_min)/60 + float(lon_sec)/(60*60))

    data.append(lat_dd)
    data.append(lon_dd)

  return data

def map_source_site(submission):
  _src_dic = {}
  testing_count2 = 0

  if (
    submission.get("A3-SourceSiteLatitude-Degrees") is not None and
    submission.get("A3-SourceSiteLatitude-Minutes") is not None and
    submission.get("A3-SourceSiteLatitude-Seconds") is not None and
    submission.get("A3-SourceSiteLongitude-Degrees") is not None and
    submission.get("A3-SourceSiteLongitude-Minutes") is not None and
    submission.get("A3-SourceSiteLongitude-Seconds") is not None
  ):
    print("Mapping sourece site ...")

    for src_header in sourceSiteHeaders:
      _src_dic[src_header] = None

    if submission.get("A1-FIRSTName") is not None : _src_dic['updateToPreviousForm'] = submission["Intro-New_form_or_update"]
    if submission.get("A1-FIRSTName") is not None : _src_dic['ownerFirstName'] = submission["A1-FIRSTName"]
    if submission.get("A1-LASTName") is not None : _src_dic['ownerLastName'] = submission["A1-LASTName"]
    if submission.get("A1-Company") is not None : _src_dic['ownerCompany'] = submission["A1-Company"]
    if submission.get("A1-Address") is not None : _src_dic['ownerAddress'] = submission["A1-Address"]
    if submission.get("A1-City") is not None : _src_dic['ownerCity'] = submission["A1-City"]
    if submission.get("A1-ProvinceState") is not None : _src_dic['ownerProvince'] = submission["A1-ProvinceState"]
    if submission.get("A1-Country") is not None : _src_dic['ownerCountry'] = submission["A1-Country"]
    if submission.get("A1-PostalZipCode") is not None : _src_dic['ownerPostalCode'] = submission["A1-PostalZipCode"]
    if submission.get("A1-Phone") is not None : _src_dic['ownerPhoneNumber'] = submission["A1-Phone"]
    if submission.get("A1-Email") is not None : _src_dic['ownerEmail'] = submission["A1-Email"]

    if submission.get("A1-additionalownerFIRSTName") is not None : _src_dic['owner2FirstName'] = submission["A1-additionalownerFIRSTName"]
    if submission.get("A1-additionalownerLASTName1") is not None : _src_dic['owner2LastName'] = submission["A1-additionalownerLASTName1"]
    if submission.get("A1-additionalownerCompany1") is not None : _src_dic['owner2Company'] = submission["A1-additionalownerCompany1"]
    if submission.get("A1-additionalownerAddress1") is not None : _src_dic['owner2Address'] = submission["A1-additionalownerAddress1"]
    if submission.get("A1-additionalownerCity1") is not None : _src_dic['owner2City'] = submission["A1-additionalownerCity1"]
    if submission.get("A1-additionalownerPhone1") is not None : _src_dic['owner2PhoneNumber'] = submission["A1-additionalownerPhone1"]
    if submission.get("A1-additionalownerEmail1") is not None : _src_dic['owner2Email'] = submission["A1-additionalownerEmail1"]

    if submission.get("areThereMoreThanTwoOwnersIncludeTheirInformationBelow") is not None : _src_dic['additionalOwners'] = submission["areThereMoreThanTwoOwnersIncludeTheirInformationBelow"]
    if submission.get("A2-SourceSiteContactFirstName") is not None : _src_dic['contactFirstName'] = submission["A2-SourceSiteContactFirstName"]
    if submission.get("A2-SourceSiteContactLastName") is not None : _src_dic['contactLastName'] = submission["A2-SourceSiteContactLastName"]
    if submission.get("A2-SourceSiteContactCompany") is not None : _src_dic['contactCompany'] = submission["A2-SourceSiteContactCompany"]
    if submission.get("A2-SourceSiteContactAddress") is not None : _src_dic['contactAddress'] = submission["A2-SourceSiteContactAddress"]
    if submission.get("A2-SourceSiteContactCity") is not None : _src_dic['contactCity'] = submission["A2-SourceSiteContactCity"]
    if submission.get("SourceSiteContactphoneNumber") is not None : _src_dic['contactPhoneNumber'] = submission["SourceSiteContactphoneNumber"]
    if submission.get("A2-SourceSiteContactEmail") is not None : _src_dic['contactEmail'] = submission["A2-SourceSiteContactEmail"]

    if submission.get("A3-SourcesiteIdentificationNumberSiteIdIfAvailable") is not None : _src_dic['SID'] = submission["A3-SourcesiteIdentificationNumberSiteIdIfAvailable"]

    # convert lat/lon
    _src_lat_lon = convert_deciaml_lat_long(
      submission["A3-SourceSiteLatitude-Degrees"], submission["A3-SourceSiteLatitude-Minutes"], submission["A3-SourceSiteLatitude-Seconds"], 
      submission["A3-SourceSiteLongitude-Degrees"], submission["A3-SourceSiteLongitude-Minutes"], submission["A3-SourceSiteLongitude-Seconds"])
    #_src_dic['latitude'] = _src_lat_lon[0]
    #_src_dic['longitude'] = _src_lat_lon[0]
    _src_dic['latitude'] = testSrcLats[testing_count2] #for testing
    _src_dic['longitude'] = testSrcLons[testing_count2] #for testing
    testing_count2 = testing_count2 + 1

    if submission.get("SourceSiteregionalDistrict") is not None and len(submission['SourceSiteregionalDistrict']) > 0 : 
      _src_dic['regionalDistrict'] = "\"" + ",".join(submission["SourceSiteregionalDistrict"]) + "\""   # could be more than one

    if submission.get("SourcelandOwnership-checkbox") is not None : _src_dic['landOwnership'] = submission["SourcelandOwnership-checkbox"]
    if submission.get("A-LegallyTitled-AddressSource") is not None : _src_dic['legallyTitledSiteAddress'] = submission["A-LegallyTitled-AddressSource"]
    if submission.get("A-LegallyTitled-CitySource") is not None : _src_dic['legallyTitledSiteCity'] = submission["A-LegallyTitled-CitySource"]
    if submission.get("A-LegallyTitled-PostalZipCodeSource") is not None : _src_dic['legallyTitledSitePostalCode'] = submission["A-LegallyTitled-PostalZipCodeSource"]

    if submission.get("dataGrid") is not None and len(submission["dataGrid"]) > 0: 
      _dg = submission["dataGrid"][0] # could be more than one, but take only one
      if _dg.get("A-LegallyTitled-PID") is not None: _src_dic['PID'] = _dg["A-LegallyTitled-PID"]
      if _dg.get("legalLandDescriptionSource") is not None: _src_dic['legalLandDescription'] = _dg["legalLandDescriptionSource"]
    elif submission.get("dataGrid1") is not None and len(submission["dataGrid1"]) > 0: 
      _dg1 = submission["dataGrid1"][0] # could be more than one, but take only one
      if _dg1.get("A-UntitledPINSource") is not None: _src_dic['PIN'] = _dg1["A-UntitledPINSource"]
      if _dg1.get("legalLandDescriptionUntitledSource") is not None: _src_dic['legalLandDescription'] = _dg1["legalLandDescriptionUntitledSource"]
    elif submission.get("A-UntitledMunicipalLand-PIDColumnSource") is not None : _src_dic['legalLandDescription'] = submission["A-UntitledMunicipalLand-PIDColumnSource"]

    if submission.get("A-UntitledCrownLand-FileNumberColumnSource") is not None : 
      for _item in submission["A-UntitledCrownLand-FileNumberColumnSource"]:
        for _v in _item.values():
          if _v != '':
            _src_dic['crownLandFileNumbers'] = _v
            break    #could be more than one, but take only one
        if 'crownLandFileNumbers' in _src_dic:
          break

    if submission.get("A4-schedule2ReferenceSourceSite") is not None and len(submission.get("A4-schedule2ReferenceSourceSite")) > 0 : 
        _src_dic['sourceSiteLandUse'] = "\"" + ",".join(submission.get("A4-schedule2ReferenceSourceSite")) + "\""

    if submission.get("isTheSourceSiteHighRisk") is not None : _src_dic['highVolumneSite'] = submission["isTheSourceSiteHighRisk"]
    if submission.get("A5-PurposeOfSoilExcavationSource") is not None : _src_dic['soilRelocationPurpose'] = submission["A5-PurposeOfSoilExcavationSource"]
    if submission.get("B4-currentTypeOfSoilStorageEGStockpiledInSitu1Source") is not None : _src_dic['soilStorageType'] = submission["B4-currentTypeOfSoilStorageEGStockpiledInSitu1Source"]

    if submission.get("dataGrid9") is not None and len(submission["dataGrid9"]) > 0: 
      _dg9 = submission["dataGrid9"][0] # could be more than one, but take only one
      if _dg9.get("B1-soilVolumeToBeRelocationedInCubicMetresM3Source") is not None: _src_dic['soilVolume'] = _dg9["B1-soilVolumeToBeRelocationedInCubicMetresM3Source"]
      if _dg9.get("B1-soilClassificationSource") is not None and len(_dg9.get("B1-soilClassificationSource")) > 0 : 
        _soil_class = []
        for _k, _v in _dg9.get("B1-soilClassificationSource").items():
          if _v == True:
            _soil_class.append(_k)
            if len(_soil_class) > 0:
              _src_dic['soilQuality'] = "\"" + ",".join(_soil_class) + "\""
              break

    if submission.get("B2-describeSoilCharacterizationMethod1") is not None : _src_dic['soilCharacterMethod'] = submission["B2-describeSoilCharacterizationMethod1"]
    if submission.get("B3-yesOrNoVapourexemptionsource") is not None : _src_dic['vapourExemption'] = submission["B3-yesOrNoVapourexemptionsource"]
    if submission.get("B3-ifExemptionsApplyPleaseDescribe") is not None : _src_dic['vapourExemptionDesc'] = submission["B3-ifExemptionsApplyPleaseDescribe"]
    if submission.get("B3-describeVapourCharacterizationMethod") is not None : _src_dic['vapourCharacterMethodDesc'] = submission["B3-describeVapourCharacterizationMethod"]
    if submission.get("B4-soilRelocationEstimatedStartDateMonthDayYear") is not None : _src_dic['soilRelocationStartDate'] = submission["B4-soilRelocationEstimatedStartDateMonthDayYear"]
    if submission.get("B4-soilRelocationEstimatedCompletionDateMonthDayYear") is not None : _src_dic['soilRelocationCompletionDate'] = submission["B4-soilRelocationEstimatedCompletionDateMonthDayYear"]
    if submission.get("B4-RelocationMethod") is not None : _src_dic['relocationMethod'] = submission["B4-RelocationMethod"]

    if submission.get("D1-FirstNameQualifiedProfessional") is not None : _src_dic['qualifiedProfessionalFirstName'] = submission["D1-FirstNameQualifiedProfessional"]
    if submission.get("LastNameQualifiedProfessional") is not None : _src_dic['qualifiedProfessionalLastName'] = submission["LastNameQualifiedProfessional"]
    if submission.get("D1-TypeofQP1") is not None : _src_dic['qualifiedProfessionalType'] = submission["D1-TypeofQP1"]
    if submission.get("D1-professionalLicenseRegistrationEGPEngRpBio") is not None : _src_dic['professionalLicenceRegistration'] = submission["D1-professionalLicenseRegistrationEGPEngRpBio"]
    if submission.get("D1-organization1QualifiedProfessional") is not None : _src_dic['qualifiedProfessionalOrganization'] = submission["D1-organization1QualifiedProfessional"]
    if submission.get("D1-streetAddress1QualifiedProfessional") is not None : _src_dic['qualifiedProfessionalAddress'] = submission["D1-streetAddress1QualifiedProfessional"]
    if submission.get("D1-city1QualifiedProfessional") is not None : _src_dic['qualifiedProfessionalCity'] = submission["D1-city1QualifiedProfessional"]
    if submission.get("D1-provinceState3QualifiedProfessional") is not None : _src_dic['qualifiedProfessionalProvince'] = submission["D1-provinceState3QualifiedProfessional"]
    if submission.get("D1-canadaQualifiedProfessional") is not None : _src_dic['qualifiedProfessionalCountry'] = submission["D1-canadaQualifiedProfessional"]
    if submission.get("D1-postalZipCode3QualifiedProfessional") is not None : _src_dic['qualifiedProfessionalPostalCode'] = submission["D1-postalZipCode3QualifiedProfessional"]
    if submission.get("simplephonenumber1QualifiedProfessional") is not None : _src_dic['qualifiedProfessionalPhoneNumber'] = submission["simplephonenumber1QualifiedProfessional"]
    if submission.get("EmailAddressQualifiedProfessional") is not None : _src_dic['qualifiedProfessionalEmail'] = submission["EmailAddressQualifiedProfessional"]
    if submission.get("sig-firstAndLastNameQualifiedProfessional") is not None : _src_dic['signaturerFirstAndLastName'] = submission["sig-firstAndLastNameQualifiedProfessional"]
    if submission.get("simpledatetime") is not None : _src_dic['dateSigned'] = submission["simpledatetime"]

    if submission.get("form") is not None : 
      form_str = json.dumps(submission.get("form"))
      form_json = json.loads(form_str)
      created_at = datetime.datetime.strptime(form_json['createdAt'], DATE_TIME_FORMAT).replace(tzinfo = None, hour = 0, minute = 0, second = 0, microsecond = 0) # remove the timezone awareness
      confirmation_id = form_json['confirmationId']
      # not in attributes, but in json
      _src_dic['createAt'] = created_at
      if confirmation_id is not None : _src_dic['confirmationId'] = confirmation_id

  return _src_dic

def map_rcv_1st_rcver(submission):
  _rcv_dic = {}
  testing_count2 = 0
  if (
    submission.get("C2-Latitude-DegreesReceivingSite") is not None and
    submission.get("C2-Latitude-MinutesReceivingSite") is not None and
    submission.get("Section2-Latitude-Seconds1ReceivingSite") is not None and
    submission.get("C2-Longitude-DegreesReceivingSite") is not None and
    submission.get("C2-Longitude-MinutesReceivingSite") is not None and
    submission.get("C2-Longitude-SecondsReceivingSite") is not None
  ):
    print("Mapping 1st receiver ...")

    for rcv_header in receivingSiteHeaders:
      _rcv_dic[rcv_header] = None

    if submission.get("C1-FirstNameReceivingSiteOwner") is not None : _rcv_dic['ownerFirstName'] = submission["C1-FirstNameReceivingSiteOwner"]
    if submission.get("C1-LastNameReceivingSiteOwner") is not None : _rcv_dic['ownerLastName'] = submission["C1-LastNameReceivingSiteOwner"]
    if submission.get("C1-CompanyReceivingSiteOwner") is not None : _rcv_dic['ownerCompany'] = submission["C1-CompanyReceivingSiteOwner"]
    if submission.get("C1-AddressReceivingSiteOwner") is not None : _rcv_dic['ownerAddress'] = submission["C1-AddressReceivingSiteOwner"]
    if submission.get("C1-CityReceivingSiteOwner") is not None : _rcv_dic['ownerCity'] = submission["C1-CityReceivingSiteOwner"]
    if submission.get("C1-PhoneRecevingSiteOwner") is not None : _rcv_dic['ownerPhoneNumber'] = submission["C1-PhoneRecevingSiteOwner"]
    if submission.get("C1-EmailReceivingSiteOwner") is not None : _rcv_dic['ownerEmail'] = submission["C1-EmailReceivingSiteOwner"]

    if submission.get("C1-FirstName1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2FirstName'] = submission["C1-FirstName1ReceivingSiteAdditionalOwners"]
    if submission.get("C1-LastName1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2LastName'] = submission["C1-LastName1ReceivingSiteAdditionalOwners"]
    if submission.get("C1-Company1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2Company'] = submission["C1-Company1ReceivingSiteAdditionalOwners"]
    if submission.get("C1-Address1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2Address'] = submission["C1-Address1ReceivingSiteAdditionalOwners"]
    if submission.get("C1-City1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2City'] = submission["C1-City1ReceivingSiteAdditionalOwners"]
    if submission.get("C1-Phone1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2PhoneNumber'] = submission["C1-Phone1ReceivingSiteAdditionalOwners"]
    if submission.get("C1-Email1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2Email'] = submission["C1-Email1ReceivingSiteAdditionalOwners"]

    if submission.get("haveMoreThatTwoOwnersEnterTheirInformationBelow") is not None : _rcv_dic['additionalOwners'] = submission["haveMoreThatTwoOwnersEnterTheirInformationBelow"]
    if submission.get("C2-RSC-FirstName") is not None : _rcv_dic['contactFirstName'] = submission["C2-RSC-FirstName"]
    if submission.get("C2-RSC-LastName") is not None : _rcv_dic['contactLastName'] = submission["C2-RSC-LastName"]
    if submission.get("C2-RSC-Company") is not None : _rcv_dic['contactCompany'] = submission["C2-RSC-Company"]
    if submission.get("C2-RSC-Address") is not None : _rcv_dic['contactAddress'] = submission["C2-RSC-Address"]
    if submission.get("C2-RSC-City") is not None : _rcv_dic['contactCity'] = submission["C2-RSC-City"]
    if submission.get("C2-RSCphoneNumber1") is not None : _rcv_dic['contactPhoneNumber'] = submission["C2-RSCphoneNumber1"]
    if submission.get("C2-RSC-Email") is not None : _rcv_dic['contactEmail'] = submission["C2-RSC-Email"]
    if submission.get("C2-siteIdentificationNumberSiteIdIfAvailableReceivingSite") is not None : _rcv_dic['SID'] = submission["C2-siteIdentificationNumberSiteIdIfAvailableReceivingSite"]

    # convert lat/lon
    _rcv_lat_lon = convert_deciaml_lat_long(
      submission["C2-Latitude-DegreesReceivingSite"], submission["C2-Latitude-MinutesReceivingSite"], submission["Section2-Latitude-Seconds1ReceivingSite"], 
      submission["C2-Longitude-DegreesReceivingSite"], submission["C2-Longitude-MinutesReceivingSite"], submission["C2-Longitude-SecondsReceivingSite"])
    #_rcv_dic['latitude'] = _rcv_lat_lon[0]
    #_rcv_dic['longitude'] = _rcv_lat_lon[0]
    _rcv_dic['latitude'] = testRcvLats[testing_count2] #for testing
    _rcv_dic['longitude'] = testRcvLons[testing_count2] #for testing
    testing_count2 = testing_count2 + 1

    if submission.get("ReceivingSiteregionalDistrict") is not None and len(submission['ReceivingSiteregionalDistrict']) > 0 : 
      _rcv_dic['regionalDistrict'] = "\"" + ",".join(submission["ReceivingSiteregionalDistrict"]) + "\""

    #if submission.get("ReceivingSiteregionalDistrict") is not None and len(submission['ReceivingSiteregionalDistrict']) > 0 : _rcvDic['regionalDistrict'] = submission["ReceivingSiteregionalDistrict"][0] # could be more than one, but take only one
    if submission.get("C2-receivinglandOwnership-checkbox") is not None : _rcv_dic['landOwnership'] = submission["C2-receivinglandOwnership-checkbox"]
    if submission.get("C2-LegallyTitled-AddressReceivingSite") is not None : _rcv_dic['legallyTitledSiteAddress'] = submission["C2-LegallyTitled-AddressReceivingSite"]
    if submission.get("C2-LegallyTitled-CityReceivingSite") is not None : _rcv_dic['legallyTitledSiteCity'] = submission["C2-LegallyTitled-CityReceivingSite"]
    if submission.get("C2-LegallyTitled-PostalReceivingSite") is not None : _rcv_dic['legallyTitledSitePostalCode'] = submission["C2-LegallyTitled-PostalReceivingSite"]

    if submission.get("dataGrid2") is not None and len(submission["dataGrid2"]) > 0: 
      _dg2 = submission["dataGrid2"][0] # could be more than one, but take only one
      if _dg2.get("A-LegallyTitled-PIDReceivingSite") is not None: _rcv_dic['PID'] = _dg2["A-LegallyTitled-PIDReceivingSite"]
      if _dg2.get("legalLandDescriptionReceivingSite") is not None: _rcv_dic['legalLandDescription'] = _dg2["legalLandDescriptionReceivingSite"]
    elif submission.get("dataGrid5") is not None and len(submission["dataGrid5"]) > 0: 
      _dg5 = submission["dataGrid5"][0] # could be more than one, but take only one
      if _dg5.get("A-LegallyTitled-PID") is not None: _rcv_dic['PIN'] = _dg5["A-LegallyTitled-PID"]
      if _dg5.get("legalLandDescriptionUntitledCrownLandReceivingSite") is not None: _rcv_dic['legalLandDescription'] = _dg5["legalLandDescriptionUntitledCrownLandReceivingSite"]
    elif submission.get("A-UntitledMunicipalLand-PIDColumn1") is not None : _rcv_dic['legalLandDescription'] = submission["A-UntitledMunicipalLand-PIDColumn1"]

    if submission.get("C3-soilClassification1ReceivingSite") is not None : 
      _land_uses = []
      for _k, _v in submission["C3-soilClassification1ReceivingSite"].items():
        if _v == True:
          _land_uses.append(_k)
      if len(_land_uses) > 0:
        _rcv_dic['receivingSiteLandUse'] = "\"" + ",".join(_land_uses) + "\""

    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule31ReceivingSite") is not None : _rcv_dic['CSRFactors'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule31ReceivingSite"]
    if submission.get("C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime") is not None : _rcv_dic['highVolumneSite'] = submission["C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime"]
    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule32ReceivingSite") is not None : _rcv_dic['relocatedSoilUse'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule32ReceivingSite"]

    if submission.get("form") is not None : 
      form_str = json.dumps(submission.get("form"))
      form_json = json.loads(form_str)
      created_at = datetime.datetime.strptime(form_json['createdAt'], DATE_TIME_FORMAT).replace(tzinfo = None, hour = 0, minute = 0, second = 0, microsecond = 0) # remove the timezone awareness
      confirmation_id = form_json['confirmationId']
      # not in attributes, but in json
      _rcv_dic['createAt'] = created_at
      if confirmation_id is not None : _rcv_dic['confirmationId'] = confirmation_id

  return _rcv_dic

def map_rcv_2nd_rcver(submission):
  _rcv_dic = {}
  testing_count2 = 0
  if (
    submission.get("C2-Latitude-Degrees1FirstAdditionalReceivingSite") is not None and
    submission.get("C2-Latitude-Minutes1FirstAdditionalReceivingSite") is not None and
    submission.get("Section2-Latitude-Seconds2FirstAdditionalReceivingSite") is not None and
    submission.get("C2-Longitude-Degrees1FirstAdditionalReceivingSite") is not None and
    submission.get("C2-Longitude-Minutes1FirstAdditionalReceivingSite") is not None and
    submission.get("C2-Longitude-Seconds1FirstAdditionalReceivingSite") is not None
  ):
    print("Mapping 2nd receiver ...")

    for rcv_header in receivingSiteHeaders:
      _rcv_dic[rcv_header] = None

    if submission.get("C1-FirstName2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerFirstName'] = submission["C1-FirstName2FirstAdditionalReceivingSite"]
    if submission.get("C1-LastName2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerLastName'] = submission["C1-LastName2FirstAdditionalReceivingSite"]
    if submission.get("C1-Company2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerCompany'] = submission["C1-Company2FirstAdditionalReceivingSite"]
    if submission.get("C1-Address2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerAddress'] = submission["C1-Address2FirstAdditionalReceivingSite"]
    if submission.get("C1-City2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerCity'] = submission["C1-City2FirstAdditionalReceivingSite"]
    if submission.get("phoneNumber4FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerPhoneNumber'] = submission["phoneNumber4FirstAdditionalReceivingSite"]
    if submission.get("C1-Email2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerEmail'] = submission["C1-Email2FirstAdditionalReceivingSite"]

    if submission.get("C1-FirstName3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2FirstName'] = submission["C1-FirstName3AdditionalReceivingSiteOwner"]
    if submission.get("C1-LastName3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2LastName'] = submission["C1-LastName3AdditionalReceivingSiteOwner"]
    if submission.get("C1-Company3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2Company'] = submission["C1-Company3AdditionalReceivingSiteOwner"]
    if submission.get("C1-Address3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2Address'] = submission["C1-Address3AdditionalReceivingSiteOwner"]
    if submission.get("C1-City3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2City'] = submission["C1-City3AdditionalReceivingSiteOwner"]
    if submission.get("phoneNumber2AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2PhoneNumber'] = submission["phoneNumber2AdditionalReceivingSiteOwner"]
    if submission.get("C1-Email3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2Email'] = submission["C1-Email3AdditionalReceivingSiteOwner"]

    if submission.get("C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow2ReceivingSite") is not None : _rcv_dic['additionalOwners'] = submission["C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow2ReceivingSite"]
    if submission.get("C2-RSC-FirstName1AdditionalReceivingSite") is not None : _rcv_dic['contactFirstName'] = submission["C2-RSC-FirstName1AdditionalReceivingSite"]
    if submission.get("C2-RSC-LastName1AdditionalReceivingSite") is not None : _rcv_dic['contactLastName'] = submission["C2-RSC-LastName1AdditionalReceivingSite"]
    if submission.get("C2-RSC-Company1AdditionalReceivingSite") is not None : _rcv_dic['contactCompany'] = submission["C2-RSC-Company1AdditionalReceivingSite"]
    if submission.get("C2-RSC-Address1AdditionalReceivingSite") is not None : _rcv_dic['contactAddress'] = submission["C2-RSC-Address1AdditionalReceivingSite"]
    if submission.get("C2-RSC-City1AdditionalReceivingSite") is not None : _rcv_dic['contactCity'] = submission["C2-RSC-City1AdditionalReceivingSite"]
    if submission.get("phoneNumber3AdditionalReceivingSite") is not None : _rcv_dic['contactPhoneNumber'] = submission["phoneNumber3AdditionalReceivingSite"]
    if submission.get("C2-RSC-Email1AdditionalReceivingSite") is not None : _rcv_dic['contactEmail'] = submission["C2-RSC-Email1AdditionalReceivingSite"]
    if submission.get("C2-siteIdentificationNumberSiteIdIfAvailable1FirstAdditionalReceivingSite") is not None : _rcv_dic['SID'] = submission["C2-siteIdentificationNumberSiteIdIfAvailable1FirstAdditionalReceivingSite"]

    # convert lat/lon
    _rcv_lat_lon = convert_deciaml_lat_long(
      submission["C2-Latitude-Degrees1FirstAdditionalReceivingSite"], submission["C2-Latitude-Minutes1FirstAdditionalReceivingSite"], submission["Section2-Latitude-Seconds2FirstAdditionalReceivingSite"], 
      submission["C2-Longitude-Degrees1FirstAdditionalReceivingSite"], submission["C2-Longitude-Minutes1FirstAdditionalReceivingSite"], submission["C2-Longitude-Seconds1FirstAdditionalReceivingSite"])
    #_rcv_dic['latitude'] = _rcv_lat_lon[0]
    #_rcv_dic['longitude'] = _rcv_lat_lon[0]
    _rcv_dic['latitude'] = testRcvLats[testing_count2] #for testing
    _rcv_dic['longitude'] = testRcvLons[testing_count2] #for testing
    testing_count2 = testing_count2 + 1

    if submission.get("FirstAdditionalReceivingSiteregionalDistrict1") is not None and len(submission['FirstAdditionalReceivingSiteregionalDistrict1']) > 0 : 
      _rcv_dic['regionalDistrict'] = "\"" + ",".join(submission["FirstAdditionalReceivingSiteregionalDistrict1"]) + "\""

    if submission.get("Firstadditionalreceiving-landOwnership-checkbox1") is not None : _rcv_dic['landOwnership'] = submission["Firstadditionalreceiving-landOwnership-checkbox1"]
    if submission.get("C2-LegallyTitled-Address1FirstAdditionalReceivingSite") is not None : _rcv_dic['legallyTitledSiteAddress'] = submission["C2-LegallyTitled-Address1FirstAdditionalReceivingSite"]
    if submission.get("C2-LegallyTitled-City1FirstAdditionalReceivingSite") is not None : _rcv_dic['legallyTitledSiteCity'] = submission["C2-LegallyTitled-City1FirstAdditionalReceivingSite"]
    if submission.get("C2-LegallyTitled-PostalZipCode1FirstAdditionalReceivingSite") is not None : _rcv_dic['legallyTitledSitePostalCode'] = submission["C2-LegallyTitled-PostalZipCode1FirstAdditionalReceivingSite"]

    if submission.get("dataGrid3") is not None and len(submission["dataGrid3"]) > 0: 
      _dg3 = submission["dataGrid3"][0] # could be more than one, but take only one
      if _dg3.get("A-LegallyTitled-PIDFirstAdditionalReceivingSite") is not None: _rcv_dic['PID'] = _dg3["A-LegallyTitled-PIDFirstAdditionalReceivingSite"]
      if _dg3.get("legalLandDescriptionFirstAdditionalReceivingSite") is not None: _rcv_dic['legalLandDescription'] = _dg3["legalLandDescriptionFirstAdditionalReceivingSite"]
    elif submission.get("dataGrid6") is not None and len(submission["dataGrid6"]) > 0: 
      _dg6 = submission["dataGrid6"][0] # could be more than one, but take only one
      if _dg6.get("A-UntitledCrown-PINFirstAdditionalReceivingSite") is not None: _rcv_dic['PIN'] = _dg6["A-UntitledCrown-PINFirstAdditionalReceivingSite"]
      if _dg6.get("legalLandDescriptionUntitledCrownFirstAdditionalReceivingSite") is not None: _rcv_dic['legalLandDescription'] = _dg6["legalLandDescriptionUntitledCrownFirstAdditionalReceivingSite"]
    elif submission.get("A-UntitledMunicipalLand-PIDColumn2") is not None : _rcv_dic['legalLandDescription'] = submission["A-UntitledMunicipalLand-PIDColumn2"]

    #if submission.get("C3-soilClassification2FirstAdditionalReceivingSite") is not None : _rcvDic['receivingSiteLandUse'] = submission["C3-soilClassification2FirstAdditionalReceivingSite"]
    if submission.get("C3-soilClassification2FirstAdditionalReceivingSite") is not None : 
      _land_uses = []
      for _k, _v in submission["C3-soilClassification2FirstAdditionalReceivingSite"].items():
        if _v == True:
          _land_uses.append(_k)
      if len(_land_uses) > 0:
        _rcv_dic['receivingSiteLandUse'] = "\"" + ",".join(_land_uses) + "\""

    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule33FirstAdditionalReceivingSite") is not None : _rcv_dic['CSRFactors'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule33FirstAdditionalReceivingSite"]
    if submission.get("C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1") is not None : _rcv_dic['highVolumneSite'] = submission["C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1"]
    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule34FirstAdditionalReceivingSite") is not None : _rcv_dic['relocatedSoilUse'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule34FirstAdditionalReceivingSite"]

    if submission.get("form") is not None : 
      form_str = json.dumps(submission.get("form"))
      form_json = json.loads(form_str)
      created_at = datetime.datetime.strptime(form_json['createdAt'], DATE_TIME_FORMAT).replace(tzinfo = None, hour = 0, minute = 0, second = 0, microsecond = 0) # remove the timezone awareness
      confirmation_id = form_json['confirmationId']
      # not in attributes, but in json
      _rcv_dic['createAt'] = created_at
      if confirmation_id is not None : _rcv_dic['confirmationId'] = confirmation_id

  return _rcv_dic

def map_rcv_3rd_rcver(submission):
  _rcv_dic = {}
  testing_count2 = 0
  if (
    submission.get("C2-Latitude-Degrees3SecondAdditionalreceivingSite") is not None and
    submission.get("C2-Latitude-Minutes3SecondAdditionalreceivingSite") is not None and
    submission.get("Section2-Latitude-Seconds4SecondAdditionalreceivingSite") is not None and
    submission.get("C2-Longitude-Degrees3SecondAdditionalreceivingSite") is not None and
    submission.get("C2-Longitude-Minutes3SecondAdditionalreceivingSite") is not None and
    submission.get("C2-Longitude-Seconds3SecondAdditionalreceivingSite") is not None
  ):
    print("Mapping 3rd receiver ...")

    for rcv_header in receivingSiteHeaders:
      _rcv_dic[rcv_header] = None

    if submission.get("C1-FirstName6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerFirstName'] = submission["C1-FirstName6SecondAdditionalreceivingSite"]
    if submission.get("C1-LastName6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerLastName'] = submission["C1-LastName6SecondAdditionalreceivingSite"]
    if submission.get("C1-Company6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerCompany'] = submission["C1-Company6SecondAdditionalreceivingSite"]
    if submission.get("C1-Address6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerAddress'] = submission["C1-Address6SecondAdditionalreceivingSite"]
    if submission.get("C1-City6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerCity'] = submission["C1-City6SecondAdditionalreceivingSite"]
    if submission.get("phoneNumber7SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerPhoneNumber'] = submission["phoneNumber7SecondAdditionalreceivingSite"]
    if submission.get("C1-Email6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerEmail'] = submission["C1-Email6SecondAdditionalreceivingSite"]

    if submission.get("C1-FirstName7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2FirstName'] = submission["C1-FirstName7SecondAdditionalreceivingSite"]
    if submission.get("C1-LastName7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2LastName'] = submission["C1-LastName7SecondAdditionalreceivingSite"]
    if submission.get("C1-Company7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2Company'] = submission["C1-Company7SecondAdditionalreceivingSite"]
    if submission.get("C1-Address7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2Address'] = submission["C1-Address7SecondAdditionalreceivingSite"]
    if submission.get("C1-City7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2City'] = submission["C1-City7SecondAdditionalreceivingSite"]
    if submission.get("phoneNumber5SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2PhoneNumber'] = submission["phoneNumber5SecondAdditionalreceivingSite"]
    if submission.get("C1-Email7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2Email'] = submission["C1-Email7SecondAdditionalreceivingSite"]

    if submission.get("C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow4SecondAdditionalreceivingSite") is not None : _rcv_dic['additionalOwners'] = submission["C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow4SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-FirstName3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactFirstName'] = submission["C2-RSC-FirstName3SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-LastName3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactLastName'] = submission["C2-RSC-LastName3SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-Company3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactCompany'] = submission["C2-RSC-Company3SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-Address3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactAddress'] = submission["C2-RSC-Address3SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-City3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactCity'] = submission["C2-RSC-City3SecondAdditionalreceivingSite"]
    if submission.get("phoneNumber6SecondAdditionalreceivingSite") is not None : _rcv_dic['contactPhoneNumber'] = submission["phoneNumber6SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-Email3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactEmail'] = submission["C2-RSC-Email3SecondAdditionalreceivingSite"]
    if submission.get("C2-siteIdentificationNumberSiteIdIfAvailable3SecondAdditionalreceivingSite") is not None : _rcv_dic['SID'] = submission["C2-siteIdentificationNumberSiteIdIfAvailable3SecondAdditionalreceivingSite"]

    # convert lat/lon
    _rcv_lat_lon = convert_deciaml_lat_long(
      submission["C2-Latitude-Degrees3SecondAdditionalreceivingSite"], submission["C2-Latitude-Minutes3SecondAdditionalreceivingSite"], submission["Section2-Latitude-Seconds4SecondAdditionalreceivingSite"], 
      submission["C2-Longitude-Degrees3SecondAdditionalreceivingSite"], submission["C2-Longitude-Minutes3SecondAdditionalreceivingSite"], submission["C2-Longitude-Seconds3SecondAdditionalreceivingSite"])
    #_rcv_dic['latitude'] = _rcv_lat_lon[0]
    #_rcv_dic['longitude'] = _rcv_lat_lon[0]
    _rcv_dic['latitude'] = testRcvLats[testing_count2] #for testing
    _rcv_dic['longitude'] = testRcvLons[testing_count2] #for testing
    testing_count2 = testing_count2 + 1

    if submission.get("SecondAdditionalReceivingSiteregionalDistrict") is not None and len(submission['SecondAdditionalReceivingSiteregionalDistrict']) > 0 : 
      _rcv_dic['regionalDistrict'] = "\"" + ",".join(submission["SecondAdditionalReceivingSiteregionalDistrict"]) + "\""

    if submission.get("Secondadditionalreceiving-landOwnership-checkbox3") is not None : _rcv_dic['landOwnership'] = submission["Secondadditionalreceiving-landOwnership-checkbox3"]
    if submission.get("C2-LegallyTitled-Address3SecondAdditionalreceivingSite") is not None : _rcv_dic['legallyTitledSiteAddress'] = submission["C2-LegallyTitled-Address3SecondAdditionalreceivingSite"]
    if submission.get("C2-LegallyTitled-City3SecondAdditionalreceivingSite") is not None : _rcv_dic['legallyTitledSiteCity'] = submission["C2-LegallyTitled-City3SecondAdditionalreceivingSite"]
    if submission.get("C2-LegallyTitled-PostalZipCode3SecondAdditionalreceivingSite") is not None : _rcv_dic['legallyTitledSitePostalCode'] = submission["C2-LegallyTitled-PostalZipCode3SecondAdditionalreceivingSite"]

    if submission.get("dataGrid4") is not None and len(submission["dataGrid4"]) > 0: 
      _dg4 = submission["dataGrid4"][0] # could be more than one, but take only one
      if _dg4.get("A-LegallyTitled-PIDSecondAdditionalreceivingSite") is not None: _rcv_dic['PID'] = _dg4["A-LegallyTitled-PIDSecondAdditionalreceivingSite"]
      if _dg4.get("legalLandDescriptionSecondAdditionalreceivingSite") is not None: _rcv_dic['legalLandDescription'] = _dg4["legalLandDescriptionSecondAdditionalreceivingSite"]
    elif submission.get("dataGrid7") is not None and len(submission["dataGrid7"]) > 0: 
      _dg7 = submission["dataGrid7"][0] # could be more than one, but take only one
      if _dg7.get("A-UntitledCrownLand-PINSecondAdditionalreceivingSite") is not None: _rcv_dic['PIN'] = _dg7["A-UntitledCrownLand-PINSecondAdditionalreceivingSite"]
      if _dg7.get("UntitledCrownLandLegalLandDescriptionSecondAdditionalreceivingSite") is not None: _rcv_dic['legalLandDescription'] = _dg7["UntitledCrownLandLegalLandDescriptionSecondAdditionalreceivingSite"]
    elif submission.get("legalLandDescriptionUntitledMunicipalSecondAdditionalreceivingSite") is not None : _rcv_dic['legalLandDescription'] = submission["legalLandDescriptionUntitledMunicipalSecondAdditionalreceivingSite"]

    #if submission.get("C3-soilClassification4SecondAdditionalreceivingSite") is not None : _rcvDic['receivingSiteLandUse'] = submission["C3-soilClassification4SecondAdditionalreceivingSite"]
    if submission.get("C3-soilClassification4SecondAdditionalreceivingSite") is not None : 
      _land_uses = []
      for _k, _v in submission["C3-soilClassification4SecondAdditionalreceivingSite"].items():
        if _v == True:
          _land_uses.append(_k)
      if len(_land_uses) > 0:
        _rcv_dic['receivingSiteLandUse'] = "\""+ ",".join(_land_uses) + "\""


    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule37SecondAdditionalreceivingSite") is not None : _rcv_dic['CSRFactors'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule37SecondAdditionalreceivingSite"]
    if submission.get("C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1") is not None : _rcv_dic['highVolumneSite'] = submission["C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1"]
    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule38SecondAdditionalreceivingSite") is not None : _rcv_dic['relocatedSoilUse'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule38SecondAdditionalreceivingSite"]

    if submission.get("form") is not None : 
      form_str = json.dumps(submission.get("form"))
      form_json = json.loads(form_str)
      created_at = datetime.datetime.strptime(form_json['createdAt'], DATE_TIME_FORMAT).replace(tzinfo = None, hour = 0, minute = 0, second = 0, microsecond = 0) # remove the timezone awareness
      confirmation_id = form_json['confirmationId']
      # not in attributes, but in json
      _rcv_dic['createAt'] = created_at
      if confirmation_id is not None : _rcv_dic['confirmationId'] = confirmation_id  

  return _rcv_dic

# Receiving Sites Regional District dictionary - key:regional district string / value:receiving site data dictionary
def add_regional_district_dic(rcv_dic, rcv_reg_dist_dic):

  if 'regionalDistrict' in rcv_dic and rcv_dic['regionalDistrict'] is not None: # could be none regional district key
    _rcv_dic_copy = {}
    _rcv_dic_copy = copy.deepcopy(rcv_dic)
    _rd_str = rcv_dic['regionalDistrict'] # could be more than one
    if _rd_str is not None:
      _rd_str = _rd_str.strip('\"')
      _rds = []
      _rds = _rd_str.split(",")
      for _rd in _rds:

        _rd = 'metroVancouverRegionalDistrict' #for testing SHOULD BE REMOVED

        if _rd in rcv_reg_dist_dic:
          rcv_reg_dist_dic[_rd].append(_rcv_dic_copy)
        else:
          rcv_reg_dist_dic[_rd] = [_rcv_dic_copy]

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
#print(soilsAttributes)


sourceSiteHeaders = [
  "updateToPreviousForm",
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
  "owner2PhoneNumber",
  "owner2Email",
  "additionalOwners",
  "contactFirstName",
  "contactLastName",
  "contactCompany",
  "contactAddress",
  "contactCity",
  "contactPhoneNumber",
  "contactEmail",
  "SID",
  "latitude",
  "longitude",
  "regionalDistrict",  
  "landOwnership",
  "legallyTitledSiteAddress",
  "legallyTitledSiteCity",
  "legallyTitledSitePostalCode",
  "PID",
  "legalLandDescription",
  "PIN",
  "crownLandFileNumbers",
  "sourceSiteLandUse",
  "highVolumneSite",
  "soilRelocationPurpose",
  "soilStorageType",
  "soilVolume",
  "soilQuality",
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
  "createAt", # not in soilsAttributes, but in submissionsJson
  "confirmationId" # not in soilsAttributes, but in submissionsJson
]

receivingSiteHeaders = [
  "ownerFirstName",
  "ownerLastName",
  "ownerCompany",
  "ownerAddress",
  "ownerCity",
  "ownerPhoneNumber",
  "ownerEmail",
  "owner2FirstName",
  "owner2LastName",
  "owner2Company",
  "owner2Address",
  "owner2City",
  "owner2PhoneNumber",
  "owner2Email",
  "additionalOwners",
  "contactFirstName",
  "contactLastName",
  "contactCompany",
  "contactAddress",
  "contactCity",
  "contactPhoneNumber",
  "contactEmail",
  "SID",
  "latitude",
  "longitude",
  "regionalDistrict",
  "landOwnership",
  "legallyTitledSiteAddress",
  "legallyTitledSiteCity",
  "legallyTitledSitePostalCode",
  "PID",
  "legalLandDescription",
  "PIN",
  "receivingSiteLandUse",
  "CSRFactors",
  "relocatedSoilUse",
  "highVolumneSite",
  "createAt",
  "confirmationId"
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
  "Longitude",
  "PID",
  "PIN"
]

sourceSites = []
receivingSites = []
rcvRegDistDic = {}
testingCount2 = 0

# create source site, receiving site records
for submission in submissionsJson:
  # Mapping submission data to the source site =====================================================================
  _srcDic = map_source_site(submission)
  if _srcDic:
    sourceSites.append(_srcDic)

  # Mapping submission data to the receiving site =================================================================
  _1rcvDic = map_rcv_1st_rcver(submission)
  if _1rcvDic:
    receivingSites.append(_1rcvDic)
    add_regional_district_dic(_1rcvDic, rcvRegDistDic)

  _2rcvDic = map_rcv_2nd_rcver(submission)
  if _2rcvDic:
    receivingSites.append(_2rcvDic)
    add_regional_district_dic(_2rcvDic, rcvRegDistDic)

  _3rcvDic = map_rcv_3rd_rcver(submission)
  if _3rcvDic:
    receivingSites.append(_3rcvDic)
    add_regional_district_dic(_3rcvDic, rcvRegDistDic)  
  


hvSites = []
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
    _createdAt = datetime.datetime.strptime(formJson['createdAt'], DATE_TIME_FORMAT).replace(tzinfo = None, hour = 0, minute = 0, second = 0, microsecond = 0) # remove the timezone awareness
    confirmationId = formJson['confirmationId']
    # not in attributes, but in json
    if _createdAt is not None : hvSiteData[70] = _createdAt 
    if confirmationId is not None : hvSiteData[71] = confirmationId

  # convert to lat/lon
  _hvSiteLatLon = convert_deciaml_lat_long(hvSiteData[34], hvSiteData[35], hvSiteData[36], hvSiteData[37], hvSiteData[38], hvSiteData[39])
  #for testing
  #hvSiteData[72] = _hvSiteLatLon[0] # High Volume Site latitude
  #hvSiteData[73] = _hvSiteLatLon[1] # High Volume Site longitude
  hvSiteData[72] = testHVLats[testingCount3]
  hvSiteData[73] = testHVLons[testingCount3]
  testingCount3 = testingCount3 +1

  #PID
  if submission.get("dataGrid") is not None : 
    for dg in submission.get("dataGrid"):
      if dg["A-LegallyTitled-PID"] is not None and dg["A-LegallyTitled-PID"] != '':
        sourceSiteData[74] = dg["A-LegallyTitled-PID"]
        break
  #PIN
  if submission.get("dataGrid1") is not None : 
    for dg1 in submission.get("dataGrid1"):
      if dg1["A-LegallyTitled-PID"] is not None and dg1["A-LegallyTitled-PID"] != '':
        sourceSiteData[75] = dg1["A-LegallyTitled-PID"]
        break

  hvSites.append(hvSiteData)

  # 'hvSitesDic' dictionary - key:regionalDistrict / value:hvSiteData
  hvSiteDataCopy = copy.deepcopy(hvSiteData)
  for _srd in hvSiteData[40]: # could be more than one
    if _srd is not None: 

      #for testing
      _srd = 'metroVancouverRegionalDistrict' 

      if _srd in hvSitesDic:
        hvSitesDic[_srd].append(hvSiteDataCopy)
      else:
        hvSitesDic[_srd] = [hvSiteDataCopy]




print('Creating soil source site CSV...')
with open(SOURCE_CSV_FILE, 'w', encoding='UTF8', newline='') as f:
  writer = csv.DictWriter(f, fieldnames=sourceSiteHeaders)
  writer.writeheader()
  writer.writerows(sourceSites)

print('Creating soil receiving site CSV...')
with open(RECEIVE_CSV_FILE, 'w', encoding='UTF8', newline='') as f:
  writer = csv.DictWriter(f, fieldnames=receivingSiteHeaders)
  writer.writeheader()
  writer.writerows(receivingSites)


"""
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
if srcCsvItem is None:
  print('Error: Source Site CSV Item ID is invalid!')
else:
  srcCsvUpdateResult = srcCsvItem.update({}, SOURCE_CSV_FILE)
  print('Updated Soil Relocation Source Site CSV sucessfully: ' + str(srcCsvUpdateResult))

  print('Updating Soil Relocation Soruce Site Feature Layer...')
  srcLyrItem = gis.content.get(srcLayerId)
  if srcLyrItem is None:
    print('Error: Source Site Layter Item ID is invalid!')
  else:
    srcFlc = FeatureLayerCollection.fromitem(srcLyrItem)
    srcLyrOverwriteResult = srcFlc.manager.overwrite(SOURCE_CSV_FILE)
    print('Updated Soil Relocation Source Site Feature Layer sucessfully: ' + json.dumps(srcLyrOverwriteResult))

print('Updating Soil Relocation Receiving Site CSV...')
rcvCsvItem = gis.content.get(rcvCSVId)
if rcvCsvItem is None:
  print('Error: Receiving Site CSV Item ID is invalid!')
else:
  rcvCsvUpdateResult = rcvCsvItem.update({}, RECEIVE_CSV_FILE)
  print('Updated Soil Relocation Receiving Site CSV sucessfully: ' + str(rcvCsvUpdateResult))

  print('Updating Soil Relocation Receiving Site Feature Layer...')
  rcvLyrItem = gis.content.get(rcvLayerId)
  if rcvLyrItem is None:
    print('Error: Receiving Site Layer Item ID is invalid!')
  else:    
    rcvFlc = FeatureLayerCollection.fromitem(rcvLyrItem)
    rcvLyrOverwriteResult = rcvFlc.manager.overwrite(RECEIVE_CSV_FILE)
    print('Updated Soil Relocation Receiving Site Feature Layer sucessfully: ' + json.dumps(rcvLyrOverwriteResult))

"""
print('Updating High Volume Receiving Site CSV...')
hvCsvItem = gis.content.get(hvCSVId)
hvCsvUpdateResult = hvCsvItem.update({}, HIGH_VOLUME_CSV_FILE)
print('Updating High Volume Receiving Site Feature Layer...')
hvLyrItem = gis.content.get(hvLayerId)
hvFlc = FeatureLayerCollection.fromitem(hvLyrItem)
hvLyrOverwriteResult = hvFlc.manager.overwrite(HIGH_VOLUME_CSV_FILE)
"""



"""
print('Sending subscriber emails...')
# iterate through the submissions and send an email
# Only send emails for sites that are new (don't resend for old sites)

EMAIL_SUBJECT_SOIL_RELOCATION = 'SRIS Subscription Service - New Notification(s) Received (Soil Relocation)'
EMAIL_SUBJECT_HIGH_VOLUME = 'SRIS Subscription Service - New Registration(s) Received (High Volume Receiving Site)'

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
  subscriberRegionalDistrict = [] # could be more than one
  notifyOnHighVolumeSiteRegistrations = False
  notifyOnSoilRelocationsInSelectedDistrict = False
  unsubscribe = False

  if subscriber.get("emailAddress") is not None : subscriberEmail = subscriber["emailAddress"]
  if subscriber.get("regionalDistrict") is not None : subscriberRegionalDistrict = subscriber["regionalDistrict"] 
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

  if subscriberEmail is not None and subscriberRegionalDistrict is not None and unsubscribe == False:
    

    # Notification of soil relocation in selected Regional District(s)
    if notifyOnSoilRelocationsInSelectedDistrict == True:
      for _receivingSiteDic in receivingSites:

        if counterTesting2 == 1:
          break
        counterTesting2 = 1

        # For new/old submissions, you'll have to compare the submission create date against the current script runtime. 
        # This may require finding a way to store a "last run time" for the script, or running the script once per day, 
        # and only sending submissions for where a create-date is within the last 24 hours.
        # d1 = datetime.datetime.utcfromtimestamp(receivingSiteData[140])
        _createdAt = _receivingSiteDic['createAt']
        # print(_createdAt)
        _daysDiff = (today - _createdAt).days
        # print(_daysDiff)

        if (_daysDiff >= 1):
          for _srd in subscriberRegionalDistrict:
            # finding if subscriber's regional district in receiving site registration
            sitesInRD = rcvRegDistDic.get(_srd)
            popupLinks = create_rcv_popup_links(sitesInRD)

            #for testing the following condition line commented out, SHOULD BE UNCOMMENT OUT after testing!!!!
            #if receivingSiteData[31] == regionalDistrict: # ReceivingSiteregionalDistrict
            if sitesInRD is not None:
              regDis = convert_regional_district_to_name(_srd)
              emailMsg = create_site_relocation_email_msg(regDis, popupLinks)
              send_mail('rjeong@vividsolutions.com', EMAIL_SUBJECT_SOIL_RELOCATION, emailMsg)
    

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
            send_mail('rjeong@vividsolutions.com', EMAIL_SUBJECT_HIGH_VOLUME, hvEmailMsg)
    
"""
print('Completed Soils data publishing')