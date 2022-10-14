# pylint: disable=line-too-long
"""
Functions to need to execute  chefs_soil.py
"""
import json
import os
import copy
import datetime
import re
import configparser
from pytz import timezone
import requests
from requests.auth import HTTPBasicAuth
import constant

CHES_API_OAUTH_SECRET = os.getenv('CHES_API_OAUTH_SECRET')

def read_config():
    """Read configuration information to access AGOL and CHES"""
    _config = configparser.ConfigParser()
    _config.read('configurations.ini')
    return _config

config = read_config()
CHEFS_API_URL = config['COMMON_SERVICES']['CHEFS_API_URL']
AUTH_URL = config['COMMON_SERVICES']['AUTH_URL']
CHES_URL = config['COMMON_SERVICES']['CHES_URL']

def convert_deciaml_lat_long(lat_deg, lat_min, lat_sec, lon_deg, lon_min, lon_sec):
    """Convert to DD in mapLatitude and mapLongitude"""
    _lat_dd = 0
    _lon_dd = 0
    try:
        if (lat_deg is not None and lat_deg != '' and
            lat_min is not None and lat_min != '' and
            lat_sec is not None and lat_sec != '' and
            lon_deg is not None and lon_deg != '' and
            lon_min is not None and lon_min != '' and
            lon_sec is not None and lon_sec != ''
        ):
            # extract floating number from text
            _lat_deg = re.findall(constant.EXP_EXTRACT_FLOATING, lat_deg)
            _lat_min = re.findall(constant.EXP_EXTRACT_FLOATING, lat_min)
            _lat_sec = re.findall(constant.EXP_EXTRACT_FLOATING, lat_sec)
            _lon_deg = re.findall(constant.EXP_EXTRACT_FLOATING, lon_deg)
            _lon_min = re.findall(constant.EXP_EXTRACT_FLOATING, lon_min)
            _lon_sec = re.findall(constant.EXP_EXTRACT_FLOATING, lon_sec)

            if (len(_lat_deg) > 0 and len(_lat_min) > 0 and len(_lat_sec) > 0 
                and len(_lon_deg) > 0 and len(_lon_min) > 0 and len(_lon_sec) > 0):
                _lat_dd = (float(_lat_deg[0]) + float(_lat_min[0])/60 + float(_lat_sec[0])/(60*60))
                _lon_dd = - (float(_lon_deg[0])
                            + float(_lon_min[0])/60 + float(_lon_sec[0])/(60*60))

            if _lon_dd > 0:
                _lon_dd = - _lon_dd # longitude degrees should be minus in BC bouding box

    except ValueError as _ve:
        print(constant.VALUE_ERROR_EXCEPTION_RAISED, _ve)

    return _lat_dd, _lon_dd

def validate_lat_lon(
    lat_deg, lat_min, lat_sec, lon_deg,
    lon_min, lon_sec, confirmation_id, form_name):
    """Validate if coordinates are within BC bounds"""
    _lat_dd, _lon_dd = convert_deciaml_lat_long(
                        lat_deg, lat_min, lat_sec, lon_deg, lon_min, lon_sec)
    if (_lat_dd is not None and _lat_dd != 0 and
        _lon_dd is not None and _lon_dd != 0 and
        _lat_dd >= 48.30 and _lat_dd <= 60.00 and
        _lon_dd >=-139.06 and _lon_dd <= -114.02):
        return True
    print("[INFO] Can't publish data to AGOL due to Invalidate site coordinates - Latitude(deg/min/sec):",
          _lat_dd,"(",lat_deg,"/",lat_min,"/",lat_sec,"), Longitude(deg/min/sec):",
          _lon_dd,"(",lon_deg,"/",lon_min,"/",lon_sec,"), Confirm ID:",confirmation_id
                  ,", Form:",form_name)
    return False

def is_boolean(obj):
    """Check if boolen type is"""
    return True if isinstance(obj, bool) else False

def send_mail(to_email, subject, message):
    """Send email via CHES API"""
    ches_response = None
    try:
        auth_pay_load = 'grant_type=client_credentials'
        auth_headers = {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Authorization': 'Basic ' + CHES_API_OAUTH_SECRET
        }
        auth_response = requests.request("POST", AUTH_URL +
          '/auth/realms/jbd6rnxw/protocol/openid-connect/token',
          headers=auth_headers, data=auth_pay_load)
        auth_response_json = json.loads(auth_response.content)
        if auth_response_json.get('access_token'):
            access_token = auth_response_json['access_token']

            from_email = "donotreplySRIS@gov.bc.ca"
            ches_pay_load = "{\n \"bodyType\": \"html\",\n \"body\": \""+message+"\",\n \"delayTS\": 0,\n \"encoding\": \"utf-8\",\n \"from\": \""+from_email+"\",\n \"priority\": \"normal\",\n  \"subject\": \""+subject+"\",\n  \"to\": [\""+to_email+"\"]\n }\n"
            ches_headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + access_token
            }
            ches_response = requests.request("POST", CHES_URL +
              '/api/v1/email', headers=ches_headers, data=ches_pay_load)
        else:
            raise KeyError(auth_response_json.get('error_description') + ", "
                + auth_response_json.get('error') + ", status code:"
                + str(auth_response.status_code) + ", reason:"+ auth_response.reason)
    except KeyError as _ke:
        print("[ERROR] The email could not be sent due to an authorization issue. (" , _ke , ")")
    return ches_response

def site_list(form_id, form_key):
    """Retrieve CHEFS form data via CHEFS API"""
    request = requests.get(CHEFS_API_URL + '/forms/' + form_id + '/export?format=json&type=submissions', auth=HTTPBasicAuth(form_id, form_key), headers={'Content-type': 'application/json'})
    # print('Parsing JSON response')
    content = json.loads(request.content)
    return content

def fetch_columns(form_id, form_key):
    """Retrieve CHEFS form columns"""
    request = requests.get(CHEFS_API_URL + '/forms/' + form_id + '/versions', auth=HTTPBasicAuth(form_id, form_key), headers={'Content-type': 'application/json'})
    request_json = json.loads(request.content)
    version = request_json[0]['id']

    attribute_request = requests.get(CHEFS_API_URL + '/forms/' + form_id + '/versions/' + version + '/fields', auth=HTTPBasicAuth(form_id, form_key), headers={'Content-type': 'application/json'})
    attributes = json.loads(attribute_request.content)
    return attributes

def get_difference_datetimes_in_hour(datetime1, datetime2):
    """Calculates and returns the difference between two given dates/times in hours"""
    _diff = None
    if datetime1 is not None and datetime2 is not None:
        _diff = (datetime1 - datetime2).total_seconds() / 60 / 60 #difference in hour
        #print('difference datetimes in hour:',_diff)
    return _diff

def get_create_date(cefs_dic, form_field, create_at_field):
    """Returns create at field value in forms"""
    _created_at = None
    if cefs_dic.get(form_field) is not None :
        _created_at = cefs_dic.get(form_field).get(create_at_field)
        if _created_at is not None:
            #print('the supported timezones by the pytz module:', pytz.all_timezones, '\n')
            _created_at = datetime.datetime.strptime(_created_at, '%Y-%m-%dT%H:%M:%S.%f%z') #convert string to datetime with timezone(UTC)
            _created_at = _created_at.astimezone(timezone('Canada/Pacific'))  #convert to PST
    return _created_at

def get_confirm_id(cefs_dic, form_field, confirm_id_field):
    """Returns confirmation ID field value in forms"""
    _confirmation_id = None
    if cefs_dic.get(form_field) is not None :
        _confirmation_id = cefs_dic.get(form_field).get(confirm_id_field)
    return _confirmation_id

def convert_simple_datetime_format_in_str(str_date):
    """
    Convert and returns simple datetime format
    str_date: '2022-09-22T00:00:00-07:00' or '09/02/2022' format
    return: 'MM/DD/YYYY' string format
    """
    _result = None
    try:
        if str_date is not None and str_date != '':
            _datetime_in_str = str_date.split('T')
            if len(_datetime_in_str) > 1:
                _result = datetime.datetime.strptime(_datetime_in_str[0],
                            '%Y-%m-%d').strftime('%m/%d/%Y')
    except ValueError as _ve:
        print(constant.VALUE_ERROR_EXCEPTION_RAISED, _ve)
    return _result if _result is not None else str_date

def isfloat(value):
    """Check if the given value is double type value"""
    try:
        float(value)
        return True
    except ValueError:
        return False

def extract_floating_from_string(value):
    """Extract floating number from text"""
    _result = 0
    try:
        if (value is not None and value != ''):
            _exp_result = re.findall(constant.EXP_EXTRACT_FLOATING, value)
            if isinstance(_exp_result, list) and len(_exp_result) > 0:
                _result = _exp_result[0]

    except ValueError as _ve:
        print(constant.VALUE_ERROR_EXCEPTION_RAISED, _ve)

    return _result
def str_to_double(obj):
    """Convert string to double type value"""
    return float(obj) if isinstance(obj, str) else obj

def is_not_none_true(val):
    """Returns boolen value(True or Falue) if the given value is not none and boolean value type"""
    if val is not None and is_boolean(val):
        return val
    else:
        return False

def chefs_rcv_param(key, rcv_clz):
    """
    Returns receiver parameter name that matching in receiver dictionary
    according to receiver classfication(1st, 2nd, 3rd receiver)
    """
    if rcv_clz == 1: # 1st receiver
        name = constant.CHEFS_RCV1_PARAM_DIC.get(key)
    elif rcv_clz == 2: # 2nd receiver
        name = constant.CHEFS_RCV2_PARAM_DIC.get(key)
    elif rcv_clz == 3: # 3rd receiver
        name = constant.CHEFS_RCV3_PARAM_DIC.get(key)

    if name is not None:
        return name
    else:
        return key

def chefs_hv_param(key):
    """
    Returns high volume site parameter name that matching in hv dictionary
    """
    name = constant.CHEFS_HV_PARAM_DIC.get(key)
    if name is not None:
        return name
    else:
        return key

def validate_additional_rcv_site(chefs_dic, rcv_clz):
    """
    in case of 2nd or 3rd receivers,
    check if the given fields exists that to see
    additional receiver information is provided
    """
    if rcv_clz == 2 or rcv_clz == 3:
        return is_not_none_true(chefs_dic.get(chefs_rcv_param('additionalRcvSite', 
              rcv_clz)).get(chefs_rcv_param('additionalRcvInformation', rcv_clz)))
    else:
        return True

def chefs_src_param(key):
    """
    Returns source site parameter name that matching in hv dictionary
    """
    name = constant.CHEFS_SOURCE_PARAM_DIC.get(key)
    if name is not None:
        return name
    else:
        return key

def convert_regional_district_to_name(key):
    """"Returns regional district name matching with the given key in regional district dictionay"""
    name = constant.REGIONAL_DISTRICT_NAME_DIC.get(key)
    if name is not None:
        return name
    else:
        return key

def convert_source_site_use_to_name(key):
    """Returns source site use name matching with the given key in source site use dictionay"""
    name = constant.SOURCE_SITE_USE_NAME_DIC.get(key)
    if name is not None:
        return name
    else:
        return key

def convert_receiving_site_use_to_name(key):
    """
    Returns receiving site use name matching with the given key in
    receiving site use dictionay
    """
    name = constant.RECEIVING_SITE_USE_NAME_DIC.get(key)
    if name is not None:
        return name
    else:
        return key

def convert_soil_quality_to_name(key):
    """
    Returns soil quality name matching with the given key in
    soil quality dictionay
    """
    name = constant.SOIL_QUALITY_NAME_DIC.get(key)
    if name is not None:
        return name
    else:
        return key

def create_receiving_site_lan_uses(chefs_dic, field):
    """
    Extract "receiving site lan uses" value from form
    (in case of multiple data, they are joined with comma)
    """
    _land_uses = []
    for _key, _value in chefs_dic[field].items():
        if is_not_none_true(_value):
            _land_uses.append(convert_receiving_site_use_to_name(_key))
    if len(_land_uses) > 0:
        _land_uses = "\"" + ",".join(_land_uses) + "\""
    return _land_uses

def create_regional_district(chefs_dic, field):
    """
    Extract only first "regional district" value from form
    """
    _regional_district = None
    if chefs_dic.get(field) is not None and len(chefs_dic[field]) > 0:
        _regional_district = convert_regional_district_to_name(chefs_dic[field][0])
    return _regional_district

def convert_land_ownership_to_name(key):
    """
    Returns land ownership name matching with the given key in
    land ownership dictionay
    """
    name = constant.LAND_OWNERSHIP_NAME_DIC.get(key)
    if name is not None:
        return name
    else:
        return key

def create_land_ownership(chefs_dic, field):
    """
    Extract "land ownership" value from form
    """
    _land_ownership = None
    if chefs_dic.get(field) is not None :
        _land_ownership = convert_land_ownership_to_name(chefs_dic[field])
    return _land_ownership

def create_land_file_numbers(chefs_dic, field):
    """
    Extract "land file numbers" value from form
    (in case of multiple data, they are joined with comma)
    """
    _land_file_numbers = []
    if chefs_dic.get(field) is not None : 
        for _item in chefs_dic[field]:
            for _v in _item.values():
                if _v != '':
                    _land_file_numbers.append(_v)

    if len(_land_file_numbers) > 0:
        _land_file_numbers = "\"" + ",".join(_land_file_numbers) + "\""   # could be more than one

    return _land_file_numbers if len(_land_file_numbers) > 0 else None

def create_pid_pin_and_desc(chefs_dic, data_grid_field, pid_pin_field, desc_field):
    """
    Extract only first "PID and description" or "PIN and description" value from form
    """
    _pid = None
    _desc = None
    if chefs_dic.get(data_grid_field) is not None and len(chefs_dic[data_grid_field]) > 0:
        if chefs_dic.get(data_grid_field)[0].get(pid_pin_field) is not None and chefs_dic.get(data_grid_field)[0].get(pid_pin_field).strip() != '':
            _pid = chefs_dic.get(data_grid_field)[0].get(pid_pin_field)
            if _pid is not None and chefs_dic.get(data_grid_field)[0].get(desc_field) and chefs_dic.get(data_grid_field)[0].get(desc_field).strip() != '':
                _desc = chefs_dic.get(data_grid_field)[0].get(desc_field).strip()
    return _pid, _desc

def create_untitled_municipal_land_desc(chefs_dic, parent_field, desc_field):
    """
    Extract only first "Untitled Municipal Land Description" value from form
    """
    _desc = None
    if chefs_dic.get(parent_field) is not None and len(chefs_dic.get(parent_field)) > 0:
        if chefs_dic[parent_field][0].get(desc_field) is not None and chefs_dic[parent_field][0].get(desc_field).strip() != '':
            _desc = chefs_dic[parent_field][0].get(desc_field).strip()
    return _desc

def create_soil_volumes(chefs_dic, data_grid, volume_field, claz_field, working_dic):
    """
    Extract "Soil Volume" value from form
    to be volume/quality pairs,
    1.create a column in the CSV for each soil quality type
    2.add the sum of that quality type to the column
    3.add a totalVolume column that sums all soil volumes by quality type
    """
    _total_soil_volume = 0
    _soil_volume = 0
    if chefs_dic.get(data_grid) is not None and len(chefs_dic[data_grid]) > 0: 
        for _dg9 in chefs_dic[data_grid]:
            if (_dg9.get(volume_field) is not None
                and _dg9.get(claz_field) is not None and len(_dg9.get(claz_field)) > 0): 
                _soil_volume = _dg9[volume_field]
                if not isfloat(_soil_volume):
                    _soil_volume = extract_floating_from_string(_soil_volume)
                _soil_volume = str_to_double(_soil_volume)
                _soil_claz = _dg9.get("B1-soilClassificationSource")
                if is_not_none_true(_soil_claz.get("urbanParkLandUsePl")):
                    working_dic['urbanParkLandUseSoilVolume'] = working_dic['urbanParkLandUseSoilVolume'] + _soil_volume if working_dic['urbanParkLandUseSoilVolume'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("commercialLandUseCl")):
                    working_dic['commercialLandUseSoilVolume'] = working_dic['commercialLandUseSoilVolume'] + _soil_volume if working_dic['commercialLandUseSoilVolume'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("industrialLandUseIl")):
                    working_dic['industrialLandUseSoilVolume'] = working_dic['industrialLandUseSoilVolume'] + _soil_volume if working_dic['industrialLandUseSoilVolume'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("agriculturalLandUseAl")):
                    working_dic['agriculturalLandUseSoilVolume'] = working_dic['agriculturalLandUseSoilVolume'] + _soil_volume if working_dic['agriculturalLandUseSoilVolume'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("wildlandsNaturalLandUseWln")):
                    working_dic['wildlandsNaturalLandUseSoilVolume'] = working_dic['wildlandsNaturalLandUseSoilVolume'] + _soil_volume if working_dic['wildlandsNaturalLandUseSoilVolume'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("wildlandsRevertedLandUseWlr")):
                    working_dic['wildlandsRevertedLandUseSoilVolume'] = working_dic['wildlandsRevertedLandUseSoilVolume'] + _soil_volume if working_dic['wildlandsRevertedLandUseSoilVolume'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("residentialLandUseLowDensityRlld")):
                    working_dic['residentialLandUseLowDensitySoilVolume'] = working_dic['residentialLandUseLowDensitySoilVolume'] + _soil_volume if working_dic['residentialLandUseLowDensitySoilVolume'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("residentialLandUseHighDensityRlhd")):
                    working_dic['residentialLandUseHighDensitySoilVolume'] = working_dic['residentialLandUseHighDensitySoilVolume'] + _soil_volume if working_dic['residentialLandUseHighDensitySoilVolume'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
        if _total_soil_volume != 0:
            working_dic['totalSoilVolme'] = _total_soil_volume

def add_regional_district_dic(site_dic, reg_dist_dic):
    """
    Add Regional Districts in site forms to dictionary
    - key:regional district string / value:site data dictionary
    """
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
