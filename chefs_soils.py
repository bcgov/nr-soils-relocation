import json, csv, copy, os
import urllib.parse
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
import helper
import datetime
import pytz
from pytz import timezone
import constant

#### to track the version of forms (Sept/26/2022)
# CHEFS generates new vresion of forms when changes of data fields, manages data by each version
# 1.soil relocation form version: v9
# 2.high volume submission version v7
# 3.subscriber form version: v9

config = helper.read_config()
MAPHUB_URL = config['AGOL']['MAPHUB_URL']
WEBMAP_POPUP_URL = config['AGOL']['WEBMAP_POPUP_URL']
SRC_CSV_ID = config['AGOL_ITEMS']['SRC_CSV_ID']
SRC_LAYER_ID = config['AGOL_ITEMS']['SRC_LAYER_ID']
RCV_CSV_ID = config['AGOL_ITEMS']['RCV_CSV_ID']
RCV_LAYER_ID = config['AGOL_ITEMS']['RCV_LAYER_ID']
HV_CSV_ID = config['AGOL_ITEMS']['HV_CSV_ID']
HV_LAYER_ID = config['AGOL_ITEMS']['HV_LAYER_ID']
WEB_MAP_APP_ID = config['AGOL_ITEMS']['WEB_MAP_APP_ID']

def convert_regional_district_to_name(key):
  name = constant.REGIONAL_DISTRICT_NAME_DIC.get(key)
  if name is not None:
    return name
  else:
    return key

def convert_source_site_use_to_name(key):
  name = constant.SOURCE_SITE_USE_NAME_DIC.get(key)
  if name is not None:
    return name
  else:
    return key

def convert_receiving_site_use_to_name(key):
  name = constant.RECEIVING_SITE_USE_NAME_DIC.get(key)
  if name is not None:
    return name
  else:
    return key

def convert_soil_quality_to_name(key):
  name = constant.SOIL_QUALITY_NAME_DIC.get(key)
  if name is not None:
    return name
  else:
    return key

def convert_land_ownership_to_name(key):
  name = constant.LAND_OWNERSHIP_NAME_DIC.get(key)
  if name is not None:
    return name
  else:
    return key

def create_popup_link_body(_site_dic):
  _link_body = ''

  if _site_dic['SID'] is not None and _site_dic['SID'].strip() != '':
    _link_body = urllib.parse.quote(_site_dic['SID']) #Site ID
  elif _site_dic['PID'] is not None and _site_dic['PID'].strip() != '':
    _link_body = urllib.parse.quote(_site_dic['PID']) #PID
  elif _site_dic['PIN'] is not None and _site_dic['PIN'].strip() != '':
    _link_body = urllib.parse.quote(_site_dic['PIN']) #PIN
  elif _site_dic['latitude'] is not None and _site_dic['longitude'] is not None:
    _link_body = urllib.parse.quote(str(_site_dic['latitude'])+','+str(_site_dic['latitude'])) #Site lat/lon
  elif _site_dic['ownerAddress'] is not None and _site_dic['ownerAddress'].strip() != '':
    _link_body = urllib.parse.quote(_site_dic['ownerAddress']) #Site Owner Address
  elif _site_dic['ownerCompany'] is not None and _site_dic['ownerCompany'].strip() != '':
    _link_body = urllib.parse.quote(_site_dic['ownerCompany'])  #Site Owner Company  

  return _link_body

def create_popup_links(sites, site_type):
  _popup_links = '' 

  if sites is not None:
    for _site_dic in sites:
      _link_body = create_popup_link_body(_site_dic)

      # create popup link
      if _link_body != '' and (site_type  == 'SR' or site_type  == 'HV'): #SR: for Soil Relocation Notication, HV: High Volume Receiving Notification
        _link = '<a href=' + WEBMAP_POPUP_URL + '?id=' + WEB_MAP_APP_ID + '&find=' 
        _link += _link_body
        if site_type  == 'SR':
          _link += '>Link to new submission</a><br/>'
        elif site_type  == 'HV':
          _link += '>Link to new high volume receiving site registration</a><br/>'

      _popup_links += _link
  return _popup_links

def create_land_file_numbers(chefs_dic, field):
  _land_file_numbers = []
  if chefs_dic.get(field) is not None : 
    for _item in chefs_dic[field]:
      for _v in _item.values():
        if _v != '':
          _land_file_numbers.append(_v)

  if len(_land_file_numbers) > 0: 
    _land_file_numbers = "\"" + ",".join(_land_file_numbers) + "\""   # could be more than one    

  return _land_file_numbers if len(_land_file_numbers) > 0 else None

def create_receiving_site_lan_uses(chefs_dic, field):
  _land_uses = []
  for _k, _v in chefs_dic[field].items():
    if helper.is_not_none_true(_v):
      _land_uses.append(convert_receiving_site_use_to_name(_k))
  if len(_land_uses) > 0:
    _land_uses = "\"" + ",".join(_land_uses) + "\""
  return _land_uses

def create_regional_district(chefs_dic, field):
  _regional_district = None
  if chefs_dic.get(field) is not None and len(chefs_dic[field]) > 0: 
    _regional_district = convert_regional_district_to_name(chefs_dic[field][0])
  return _regional_district

def create_land_ownership(chefs_dic, field):
  _land_ownership = None
  if chefs_dic.get(field) is not None : 
    _land_ownership = convert_land_ownership_to_name(chefs_dic[field])
  return _land_ownership

def create_soil_volumes(chefs_dic, data_grid, volume_field, claz_field, working_dic):
  _total_soil_volume = 0
  _soil_volume = 0
  if chefs_dic.get(data_grid) is not None and len(chefs_dic[data_grid]) > 0: 
    for _dg9 in chefs_dic[data_grid]:
      if (_dg9.get(volume_field) is not None 
          and _dg9.get(claz_field) is not None and len(_dg9.get(claz_field)) > 0): 
        _soil_volume = _dg9[volume_field]
        if not helper.isfloat(_soil_volume):
          _soil_volume = helper.extract_floating_from_string(_soil_volume)
        _soil_volume = helper.str_to_double(_soil_volume)
        _soil_claz = _dg9.get("B1-soilClassificationSource")
        if helper.is_not_none_true(_soil_claz.get("urbanParkLandUsePl")):
          working_dic['urbanParkLandUseSoilVolume'] = working_dic['urbanParkLandUseSoilVolume'] + _soil_volume if working_dic['urbanParkLandUseSoilVolume'] is not None else _soil_volume
          _total_soil_volume += _soil_volume
        elif helper.is_not_none_true(_soil_claz.get("commercialLandUseCl")):
          working_dic['commercialLandUseSoilVolume'] = working_dic['commercialLandUseSoilVolume'] + _soil_volume if working_dic['commercialLandUseSoilVolume'] is not None else _soil_volume
          _total_soil_volume += _soil_volume            
        elif helper.is_not_none_true(_soil_claz.get("industrialLandUseIl")):
          working_dic['industrialLandUseSoilVolume'] = working_dic['industrialLandUseSoilVolume'] + _soil_volume if working_dic['industrialLandUseSoilVolume'] is not None else _soil_volume
          _total_soil_volume += _soil_volume            
        elif helper.is_not_none_true(_soil_claz.get("agriculturalLandUseAl")):
          working_dic['agriculturalLandUseSoilVolume'] = working_dic['agriculturalLandUseSoilVolume'] + _soil_volume if working_dic['agriculturalLandUseSoilVolume'] is not None else _soil_volume
          _total_soil_volume += _soil_volume            
        elif helper.is_not_none_true(_soil_claz.get("wildlandsNaturalLandUseWln")):
          working_dic['wildlandsNaturalLandUseSoilVolume'] = working_dic['wildlandsNaturalLandUseSoilVolume'] + _soil_volume if working_dic['wildlandsNaturalLandUseSoilVolume'] is not None else _soil_volume
          _total_soil_volume += _soil_volume            
        elif helper.is_not_none_true(_soil_claz.get("wildlandsRevertedLandUseWlr")):
          working_dic['wildlandsRevertedLandUseSoilVolume'] = working_dic['wildlandsRevertedLandUseSoilVolume'] + _soil_volume if working_dic['wildlandsRevertedLandUseSoilVolume'] is not None else _soil_volume
          _total_soil_volume += _soil_volume
        elif helper.is_not_none_true(_soil_claz.get("residentialLandUseLowDensityRlld")):
          working_dic['residentialLandUseLowDensitySoilVolume'] = working_dic['residentialLandUseLowDensitySoilVolume'] + _soil_volume if working_dic['residentialLandUseLowDensitySoilVolume'] is not None else _soil_volume
          _total_soil_volume += _soil_volume
        elif helper.is_not_none_true(_soil_claz.get("residentialLandUseHighDensityRlhd")):
          working_dic['residentialLandUseHighDensitySoilVolume'] = working_dic['residentialLandUseHighDensitySoilVolume'] + _soil_volume if working_dic['residentialLandUseHighDensitySoilVolume'] is not None else _soil_volume
          _total_soil_volume += _soil_volume
    if _total_soil_volume != 0:
      working_dic['totalSoilVolme'] = _total_soil_volume

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
  msg = '<p>High Volume Receiving Site Registrations are received by the ministry under section 55.1 of the <i>Environmental Management Act</i>. For more information on soil relocation from commercial and industrial sites in BC, please visit our <a href=https://soil-relocation-information-system-governmentofbc.hub.arcgis.com/>webpage</a>.</p>'
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

def create_pid_pin_and_desc(chefs_dic, data_grid_field, pid_pin_field, desc_field):
  _pid = None
  _desc = None
  if chefs_dic.get(data_grid_field) is not None and len(chefs_dic[data_grid_field]) > 0: 
    if chefs_dic.get(data_grid_field)[0].get(pid_pin_field) is not None and chefs_dic.get(data_grid_field)[0].get(pid_pin_field).strip() != '':
      _pid = chefs_dic.get(data_grid_field)[0].get(pid_pin_field)
      if _pid is not None and chefs_dic.get(data_grid_field)[0].get(desc_field) and chefs_dic.get(data_grid_field)[0].get(desc_field).strip() != '':
        _desc = chefs_dic.get(data_grid_field)[0].get(desc_field).strip()
  return _pid, _desc

def create_untitled_municipal_land_desc(chefs_dic, parent_field, desc_field):
  _desc = None
  if chefs_dic.get(parent_field) is not None and len(chefs_dic.get(parent_field)) > 0: 
    if chefs_dic[parent_field][0].get(desc_field) is not None and chefs_dic[parent_field][0].get(desc_field).strip() != '':
      _desc = chefs_dic[parent_field][0].get(desc_field).strip()
  return _desc

def chefs_src_param(key):
  name = constant.CHEFS_SOURCE_PARAM_DIC.get(key)
  if name is not None:
    return name
  else:
    return key

def chefs_hv_param(key):
  name = constant.CHEFS_HV_PARAM_DIC.get(key)
  if name is not None:
    return name
  else:
    return key

def map_source_site(submission):
  _src_dic = {}
  _confirmation_id = helper.get_confirm_id(submission, chefs_src_param('form'), chefs_src_param('confirmationId'))
  if (helper.validate_lat_lon(submission.get(chefs_src_param('latitudeDegrees')), submission.get(chefs_src_param('latitudeMinutes')), submission.get(chefs_src_param('latitudeSeconds')), 
                              submission.get(chefs_src_param('longitudeDegrees')), submission.get(chefs_src_param('longitudeMinutes')), submission.get(chefs_src_param('longitudeSeconds')),
                              _confirmation_id, 'Soil Relocation Notification Form-Source Site')
  ):  
    #print("Mapping sourece site ...")

    #initialize
    for src_header in constant.SOURCE_SITE_HEADERS:
      _src_dic[src_header] = None

    _src_dic['updateToPreviousForm'] = submission.get(chefs_src_param('updateToPreviousForm'))
    _src_dic['ownerFirstName'] = submission.get(chefs_src_param('ownerFirstName'))
    _src_dic['ownerLastName'] = submission.get(chefs_src_param('ownerLastName'))
    _src_dic['ownerCompany'] = submission.get(chefs_src_param('ownerCompany'))
    _src_dic['ownerAddress'] = submission.get(chefs_src_param('ownerAddress'))
    _src_dic['ownerCity'] = submission.get(chefs_src_param('ownerCity'))
    _src_dic['ownerProvince'] = submission.get(chefs_src_param('ownerProvince'))
    _src_dic['ownerCountry'] = submission.get(chefs_src_param('ownerCountry'))
    _src_dic['ownerPostalCode'] = submission.get(chefs_src_param('ownerPostalCode'))
    _src_dic['ownerPhoneNumber'] = submission.get(chefs_src_param('ownerPhoneNumber'))
    _src_dic['ownerEmail'] = submission.get(chefs_src_param('ownerEmail'))
    _src_dic['owner2FirstName'] = submission.get(chefs_src_param('owner2FirstName'))
    _src_dic['owner2LastName'] = submission.get(chefs_src_param('owner2LastName'))
    _src_dic['owner2Company'] = submission.get(chefs_src_param('owner2Company'))
    _src_dic['owner2Address'] = submission.get(chefs_src_param('owner2Address'))
    _src_dic['owner2City'] = submission.get(chefs_src_param('owner2City'))
    _src_dic['owner2Province'] = submission.get(chefs_src_param('owner2Province'))
    _src_dic['owner2Country'] = submission.get(chefs_src_param('owner2Country'))
    _src_dic['owner2PostalCode'] = submission.get(chefs_src_param('owner2PostalCode'))
    _src_dic['owner2PhoneNumber'] = submission.get(chefs_src_param('owner2PhoneNumber'))
    _src_dic['owner2Email'] = submission.get(chefs_src_param('owner2Email'))
    _src_dic['additionalOwners'] = submission.get(chefs_src_param('additionalOwners'))
    _src_dic['contactFirstName'] = submission.get(chefs_src_param('contactFirstName'))
    _src_dic['contactLastName'] = submission.get(chefs_src_param('contactLastName'))
    _src_dic['contactCompany'] = submission.get(chefs_src_param('contactCompany'))
    _src_dic['contactAddress'] = submission.get(chefs_src_param('contactAddress'))
    _src_dic['contactCity'] = submission.get(chefs_src_param('contactCity'))
    _src_dic['contactProvince'] = submission.get(chefs_src_param('contactProvince'))
    _src_dic['contactCountry'] = submission.get(chefs_src_param('contactCountry'))
    _src_dic['contactPostalCode'] = submission.get(chefs_src_param('contactPostalCode'))
    _src_dic['contactPhoneNumber'] = submission.get(chefs_src_param('contactPhoneNumber'))
    _src_dic['contactEmail'] = submission.get(chefs_src_param('contactEmail'))
    _src_dic['SID'] = submission.get(chefs_src_param('SID'))

    _src_dic['latitude'], _src_dic['longitude'] = helper.convert_deciaml_lat_long(
      submission[chefs_src_param('latitudeDegrees')], submission[chefs_src_param('latitudeMinutes')], submission[chefs_src_param('latitudeSeconds')], 
      submission[chefs_src_param('longitudeDegrees')], submission[chefs_src_param('longitudeMinutes')], submission[chefs_src_param('longitudeSeconds')])

    _src_dic['landOwnership'] = create_land_ownership(submission, chefs_src_param('landOwnership'))
    _src_dic['regionalDistrict'] = create_regional_district(submission, chefs_src_param('regionalDistrict'))
    _src_dic['legallyTitledSiteAddress'] = submission.get(chefs_src_param('legallyTitledSiteAddress'))
    _src_dic['legallyTitledSiteCity'] = submission.get(chefs_src_param('legallyTitledSiteCity'))
    _src_dic['legallyTitledSitePostalCode'] = submission.get(chefs_src_param('legallyTitledSitePostalCode'))
    _src_dic['crownLandFileNumbers'] = create_land_file_numbers(submission, chefs_src_param('crownLandFileNumbers'))

    #PIN, PIN, description
    _src_dic['PID'], _src_dic['legalLandDescription'] = create_pid_pin_and_desc(submission, chefs_src_param('pidDataGrid'), chefs_src_param('pid'), chefs_src_param('pidDesc'))  #PID
    if (_src_dic['PID'] is None or _src_dic['PID'].strip() == ''): #PIN
      _src_dic['PIN'], _src_dic['legalLandDescription'] = create_pid_pin_and_desc(submission, chefs_src_param('pinDataGrid'), chefs_src_param('pin'), chefs_src_param('pinDesc'))
    if ((_src_dic['PID'] is None or _src_dic['PID'].strip() == '')
        and (_src_dic['PIN'] is None or _src_dic['PIN'].strip() == '')): #Description when selecting 'Untitled Municipal Land'
      _src_dic['legalLandDescription'] = create_untitled_municipal_land_desc(submission, chefs_src_param('untitledMunicipalLand'), chefs_src_param('untitledMunicipalLandDesc'))

    if submission.get(chefs_src_param('sourceSiteLandUse')) is not None and len(submission.get(chefs_src_param('sourceSiteLandUse'))) > 0 : 
      _source_site_land_uses = []
      for _ref_source_site in submission.get(chefs_src_param('sourceSiteLandUse')):
        _source_site_land_uses.append(convert_source_site_use_to_name(_ref_source_site))
      _src_dic['sourceSiteLandUse'] = "\"" + ",".join(_source_site_land_uses) + "\""

    _src_dic['highVolumeSite'] = submission.get(chefs_src_param('highVolumeSite'))
    _src_dic['soilRelocationPurpose'] = submission.get(chefs_src_param('soilRelocationPurpose'))
    _src_dic['soilStorageType'] = submission.get(chefs_src_param('soilStorageType'))

    # Soil Volume
    create_soil_volumes(submission, chefs_src_param('soilVolumeDataGrid'), chefs_src_param('soilVolume'), chefs_src_param('soilClassificationSource'), _src_dic)

    _src_dic['soilCharacterMethod'] = submission.get(chefs_src_param('soilCharacterMethod'))
    _src_dic['vapourExemption'] = submission.get(chefs_src_param('vapourExemption'))
    _src_dic['vapourExemptionDesc'] = submission.get(chefs_src_param('vapourExemptionDesc'))
    _src_dic['vapourCharacterMethodDesc'] = submission.get(chefs_src_param('vapourCharacterMethodDesc'))
    _src_dic['soilRelocationStartDate'] = helper.convert_simple_datetime_format_in_str(submission.get(chefs_src_param('soilRelocationStartDate')))
    _src_dic['soilRelocationCompletionDate'] = helper.convert_simple_datetime_format_in_str(submission.get(chefs_src_param('soilRelocationCompletionDate')))
    _src_dic['relocationMethod'] = submission.get(chefs_src_param('relocationMethod'))
    _src_dic['qualifiedProfessionalFirstName'] = submission.get(chefs_src_param('qualifiedProfessionalFirstName'))
    _src_dic['qualifiedProfessionalLastName'] = submission.get(chefs_src_param('qualifiedProfessionalLastName'))
    _src_dic['qualifiedProfessionalType'] = submission.get(chefs_src_param('qualifiedProfessionalType'))
    _src_dic['professionalLicenceRegistration'] = submission.get(chefs_src_param('professionalLicenceRegistration'))
    _src_dic['qualifiedProfessionalOrganization'] = submission.get(chefs_src_param('qualifiedProfessionalOrganization'))
    _src_dic['qualifiedProfessionalAddress'] = submission.get(chefs_src_param('qualifiedProfessionalAddress'))
    _src_dic['qualifiedProfessionalCity'] = submission.get(chefs_src_param('qualifiedProfessionalCity'))
    _src_dic['qualifiedProfessionalProvince'] = submission.get(chefs_src_param('qualifiedProfessionalProvince'))
    _src_dic['qualifiedProfessionalCountry'] = submission.get(chefs_src_param('qualifiedProfessionalCountry'))
    _src_dic['qualifiedProfessionalPostalCode'] = submission.get(chefs_src_param('qualifiedProfessionalPostalCode'))
    _src_dic['qualifiedProfessionalPhoneNumber'] = submission.get(chefs_src_param('qualifiedProfessionalPhoneNumber'))
    _src_dic['qualifiedProfessionalEmail'] = submission.get(chefs_src_param('qualifiedProfessionalEmail'))
    _src_dic['signaturerFirstAndLastName'] = submission.get(chefs_src_param('signaturerFirstAndLastName'))
    _src_dic['dateSigned'] = helper.convert_simple_datetime_format_in_str(submission.get(chefs_src_param('dateSigned')))
    _src_dic['createAt'] = helper.get_create_date(submission, chefs_src_param('form'), chefs_src_param('createdAt'))
    _src_dic['confirmationId'] = _confirmation_id

  return _src_dic

def map_rcv_1st_rcver(submission):
  _rcv_dic = {}
  _confirmation_id = helper.get_confirm_id(submission, 'form', 'confirmationId')
  if (helper.validate_lat_lon(submission.get("C2-Latitude-DegreesReceivingSite"), submission.get("C2-Latitude-MinutesReceivingSite"), submission.get("Section2-Latitude-Seconds1ReceivingSite"), 
                              submission.get("C2-Longitude-DegreesReceivingSite"), submission.get("C2-Longitude-MinutesReceivingSite"), submission.get("C2-Longitude-SecondsReceivingSite"),
                              _confirmation_id, 'Soil Relocation Notification Form-Receiving Site')
  ):  
    #print("Mapping 1st receiver ...")

    for rcv_header in constant.RECEIVING_SITE_HEADERS:
      _rcv_dic[rcv_header] = None

    if submission.get("C1-FirstNameReceivingSiteOwner") is not None : _rcv_dic['ownerFirstName'] = submission["C1-FirstNameReceivingSiteOwner"]
    if submission.get("C1-LastNameReceivingSiteOwner") is not None : _rcv_dic['ownerLastName'] = submission["C1-LastNameReceivingSiteOwner"]
    if submission.get("C1-CompanyReceivingSiteOwner") is not None : _rcv_dic['ownerCompany'] = submission["C1-CompanyReceivingSiteOwner"]
    if submission.get("C1-AddressReceivingSiteOwner") is not None : _rcv_dic['ownerAddress'] = submission["C1-AddressReceivingSiteOwner"]
    if submission.get("C1-CityReceivingSiteOwner") is not None : _rcv_dic['ownerCity'] = submission["C1-CityReceivingSiteOwner"]
    if submission.get("A1-receivingsiteownerProvinceState4") is not None : _rcv_dic['ownerProvince'] = submission["A1-receivingsiteownerProvinceState4"]    
    if submission.get("A1-receivingsiteownerCountry4") is not None : _rcv_dic['ownerCountry'] = submission["A1-receivingsiteownerCountry4"]
    if submission.get("A1-receivingsiteownerPostalCode3") is not None : _rcv_dic['ownerPostalCode'] = submission["A1-receivingsiteownerPostalCode3"]
    if submission.get("C1-PhoneRecevingSiteOwner") is not None : _rcv_dic['ownerPhoneNumber'] = submission["C1-PhoneRecevingSiteOwner"]
    if submission.get("C1-EmailReceivingSiteOwner") is not None : _rcv_dic['ownerEmail'] = submission["C1-EmailReceivingSiteOwner"]

    if submission.get("C1-FirstName1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2FirstName'] = submission["C1-FirstName1ReceivingSiteAdditionalOwners"]
    if submission.get("C1-LastName1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2LastName'] = submission["C1-LastName1ReceivingSiteAdditionalOwners"]
    if submission.get("C1-Company1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2Company'] = submission["C1-Company1ReceivingSiteAdditionalOwners"]
    if submission.get("C1-Address1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2Address'] = submission["C1-Address1ReceivingSiteAdditionalOwners"]
    if submission.get("C1-City1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2City'] = submission["C1-City1ReceivingSiteAdditionalOwners"]
    if submission.get("A1-additionareceivingsiteownerProvinceState5") is not None : _rcv_dic['owner2Province'] = submission["A1-additionareceivingsiteownerProvinceState5"]
    if submission.get("A1-additionareceivingsiteownerCountry5") is not None : _rcv_dic['owner2Country'] = submission["A1-additionareceivingsiteownerCountry5"]
    if submission.get("A1-additionalreceivingsiteownerPostalCode4") is not None : _rcv_dic['owner2PostalCode'] = submission["A1-additionalreceivingsiteownerPostalCode4"]    
    if submission.get("C1-Phone1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2PhoneNumber'] = submission["C1-Phone1ReceivingSiteAdditionalOwners"]
    if submission.get("C1-Email1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2Email'] = submission["C1-Email1ReceivingSiteAdditionalOwners"]

    if submission.get("haveMoreThatTwoOwnersEnterTheirInformationBelow") is not None : _rcv_dic['additionalOwners'] = submission["haveMoreThatTwoOwnersEnterTheirInformationBelow"]
    if submission.get("C2-RSC-FirstName") is not None : _rcv_dic['contactFirstName'] = submission["C2-RSC-FirstName"]
    if submission.get("C2-RSC-LastName") is not None : _rcv_dic['contactLastName'] = submission["C2-RSC-LastName"]
    if submission.get("C2-RSC-Company") is not None : _rcv_dic['contactCompany'] = submission["C2-RSC-Company"]
    if submission.get("C2-RSC-Address") is not None : _rcv_dic['contactAddress'] = submission["C2-RSC-Address"]
    if submission.get("C2-RSC-City") is not None : _rcv_dic['contactCity'] = submission["C2-RSC-City"]
    if submission.get("A1-additionareceivingsitecontactpersonProvinceState6") is not None : _rcv_dic['contactProvince'] = submission["A1-additionareceivingsitecontactpersonProvinceState6"]
    if submission.get("A1-additionareceivingsitecontactpersonCountry6") is not None : _rcv_dic['contactCountry'] = submission["A1-additionareceivingsitecontactpersonCountry6"]
    if submission.get("A1-additionalreceivingsitecontactpersonPostalCode5") is not None : _rcv_dic['contactPostalCode'] = submission["A1-additionalreceivingsitecontactpersonPostalCode5"]
    if submission.get("C2-RSCphoneNumber1") is not None : _rcv_dic['contactPhoneNumber'] = submission["C2-RSCphoneNumber1"]
    if submission.get("C2-RSC-Email") is not None : _rcv_dic['contactEmail'] = submission["C2-RSC-Email"]
    if submission.get("C2-siteIdentificationNumberSiteIdIfAvailableReceivingSite") is not None : _rcv_dic['SID'] = submission["C2-siteIdentificationNumberSiteIdIfAvailableReceivingSite"]

    _rcv_lat, _rcv_lon = helper.convert_deciaml_lat_long(
      submission["C2-Latitude-DegreesReceivingSite"], submission["C2-Latitude-MinutesReceivingSite"], submission["Section2-Latitude-Seconds1ReceivingSite"], 
      submission["C2-Longitude-DegreesReceivingSite"], submission["C2-Longitude-MinutesReceivingSite"], submission["C2-Longitude-SecondsReceivingSite"])
    _rcv_dic['latitude'] = _rcv_lat
    _rcv_dic['longitude'] = _rcv_lon

    _rcv_dic['regionalDistrict'] = create_regional_district(submission, 'ReceivingSiteregionalDistrict')
    _rcv_dic['landOwnership'] = create_land_ownership(submission, 'C2-receivinglandOwnership-checkbox')

    if submission.get("C2-LegallyTitled-AddressReceivingSite") is not None : _rcv_dic['legallyTitledSiteAddress'] = submission["C2-LegallyTitled-AddressReceivingSite"]
    if submission.get("C2-LegallyTitled-CityReceivingSite") is not None : _rcv_dic['legallyTitledSiteCity'] = submission["C2-LegallyTitled-CityReceivingSite"]
    if submission.get("C2-LegallyTitled-PostalReceivingSite") is not None : _rcv_dic['legallyTitledSitePostalCode'] = submission["C2-LegallyTitled-PostalReceivingSite"]

    #PIN, PIN, description
    _rcv_dic['PID'], _rcv_dic['legalLandDescription'] = create_pid_pin_and_desc(submission, 'dataGrid2', 'A-LegallyTitled-PIDReceivingSite', 'legalLandDescriptionReceivingSite')  #PID
    if (_rcv_dic['PID'] is None or _rcv_dic['PID'].strip() == ''): #PIN
      _rcv_dic['PIN'], _rcv_dic['legalLandDescription'] = create_pid_pin_and_desc(submission, 'dataGrid5', 'A-LegallyTitled-PID', 'legalLandDescriptionUntitledCrownLandReceivingSite')
    if ((_rcv_dic['PID'] is None or _rcv_dic['PID'].strip() == '')
        and (_rcv_dic['PIN'] is None or _rcv_dic['PIN'].strip() == '')): #Description when selecting 'Untitled Municipal Land'
      _rcv_dic['legalLandDescription'] = create_untitled_municipal_land_desc(submission, 'A-UntitledMunicipalLand-PIDColumn1', 'legalLandDescription')

    _rcv_dic['crownLandFileNumbers'] = create_land_file_numbers(submission, 'A-UntitledCrownLand-FileNumberColumn1')
    _rcv_dic['receivingSiteLandUse'] = create_receiving_site_lan_uses(submission, 'C3-soilClassification1ReceivingSite')

    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule31ReceivingSite") is not None : _rcv_dic['CSRFactors'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule31ReceivingSite"]
    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule32ReceivingSite") is not None : _rcv_dic['relocatedSoilUse'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule32ReceivingSite"]
    if submission.get("C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime3") is not None : _rcv_dic['highVolumeSite'] = submission["C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime3"]
    if submission.get("D2-receivingsitesoilDepositIsInTheAgriculturalLandReserveAlr1") is not None : _rcv_dic['soilDepositIsALR'] = submission["D2-receivingsitesoilDepositIsInTheAgriculturalLandReserveAlr1"]
    if submission.get("D2-receivingsitesoilDepositIsInTheReserveLands1") is not None : _rcv_dic['soilDepositIsReserveLands'] = submission["D2-receivingsitesoilDepositIsInTheReserveLands1"]
    _rcv_dic['dateSigned'] = helper.convert_simple_datetime_format_in_str(submission.get("simpledatetime"))    
    _rcv_dic['createAt'] = helper.get_create_date(submission, 'form', 'createdAt')
    _rcv_dic['confirmationId'] = _confirmation_id
  return _rcv_dic

def map_rcv_2nd_rcver(submission):
  _rcv_dic = {}
  _confirmation_id = helper.get_confirm_id(submission, 'form', 'confirmationId')
  if (helper.is_not_none_true(submission.get('additionalReceivingSites').get('firstAdditionalReceivingSiteInformation')) and
      helper.validate_lat_lon(submission.get("C2-Latitude-Degrees1FirstAdditionalReceivingSite"), submission.get("C2-Latitude-Minutes1FirstAdditionalReceivingSite"), submission.get("Section2-Latitude-Seconds2FirstAdditionalReceivingSite"), 
                              submission.get("C2-Longitude-Degrees1FirstAdditionalReceivingSite"), submission.get("C2-Longitude-Minutes1FirstAdditionalReceivingSite"), submission.get("C2-Longitude-Seconds1FirstAdditionalReceivingSite"),
                              _confirmation_id, 'Soil Relocation Notification Form-Receiving Site')
  ):
    #print("Mapping 2nd receiver ...")

    for rcv_header in constant.RECEIVING_SITE_HEADERS:
      _rcv_dic[rcv_header] = None

    if submission.get("C1-FirstName2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerFirstName'] = submission["C1-FirstName2FirstAdditionalReceivingSite"]
    if submission.get("C1-LastName2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerLastName'] = submission["C1-LastName2FirstAdditionalReceivingSite"]
    if submission.get("C1-Company2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerCompany'] = submission["C1-Company2FirstAdditionalReceivingSite"]
    if submission.get("C1-Address2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerAddress'] = submission["C1-Address2FirstAdditionalReceivingSite"]
    if submission.get("C1-City2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerCity'] = submission["C1-City2FirstAdditionalReceivingSite"]
    if submission.get("A1-firstadditionalreceivingsiteownerProvinceState7") is not None : _rcv_dic['ownerProvince'] = submission["A1-firstadditionalreceivingsiteownerProvinceState7"]    
    if submission.get("A1-firstadditionalreceivingsiteownerCountry7") is not None : _rcv_dic['ownerCountry'] = submission["A1-firstadditionalreceivingsiteownerCountry7"]
    if submission.get("A1-firstadditionalreceivingsiteownerPostalCode6") is not None : _rcv_dic['ownerPostalCode'] = submission["A1-firstadditionalreceivingsiteownerPostalCode6"]
    if submission.get("phoneNumber4FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerPhoneNumber'] = submission["phoneNumber4FirstAdditionalReceivingSite"]
    if submission.get("C1-Email2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerEmail'] = submission["C1-Email2FirstAdditionalReceivingSite"]

    if submission.get("C1-FirstName3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2FirstName'] = submission["C1-FirstName3AdditionalReceivingSiteOwner"]
    if submission.get("C1-LastName3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2LastName'] = submission["C1-LastName3AdditionalReceivingSiteOwner"]
    if submission.get("C1-Company3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2Company'] = submission["C1-Company3AdditionalReceivingSiteOwner"]
    if submission.get("C1-Address3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2Address'] = submission["C1-Address3AdditionalReceivingSiteOwner"]
    if submission.get("C1-City3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2City'] = submission["C1-City3AdditionalReceivingSiteOwner"]
    if submission.get("A1-firstadditionalreceivingmoreownersProvinceState8") is not None : _rcv_dic['owner2Province'] = submission["A1-additionareceivingsiteownerProvinceState5"]
    if submission.get("A1-firstadditionalreceivingmoreownersCountry8") is not None : _rcv_dic['owner2Country'] = submission["A1-firstadditionalreceivingmoreownersCountry8"]
    if submission.get("A1-firstadditionalreceivingmoreownersPostalCode7") is not None : _rcv_dic['owner2PostalCode'] = submission["A1-firstadditionalreceivingmoreownersPostalCode7"]    
    if submission.get("phoneNumber2AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2PhoneNumber'] = submission["phoneNumber2AdditionalReceivingSiteOwner"]
    if submission.get("C1-Email3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2Email'] = submission["C1-Email3AdditionalReceivingSiteOwner"]

    if submission.get("C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow2ReceivingSite") is not None : _rcv_dic['additionalOwners'] = submission["C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow2ReceivingSite"]
    if submission.get("C2-RSC-FirstName1AdditionalReceivingSite") is not None : _rcv_dic['contactFirstName'] = submission["C2-RSC-FirstName1AdditionalReceivingSite"]
    if submission.get("C2-RSC-LastName1AdditionalReceivingSite") is not None : _rcv_dic['contactLastName'] = submission["C2-RSC-LastName1AdditionalReceivingSite"]
    if submission.get("C2-RSC-Company1AdditionalReceivingSite") is not None : _rcv_dic['contactCompany'] = submission["C2-RSC-Company1AdditionalReceivingSite"]
    if submission.get("C2-RSC-Address1AdditionalReceivingSite") is not None : _rcv_dic['contactAddress'] = submission["C2-RSC-Address1AdditionalReceivingSite"]
    if submission.get("C2-RSC-City1AdditionalReceivingSite") is not None : _rcv_dic['contactCity'] = submission["C2-RSC-City1AdditionalReceivingSite"]
    if submission.get("A1-firstadditionalreceivingsitecontactProvinceState9") is not None : _rcv_dic['contactProvince'] = submission["A1-firstadditionalreceivingsitecontactProvinceState9"]
    if submission.get("A1-firstadditionalreceivingsitecontactCountry9") is not None : _rcv_dic['contactCountry'] = submission["A1-firstadditionalreceivingsitecontactCountry9"]
    if submission.get("A1-firstadditionalreceivingsitecontactPostalCode8") is not None : _rcv_dic['contactPostalCode'] = submission["A1-firstadditionalreceivingsitecontactPostalCode8"]
    if submission.get("phoneNumber3AdditionalReceivingSite") is not None : _rcv_dic['contactPhoneNumber'] = submission["phoneNumber3AdditionalReceivingSite"]
    if submission.get("C2-RSC-Email1AdditionalReceivingSite") is not None : _rcv_dic['contactEmail'] = submission["C2-RSC-Email1AdditionalReceivingSite"]
    if submission.get("C2-siteIdentificationNumberSiteIdIfAvailable1FirstAdditionalReceivingSite") is not None : _rcv_dic['SID'] = submission["C2-siteIdentificationNumberSiteIdIfAvailable1FirstAdditionalReceivingSite"]

    _rcv_lat, _rcv_lon = helper.convert_deciaml_lat_long(
      submission["C2-Latitude-Degrees1FirstAdditionalReceivingSite"], submission["C2-Latitude-Minutes1FirstAdditionalReceivingSite"], submission["Section2-Latitude-Seconds2FirstAdditionalReceivingSite"], 
      submission["C2-Longitude-Degrees1FirstAdditionalReceivingSite"], submission["C2-Longitude-Minutes1FirstAdditionalReceivingSite"], submission["C2-Longitude-Seconds1FirstAdditionalReceivingSite"])
    _rcv_dic['latitude'] = _rcv_lat
    _rcv_dic['longitude'] = _rcv_lon

    _rcv_dic['regionalDistrict'] = create_regional_district(submission, 'FirstAdditionalReceivingSiteregionalDistrict1')
    _rcv_dic['landOwnership'] = create_land_ownership(submission, 'Firstadditionalreceiving-landOwnership-checkbox1')

    if submission.get("C2-LegallyTitled-Address1FirstAdditionalReceivingSite") is not None : _rcv_dic['legallyTitledSiteAddress'] = submission["C2-LegallyTitled-Address1FirstAdditionalReceivingSite"]
    if submission.get("C2-LegallyTitled-City1FirstAdditionalReceivingSite") is not None : _rcv_dic['legallyTitledSiteCity'] = submission["C2-LegallyTitled-City1FirstAdditionalReceivingSite"]
    if submission.get("C2-LegallyTitled-PostalZipCode1FirstAdditionalReceivingSite") is not None : _rcv_dic['legallyTitledSitePostalCode'] = submission["C2-LegallyTitled-PostalZipCode1FirstAdditionalReceivingSite"]

    #PIN, PIN, description
    _rcv_dic['PID'], _rcv_dic['legalLandDescription'] = create_pid_pin_and_desc(submission, 'dataGrid3', 'A-LegallyTitled-PIDFirstAdditionalReceivingSite', 'legalLandDescriptionFirstAdditionalReceivingSite')  #PID
    if (_rcv_dic['PID'] is None or _rcv_dic['PID'].strip() == ''): #PIN
      _rcv_dic['PIN'], _rcv_dic['legalLandDescription'] = create_pid_pin_and_desc(submission, 'dataGrid6', 'A-UntitledCrown-PINFirstAdditionalReceivingSite', 'legalLandDescriptionUntitledCrownFirstAdditionalReceivingSite')
    if ((_rcv_dic['PID'] is None or _rcv_dic['PID'].strip() == '')
        and (_rcv_dic['PIN'] is None or _rcv_dic['PIN'].strip() == '')): #Description when selecting 'Untitled Municipal Land'
      _rcv_dic['legalLandDescription'] = create_untitled_municipal_land_desc(submission, 'A-UntitledMunicipalLand-PIDColumn2', 'legalLandDescriptionUntitledMunicipalFirstAdditionalReceivingSite')

    _rcv_dic['crownLandFileNumbers'] = create_land_file_numbers(submission, 'A-UntitledCrownLand-FileNumberColumn2')
    _rcv_dic['receivingSiteLandUse'] = create_receiving_site_lan_uses(submission, 'C3-soilClassification2FirstAdditionalReceivingSite')

    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule33FirstAdditionalReceivingSite") is not None : _rcv_dic['CSRFactors'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule33FirstAdditionalReceivingSite"]
    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule34FirstAdditionalReceivingSite") is not None : _rcv_dic['relocatedSoilUse'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule34FirstAdditionalReceivingSite"]
    if submission.get("C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1") is not None : _rcv_dic['highVolumeSite'] = submission["C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1"]
    if submission.get("D2-firstaddtlreceivingsitesoilDepositIsInTheAgriculturalLandReserveAlr2") is not None : _rcv_dic['soilDepositIsALR'] = submission["D2-firstaddtlreceivingsitesoilDepositIsInTheAgriculturalLandReserveAlr2"]
    if submission.get("D2-firstaddtlreceivingsitesoilDepositIsInTheReserveLands2") is not None : _rcv_dic['soilDepositIsReserveLands'] = submission["D2-firstaddtlreceivingsitesoilDepositIsInTheReserveLands2"]
    _rcv_dic['dateSigned'] = helper.convert_simple_datetime_format_in_str(submission.get("simpledatetime"))       
    _rcv_dic['createAt'] = helper.get_create_date(submission, 'form', 'createdAt')
    _rcv_dic['confirmationId'] = _confirmation_id
  return _rcv_dic

def map_rcv_3rd_rcver(submission):
  _rcv_dic = {}
  _confirmation_id = helper.get_confirm_id(submission, 'form', 'confirmationId')
  if (helper.is_not_none_true(submission.get('secondadditionalReceivingSites1').get('secondAdditionalReceivingSiteInformation')) and
      helper.validate_lat_lon(submission.get("C2-Latitude-Degrees3SecondAdditionalreceivingSite"), submission.get("C2-Latitude-Minutes3SecondAdditionalreceivingSite"), submission.get("Section2-Latitude-Seconds4SecondAdditionalreceivingSite"), 
                              submission.get("C2-Longitude-Degrees3SecondAdditionalreceivingSite"), submission.get("C2-Longitude-Minutes3SecondAdditionalreceivingSite"), submission.get("C2-Longitude-Seconds3SecondAdditionalreceivingSite"),
                              _confirmation_id, 'Soil Relocation Notification Form-Receiving Site')
  ):  
    #print("Mapping 3rd receiver ...")

    for rcv_header in constant.RECEIVING_SITE_HEADERS:
      _rcv_dic[rcv_header] = None

    if submission.get("C1-FirstName6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerFirstName'] = submission["C1-FirstName6SecondAdditionalreceivingSite"]
    if submission.get("C1-LastName6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerLastName'] = submission["C1-LastName6SecondAdditionalreceivingSite"]
    if submission.get("C1-Company6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerCompany'] = submission["C1-Company6SecondAdditionalreceivingSite"]
    if submission.get("C1-Address6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerAddress'] = submission["C1-Address6SecondAdditionalreceivingSite"]
    if submission.get("C1-City6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerCity'] = submission["C1-City6SecondAdditionalreceivingSite"]
    if submission.get("A1-secondadditionalreceivingsiteownerProvinceState10") is not None : _rcv_dic['ownerProvince'] = submission["A1-secondadditionalreceivingsiteownerProvinceState10"]    
    if submission.get("A1-secondadditionalreceivingsiteownerCountry10") is not None : _rcv_dic['ownerCountry'] = submission["A1-secondadditionalreceivingsiteownerCountry10"]
    if submission.get("A1-secondadditionalreceivingsiteownerPostalCode9") is not None : _rcv_dic['ownerPostalCode'] = submission["A1-secondadditionalreceivingsiteownerPostalCode9"]
    if submission.get("phoneNumber7SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerPhoneNumber'] = submission["phoneNumber7SecondAdditionalreceivingSite"]
    if submission.get("C1-Email6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerEmail'] = submission["C1-Email6SecondAdditionalreceivingSite"]

    if submission.get("C1-FirstName7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2FirstName'] = submission["C1-FirstName7SecondAdditionalreceivingSite"]
    if submission.get("C1-LastName7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2LastName'] = submission["C1-LastName7SecondAdditionalreceivingSite"]
    if submission.get("C1-Company7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2Company'] = submission["C1-Company7SecondAdditionalreceivingSite"]
    if submission.get("C1-Address7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2Address'] = submission["C1-Address7SecondAdditionalreceivingSite"]
    if submission.get("C1-City7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2City'] = submission["C1-City7SecondAdditionalreceivingSite"]
    if submission.get("A1-secondadditionalreceivingsiteadditionalownerProvinceState11") is not None : _rcv_dic['owner2Province'] = submission["A1-secondadditionalreceivingsiteadditionalownerProvinceState11"]
    if submission.get("A1-secondadditionalreceivingsiteadditionalownerCountry11") is not None : _rcv_dic['owner2Country'] = submission["A1-secondadditionalreceivingsiteadditionalownerCountry11"]
    if submission.get("A1-secondadditionalreceivingsiteadditionalownerPostalCode10") is not None : _rcv_dic['owner2PostalCode'] = submission["A1-secondadditionalreceivingsiteadditionalownerPostalCode10"]    
    if submission.get("phoneNumber5SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2PhoneNumber'] = submission["phoneNumber5SecondAdditionalreceivingSite"]
    if submission.get("C1-Email7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2Email'] = submission["C1-Email7SecondAdditionalreceivingSite"]

    if submission.get("C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow4SecondAdditionalreceivingSite") is not None : _rcv_dic['additionalOwners'] = submission["C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow4SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-FirstName3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactFirstName'] = submission["C2-RSC-FirstName3SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-LastName3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactLastName'] = submission["C2-RSC-LastName3SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-Company3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactCompany'] = submission["C2-RSC-Company3SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-Address3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactAddress'] = submission["C2-RSC-Address3SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-City3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactCity'] = submission["C2-RSC-City3SecondAdditionalreceivingSite"]
    if submission.get("A1-secondadditionalreceivingsitecontactProvinceState12") is not None : _rcv_dic['contactProvince'] = submission["A1-firstadditionalreceivingsitecontactProvinceState9"]
    if submission.get("A1-secondadditionalreceivingsitecontactrCountry12") is not None : _rcv_dic['contactCountry'] = submission["A1-secondadditionalreceivingsitecontactrCountry12"]
    if submission.get("A1-secondadditionalreceivingsitecontactPostalCode11") is not None : _rcv_dic['contactPostalCode'] = submission["A1-secondadditionalreceivingsitecontactPostalCode11"]

    if submission.get("phoneNumber6SecondAdditionalreceivingSite") is not None : _rcv_dic['contactPhoneNumber'] = submission["phoneNumber6SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-Email3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactEmail'] = submission["C2-RSC-Email3SecondAdditionalreceivingSite"]
    if submission.get("C2-siteIdentificationNumberSiteIdIfAvailable3SecondAdditionalreceivingSite") is not None : _rcv_dic['SID'] = submission["C2-siteIdentificationNumberSiteIdIfAvailable3SecondAdditionalreceivingSite"]

    _rcv_lat, _rcv_lon = helper.convert_deciaml_lat_long(
      submission["C2-Latitude-Degrees3SecondAdditionalreceivingSite"], submission["C2-Latitude-Minutes3SecondAdditionalreceivingSite"], submission["Section2-Latitude-Seconds4SecondAdditionalreceivingSite"], 
      submission["C2-Longitude-Degrees3SecondAdditionalreceivingSite"], submission["C2-Longitude-Minutes3SecondAdditionalreceivingSite"], submission["C2-Longitude-Seconds3SecondAdditionalreceivingSite"])
    _rcv_dic['latitude'] = _rcv_lat
    _rcv_dic['longitude'] = _rcv_lon

    _rcv_dic['regionalDistrict'] = create_regional_district(submission, 'SecondAdditionalReceivingSiteregionalDistrict')
    _rcv_dic['landOwnership'] = create_land_ownership(submission, 'Secondadditionalreceiving-landOwnership-checkbox3')

    if submission.get("C2-LegallyTitled-Address3SecondAdditionalreceivingSite") is not None : _rcv_dic['legallyTitledSiteAddress'] = submission["C2-LegallyTitled-Address3SecondAdditionalreceivingSite"]
    if submission.get("C2-LegallyTitled-City3SecondAdditionalreceivingSite") is not None : _rcv_dic['legallyTitledSiteCity'] = submission["C2-LegallyTitled-City3SecondAdditionalreceivingSite"]
    if submission.get("C2-LegallyTitled-PostalZipCode3SecondAdditionalreceivingSite") is not None : _rcv_dic['legallyTitledSitePostalCode'] = submission["C2-LegallyTitled-PostalZipCode3SecondAdditionalreceivingSite"]

    #PIN, PIN, description
    _rcv_dic['PID'], _rcv_dic['legalLandDescription'] = create_pid_pin_and_desc(submission, 'dataGrid4', 'A-LegallyTitled-PIDSecondAdditionalreceivingSite', 'legalLandDescriptionSecondAdditionalreceivingSite')  #PID
    if (_rcv_dic['PID'] is None or _rcv_dic['PID'].strip() == ''): #PIN
      _rcv_dic['PIN'], _rcv_dic['legalLandDescription'] = create_pid_pin_and_desc(submission, 'dataGrid7', 'A-UntitledCrownLand-PINSecondAdditionalreceivingSite', 'UntitledCrownLandLegalLandDescriptionSecondAdditionalreceivingSite')
    if ((_rcv_dic['PID'] is None or _rcv_dic['PID'].strip() == '')
        and (_rcv_dic['PIN'] is None or _rcv_dic['PIN'].strip() == '')): #Description when selecting 'Untitled Municipal Land'
      _rcv_dic['legalLandDescription'] = create_untitled_municipal_land_desc(submission, 'A-UntitledMunicipalLand-PIDColumn3', 'legalLandDescriptionUntitledMunicipalSecondAdditionalreceivingSite')

    _rcv_dic['crownLandFileNumbers'] = create_land_file_numbers(submission, 'A-UntitledCrownLand-FileNumberColumn2')        
    _rcv_dic['receivingSiteLandUse'] = create_receiving_site_lan_uses(submission, 'C3-soilClassification4SecondAdditionalreceivingSite')

    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule37SecondAdditionalreceivingSite") is not None : _rcv_dic['CSRFactors'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule37SecondAdditionalreceivingSite"]
    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule38SecondAdditionalreceivingSite") is not None : _rcv_dic['relocatedSoilUse'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule38SecondAdditionalreceivingSite"]
    if submission.get("C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime3") is not None : _rcv_dic['highVolumeSite'] = submission["C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime3"]
    if submission.get("D2-secondaddtlreceivingsitesoilDepositIsInTheAgriculturalLandReserveAlr3") is not None : _rcv_dic['soilDepositIsALR'] = submission["D2-secondaddtlreceivingsitesoilDepositIsInTheAgriculturalLandReserveAlr3"]
    if submission.get("D2-secondaddtlreceivingsitesoilDepositIsInTheReserveLands3") is not None : _rcv_dic['soilDepositIsReserveLands'] = submission["D2-secondaddtlreceivingsitesoilDepositIsInTheReserveLands3"]
    _rcv_dic['dateSigned'] = helper.convert_simple_datetime_format_in_str(submission.get("simpledatetime"))       
    _rcv_dic['createAt'] = helper.get_create_date(submission, 'form', 'createdAt')
    _rcv_dic['confirmationId'] = _confirmation_id
  return _rcv_dic

def map_hv_site(hvs):
  _hv_dic = {}
  _confirmation_id = helper.get_confirm_id(hvs, chefs_hv_param('form'), chefs_hv_param('confirmationId'))
  if (helper.validate_lat_lon(hvs.get(chefs_hv_param('latitudeDegrees')), hvs.get(chefs_hv_param('latitudeMinutes')), hvs.get(chefs_hv_param('latitudeSeconds')), 
                              hvs.get(chefs_hv_param('longitudeDegrees')), hvs.get(chefs_hv_param('longitudeMinutes')), hvs.get(chefs_hv_param('longitudeSeconds')),
                              _confirmation_id, 'High Volume Receiving Site Form')
  ):
    #print("Mapping high volume site ...")

    # initialize
    for hv_header in constant.HV_SITE_HEADERS:
      _hv_dic[hv_header] = None

    _hv_dic['ownerFirstName'] = hvs.get(chefs_hv_param('ownerFirstName'))
    _hv_dic['ownerLastName'] = hvs.get(chefs_hv_param('ownerLastName'))
    _hv_dic['ownerCompany'] = hvs.get(chefs_hv_param('ownerCompany'))
    _hv_dic['ownerAddress'] = hvs.get(chefs_hv_param('ownerAddress'))
    _hv_dic['ownerCity'] = hvs.get(chefs_hv_param('ownerCity'))
    _hv_dic['ownerProvince'] = hvs.get(chefs_hv_param('ownerProvince'))
    _hv_dic['ownerCountry'] = hvs.get(chefs_hv_param('ownerCountry'))
    _hv_dic['ownerPostalCode'] = hvs.get(chefs_hv_param('ownerPostalCode'))
    _hv_dic['ownerPhoneNumber'] = hvs.get(chefs_hv_param('ownerPhoneNumber'))
    _hv_dic['ownerEmail'] = hvs.get(chefs_hv_param('ownerEmail'))
    _hv_dic['owner2FirstName'] = hvs.get(chefs_hv_param('owner2FirstName'))
    _hv_dic['owner2LastName'] = hvs.get(chefs_hv_param('owner2LastName'))
    _hv_dic['owner2Company'] = hvs.get(chefs_hv_param('owner2Company'))
    _hv_dic['owner2Address'] = hvs.get(chefs_hv_param('owner2Address'))
    _hv_dic['owner2City'] = hvs.get(chefs_hv_param('owner2City'))
    _hv_dic['owner2Province'] = hvs.get(chefs_hv_param('owner2Province'))
    _hv_dic['owner2Country'] = hvs.get(chefs_hv_param('owner2Country'))
    _hv_dic['owner2PostalCode'] = hvs.get(chefs_hv_param('owner2PostalCode'))
    _hv_dic['owner2PhoneNumber'] = hvs.get(chefs_hv_param('owner2PhoneNumber'))
    _hv_dic['owner2Email'] = hvs.get(chefs_hv_param('owner2Email'))
    _hv_dic['additionalOwners'] = hvs.get(chefs_hv_param('additionalOwners'))
    _hv_dic['contactFirstName'] = hvs.get(chefs_hv_param('contactFirstName'))
    _hv_dic['contactLastName'] = hvs.get(chefs_hv_param('contactLastName'))
    _hv_dic['contactCompany'] = hvs.get(chefs_hv_param('contactCompany'))
    _hv_dic['contactAddress'] = hvs.get(chefs_hv_param('contactAddress'))
    _hv_dic['contactCity'] = hvs.get(chefs_hv_param('contactCity'))
    _hv_dic['contactProvince'] = hvs.get(chefs_hv_param('contactProvince'))
    _hv_dic['contactCountry'] = hvs.get(chefs_hv_param('contactCountry'))
    _hv_dic['contactPostalCode'] = hvs.get(chefs_hv_param('contactPostalCode'))
    _hv_dic['contactPhoneNumber'] = hvs.get(chefs_hv_param('contactPhoneNumber'))
    _hv_dic['contactEmail'] = hvs.get(chefs_hv_param('contactEmail'))
    _hv_dic['SID'] = hvs.get(chefs_hv_param('SID'))

    _hv_dic['latitude'], _hv_dic['longitude'] = helper.convert_deciaml_lat_long(
      hvs[chefs_hv_param('latitudeDegrees')], hvs[chefs_hv_param('latitudeMinutes')], hvs[chefs_hv_param('latitudeSeconds')], 
      hvs[chefs_hv_param('longitudeDegrees')], hvs[chefs_hv_param('longitudeMinutes')], hvs[chefs_hv_param('longitudeSeconds')])

    _hv_dic['regionalDistrict'] = create_regional_district(hvs, chefs_hv_param('regionalDistrict'))
    _hv_dic['landOwnership'] = create_land_ownership(hvs, chefs_hv_param('landOwnership'))
    _hv_dic['legallyTitledSiteAddress'] = hvs.get(chefs_hv_param('legallyTitledSiteAddress'))
    _hv_dic['legallyTitledSiteCity'] = hvs.get(chefs_hv_param('legallyTitledSiteCity'))
    _hv_dic['legallyTitledSitePostalCode'] = hvs.get(chefs_hv_param('legallyTitledSitePostalCode'))
    #PIN, PIN, description
    _hv_dic['PID'], _hv_dic['legalLandDescription'] = create_pid_pin_and_desc(hvs, chefs_hv_param('pidDataGrid'), chefs_hv_param('pid'), chefs_hv_param('pidDesc')) #PID
    if (_hv_dic['PID'] is None or _hv_dic['PID'].strip() == ''): #PIN
      _hv_dic['PIN'], _hv_dic['legalLandDescription'] = create_pid_pin_and_desc(hvs, chefs_hv_param('pinDataGrid'), chefs_hv_param('pin'), chefs_hv_param('pinDesc'))
    if ((_hv_dic['PID'] is None or _hv_dic['PID'].strip() == '')
        and (_hv_dic['PIN'] is None or _hv_dic['PIN'].strip() == '')): #Description when selecting 'Untitled Municipal Land'
      _hv_dic['legalLandDescription'] = create_untitled_municipal_land_desc(hvs, chefs_hv_param('untitledMunicipalLand'), chefs_hv_param('untitledMunicipalLandDesc'))

    _hv_dic['crownLandFileNumbers'] = create_land_file_numbers(hvs, chefs_hv_param('crownLandFileNumbers'))
    _hv_dic['receivingSiteLandUse'] = create_receiving_site_lan_uses(hvs, chefs_hv_param('receivingSiteLandUse'))
    _hv_dic['hvsConfirmation'] = hvs.get(chefs_hv_param('hvsConfirmation'))
    _hv_dic['dateSiteBecameHighVolume'] = helper.convert_simple_datetime_format_in_str(hvs.get(chefs_hv_param('dateSiteBecameHighVolume')))
    _hv_dic['howRelocatedSoilWillBeUsed'] = hvs.get(chefs_hv_param('howRelocatedSoilWillBeUsed'))
    _hv_dic['soilDepositIsALR'] = hvs.get(chefs_hv_param('soilDepositIsALR'))
    _hv_dic['soilDepositIsReserveLands'] = hvs.get(chefs_hv_param('soilDepositIsReserveLands'))
    _hv_dic['qualifiedProfessionalFirstName'] = hvs.get(chefs_hv_param('qualifiedProfessionalFirstName'))
    _hv_dic['qualifiedProfessionalLastName'] = hvs.get(chefs_hv_param('qualifiedProfessionalLastName'))
    _hv_dic['qualifiedProfessionalType'] = hvs.get(chefs_hv_param('qualifiedProfessionalType'))
    _hv_dic['qualifiedProfessionalOrganization'] = hvs.get(chefs_hv_param('qualifiedProfessionalOrganization'))
    _hv_dic['professionalLicenceRegistration'] = hvs.get(chefs_hv_param('professionalLicenceRegistration'))
    _hv_dic['qualifiedProfessionalAddress'] = hvs.get(chefs_hv_param('qualifiedProfessionalAddress'))
    _hv_dic['qualifiedProfessionalCity'] = hvs.get(chefs_hv_param('qualifiedProfessionalCity'))
    _hv_dic['qualifiedProfessionalProvince'] = hvs.get(chefs_hv_param('qualifiedProfessionalProvince'))
    _hv_dic['qualifiedProfessionalCountry'] = hvs.get(chefs_hv_param('qualifiedProfessionalCountry'))
    _hv_dic['qualifiedProfessionalPostalCode'] = hvs.get(chefs_hv_param('qualifiedProfessionalPostalCode'))
    _hv_dic['qualifiedProfessionalPhoneNumber'] = hvs.get(chefs_hv_param('qualifiedProfessionalPhoneNumber'))
    _hv_dic['qualifiedProfessionalEmail'] = hvs.get(chefs_hv_param('qualifiedProfessionalEmail'))
    _hv_dic['signaturerFirstAndLastName'] = hvs.get(chefs_hv_param('signaturerFirstAndLastName'))
    _hv_dic['dateSigned'] = helper.convert_simple_datetime_format_in_str(hvs.get(chefs_hv_param('dateSigned')))
    _hv_dic['createAt'] = helper.get_create_date(hvs, chefs_hv_param('form'), chefs_hv_param('createdAt'))
    _hv_dic['confirmationId'] = _confirmation_id
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
        # reverse-convert name to id for searching key
        _rd_key = [k for k, v in constant.REGIONAL_DISTRICT_NAME_DIC.items() if v == _rd]
        if len(_rd_key) > 0:
          if _rd_key[0] in reg_dist_dic:
            reg_dist_dic[_rd_key[0]].append(_dic_copy)
          else:
            reg_dist_dic[_rd_key[0]] = [_dic_copy]

# iterate through the submissions and send an email
# only send emails for sites that are new (don't resend for old sites)
def send_email_subscribers(today):
  notify_soil_reloc_subscriber_dic = {}
  notify_hvs_subscriber_dic = {}
  unsubscribers_dic = {}

  for _subscriber in subscribersJson:
    #print(_subscriber)
    _subscriber_email = None
    _subscriber_regional_district = []
    _unsubscribe = False
    _notify_hvs = False
    _notify_soil_reloc = False
    _subscription_created_at = None
    _subscription_confirm_id = None

    if _subscriber.get("emailAddress") is not None : _subscriber_email = _subscriber["emailAddress"]
    if _subscriber.get("regionalDistrict") is not None : _subscriber_regional_district = _subscriber["regionalDistrict"] 
    if _subscriber.get("unsubscribe") is not None :
      if (_subscriber["unsubscribe"]).get("unsubscribe") is not None :
        if helper.is_boolean(_subscriber["unsubscribe"]["unsubscribe"]):
            _unsubscribe = _subscriber["unsubscribe"]["unsubscribe"]

    if _subscriber.get("notificationSelection") is not None : 
      _notice_selection = _subscriber["notificationSelection"]
      if _notice_selection.get('notifyOnHighVolumeSiteRegistrationsInSelectedRegionalDistrict') is not None:
        if helper.is_boolean(_notice_selection['notifyOnHighVolumeSiteRegistrationsInSelectedRegionalDistrict']):
          _notify_hvs = _notice_selection['notifyOnHighVolumeSiteRegistrationsInSelectedRegionalDistrict']
      if _notice_selection.get('notifyOnSoilRelocationsInSelectedRegionalDistrict') is not None:
        if helper.is_boolean(_notice_selection['notifyOnSoilRelocationsInSelectedRegionalDistrict']):
          _notify_soil_reloc = _notice_selection['notifyOnSoilRelocationsInSelectedRegionalDistrict']

    _subscription_created_at = helper.get_create_date(_subscriber, 'form', 'createdAt')
    _subscription_confirm_id = helper.get_confirm_id(_subscriber, 'form', 'confirmationId')  

    if (_subscriber_email is not None and _subscriber_email.strip() != '' and
        _subscriber_regional_district is not None and len(_subscriber_regional_district) > 0 and
        not _unsubscribe and 
        (
          _notify_hvs or
          _notify_soil_reloc
        )):

      # Notification of soil relocation in selected Regional District(s)  =========================================================
      if _notify_soil_reloc:
        for _srd in _subscriber_regional_district:

          # finding if subscriber's regional district in receiving site registration
          _rcv_sites_in_rd = rcvRegDistDic.get(_srd)

          if _rcv_sites_in_rd is not None:
            for _receiving_site_dic in _rcv_sites_in_rd:

              #print('today:',today,',created at:',_receivingSiteDic['createAt'],'confirm Id:',_receivingSiteDic['confirmationId'])
              # comparing the submission create date against the current script runtime. 
              _diff = helper.get_difference_datetimes_in_hour(today, _receiving_site_dic['createAt'])
              if (_diff is not None and _diff <= 24):  #within the last 24 hours.
                _rcv_popup_links = create_popup_links(_rcv_sites_in_rd, 'SR')
                _reg_dis_name = convert_regional_district_to_name(_srd)
                _email_msg = create_site_relocation_email_msg(_reg_dis_name, _rcv_popup_links)

                # create soil relocation notification substriber dictionary
                # key-Tuple of email address, RegionalDistrict Tuple, value=Tuple of email maessage, subscription create date, subscription confirm id
                if (_subscriber_email,_srd) not in notify_soil_reloc_subscriber_dic:
                  notify_soil_reloc_subscriber_dic[(_subscriber_email,_srd)] = (_email_msg, _subscription_created_at, _subscription_confirm_id)
                  #print("notifySoilRelocSubscriberDic added email:" + _subscriberEmail+ ', region:' + _srd + ', confirm id:' 
                  #      + str(_subscription_confirm_id) + ', subscription created at:' + str(_subscription_created_at))
                else:
                  _subscrb_created = notify_soil_reloc_subscriber_dic.get((_subscriber_email,_srd))[1]
                  if (_subscription_created_at is not None and _subscription_created_at > _subscrb_created):
                    notify_soil_reloc_subscriber_dic.update({(_subscriber_email,_srd):(_email_msg, _subscription_created_at, _subscription_confirm_id)})
                    #print("notifySoilRelocSubscriberDic updated email:" + _subscriberEmail+ ', region:' + _srd + ', confirm id:' 
                    #      + str(_subscription_confirm_id) + ', subscription created at:' + str(_subscription_created_at))

      # Notification of high volume site registration in selected Regional District(s) ============================================
      if _notify_hvs:
        for _srd in _subscriber_regional_district:

          # finding if subscriber's regional district in high volume receiving site registration
          _hv_sites_in_rd = hvRegDistDic.get(_srd)

          if _hv_sites_in_rd is not None:
            for _hv_site_dic in _hv_sites_in_rd:

              #print('today:',today,',created at:',_hvSiteDic['createAt'],'confirm Id:',_hvSiteDic['confirmationId'])
              # comparing the submission create date against the current script runtime.             
              _diff = helper.get_difference_datetimes_in_hour(today, _hv_site_dic['createAt'])
              if (_diff is not None and _diff <= 24):  #within the last 24 hours.
                _hv_popup_links = create_popup_links(_hv_sites_in_rd, 'HV')
                _hv_reg_dis = convert_regional_district_to_name(_srd)
                _hv_email_msg = create_hv_site_email_msg(_hv_reg_dis, _hv_popup_links)

                # create high volume relocation notification substriber dictionary
                # key-Tuple of email address, RegionalDistrict Tuple, value=Tuple of email maessage, subscription create date, subscription confirm id
                if (_subscriber_email,_srd) not in notify_hvs_subscriber_dic:
                  notify_hvs_subscriber_dic[(_subscriber_email,_srd)] = (_hv_email_msg, _subscription_created_at, _subscription_confirm_id)
                  #print("notifyHVSSubscriberDic added email:" + _subscriberEmail+ ', region:' + _srd + ', confirm id:' 
                  #      + str(_subscription_confirm_id) + ', subscription created at:' + str(_subscription_created_at))
                else:
                  _subscrb_created = notify_hvs_subscriber_dic.get((_subscriber_email,_srd))[1]
                  if (_subscription_created_at is not None and _subscription_created_at > _subscrb_created):
                    notify_hvs_subscriber_dic.update({(_subscriber_email,_srd):(_hv_email_msg, _subscription_created_at, _subscription_confirm_id)})
                    #print("notifyHVSSubscriberDic updated email:" + _subscriberEmail+ ', region:' + _srd + ', confirm id:' 
                    #    + str(_subscription_confirm_id) + ', subscription created at:' + str(_subscription_created_at))

    elif (_subscriber_email is not None and _subscriber_email.strip() != '' and
          _subscriber_regional_district is not None and len(_subscriber_regional_district) > 0 and  
          _unsubscribe):
      # create unSubscriber list
      for _srd in _subscriber_regional_district:
        if (_subscriber_email,_srd) not in unsubscribers_dic:
          unsubscribers_dic[(_subscriber_email,_srd)] = _subscription_created_at
          #print("unSubscribersDic added email:" + _subscriberEmail+ ', region:' + _srd + ', confirm id:' 
          #      + str(_subscription_confirm_id) + ', unsubscription created at:' + str(_subscription_created_at))
        else:  
          _unsubscrb_created = unsubscribers_dic.get((_subscriber_email,_srd))
          if (_subscription_created_at is not None and _subscription_created_at > _unsubscrb_created):
            unsubscribers_dic.update({(_subscriber_email,_srd):_subscription_created_at})
            #print("unSubscribersDic updated email:" + _subscriberEmail+ ', region:' + _srd + ', confirm id:' 
            #    + str( _subscription_confirm_id) + ', unsubscription created at:' + str(_subscription_created_at))

  print('Removing unsubscribers from notifyHVSSubscriberDic and notifySoilRelocSubscriberDic ...')
  # Processing of data subscribed and unsubscribed by the same email in the same region -
  # This is processed based on the most recent submission date.
  for (_k1_subscriber_email,_k2_srd), _unsubscribe_create_at in unsubscribers_dic.items():
    if (_k1_subscriber_email,_k2_srd) in notify_soil_reloc_subscriber_dic:
      _subscribe_create_at = notify_soil_reloc_subscriber_dic.get((_k1_subscriber_email,_k2_srd))[1]
      _subscribe_confirm_id = notify_soil_reloc_subscriber_dic.get((_k1_subscriber_email,_k2_srd))[2]    
      if (_unsubscribe_create_at is not None and _subscribe_create_at is not None and _unsubscribe_create_at > _subscribe_create_at):
        notify_soil_reloc_subscriber_dic.pop(_k1_subscriber_email,_k2_srd)
        #print("remove subscription from notifySoilRelocSubscriberDic - email:" + _k1_subscriberEmail+ ', region:' 
        #      + _k2_srd + ', confirm id:' +str( _subscription_confirm_id) + ', unsubscription created at:' + str(_unsubscribe_create_at))

    if (_k1_subscriber_email,_k2_srd) in notify_hvs_subscriber_dic:
      _subscribe_create_at = notify_hvs_subscriber_dic.get((_k1_subscriber_email,_k2_srd))[1]
      _subscribe_confirm_id = notify_hvs_subscriber_dic.get((_k1_subscriber_email,_k2_srd))[2]        
      if (_unsubscribe_create_at is not None and _subscribe_create_at is not None and _unsubscribe_create_at > _subscribe_create_at):
        notify_hvs_subscriber_dic.pop((_k1_subscriber_email,_k2_srd))
        #print("remove subscription from notifyHVSSubscriberDic - email:" + _k1_subscriberEmail+ ', region:' 
        #      + _k2_srd + ', confirm id:' +str( _subscribe_confirm_id) + ', unsubscription created at:' + str(_unsubscribe_create_at))


  print('Sending Notification of soil relocation in selected Regional District(s) ...')
  for _k, _v in notify_soil_reloc_subscriber_dic.items(): #key:(subscriber email, regional district), value:email message, subscription create date, subscription confirm id)
    _ches_response = helper.send_mail(_k[0], constant.EMAIL_SUBJECT_SOIL_RELOCATION, _v[0])
    if _ches_response is not None and _ches_response.status_code is not None:
      print("[INFO] CHEFS Email response: " + str(_ches_response.status_code) + ", subscriber email: " + _k[0])

  print('Sending Notification of high volume site registration in selected Regional District(s) ...')
  for _k, _v in notify_hvs_subscriber_dic.items(): #key:(subscriber email, regional district), value:email message, subscription create date, subscription confirm id)
    _ches_response = helper.send_mail(_k[0], constant.EMAIL_SUBJECT_HIGH_VOLUME, _v[0])
    if _ches_response is not None and _ches_response.status_code is not None:
      print("[INFO] CHEFS Email response: " + str(_ches_response.status_code) + ", subscriber email: " + _k[0])



CHEFS_SOILS_FORM_ID = os.getenv('CHEFS_SOILS_FORM_ID')
CHEFS_SOILS_API_KEY = os.getenv('CHEFS_SOILS_API_KEY')
CHEFS_HV_FORM_ID = os.getenv('CHEFS_HV_FORM_ID')
CHEFS_HV_API_KEY = os.getenv('CHEFS_HV_API_KEY')
CHEFS_MAIL_FORM_ID = os.getenv('CHEFS_MAIL_FORM_ID')
CHEFS_MAIL_API_KEY = os.getenv('CHEFS_MAIL_API_KEY')
MAPHUB_USER = os.getenv('MAPHUB_USER')
MAPHUB_PASS = os.getenv('MAPHUB_PASS')


# Fetch all submissions from chefs API
print('Loading Submissions List...')
submissionsJson = helper.site_list(CHEFS_SOILS_FORM_ID, CHEFS_SOILS_API_KEY)
#print(submissionsJson)
print('Loading Submission attributes and headers...')
soilsAttributes = helper.fetch_columns(CHEFS_SOILS_FORM_ID, CHEFS_SOILS_API_KEY)
#print(soilsAttributes)

print('Loading High Volume Sites list...')
hvsJson = helper.site_list(CHEFS_HV_FORM_ID, CHEFS_HV_API_KEY)
#print(hvsJson)
print('Loading High Volume Sites attributes and headers...')
hvsAttributes = helper.fetch_columns(CHEFS_HV_FORM_ID, CHEFS_HV_API_KEY)
# print(hvsAttributes)

# Fetch subscribers list
print('Loading submission subscribers list...')
subscribersJson = helper.site_list(CHEFS_MAIL_FORM_ID, CHEFS_MAIL_API_KEY)
#print(subscribersJson)
print('Loading submission subscribers attributes and headers...')
subscribeAttributes = helper.fetch_columns(CHEFS_MAIL_FORM_ID, CHEFS_MAIL_API_KEY)
# print(subscribeAttributes)


print('Creating source site, receiving site records...')
sourceSites = []
receivingSites = []
rcvRegDistDic = {}
for submission in submissionsJson:
  #print('Mapping submission data to the source site...')
  _srcDic = map_source_site(submission)
  if _srcDic:
    sourceSites.append(_srcDic)

  #print('Mapping submission data to the receiving site...')  
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
  #print('Mapping hv data to the hv site...')  
  _hvDic = map_hv_site(hvs)
  if _hvDic:
    hvSites.append(_hvDic)
    add_regional_district_dic(_hvDic, hvRegDistDic)  



print('Creating soil source site CSV...')
print('>> current directory:' + os.getcwd())
with open(constant.SOURCE_CSV_FILE, 'w', encoding='UTF8', newline='') as f:
  writer = csv.DictWriter(f, fieldnames=constant.SOURCE_SITE_HEADERS)
  writer.writeheader()
  writer.writerows(sourceSites)

print('Creating soil receiving site CSV...')
with open(constant.RECEIVE_CSV_FILE, 'w', encoding='UTF8', newline='') as f:
  writer = csv.DictWriter(f, fieldnames=constant.RECEIVING_SITE_HEADERS)
  writer.writeheader()
  writer.writerows(receivingSites)

print('Creating soil high volume site CSV...')
with open(constant.HIGH_VOLUME_CSV_FILE, 'w', encoding='UTF8', newline='') as f:
  writer = csv.DictWriter(f, fieldnames=constant.HV_SITE_HEADERS)
  writer.writeheader()
  writer.writerows(hvSites)


"""
print('Connecting to AGOL GIS...')
# connect to GIS
_gis = GIS(MAPHUB_URL, username=MAPHUB_USER, password=MAPHUB_PASS)

print('Updating Soil Relocation Soruce Site CSV...')
_srcCsvItem = _gis.content.get(SRC_CSV_ID)
if _srcCsvItem is None:
  print('Error: Source Site CSV Item ID is invalid!')
else:
  _srcCsvUpdateResult = _srcCsvItem.update({}, constant.SOURCE_CSV_FILE)
  print('Updated Soil Relocation Source Site CSV successfully: ' + str(_srcCsvUpdateResult))

  print('Updating Soil Relocation Soruce Site Feature Layer...')
  _srcLyrItem = _gis.content.get(SRC_LAYER_ID)
  if _srcLyrItem is None:
    print('Error: Source Site Layter Item ID is invalid!')
  else:
    _srcFlc = FeatureLayerCollection.fromitem(_srcLyrItem)
    _srcLyrOverwriteResult = _srcFlc.manager.overwrite(constant.SOURCE_CSV_FILE)
    print('Updated Soil Relocation Source Site Feature Layer successfully: ' + json.dumps(_srcLyrOverwriteResult))


print('Updating Soil Relocation Receiving Site CSV...')
_rcvCsvItem = _gis.content.get(RCV_CSV_ID)
if _rcvCsvItem is None:
  print('Error: Receiving Site CSV Item ID is invalid!')
else:
  _rcvCsvUpdateResult = _rcvCsvItem.update({}, constant.RECEIVE_CSV_FILE)
  print('Updated Soil Relocation Receiving Site CSV successfully: ' + str(_rcvCsvUpdateResult))

  print('Updating Soil Relocation Receiving Site Feature Layer...')
  _rcvLyrItem = _gis.content.get(RCV_LAYER_ID)
  if _rcvLyrItem is None:
    print('Error: Receiving Site Layer Item ID is invalid!')
  else:    
    _rcvFlc = FeatureLayerCollection.fromitem(_rcvLyrItem)
    _rcvLyrOverwriteResult = _rcvFlc.manager.overwrite(constant.RECEIVE_CSV_FILE)
    print('Updated Soil Relocation Receiving Site Feature Layer successfully: ' + json.dumps(_rcvLyrOverwriteResult))


print('Updating High Volume Receiving Site CSV...')
_hvCsvItem = _gis.content.get(HV_CSV_ID)
if _hvCsvItem is None:
  print('Error: High Volume Receiving Site CSV Item ID is invalid!')
else:
  _hvCsvUpdateResult = _hvCsvItem.update({}, constant.HIGH_VOLUME_CSV_FILE)
  print('Updated High Volume Receiving Site CSV successfully: ' + str(_hvCsvUpdateResult))

  print('Updating High Volume Receiving Site Feature Layer...')
  _hvLyrItem = _gis.content.get(HV_LAYER_ID)
  if _hvLyrItem is None:
    print('Error: High Volume Receiving Site Layer Item ID is invalid!')
  else:      
    _hvFlc = FeatureLayerCollection.fromitem(_hvLyrItem)
    _hvLyrOverwriteResult = _hvFlc.manager.overwrite(constant.HIGH_VOLUME_CSV_FILE)
    print('Updated High Volume Receiving Site Feature Layer successfully: ' + json.dumps(_hvLyrOverwriteResult))


print('Sending subscriber emails...')
today = datetime.datetime.now(tz=pytz.timezone('Canada/Pacific'))
send_email_subscribers(today)
"""

print('Completed Soils data publishing')