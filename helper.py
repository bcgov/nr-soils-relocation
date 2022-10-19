# pylint: disable=line-too-long
# pylint: disable=no-member
"""
Functions to need to execute  chefs_soil.py
"""
import json
import os
import copy
import datetime
import re
import configparser
import logging
from pytz import timezone
import pytz
import requests
from requests.auth import HTTPBasicAuth
from jinja2 import Environment, select_autoescape, FileSystemLoader
import constant

WEB_MAP_APP_ID = os.getenv('WEB_MAP_APP_ID')
CHEFS_MAIL_FORM_ID = os.getenv('CHEFS_MAIL_FORM_ID')
CHES_API_OAUTH_SECRET = os.getenv('CHES_API_OAUTH_SECRET')
CHEFS_API_URL = os.getenv('CHEFS_API_URL')
AUTH_URL = os.getenv('AUTH_URL')
CHES_URL = os.getenv('CHES_URL')
LOGLEVEL = os.getenv('LOGLEVEL')

logging.basicConfig(level=LOGLEVEL)

def read_config():
    """Read configuration information to access AGOL and CHES"""
    _config = configparser.ConfigParser()
    _config.read('configurations.ini')
    return _config

config = read_config()
WEBMAP_POPUP_URL = config['AGOL']['WEBMAP_POPUP_URL']


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
        logging.exception(constant.VALUE_ERROR_EXCEPTION_RAISED, _ve)

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
    logging.warning("Can't publish data to AGOL due to invalidate site coordinates - Latitude(deg/min/sec):%s(%s/%s,%s), Longitude(deg/min/sec):%s(%s/%s/%s), Confirm ID:%s, Form:%s"
    , _lat_dd, lat_deg, lat_min, lat_sec, _lon_dd, lon_deg, lon_min, lon_sec, confirmation_id, form_name)
    return False

def is_boolean(obj):
    """Check if boolen type is"""
    return True if isinstance(obj, bool) else False

def get_ches_token():
    """"Get GHES Token"""
    _auth_response = None
    try:
        _auth_pay_load = 'grant_type=client_credentials'
        _auth_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + CHES_API_OAUTH_SECRET
        }
        _ches_token_enpont = AUTH_URL + '/auth/realms/jbd6rnxw/protocol/openid-connect/token'
        _auth_response = requests.request("POST", _ches_token_enpont, headers=_auth_headers, data=_auth_pay_load)
        _auth_response_json = json.loads(_auth_response.content)
        if _auth_response_json.get('access_token'):
            return _auth_response_json['access_token']
        else:
            raise KeyError(_auth_response_json.get('error_description') + ", "
                + _auth_response_json.get('error') + ", status code:"
                + str(_auth_response.status_code) + ", reason:"+ _auth_response.reason)
    except KeyError as _ke:
        logging.exception("Email could not be sent due to an authorization issue:%s", _ke)
    return _auth_response

def check_ches_health():
    """Returns health checks of external service dependencies"""
    _access_token = get_ches_token()
    ches_headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + _access_token
    }
    _ches_api_health_endpoint = CHES_URL + '/api/v1/health'
    _ches_response = requests.request("GET", _ches_api_health_endpoint, headers=ches_headers)
    if _ches_response.status_code == 200:
        logging.info(constant.CHES_HEALTH_200_STATUS)
    elif _ches_response.status_code == 401:
        logging.error(constant.CHES_HEALTH_401_STATUS)
    elif _ches_response.status_code == 403:
        logging.error(constant.CHES_HEALTH_403_STATUS)
    else:
        logging.error("CHES Health returned staus code:%s, text:%s", str(_ches_response.status_code), _ches_response.text)

def send_single_email(to_email, subject, message):
    """Send email via CHES API"""
    _ches_response = None
    _access_token = get_ches_token()
    if _access_token is not None:
        from_email = constant.EMAIL_SENDER_ADDRESS
        ches_pay_load = "{\n \"bodyType\": \"html\",\n \"body\": \""+message+"\",\n \"delayTS\": 0,\n \"encoding\": \"utf-8\",\n \"from\": \""+from_email+"\",\n \"priority\": \"normal\",\n  \"subject\": \""+subject+"\",\n  \"to\": [\""+to_email+"\"]\n }\n"
        ches_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + _access_token
        }
        _ches_api_single_email_endpoint = CHES_URL + '/api/v1/email'
        _ches_response = requests.request("POST", _ches_api_single_email_endpoint, headers=ches_headers, data=ches_pay_load)
    return _ches_response

def site_list(form_id, form_key):
    """Retrieve CHEFS form data via CHEFS API"""
    request = requests.get(CHEFS_API_URL + '/forms/' + form_id + '/export?format=json&type=submissions', auth=HTTPBasicAuth(form_id, form_key), headers={'Content-type': 'application/json'})
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
        logging.debug("difference datetimes in hour:%s", _diff)
    return _diff

def get_create_date(cefs_dic, form_field, create_at_field):
    """Returns create at field value in forms"""
    _created_at = None
    if cefs_dic.get(form_field) is not None :
        _created_at = cefs_dic.get(form_field).get(create_at_field)
        if _created_at is not None:
            logging.debug("The supported timezones by the pytz module:%s\n", pytz.all_timezones)
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
                _result = datetime.datetime.strptime(_datetime_in_str[0], '%Y-%m-%d').strftime('%m/%d/%Y')
    except ValueError as _ve:
        logging.exception(constant.VALUE_ERROR_EXCEPTION_RAISED, _ve)
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
        logging.exception(constant.VALUE_ERROR_EXCEPTION_RAISED, _ve)

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
                    working_dic['urbanParkLandUseSoilVolume'] = working_dic['urbanParkLandUseSoilVolume'] + _soil_volume \
                        if working_dic['urbanParkLandUseSoilVolume'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("commercialLandUseCl")):
                    working_dic['commercialLandUseSoilVolume'] = working_dic['commercialLandUseSoilVolume'] + _soil_volume \
                        if working_dic['commercialLandUseSoilVolume'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("industrialLandUseIl")):
                    working_dic['industrialLandUseSoilVolume'] = working_dic['industrialLandUseSoilVolume'] + _soil_volume \
                        if working_dic['industrialLandUseSoilVolume'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("agriculturalLandUseAl")):
                    working_dic['agriculturalLandUseSoilVolume'] = working_dic['agriculturalLandUseSoilVolume'] + _soil_volume \
                        if working_dic['agriculturalLandUseSoilVolume'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("wildlandsNaturalLandUseWln")):
                    working_dic['wildlandsNaturalLandUseSoilVolume'] = working_dic['wildlandsNaturalLandUseSoilVolume'] + _soil_volume \
                        if working_dic['wildlandsNaturalLandUseSoilVolume'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("wildlandsRevertedLandUseWlr")):
                    working_dic['wildlandsRevertedLandUseSoilVolume'] = working_dic['wildlandsRevertedLandUseSoilVolume'] + _soil_volume \
                        if working_dic['wildlandsRevertedLandUseSoilVolume'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("residentialLandUseLowDensityRlld")):
                    working_dic['residentialLandUseLowDensitySoilVolume'] = working_dic['residentialLandUseLowDensitySoilVolume'] + _soil_volume \
                        if working_dic['residentialLandUseLowDensitySoilVolume'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("residentialLandUseHighDensityRlhd")):
                    working_dic['residentialLandUseHighDensitySoilVolume'] = working_dic['residentialLandUseHighDensitySoilVolume'] + _soil_volume \
                        if working_dic['residentialLandUseHighDensitySoilVolume'] is not None else _soil_volume
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

def get_popup_search_value(_site_dic):
    """Returns popup search value"""
    if _site_dic['SID'] is not None and _site_dic['SID'].strip() != '':
        return _site_dic['SID']
    elif _site_dic['PID'] is not None and _site_dic['PID'].strip() != '':
        return _site_dic['PID']
    elif _site_dic['PIN'] is not None and _site_dic['PIN'].strip() != '':
        return _site_dic['PIN']
    elif _site_dic['latitude'] is not None and _site_dic['longitude'] is not None:
        return str(_site_dic['latitude'])+','+str(_site_dic['latitude']) #Site lat/lon
    elif _site_dic['ownerAddress'] is not None and _site_dic['ownerAddress'].strip() != '':
        return _site_dic['ownerAddress'] #Site Owner Address
    elif _site_dic['ownerCompany'] is not None and _site_dic['ownerCompany'].strip() != '':
        return _site_dic['ownerCompany']  #Site Owner Company

def create_popup_links(sites):
    """Create and returns popup hyper link """
    _popup_links = []
    if sites is not None:
        for _site_dic in sites:
            _srch_val = get_popup_search_value(_site_dic)
            if get_popup_search_value(_site_dic):
                _link = WEBMAP_POPUP_URL + '?id=' + WEB_MAP_APP_ID + '&find=' + _srch_val
                _popup_links.append({'href':_link})
    return _popup_links

def create_template_email(template, **kwargs):
    """Load the given email template and do rendering with the given arguments"""
    env = Environment(
      loader = FileSystemLoader(searchpath="./email_templates", encoding='utf-8'),
      autoescape=select_autoescape(['html', 'xml']),
      trim_blocks=True,
      lstrip_blocks=True,
      keep_trailing_newline=False
    )
    template = env.get_template(template)
    rendered_temp = template.render(**kwargs).replace('\r', '').replace('\n', '')
    return rendered_temp

def create_site_relocation_email_msg(regional_district, popup_links):
    """Create and returns Site Relocation email template filled with the given arguments"""
    return create_template_email(
      template='site_relocation_email_template.html',
      regional_district=regional_district,
      popup_links=popup_links,
      chefs_mail_form_id=CHEFS_MAIL_FORM_ID
    )

def create_hv_site_email_msg(regional_district, popup_links):
    """Create and returns HV Site email template filled with the given arguments"""
    return create_template_email(
      template='hv_site_email_template.html',
      regional_district=regional_district,
      popup_links=popup_links,
      chefs_mail_form_id=CHEFS_MAIL_FORM_ID
    )

def map_source_site(_submission):
    """Mapping source site"""
    _src_dic = {}
    _confirmation_id = get_confirm_id(_submission, chefs_src_param('form'), chefs_src_param('confirmationId'))
    if (validate_lat_lon(
        _submission.get(chefs_src_param('latitudeDegrees')),
        _submission.get(chefs_src_param('latitudeMinutes')),
        _submission.get(chefs_src_param('latitudeSeconds')),
        _submission.get(chefs_src_param('longitudeDegrees')),
        _submission.get(chefs_src_param('longitudeMinutes')),
        _submission.get(chefs_src_param('longitudeSeconds')),
        _confirmation_id,
        'Soil Relocation Notification Form-Source Site')
    ):
        logging.debug("Mapping sourece site ...")
        for src_header in constant.SOURCE_SITE_HEADERS:
            _src_dic[src_header] = None

        _src_dic['updateToPreviousForm'] = _submission.get(chefs_src_param('updateToPreviousForm'))
        _src_dic['ownerFirstName'] = _submission.get(chefs_src_param('ownerFirstName'))
        _src_dic['ownerLastName'] = _submission.get(chefs_src_param('ownerLastName'))
        _src_dic['ownerCompany'] = _submission.get(chefs_src_param('ownerCompany'))
        _src_dic['ownerAddress'] = _submission.get(chefs_src_param('ownerAddress'))
        _src_dic['ownerCity'] = _submission.get(chefs_src_param('ownerCity'))
        _src_dic['ownerProvince'] = _submission.get(chefs_src_param('ownerProvince'))
        _src_dic['ownerCountry'] = _submission.get(chefs_src_param('ownerCountry'))
        _src_dic['ownerPostalCode'] = _submission.get(chefs_src_param('ownerPostalCode'))
        _src_dic['ownerPhoneNumber'] = _submission.get(chefs_src_param('ownerPhoneNumber'))
        _src_dic['ownerEmail'] = _submission.get(chefs_src_param('ownerEmail'))
        _src_dic['owner2FirstName'] = _submission.get(chefs_src_param('owner2FirstName'))
        _src_dic['owner2LastName'] = _submission.get(chefs_src_param('owner2LastName'))
        _src_dic['owner2Company'] = _submission.get(chefs_src_param('owner2Company'))
        _src_dic['owner2Address'] = _submission.get(chefs_src_param('owner2Address'))
        _src_dic['owner2City'] = _submission.get(chefs_src_param('owner2City'))
        _src_dic['owner2Province'] = _submission.get(chefs_src_param('owner2Province'))
        _src_dic['owner2Country'] = _submission.get(chefs_src_param('owner2Country'))
        _src_dic['owner2PostalCode'] = _submission.get(chefs_src_param('owner2PostalCode'))
        _src_dic['owner2PhoneNumber'] = _submission.get(chefs_src_param('owner2PhoneNumber'))
        _src_dic['owner2Email'] = _submission.get(chefs_src_param('owner2Email'))
        _src_dic['additionalOwners'] = _submission.get(chefs_src_param('additionalOwners'))
        _src_dic['contactFirstName'] = _submission.get(chefs_src_param('contactFirstName'))
        _src_dic['contactLastName'] = _submission.get(chefs_src_param('contactLastName'))
        _src_dic['contactCompany'] = _submission.get(chefs_src_param('contactCompany'))
        _src_dic['contactAddress'] = _submission.get(chefs_src_param('contactAddress'))
        _src_dic['contactCity'] = _submission.get(chefs_src_param('contactCity'))
        _src_dic['contactProvince'] = _submission.get(chefs_src_param('contactProvince'))
        _src_dic['contactCountry'] = _submission.get(chefs_src_param('contactCountry'))
        _src_dic['contactPostalCode'] = _submission.get(chefs_src_param('contactPostalCode'))
        _src_dic['contactPhoneNumber'] = _submission.get(chefs_src_param('contactPhoneNumber'))
        _src_dic['contactEmail'] = _submission.get(chefs_src_param('contactEmail'))
        _src_dic['SID'] = _submission.get(chefs_src_param('SID'))

        _src_dic['latitude'], _src_dic['longitude'] = convert_deciaml_lat_long(
                                                    _submission[chefs_src_param('latitudeDegrees')],
                                                    _submission[chefs_src_param('latitudeMinutes')],
                                                    _submission[chefs_src_param('latitudeSeconds')],
                                                    _submission[chefs_src_param('longitudeDegrees')],
                                                    _submission[chefs_src_param('longitudeMinutes')],
                                                    _submission[chefs_src_param('longitudeSeconds')])

        _src_dic['landOwnership'] = create_land_ownership(_submission, chefs_src_param('landOwnership'))
        _src_dic['regionalDistrict'] = create_regional_district(_submission, chefs_src_param('regionalDistrict'))
        _src_dic['legallyTitledSiteAddress'] = _submission.get(chefs_src_param('legallyTitledSiteAddress'))
        _src_dic['legallyTitledSiteCity'] = _submission.get(chefs_src_param('legallyTitledSiteCity'))
        _src_dic['legallyTitledSitePostalCode'] = _submission.get(chefs_src_param('legallyTitledSitePostalCode'))
        _src_dic['crownLandFileNumbers'] = create_land_file_numbers(_submission,chefs_src_param('crownLandFileNumbers'))

        _src_dic['PID'], _src_dic['legalLandDescription'] = create_pid_pin_and_desc(
                                                            _submission,
                                                            chefs_src_param('pidDataGrid'),
                                                            chefs_src_param('pid'),
                                                            chefs_src_param('pidDesc'))  #PID
        if (_src_dic['PID'] is None or _src_dic['PID'].strip() == ''): #PIN
            _src_dic['PIN'], _src_dic['legalLandDescription'] = create_pid_pin_and_desc(
                                                                _submission,
                                                                chefs_src_param('pinDataGrid'),
                                                                chefs_src_param('pin'),
                                                                chefs_src_param('pinDesc'))
        if ((_src_dic['PID'] is None or _src_dic['PID'].strip() == '')
            and (_src_dic['PIN'] is None or _src_dic['PIN'].strip() == '')):
            #Description when selecting 'Untitled Municipal Land'
            _src_dic['legalLandDescription'] = create_untitled_municipal_land_desc(
                                                _submission,
                                                chefs_src_param('untitledMunicipalLand'),
                                                chefs_src_param('untitledMunicipalLandDesc'))

        if _submission.get(chefs_src_param('sourceSiteLandUse')) is not None and len(_submission.get(chefs_src_param('sourceSiteLandUse'))) > 0 :
            _source_site_land_uses = []
            for _ref_source_site in _submission.get(chefs_src_param('sourceSiteLandUse')):
                _source_site_land_uses.append(convert_source_site_use_to_name(_ref_source_site))
            _src_dic['sourceSiteLandUse'] = "\"" + ",".join(_source_site_land_uses) + "\""

        _src_dic['highVolumeSite'] = _submission.get(chefs_src_param('highVolumeSite'))
        _src_dic['soilRelocationPurpose'] = _submission.get(chefs_src_param('soilRelocationPurpose'))
        _src_dic['soilStorageType'] = _submission.get(chefs_src_param('soilStorageType'))

        create_soil_volumes(
            _submission,
            chefs_src_param('soilVolumeDataGrid'),
            chefs_src_param('soilVolume'),
            chefs_src_param('soilClassificationSource'),
            _src_dic)

        _src_dic['soilCharacterMethod'] = _submission.get(chefs_src_param('soilCharacterMethod'))
        _src_dic['vapourExemption'] = _submission.get(chefs_src_param('vapourExemption'))
        _src_dic['vapourExemptionDesc'] = _submission.get(chefs_src_param('vapourExemptionDesc'))
        _src_dic['vapourCharacterMethodDesc'] = _submission.get(chefs_src_param('vapourCharacterMethodDesc'))
        _src_dic['soilRelocationStartDate'] = convert_simple_datetime_format_in_str(_submission.get(chefs_src_param('soilRelocationStartDate')))
        _src_dic['soilRelocationCompletionDate'] = convert_simple_datetime_format_in_str(_submission.get(chefs_src_param('soilRelocationCompletionDate')))
        _src_dic['relocationMethod'] = _submission.get(chefs_src_param('relocationMethod'))
        _src_dic['qualifiedProfessionalFirstName'] = _submission.get(chefs_src_param('qualifiedProfessionalFirstName'))
        _src_dic['qualifiedProfessionalLastName'] = _submission.get(chefs_src_param('qualifiedProfessionalLastName'))
        _src_dic['qualifiedProfessionalType'] = _submission.get(chefs_src_param('qualifiedProfessionalType'))
        _src_dic['professionalLicenceRegistration'] = _submission.get(chefs_src_param('professionalLicenceRegistration'))
        _src_dic['qualifiedProfessionalOrganization'] = _submission.get(chefs_src_param('qualifiedProfessionalOrganization'))
        _src_dic['qualifiedProfessionalAddress'] = _submission.get(chefs_src_param('qualifiedProfessionalAddress'))
        _src_dic['qualifiedProfessionalCity'] = _submission.get(chefs_src_param('qualifiedProfessionalCity'))
        _src_dic['qualifiedProfessionalProvince'] = _submission.get(chefs_src_param('qualifiedProfessionalProvince'))
        _src_dic['qualifiedProfessionalCountry'] = _submission.get(chefs_src_param('qualifiedProfessionalCountry'))
        _src_dic['qualifiedProfessionalPostalCode'] = _submission.get(chefs_src_param('qualifiedProfessionalPostalCode'))
        _src_dic['qualifiedProfessionalPhoneNumber'] = _submission.get(chefs_src_param('qualifiedProfessionalPhoneNumber'))
        _src_dic['qualifiedProfessionalEmail'] = _submission.get(chefs_src_param('qualifiedProfessionalEmail'))
        _src_dic['signaturerFirstAndLastName'] = _submission.get(chefs_src_param('signaturerFirstAndLastName'))
        _src_dic['dateSigned'] = convert_simple_datetime_format_in_str(_submission.get(chefs_src_param('dateSigned')))
        _src_dic['createAt'] = get_create_date(_submission, chefs_src_param('form'), chefs_src_param('createdAt'))
        _src_dic['confirmationId'] = _confirmation_id
    return _src_dic

def map_rcv_site(_submission, rcv_clz):
    """Mapping receiving site"""
    _rcv_dic = {}
    _confirmation_id = get_confirm_id(
      _submission,
      chefs_rcv_param('form', rcv_clz),
      chefs_rcv_param('confirmationId', rcv_clz))
    if (validate_additional_rcv_site(_submission, rcv_clz) and
        validate_lat_lon(
          _submission.get(chefs_rcv_param('latitudeDegrees', rcv_clz)),
          _submission.get(chefs_rcv_param('latitudeMinutes', rcv_clz)),
          _submission.get(chefs_rcv_param('latitudeSeconds', rcv_clz)),
          _submission.get(chefs_rcv_param('longitudeDegrees', rcv_clz)),
          _submission.get(chefs_rcv_param('longitudeMinutes', rcv_clz)),
          _submission.get(chefs_rcv_param('longitudeSeconds', rcv_clz)),
          _confirmation_id,
          'Soil Relocation Notification Form-Receiving Site')
    ):
        for rcv_header in constant.RECEIVING_SITE_HEADERS:
            _rcv_dic[rcv_header] = None

        _rcv_dic['ownerFirstName'] = _submission.get(chefs_rcv_param('ownerFirstName', rcv_clz))
        _rcv_dic['ownerLastName'] = _submission.get(chefs_rcv_param('ownerLastName', rcv_clz))
        _rcv_dic['ownerCompany'] = _submission.get(chefs_rcv_param('ownerCompany', rcv_clz))
        _rcv_dic['ownerAddress'] = _submission.get(chefs_rcv_param('ownerAddress', rcv_clz))
        _rcv_dic['ownerCity'] = _submission.get(chefs_rcv_param('ownerCity', rcv_clz))
        _rcv_dic['ownerProvince'] = _submission.get(chefs_rcv_param('ownerProvince', rcv_clz))
        _rcv_dic['ownerCountry'] = _submission.get(chefs_rcv_param('ownerCountry', rcv_clz))
        _rcv_dic['ownerPostalCode'] = _submission.get(chefs_rcv_param('ownerPostalCode', rcv_clz))
        _rcv_dic['ownerPhoneNumber'] = _submission.get(chefs_rcv_param('ownerPhoneNumber', rcv_clz))
        _rcv_dic['ownerEmail'] = _submission.get(chefs_rcv_param('ownerEmail', rcv_clz))
        _rcv_dic['owner2FirstName'] = _submission.get(chefs_rcv_param('owner2FirstName', rcv_clz))
        _rcv_dic['owner2LastName'] = _submission.get(chefs_rcv_param('owner2LastName', rcv_clz))
        _rcv_dic['owner2Company'] = _submission.get(chefs_rcv_param('owner2Company', rcv_clz))
        _rcv_dic['owner2Address'] = _submission.get(chefs_rcv_param('owner2Address', rcv_clz))
        _rcv_dic['owner2City'] = _submission.get(chefs_rcv_param('owner2City', rcv_clz))
        _rcv_dic['owner2Province'] = _submission.get(chefs_rcv_param('owner2Province', rcv_clz))
        _rcv_dic['owner2Country'] = _submission.get(chefs_rcv_param('owner2Country', rcv_clz))
        _rcv_dic['owner2PostalCode'] = _submission.get(chefs_rcv_param('owner2PostalCode', rcv_clz))
        _rcv_dic['owner2PhoneNumber'] = _submission.get(chefs_rcv_param('owner2PhoneNumber', rcv_clz))
        _rcv_dic['owner2Email'] = _submission.get(chefs_rcv_param('owner2Email', rcv_clz))
        _rcv_dic['additionalOwners'] = _submission.get(chefs_rcv_param('additionalOwners', rcv_clz))
        _rcv_dic['contactFirstName'] = _submission.get(chefs_rcv_param('contactFirstName', rcv_clz))
        _rcv_dic['contactLastName'] = _submission.get(chefs_rcv_param('contactLastName', rcv_clz))
        _rcv_dic['contactCompany'] = _submission.get(chefs_rcv_param('contactCompany', rcv_clz))
        _rcv_dic['contactAddress'] = _submission.get(chefs_rcv_param('contactAddress', rcv_clz))
        _rcv_dic['contactCity'] = _submission.get(chefs_rcv_param('contactCity', rcv_clz))
        _rcv_dic['contactProvince'] = _submission.get(chefs_rcv_param('contactProvince', rcv_clz))
        _rcv_dic['contactCountry'] = _submission.get(chefs_rcv_param('contactCountry', rcv_clz))
        _rcv_dic['contactPostalCode'] = _submission.get(chefs_rcv_param('contactPostalCode', rcv_clz))
        _rcv_dic['contactPhoneNumber'] = _submission.get(chefs_rcv_param('contactPhoneNumber', rcv_clz))
        _rcv_dic['contactEmail'] = _submission.get(chefs_rcv_param('contactEmail', rcv_clz))
        _rcv_dic['SID'] = _submission.get(chefs_rcv_param('SID', rcv_clz))

        _rcv_dic['latitude'], _rcv_dic['longitude'] = convert_deciaml_lat_long(
                                                    _submission.get(chefs_rcv_param('latitudeDegrees', rcv_clz)),
                                                    _submission.get(chefs_rcv_param('latitudeMinutes', rcv_clz)),
                                                    _submission.get(chefs_rcv_param('latitudeSeconds', rcv_clz)),
                                                    _submission.get(chefs_rcv_param('longitudeDegrees', rcv_clz)),
                                                    _submission.get(chefs_rcv_param('longitudeMinutes', rcv_clz)),
                                                    _submission.get(chefs_rcv_param('longitudeSeconds', rcv_clz)))

        _rcv_dic['regionalDistrict'] = create_regional_district(_submission, chefs_rcv_param('regionalDistrict', rcv_clz))
        _rcv_dic['landOwnership'] = create_land_ownership(_submission, chefs_rcv_param('landOwnership', rcv_clz))
        _rcv_dic['legallyTitledSiteAddress'] = _submission.get(chefs_rcv_param('legallyTitledSiteAddress', rcv_clz))
        _rcv_dic['legallyTitledSiteCity'] = _submission.get(chefs_rcv_param('legallyTitledSiteCity', rcv_clz))
        _rcv_dic['legallyTitledSitePostalCode'] = _submission.get(chefs_rcv_param('legallyTitledSitePostalCode', rcv_clz))

        _rcv_dic['PID'], _rcv_dic['legalLandDescription'] = create_pid_pin_and_desc(
                                                            _submission,
                                                            chefs_rcv_param('pidDataGrid', rcv_clz),
                                                            chefs_rcv_param('pid', rcv_clz),
                                                            chefs_rcv_param('pidDesc', rcv_clz))  #PID
        if (_rcv_dic['PID'] is None or _rcv_dic['PID'].strip() == ''): #PIN
            _rcv_dic['PIN'], _rcv_dic['legalLandDescription'] = create_pid_pin_and_desc(
                                                                _submission,
                                                                chefs_rcv_param('pinDataGrid', rcv_clz),
                                                                chefs_rcv_param('pin', rcv_clz),
                                                                chefs_rcv_param('pinDesc', rcv_clz))
        if ((_rcv_dic['PID'] is None or _rcv_dic['PID'].strip() == '')
            and (_rcv_dic['PIN'] is None or _rcv_dic['PIN'].strip() == '')):
                  #Description when selecting 'Untitled Municipal Land'
            _rcv_dic['legalLandDescription'] = create_untitled_municipal_land_desc(
                                                _submission,
                                                chefs_rcv_param('untitledMunicipalLand', rcv_clz),
                                                chefs_rcv_param('untitledMunicipalLandDesc', rcv_clz))

        _rcv_dic['crownLandFileNumbers'] = create_land_file_numbers(
                                            _submission,
                                            chefs_rcv_param('crownLandFileNumbers', rcv_clz))
        _rcv_dic['receivingSiteLandUse'] = create_receiving_site_lan_uses(
                                            _submission,
                                            chefs_rcv_param('receivingSiteLandUse', rcv_clz))

        _rcv_dic['CSRFactors'] = _submission.get(chefs_rcv_param('CSRFactors', rcv_clz))
        _rcv_dic['relocatedSoilUse'] = _submission.get(chefs_rcv_param('relocatedSoilUse', rcv_clz))
        _rcv_dic['highVolumeSite'] = _submission.get(chefs_rcv_param('highVolumeSite', rcv_clz))
        _rcv_dic['soilDepositIsALR'] = _submission.get(chefs_rcv_param('soilDepositIsALR', rcv_clz))
        _rcv_dic['soilDepositIsReserveLands'] = _submission.get(chefs_rcv_param('soilDepositIsReserveLands', rcv_clz))
        _rcv_dic['dateSigned'] = convert_simple_datetime_format_in_str(_submission.get(chefs_rcv_param('dateSigned', rcv_clz)))
        _rcv_dic['createAt'] = get_create_date(
                                _submission,
                                chefs_rcv_param('form', rcv_clz),
                                chefs_rcv_param('createdAt', rcv_clz))
        _rcv_dic['confirmationId'] = _confirmation_id
    return _rcv_dic

def map_hv_site(_hvs):
    """Mapping HV Site"""
    _hv_dic = {}
    _confirmation_id = get_confirm_id(
                        _hvs,
                        chefs_hv_param('form'),
                        chefs_hv_param('confirmationId'))
    if (validate_lat_lon(
      _hvs.get(chefs_hv_param('latitudeDegrees')),
      _hvs.get(chefs_hv_param('latitudeMinutes')),
      _hvs.get(chefs_hv_param('latitudeSeconds')),
      _hvs.get(chefs_hv_param('longitudeDegrees')),
      _hvs.get(chefs_hv_param('longitudeMinutes')),
      _hvs.get(chefs_hv_param('longitudeSeconds')),
      _confirmation_id,
      'High Volume Receiving Site Form')
    ):
        logging.debug("Mapping high volume site ...")
        for hv_header in constant.HV_SITE_HEADERS:
            _hv_dic[hv_header] = None

        _hv_dic['ownerFirstName'] = _hvs.get(chefs_hv_param('ownerFirstName'))
        _hv_dic['ownerLastName'] = _hvs.get(chefs_hv_param('ownerLastName'))
        _hv_dic['ownerCompany'] = _hvs.get(chefs_hv_param('ownerCompany'))
        _hv_dic['ownerAddress'] = _hvs.get(chefs_hv_param('ownerAddress'))
        _hv_dic['ownerCity'] = _hvs.get(chefs_hv_param('ownerCity'))
        _hv_dic['ownerProvince'] = _hvs.get(chefs_hv_param('ownerProvince'))
        _hv_dic['ownerCountry'] = _hvs.get(chefs_hv_param('ownerCountry'))
        _hv_dic['ownerPostalCode'] = _hvs.get(chefs_hv_param('ownerPostalCode'))
        _hv_dic['ownerPhoneNumber'] = _hvs.get(chefs_hv_param('ownerPhoneNumber'))
        _hv_dic['ownerEmail'] = _hvs.get(chefs_hv_param('ownerEmail'))
        _hv_dic['owner2FirstName'] = _hvs.get(chefs_hv_param('owner2FirstName'))
        _hv_dic['owner2LastName'] = _hvs.get(chefs_hv_param('owner2LastName'))
        _hv_dic['owner2Company'] = _hvs.get(chefs_hv_param('owner2Company'))
        _hv_dic['owner2Address'] = _hvs.get(chefs_hv_param('owner2Address'))
        _hv_dic['owner2City'] = _hvs.get(chefs_hv_param('owner2City'))
        _hv_dic['owner2Province'] = _hvs.get(chefs_hv_param('owner2Province'))
        _hv_dic['owner2Country'] = _hvs.get(chefs_hv_param('owner2Country'))
        _hv_dic['owner2PostalCode'] = _hvs.get(chefs_hv_param('owner2PostalCode'))
        _hv_dic['owner2PhoneNumber'] = _hvs.get(chefs_hv_param('owner2PhoneNumber'))
        _hv_dic['owner2Email'] = _hvs.get(chefs_hv_param('owner2Email'))
        _hv_dic['additionalOwners'] = _hvs.get(chefs_hv_param('additionalOwners'))
        _hv_dic['contactFirstName'] = _hvs.get(chefs_hv_param('contactFirstName'))
        _hv_dic['contactLastName'] = _hvs.get(chefs_hv_param('contactLastName'))
        _hv_dic['contactCompany'] = _hvs.get(chefs_hv_param('contactCompany'))
        _hv_dic['contactAddress'] = _hvs.get(chefs_hv_param('contactAddress'))
        _hv_dic['contactCity'] = _hvs.get(chefs_hv_param('contactCity'))
        _hv_dic['contactProvince'] = _hvs.get(chefs_hv_param('contactProvince'))
        _hv_dic['contactCountry'] = _hvs.get(chefs_hv_param('contactCountry'))
        _hv_dic['contactPostalCode'] = _hvs.get(chefs_hv_param('contactPostalCode'))
        _hv_dic['contactPhoneNumber'] = _hvs.get(chefs_hv_param('contactPhoneNumber'))
        _hv_dic['contactEmail'] = _hvs.get(chefs_hv_param('contactEmail'))
        _hv_dic['SID'] = _hvs.get(chefs_hv_param('SID'))

        _hv_dic['latitude'], _hv_dic['longitude'] = convert_deciaml_lat_long(
                                                    _hvs[chefs_hv_param('latitudeDegrees')],
                                                    _hvs[chefs_hv_param('latitudeMinutes')],
                                                    _hvs[chefs_hv_param('latitudeSeconds')],
                                                    _hvs[chefs_hv_param('longitudeDegrees')],
                                                    _hvs[chefs_hv_param('longitudeMinutes')],
                                                    _hvs[chefs_hv_param('longitudeSeconds')])

        _hv_dic['regionalDistrict'] = create_regional_district(_hvs, chefs_hv_param('regionalDistrict'))
        _hv_dic['landOwnership'] = create_land_ownership(_hvs, chefs_hv_param('landOwnership'))
        _hv_dic['legallyTitledSiteAddress'] = _hvs.get(chefs_hv_param('legallyTitledSiteAddress'))
        _hv_dic['legallyTitledSiteCity'] = _hvs.get(chefs_hv_param('legallyTitledSiteCity'))
        _hv_dic['legallyTitledSitePostalCode'] = _hvs.get(chefs_hv_param('legallyTitledSitePostalCode'))

        _hv_dic['PID'], _hv_dic['legalLandDescription'] = create_pid_pin_and_desc(
                                                        _hvs,
                                                        chefs_hv_param('pidDataGrid'),
                                                        chefs_hv_param('pid'),
                                                        chefs_hv_param('pidDesc')) #PID
        if (_hv_dic['PID'] is None or _hv_dic['PID'].strip() == ''): #PIN
            _hv_dic['PIN'], _hv_dic['legalLandDescription'] = create_pid_pin_and_desc(
                                                                _hvs,
                                                                chefs_hv_param('pinDataGrid'),
                                                                chefs_hv_param('pin'),
                                                                chefs_hv_param('pinDesc'))
        if ((_hv_dic['PID'] is None or _hv_dic['PID'].strip() == '')
            and (_hv_dic['PIN'] is None or _hv_dic['PIN'].strip() == '')):
            #Description when selecting 'Untitled Municipal Land'
            _hv_dic['legalLandDescription'] = create_untitled_municipal_land_desc(
                                                _hvs,
                                                chefs_hv_param('untitledMunicipalLand'),
                                                chefs_hv_param('untitledMunicipalLandDesc'))

        _hv_dic['crownLandFileNumbers'] = create_land_file_numbers(_hvs, chefs_hv_param('crownLandFileNumbers'))
        _hv_dic['receivingSiteLandUse'] = create_receiving_site_lan_uses(_hvs, chefs_hv_param('receivingSiteLandUse'))
        _hv_dic['hvsConfirmation'] = _hvs.get(chefs_hv_param('hvsConfirmation'))
        _hv_dic['dateSiteBecameHighVolume'] = convert_simple_datetime_format_in_str(_hvs.get(chefs_hv_param('dateSiteBecameHighVolume')))
        _hv_dic['howRelocatedSoilWillBeUsed'] = _hvs.get(chefs_hv_param('howRelocatedSoilWillBeUsed'))
        _hv_dic['soilDepositIsALR'] = _hvs.get(chefs_hv_param('soilDepositIsALR'))
        _hv_dic['soilDepositIsReserveLands'] = _hvs.get(chefs_hv_param('soilDepositIsReserveLands'))
        _hv_dic['qualifiedProfessionalFirstName'] = _hvs.get(chefs_hv_param('qualifiedProfessionalFirstName'))
        _hv_dic['qualifiedProfessionalLastName'] = _hvs.get(chefs_hv_param('qualifiedProfessionalLastName'))
        _hv_dic['qualifiedProfessionalType'] = _hvs.get(chefs_hv_param('qualifiedProfessionalType'))
        _hv_dic['qualifiedProfessionalOrganization'] = _hvs.get(chefs_hv_param('qualifiedProfessionalOrganization'))
        _hv_dic['professionalLicenceRegistration'] = _hvs.get(chefs_hv_param('professionalLicenceRegistration'))
        _hv_dic['qualifiedProfessionalAddress'] = _hvs.get(chefs_hv_param('qualifiedProfessionalAddress'))
        _hv_dic['qualifiedProfessionalCity'] = _hvs.get(chefs_hv_param('qualifiedProfessionalCity'))
        _hv_dic['qualifiedProfessionalProvince'] = _hvs.get(chefs_hv_param('qualifiedProfessionalProvince'))
        _hv_dic['qualifiedProfessionalCountry'] = _hvs.get(chefs_hv_param('qualifiedProfessionalCountry'))
        _hv_dic['qualifiedProfessionalPostalCode'] = _hvs.get(chefs_hv_param('qualifiedProfessionalPostalCode'))
        _hv_dic['qualifiedProfessionalPhoneNumber'] = _hvs.get(chefs_hv_param('qualifiedProfessionalPhoneNumber'))
        _hv_dic['qualifiedProfessionalEmail'] = _hvs.get(chefs_hv_param('qualifiedProfessionalEmail'))
        _hv_dic['signaturerFirstAndLastName'] = _hvs.get(chefs_hv_param('signaturerFirstAndLastName'))
        _hv_dic['dateSigned'] = convert_simple_datetime_format_in_str(_hvs.get(chefs_hv_param('dateSigned')))
        _hv_dic['createAt'] = get_create_date(_hvs, chefs_hv_param('form'), chefs_hv_param('createdAt'))
        _hv_dic['confirmationId'] = _confirmation_id
    return _hv_dic
