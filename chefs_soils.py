import requests
from requests.auth import HTTPBasicAuth
import json, csv, datetime, copy
import urllib.parse
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection


# CSV file names
SOURCE_CSV_FILE = 'soil_relocation_source_sites.csv'
RECEIVE_CSV_FILE = 'soil_relocation_receiving_sites.csv'
HIGH_VOLUME_CSV_FILE = 'high_volume_receiving_sites.csv'

# Soil Relocation Source Sites Item Id
SRC_CSV_ID = '4bfbda4fd22f4ab68fc548b3cfdf41cf'
SRC_CSV_ID = 'f99012760e9e4f4394e54abdbfd1f1f8'

# Soil Relocation Receiving Sites Item Id
RCV_CSV_ID = '426e40d6525747bb801c698357dea3b5'
RCV_CSV_ID = 'af9724382684495cbbc8aeeb6e20ea26'

# High Volume Receiving Sites Item Id
HV_CSV_ID = '7718b38fac0643a8b73de8cf556c5d14'
HV_LAYER_ID = 'c1e349295bf14ee9bd8df89439b2cb80'

# WEB Mapping Application Itme Id
WEB_MAP_APP_ID = '8a6afeae8fdd4960a0ea0df1fa34aa74' #should be changed

MAPHUB_URL = r'https://governmentofbc.maps.arcgis.com'

# Move these to a configuration file
CHEFS_API_URL = 'https://submit.digital.gov.bc.ca/app/api/v1'

CHEFS_SOILS_FORM_ID = 'e6083928-4bff-45b5-a447-2b9b59d61757'
CHEFS_HV_FORM_ID = '83181b39-521b-4b9f-b089-f5c794bdcc80'
CHEFS_MAIL_FORM_ID = '75a33b78-f20a-4d05-8eb6-96986604760b' #subscription

AUTH_URL = 'https://dev.oidc.gov.bc.ca' # dev
# AUTH_URL = 'https://test.oidc.gov.bc.ca' # test
# AUTH_URL	= 'https://oidc.gov.bc.ca' # prod

CHEFS_URL = 'https://ches-dev.apps.silver.devops.gov.bc.ca' # dev
# CHEFS_URL = 'https://ches-test.apps.silver.devops.gov.bc.ca' # test
# CHEFS_URL = 'https://ches.nrs.gov.bc.ca' # prod



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
    'Authorization': 'Basic ' + CHES_API_KEY
  }
  auth_response = requests.request("POST", AUTH_URL + '/auth/realms/jbd6rnxw/protocol/openid-connect/token', headers=auth_haders, data=auth_pay_load)
  # print(authResponse.text)
  auth_response_json = json.loads(auth_response.content)
  access_token = auth_response_json['access_token']

  from_email = "noreply@gov.bc.ca"
  ches_pay_load = "{\n \"bodyType\": \"html\",\n \"body\": \""+message+"\",\n \"delayTS\": 0,\n \"encoding\": \"utf-8\",\n \"from\": \""+from_email+"\",\n \"priority\": \"normal\",\n  \"subject\": \""+subject+"\",\n  \"to\": [\""+to_email+"\"]\n }\n"
  ches_headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer ' + access_token
  }
  ches_response = requests.request("POST", CHEFS_URL + '/api/v1/email', headers=ches_headers, data=ches_pay_load)
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
  request = requests.get(CHEFS_API_URL + '/forms/' + form_id + '/export?format=json&type=submissions', auth=HTTPBasicAuth(form_id, form_key), headers={'Content-type': 'application/json'})
  # print('Parsing JSON response')
  content = json.loads(request.content)
  return content

def fetch_columns(form_id, form_key):
  request = requests.get(CHEFS_API_URL + '/forms/' + form_id + '/versions', auth=HTTPBasicAuth(form_id, form_key), headers={'Content-type': 'application/json'})
  request_json = json.loads(request.content)
  version = request_json[0]['id']

  attribute_request = requests.get(CHEFS_API_URL + '/forms/' + form_id + '/versions/' + version + '/fields', auth=HTTPBasicAuth(form_id, form_key), headers={'Content-type': 'application/json'})
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
  msg += '<span style=font-style:italic;color:#4da6ff;>You are receiving this email because you subscribed to receive email notifications of soil relocation or high-volume site registrations in select Regional Districts in BC.  If you wish to stop receiving these email notifications, please select &#8216;unsubscribe&#8217; on the subscription <a href=https://chefs.nrs.gov.bc.ca/app/form/submit?f=' + CHEFS_MAIL_FORM_ID + '>form</a></span>.<br/>'
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
  msg += '<span style=font-style:italic;color:#4da6ff;>You are receiving this email because you subscribed to receive email notifications of soil relocation or high-volume site registrations in select Regional Districts in BC. If you wish to stop receiving these email notifications, please select &#8216;unsubscribe&#8217; on the subscription <a href=https://chefs.nrs.gov.bc.ca/app/form/submit?f=' + CHEFS_MAIL_FORM_ID + '>form</a></span>.<br/>'
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
  _links = ''  
  link_prx = '<a href=https://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=' + WEB_MAP_APP_ID + '&find='
  link_suf = '>Link to new submission</a><br/>'

  if rcv_sites is not None:
    for _rcv_site_dic in rcv_sites:
      _links += link_prx

      if _rcv_site_dic['SID'] is not None and _rcv_site_dic['SID'].strip() != '':
        _links += urllib.parse.quote(_rcv_site_dic['SID']) #Site ID
      elif _rcv_site_dic['PID'] is not None and _rcv_site_dic['PID'].strip() != '':
        _links += urllib.parse.quote(_rcv_site_dic['PID']) #PID
      elif _rcv_site_dic['PIN'] is not None and _rcv_site_dic['PIN'].strip() != '':
        _links += urllib.parse.quote(_rcv_site_dic['PIN']) #PIN
      elif _rcv_site_dic['latitude'] is not None and _rcv_site_dic['latitude'].strip() != '' and _rcv_site_dic['longitude'] is not None and _rcv_site_dic['longitude'].strip() != '':
        _links += urllib.parse.quote(_rcv_site_dic['latitude']+','+_rcv_site_dic['latitude']) #Receiving Site lat/lon
      elif _rcv_site_dic['ownerAddress'] is not None and _rcv_site_dic['ownerAddress'].strip() != '':
        _links += urllib.parse.quote(_rcv_site_dic['ownerAddress']) #Receiving Site Owner Address
      elif _rcv_site_dic['ownerCompany'] is not None and _rcv_site_dic['ownerCompany'].strip() != '':
        _links += urllib.parse.quote(_rcv_site_dic['ownerCompany'])  #Receiving Site Owner Company

      _links += link_suf
  return _links

# high volume soil receiving sites
def create_hv_popup_links(hv_sites):
  _links = ''  
  link_prx = '<a href=https://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=' + WEB_MAP_APP_ID + '&find='
  link_suf = '>Link to new high volume receiving site registration</a><br/>'

  if hv_sites is not None:
    for _hv_site_dic in hv_sites:
      _links += link_prx

      if _hv_site_dic['SID'] is not None and _hv_site_dic['SID'].strip() != '':
        _links += urllib.parse.quote(_hv_site_dic['SID']) #Site ID
      elif _hv_site_dic['PID'] is not None and _hv_site_dic['PID'].strip() != '':
        _links += urllib.parse.quote(_hv_site_dic['PID']) #PID
      elif _hv_site_dic['PIN'] is not None and _hv_site_dic['PIN'].strip() != '':
        _links += urllib.parse.quote(_hv_site_dic['PIN']) #PIN
      elif _hv_site_dic['latitude'] is not None and _hv_site_dic['latitude'].strip() != '' and _hv_site_dic['longitude'] is not None and _hv_site_dic['longitude'].strip() != '':
        _links += urllib.parse.quote(_hv_site_dic['latitude']+','+_hv_site_dic['longitude']) #Receiving Site lat/lon
      elif _hv_site_dic['ownerAddress'] is not None and _hv_site_dic['ownerAddress'].strip() != '':
        _links += urllib.parse.quote(_hv_site_dic['ownerAddress']) #Receiving Site Owner Address
      elif _hv_site_dic['ownerCompany'] is not None and _hv_site_dic['ownerCompany'].strip() != '':
        _links += urllib.parse.quote(_hv_site_dic['ownerCompany'])  #Receiving Site Owner Company

      _links += link_suf
  return _links

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

    if submission.get("isTheSourceSiteHighRisk") is not None : _src_dic['highVolumeSite'] = submission["isTheSourceSiteHighRisk"]
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
    if submission.get("C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime") is not None : _rcv_dic['highVolumeSite'] = submission["C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime"]
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
    if submission.get("C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1") is not None : _rcv_dic['highVolumeSite'] = submission["C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1"]
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
    if submission.get("C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1") is not None : _rcv_dic['highVolumeSite'] = submission["C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1"]
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

def map_hv_site(hvs):
  _hv_dic = {}
  testingCount3 = 0

  if (
    hvs.get("Section3-Latitude-Degrees") is not None and
    hvs.get("Section3-Latitude-Minutes") is not None and
    hvs.get("Section3-Latitude-Seconds") is not None and
    hvs.get("Section3-Longitude-Degrees") is not None and
    hvs.get("Section3-Longitude-Minutes") is not None and
    hvs.get("Section3-Longitude-Seconds") is not None
  ):
    print("Mapping sourece site ...")

    for hv_header in hvSiteHeaders:
      _hv_dic[hv_header] = None

    if hvs.get("Section1-FirstNameReceivingSiteOwner") is not None : _hv_dic['ownerFirstName'] = hvs["Section1-FirstNameReceivingSiteOwner"]
    if hvs.get("Section1-LastNameReceivingSiteOwner") is not None : _hv_dic['ownerLastName'] = hvs["Section1-LastNameReceivingSiteOwner"]
    if hvs.get("Section1-CompanyReceivingSiteOwner") is not None : _hv_dic['ownerCompany'] = hvs["Section1-CompanyReceivingSiteOwner"]
    if hvs.get("Section1-AddressReceivingSiteOwner") is not None : _hv_dic['ownerAddress'] = hvs["Section1-AddressReceivingSiteOwner"]
    if hvs.get("Section1-CityReceivingSiteOwner") is not None : _hv_dic['ownerCity'] = hvs["Section1-CityReceivingSiteOwner"]
    if hvs.get("Section1-provinceStateReceivingSiteOwner") is not None : _hv_dic['ownerProvince'] = hvs["Section1-provinceStateReceivingSiteOwner"]
    if hvs.get("Section1-countryReceivingSiteOwner") is not None : _hv_dic['ownerCountry'] = hvs["Section1-countryReceivingSiteOwner"]
    if hvs.get("Section1-postalZipCodeReceivingSiteOwner") is not None : _hv_dic['ownerPostalCode'] = hvs["Section1-postalZipCodeReceivingSiteOwner"]
    if hvs.get("ASection1-PhoneReceivingSiteOwner") is not None : _hv_dic['ownerPhoneNumber'] = hvs["Section1-PhoneReceivingSiteOwner"]
    if hvs.get("Section1-EmailReceivingSiteOwner") is not None : _hv_dic['ownerEmail'] = hvs["Section1-EmailReceivingSiteOwner"]

    if hvs.get("Section1a-FirstNameAdditionalOwner") is not None : _hv_dic['owner2FirstName'] = hvs["Section1a-FirstNameAdditionalOwner"]
    if hvs.get("Section1A-LastNameAdditionalOwner") is not None : _hv_dic['owner2LastName'] = hvs["Section1A-LastNameAdditionalOwner"]
    if hvs.get("Section1A-CompanyAdditionalOwner") is not None : _hv_dic['owner2Company'] = hvs["Section1A-CompanyAdditionalOwner"]
    if hvs.get("Section1A-AddressAdditionalOwner") is not None : _hv_dic['owner2Address'] = hvs["Section1A-AddressAdditionalOwner"]
    if hvs.get("Section1A-CityAdditionalOwner") is not None : _hv_dic['owner2City'] = hvs["Section1A-CityAdditionalOwner"]
    if hvs.get("Section1A-ProvinceStateAdditionalOwner") is not None : _hv_dic['owner2Province'] = hvs["Section1A-ProvinceStateAdditionalOwner"]
    if hvs.get("Section1A-CountryAdditionalOwner") is not None : _hv_dic['owner2Country'] = hvs["Section1A-CountryAdditionalOwner"]
    if hvs.get("Section1A-PostalZipCodeAdditionalOwner") is not None : _hv_dic['owner2PostalCode'] = hvs["Section1A-PostalZipCodeAdditionalOwner"]
    if hvs.get("Section1A-PhoneAdditionalOwner") is not None : _hv_dic['owner2PhoneNumber'] = hvs["Section1A-PhoneAdditionalOwner"]
    if hvs.get("Section1A-EmailAdditionalOwner") is not None : _hv_dic['owner2Email'] = hvs["Section1A-EmailAdditionalOwner"]

    if hvs.get("areThereMoreThanTwoOwnersIncludeTheirInformationBelow") is not None : _hv_dic['additionalOwners'] = hvs["areThereMoreThanTwoOwnersIncludeTheirInformationBelow"]
    if hvs.get("Section2-firstNameRSC") is not None : _hv_dic['contactFirstName'] = hvs["Section2-firstNameRSC"]
    if hvs.get("Section2-lastNameRSC") is not None : _hv_dic['contactLastName'] = hvs["Section2-lastNameRSC"]
    if hvs.get("Section2-organizationRSC") is not None : _hv_dic['contactCompany'] = hvs["Section2-organizationRSC"]
    if hvs.get("Section2-streetAddressRSC") is not None : _hv_dic['contactAddress'] = hvs["Section2-streetAddressRSC"]
    if hvs.get("Section2-cityRSC") is not None : _hv_dic['contactCity'] = hvs["Section2-cityRSC"]
    if hvs.get("Section2-provinceStateRSC") is not None : _hv_dic['contactProvince'] = hvs["Section2-provinceStateRSC"]
    if hvs.get("Section2-countryRSC") is not None : _hv_dic['contactCountry'] = hvs["Section2-countryRSC"]
    if hvs.get("Section2-postalZipCodeRSC") is not None : _hv_dic['contactPostalCode'] = hvs["Section2-postalZipCodeRSC"]
    if hvs.get("section2phoneNumberRSC") is not None : _hv_dic['contactPhoneNumber'] = hvs["section2phoneNumberRSC"]
    if hvs.get("Section2-simpleemailRSC") is not None : _hv_dic['contactEmail'] = hvs["Section2-simpleemailRSC"]

    if hvs.get("Section3-siteIdIncludeAllRelatedNumbers") is not None : _hv_dic['SID'] = hvs["Section3-siteIdIncludeAllRelatedNumbers"]

    # convert lat/lon
    _hv_lat_lon = convert_deciaml_lat_long(
      hvs["Section3-Latitude-Degrees"], hvs["Section3-Latitude-Minutes"], hvs["Section3-Latitude-Seconds"], 
      hvs["Section3-Longitude-Degrees"], hvs["Section3-Longitude-Minutes"], hvs["Section3-Longitude-Seconds"])
    #_hv_dic['latitude'] = _hv_lat_lon[0]
    #_hv_dic['longitude'] = _hv_lat_lon[0]
    _hv_dic['latitude'] = testHVLats[testingCount3] #for testing
    _hv_dic['longitude'] = testHVLons[testingCount3] #for testing
    testingCount3 = testingCount3 + 1

    if hvs.get("ReceivingSiteregionalDistrict") is not None and len(hvs['ReceivingSiteregionalDistrict']) > 0 : 
      _hv_dic['regionalDistrict'] = "\"" + ",".join(hvs["ReceivingSiteregionalDistrict"]) + "\""   # could be more than one

    if hvs.get("landOwnership-checkbox") is not None : _hv_dic['landOwnership'] = hvs["landOwnership-checkbox"]
    if hvs.get("Section3-LegallyTitled-Address") is not None : _hv_dic['legallyTitledSiteAddress'] = hvs["Section3-LegallyTitled-Address"]
    if hvs.get("Section3-LegallyTitled-City") is not None : _hv_dic['legallyTitledSiteCity'] = hvs["Section3-LegallyTitled-City"]
    if hvs.get("Section3-LegallyTitled-PostalZipCode") is not None : _hv_dic['legallyTitledSitePostalCode'] = hvs["Section3-LegallyTitled-PostalZipCode"]

    if hvs.get("dataGrid") is not None and len(hvs["dataGrid"]) > 0: 
      _dg = hvs["dataGrid"][0] # could be more than one, but take only one
      if _dg.get("A-LegallyTitled-PID") is not None: _hv_dic['PID'] = _dg["A-LegallyTitled-PID"]
      if _dg.get("legalLandDescription") is not None: _hv_dic['legalLandDescription'] = _dg["legalLandDescription"]
    elif hvs.get("dataGrid1") is not None and len(hvs["dataGrid1"]) > 0: 
      _dg1 = hvs["dataGrid1"][0] # could be more than one, but take only one
      if _dg1.get("A-LegallyTitled-PID") is not None: _hv_dic['PIN'] = _dg1["A-LegallyTitled-PID"]
      if _dg1.get("legalLandDescription") is not None: _hv_dic['legalLandDescription'] = _dg1["legalLandDescription"]
    elif hvs.get("legalLandDescription") is not None : _hv_dic['legalLandDescription'] = hvs["legalLandDescription"]

    if hvs.get("A-UntitledCrownLand-FileNumberColumn") is not None : 
      for _item in hvs["A-UntitledCrownLand-FileNumberColumn"]:
        for _v in _item.values():
          if _v != '':
            _hv_dic['crownLandFileNumbers'] = _v
            break    #could be more than one, but take only one
        if 'crownLandFileNumbers' in _hv_dic:
          break

    if hvs.get("primarylanduse") is not None and len(hvs.get("primarylanduse")) > 0 : 
      _hv_dic['receivingSiteLandUse'] = "\"" + ",".join(hvs.get("primarylanduse")) + "\""

    if hvs.get("highVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime") is not None : _hv_dic['hvsConfirmation'] = hvs["highVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime"]
    if hvs.get("dateSiteBecameHighVolume") is not None : _hv_dic['dateSiteBecameHighVolume'] = hvs["dateSiteBecameHighVolume"]
    if hvs.get("howrelocatedsoilwillbeused") is not None : _hv_dic['howRelocatedSoilWillBeUsed'] = hvs["howrelocatedsoilwillbeused"]
    if hvs.get("soilDepositIsInTheAgriculturalLandReserveAlr1") is not None : _hv_dic['soilDepositIsALR'] = hvs["soilDepositIsInTheAgriculturalLandReserveAlr1"]
    if hvs.get("receivingSiteIsOnReserveLands1") is not None : _hv_dic['soilDepositIsReserveLands'] = hvs["receivingSiteIsOnReserveLands1"]
    if hvs.get("Section5-FirstNameQualifiedProfessional") is not None : _hv_dic['qualifiedProfessionalFirstName'] = hvs["Section5-FirstNameQualifiedProfessional"]
    if hvs.get("Section5-LastName1QualifiedProfessional") is not None : _hv_dic['qualifiedProfessionalLastName'] = hvs["Section5-LastName1QualifiedProfessional"]
    if hvs.get("Section5-TypeofQP") is not None : _hv_dic['qualifiedProfessionalType'] = hvs["Section5-TypeofQP"]
    if hvs.get("Section5-organizationQualifiedProfessional") is not None : _hv_dic['qualifiedProfessionalOrganization'] = hvs["Section5-organizationQualifiedProfessional"]
    if hvs.get("Section5-professionalLicenseRegistrationEGPEngRpBio") is not None : _hv_dic['professionalLicenceRegistration'] = hvs["Section5-professionalLicenseRegistrationEGPEngRpBio"]
    if hvs.get("Section5-streetAddressQualifiedProfessional") is not None : _hv_dic['qualifiedProfessionalAddress'] = hvs["Section5-streetAddressQualifiedProfessional"]
    if hvs.get("Section5-cityQualifiedProfessional") is not None : _hv_dic['qualifiedProfessionalCity'] = hvs["Section5-cityQualifiedProfessional"]
    if hvs.get("Section5-provinceStateQualifiedProfessional") is not None : _hv_dic['qualifiedProfessionalProvince'] = hvs["Section5-provinceStateQualifiedProfessional"]
    if hvs.get("Section5-countryQualifiedProfessional") is not None : _hv_dic['qualifiedProfessionalCountry'] = hvs["Section5-countryQualifiedProfessional"]
    if hvs.get("Section5-postalZipCodeQualifiedProfessional") is not None : _hv_dic['qualifiedProfessionalPostalCode'] = hvs["Section5-postalZipCodeQualifiedProfessional"]
    if hvs.get("simplephonenumber1QualifiedProfessional") is not None : _hv_dic['qualifiedProfessionalPhoneNumber'] = hvs["simplephonenumber1QualifiedProfessional"]
    if hvs.get("simpleemail1QualifiedProfessional") is not None : _hv_dic['qualifiedProfessionalEmail'] = hvs["simpleemail1QualifiedProfessional"]
    if hvs.get("firstAndLastNameQualifiedProfessional") is not None : _hv_dic['signaturerFirstAndLastName'] = hvs["firstAndLastNameQualifiedProfessional"]
    if hvs.get("simpledatetime") is not None : _hv_dic['dateSigned'] = hvs["simpledatetime"]

    if hvs.get("form") is not None : 
      _form_str = json.dumps(submission.get("form"))
      _form_json = json.loads(_form_str)
      _created_at = datetime.datetime.strptime(_form_json['createdAt'], DATE_TIME_FORMAT).replace(tzinfo = None, hour = 0, minute = 0, second = 0, microsecond = 0) # remove the timezone awareness
      _confirmation_id = _form_json['confirmationId']
      # not in attributes, but in json
      _hv_dic['createAt'] = _created_at
      if _confirmation_id is not None : _hv_dic['confirmationId'] = _confirmation_id

  return _hv_dic

# add Regional Districts in site forms to dictionary - key:regional district string / value:site data dictionary
def add_regional_district_dic(site_dic, reg_dist_dic):

  if 'regionalDistrict' in site_dic and site_dic['regionalDistrict'] is not None: # could be none regional district key
    _dic_copy = {}
    _dic_copy = copy.deepcopy(site_dic)
    _rd_str = site_dic['regionalDistrict'] # could be more than one
    if _rd_str is not None:
      _rd_str = _rd_str.strip('\"')
      _rds = []
      _rds = _rd_str.split(",")
      for _rd in _rds:

        _rd = 'metroVancouverRegionalDistrict' #for testing SHOULD BE REMOVED

        if _rd in reg_dist_dic:
          reg_dist_dic[_rd].append(_dic_copy)
        else:
          reg_dist_dic[_rd] = [_dic_copy]

# Fetch subscribers list
print('Loading submission subscribers list...')
subscribersJson = site_list(CHEFS_MAIL_FORM_ID, CHEFS_MAIL_API_KEY)
# print(subscribersJson)
print('Loading submission subscribers attributes and headers...')
subscribeAttributes = fetch_columns(CHEFS_MAIL_FORM_ID, CHEFS_MAIL_API_KEY)
# print(subscribeAttributes)

print('Loading High Volume Sites list...')
hvsJson = site_list(CHEFS_HV_FORM_ID, CHEFS_HV_API_KEY)
# print(hvsJson)
print('Loading High Volume Sites attributes and headers...')
hvsAttributes = fetch_columns(CHEFS_HV_FORM_ID, CHEFS_HV_API_KEY)
# print(hvsAttributes)

# Fetch all submissions from chefs API
print('Loading Submissions List...')
submissionsJson = site_list(CHEFS_SOILS_FORM_ID, CHEFS_SOILS_API_KEY)
#print(submissionsJson)
print('Loading Submission attributes and headers...')
soilsAttributes = fetch_columns(CHEFS_SOILS_FORM_ID, CHEFS_SOILS_API_KEY)
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
  "highVolumeSite",
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
  "createAt",
  "confirmationId"
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
  "highVolumeSite",
  "createAt",
  "confirmationId"
]  

hvSiteHeaders = [
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
  "confirmationId"
]


print('Creating source site, receiving site records...')
sourceSites = []
receivingSites = []
rcvRegDistDic = {}
for submission in submissionsJson:
  print('Mapping submission data to the source site...')
  _srcDic = map_source_site(submission)
  if _srcDic:
    sourceSites.append(_srcDic)

  print('Mapping submission data to the receiving site...')  
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


print('Creating high volume site records records...')
hvSites = []
hvRegDistDic = {}
for hvs in hvsJson:
  print('Mapping hv data to the hv site...')  

  _hvDic = map_hv_site(hvs)
  if _hvDic:
    hvSites.append(_hvDic)
    add_regional_district_dic(_hvDic, hvRegDistDic)  


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

print('Creating soil high volume site CSV...')
with open(HIGH_VOLUME_CSV_FILE, 'w', encoding='UTF8', newline='') as f:
  writer = csv.DictWriter(f, fieldnames=hvSiteHeaders)
  writer.writeheader()
  writer.writerows(hvSites)


print('Connecting to AGOL GIS...')
# connect to GIS
_gis = GIS(MAPHUB_URL, username=MAPHUB_USER, password=MAPHUB_PASS)

print('Updating Soil Relocation Soruce Site CSV...')
_srcCsvItem = _gis.content.get(SRC_CSV_ID)
if _srcCsvItem is None:
  print('Error: Source Site CSV Item ID is invalid!')
else:
  _srcCsvUpdateResult = _srcCsvItem.update({}, SOURCE_CSV_FILE)
  print('Updated Soil Relocation Source Site CSV sucessfully: ' + str(_srcCsvUpdateResult))

  print('Updating Soil Relocation Soruce Site Feature Layer...')
  _srcLyrItem = _gis.content.get(SRC_CSV_ID)
  if _srcLyrItem is None:
    print('Error: Source Site Layter Item ID is invalid!')
  else:
    _srcFlc = FeatureLayerCollection.fromitem(_srcLyrItem)
    _srcLyrOverwriteResult = _srcFlc.manager.overwrite(SOURCE_CSV_FILE)
    print('Updated Soil Relocation Source Site Feature Layer sucessfully: ' + json.dumps(_srcLyrOverwriteResult))

print('Updating Soil Relocation Receiving Site CSV...')
_rcvCsvItem = _gis.content.get(RCV_CSV_ID)
if _rcvCsvItem is None:
  print('Error: Receiving Site CSV Item ID is invalid!')
else:
  _rcvCsvUpdateResult = _rcvCsvItem.update({}, RECEIVE_CSV_FILE)
  print('Updated Soil Relocation Receiving Site CSV sucessfully: ' + str(_rcvCsvUpdateResult))

  print('Updating Soil Relocation Receiving Site Feature Layer...')
  _rcvLyrItem = _gis.content.get(RCV_CSV_ID)
  if _rcvLyrItem is None:
    print('Error: Receiving Site Layer Item ID is invalid!')
  else:    
    _rcvFlc = FeatureLayerCollection.fromitem(_rcvLyrItem)
    _rcvLyrOverwriteResult = _rcvFlc.manager.overwrite(RECEIVE_CSV_FILE)
    print('Updated Soil Relocation Receiving Site Feature Layer sucessfully: ' + json.dumps(_rcvLyrOverwriteResult))


print('Updating High Volume Receiving Site CSV...')
_hvCsvItem = _gis.content.get(HV_CSV_ID)
if _hvCsvItem is None:
  print('Error: High Volume Receiving Site CSV Item ID is invalid!')
else:
  _hvCsvUpdateResult = _hvCsvItem.update({}, HIGH_VOLUME_CSV_FILE)
  print('Updated High Volume Receiving Site CSV sucessfully: ' + str(_hvCsvUpdateResult))

  print('Updating High Volume Receiving Site Feature Layer...')
  _hvLyrItem = _gis.content.get(HV_LAYER_ID)
  if _hvLyrItem is None:
    print('Error: High Volume Receiving Site Layer Item ID is invalid!')
  else:      
    _hvFlc = FeatureLayerCollection.fromitem(_hvLyrItem)
    _hvLyrOverwriteResult = _hvFlc.manager.overwrite(HIGH_VOLUME_CSV_FILE)
    print('Updated High Volume Receiving Site Feature Layer sucessfully: ' + json.dumps(_hvLyrOverwriteResult))




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

    # Notification of soil relocation in selected Regional District(s)  =========================================================
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
            _rcvSitesInRD = rcvRegDistDic.get(_srd)
            _rcvPopupLinks = create_rcv_popup_links(_rcvSitesInRD)

            #for testing the following condition line commented out, SHOULD BE UNCOMMENT OUT after testing!!!!
            #if receivingSiteData[31] == regionalDistrict: # ReceivingSiteregionalDistrict
            if _rcvSitesInRD is not None:
              _regDis = convert_regional_district_to_name(_srd)
              _emailMsg = create_site_relocation_email_msg(_regDis, _rcvPopupLinks)
              send_mail('rjeong@vividsolutions.com', EMAIL_SUBJECT_SOIL_RELOCATION, _emailMsg)
              

    # Notification of high volume site registration in selected Regional District(s) =========================================================        
    if notifyOnHighVolumeSiteRegistrations == True:
      for _hvSiteDic in hvSites:

        if counterTesting2 == 1:
          break
        counterTesting2 = 1

        _createdAt = _hvSiteDic['createAt'] 
        # print(createdAt)
        _daysDiff = (today - _createdAt).days
        # print(daysDiff)

        if (_daysDiff >= 1):
          for _srd in subscriberRegionalDistrict:
            # finding if subscriber's regional district in high volume receiving site registration
            _hvSitesInRD = hvRegDistDic.get(_srd)
            _hvPopupLinks = create_hv_popup_links(_hvSitesInRD)

            if _hvSitesInRD is not None:
              _hvRegDis = convert_regional_district_to_name(_srd)
              _hvEmailMsg = create_hv_site_email_msg(_hvRegDis, _hvPopupLinks)
              send_mail('rjeong@vividsolutions.com', EMAIL_SUBJECT_HIGH_VOLUME, _hvEmailMsg)
    

print('Completed Soils data publishing')