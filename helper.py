# pylint: disable=line-too-long
# pylint: disable=no-member
# pylint: disable=too-many-arguments
# pylint: disable=too-many-boolean-expressions
# pylint: disable=chained-comparison
# pylint: disable=simplifiable-if-expression
# pylint: disable=no-else-return
# pylint: disable=too-many-branches
# pylint: disable=inconsistent-return-statements
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
import logging.config
from pytz import timezone
import pytz
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import Timeout
from jinja2 import Environment, select_autoescape, FileSystemLoader
import constant

WEB_MAP_APP_ID = os.getenv('WEB_MAP_APP_ID')
CHEFS_MAIL_FORM_ID = os.getenv('CHEFS_MAIL_FORM_ID')
CHES_API_OAUTH_SECRET = os.getenv('CHES_API_OAUTH_SECRET')
CHEFS_API_URL = os.getenv('CHEFS_API_URL')
AUTH_URL = os.getenv('AUTH_URL')
CHES_URL = os.getenv('CHES_URL')
LOGLEVEL = os.getenv('LOGLEVEL')
CHEFS_FORM_TIMEOUT_SECONDS = os.getenv('CHEFS_FORM_TIMEOUT_SECONDS')
CHES_EMAIL_TIMEOUT_SECONDS = os.getenv('CHES_EMAIL_TIMEOUT_SECONDS')
CHES_TOKEN_TIMEOUT_SECONDS = os.getenv('CHES_TOKEN_TIMEOUT_SECONDS')
CHES_HEALTH_TIMEOUT_SECONDS = os.getenv('CHES_HEALTH_TIMEOUT_SECONDS')

# If there is no CHEFS_FORM_TIMEOUT_SECONDS, set it to 60 seconds (1 minutes)
if not CHEFS_FORM_TIMEOUT_SECONDS:
    CHEFS_FORM_TIMEOUT_SECONDS = '60'

# If there is no CHES_EMAIL_TIMEOUT_SECONDS, set it to 60 seconds (1 minutes)
if not CHES_EMAIL_TIMEOUT_SECONDS:
    CHES_EMAIL_TIMEOUT_SECONDS = '60'

# If there is no CHES_TOKEN_TIMEOUT_SECONDS, set it to 60 seconds (1 minutes)
if not CHES_TOKEN_TIMEOUT_SECONDS:
    CHES_TOKEN_TIMEOUT_SECONDS = '60'

# If there is no CHES_HEALTH_TIMEOUT_SECONDS, set it to 60 seconds (1 minutes)
if not CHES_HEALTH_TIMEOUT_SECONDS:
    CHES_HEALTH_TIMEOUT_SECONDS = '60'



def load_env():
    """Loading environment variables from .env files - for local testing"""
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def read_config():
    """Read configuration information to access AGOL and CHES"""
    _config = configparser.ConfigParser()
    _config.read('configurations.ini')
    return _config

config = read_config()
WEBMAP_POPUP_URL = config['AGOL']['WEBMAP_POPUP_URL']
FEATURE_SERVICE_URL = config['ARCGIS_REST_SERVICES']['FEATURE_SERVICE_URL']

logging.basicConfig(level=LOGLEVEL, format='%(asctime)s [%(levelname)s] %(message)s')

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
    """"Get CHES Token"""
    _auth_response = None
    try:
        _auth_pay_load = 'grant_type=client_credentials'
        _auth_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + CHES_API_OAUTH_SECRET
        }
        ches_token_timeout_seconds = int(CHES_TOKEN_TIMEOUT_SECONDS)
        _auth_response = requests.request("POST", AUTH_URL, headers=_auth_headers, data=_auth_pay_load, timeout=ches_token_timeout_seconds) # timeout in seconds
        _auth_response_json = json.loads(_auth_response.content)
        if _auth_response_json.get('access_token'):
            return _auth_response_json['access_token']
        else:
            raise KeyError(_auth_response_json.get('error_description') + ", "
                + _auth_response_json.get('error') + ", status code:"
                + str(_auth_response.status_code) + ", reason:"+ _auth_response.reason)
    except KeyError as _ke:
        logging.exception("Email could not be sent due to an authorization issue:%s", _ke)
    except Timeout:
        logging.error('The request timed out to get CHES token! - %s', AUTH_URL)
    except ValueError:
        logging.error('Invalid timeout value: %s. Must be an int or float.', CHES_TOKEN_TIMEOUT_SECONDS)
    return _auth_response

def check_ches_health():
    """Returns health checks of external service dependencies"""
    _access_token = get_ches_token()
    ches_headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + _access_token
    }
    _ches_api_health_endpoint = CHES_URL + '/api/v1/health'
    try:
        ches_health_timeout_seconds = int(CHES_HEALTH_TIMEOUT_SECONDS)
        _ches_response = requests.request("GET", _ches_api_health_endpoint, headers=ches_headers, timeout=ches_health_timeout_seconds) # timeout in seconds
        if _ches_response.status_code == 200:
            logging.info(constant.CHES_HEALTH_200_STATUS)
        elif _ches_response.status_code == 401:
            logging.error(constant.CHES_HEALTH_401_STATUS)
        elif _ches_response.status_code == 403:
            logging.error(constant.CHES_HEALTH_403_STATUS)
        else:
            logging.error("CHES Health returned staus code:%s, text:%s", str(_ches_response.status_code), _ches_response.text)
    except Timeout:
        logging.error('The request timed out to check CHES Health! - %s', _ches_api_health_endpoint)
    except ValueError:
        logging.error('Invalid timeout value: %s. Must be an int or float.', CHES_HEALTH_TIMEOUT_SECONDS)

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
        try:
            ches_email_timeout_seconds = int(CHES_EMAIL_TIMEOUT_SECONDS)
            _ches_response = requests.request("POST", _ches_api_single_email_endpoint, headers=ches_headers, data=ches_pay_load, timeout=ches_email_timeout_seconds) # timeout in seconds
        except Timeout:
            logging.error('The request timed out to send email! - %s', _ches_api_single_email_endpoint)
        except ValueError:
            logging.error('Invalid timeout value: %s. Must be an int or float.', CHES_EMAIL_TIMEOUT_SECONDS)
    return _ches_response

def get_chefs_form_data(form_id, form_key, form_version):
    """Retrieve CHEFS form data via CHEFS API"""
    content = None
    chefs_api_request_url = CHEFS_API_URL + '/forms/' + form_id + '/export?format=json&type=submissions&version=' + form_version
    try:
        chefs_form_timeout_seconds = int(CHEFS_FORM_TIMEOUT_SECONDS)
        request = requests.get(chefs_api_request_url, auth=HTTPBasicAuth(form_id, form_key), headers={'Content-type': 'application/json'}, timeout=chefs_form_timeout_seconds) # timeout in seconds
        content = json.loads(request.content)
    except Timeout:
        logging.error('The request timed out! %s', chefs_api_request_url)
        os._exit(1)
    except ValueError:
        logging.error('Invalid timeout value: %s. Must be an int or float.', CHEFS_FORM_TIMEOUT_SECONDS)
        os._exit(1)
    return content

# def fetch_columns(form_id, form_key):
#     """Retrieve CHEFS form columns"""
#     attributes = None
#     try:
#         request = requests.get(CHEFS_API_URL + '/forms/' + form_id + '/versions', auth=HTTPBasicAuth(form_id, form_key), headers={'Content-type': 'application/json'}, timeout=5) # timeout in seconds
#         request_json = json.loads(request.content)
#         version = request_json[0]['id']
#         attribute_request = requests.get(CHEFS_API_URL + '/forms/' + form_id + '/versions/' + version + '/fields', auth=HTTPBasicAuth(form_id, form_key), headers={'Content-type': 'application/json'}, timeout=5) # timeout in seconds
#         attributes = json.loads(attribute_request.content)
#     except Timeout:
#         logging.error('The request timed out to retrieve CHEFS form columns!')
#     return attributes

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
    Convert and returns simple datetime format.
    str_date: '2022-09-22T00:00:00-07:00', '09/02/2022' or '2022-09-02' format
    return: 'MM/DD/YYYY 00:00:00' string format
    """
    _result = None
    try:
        if str_date is not None and str_date != '':
            # Handling the 'YYYY-MM-DDTHH:MM:SS-07:00' format
            if 'T' in str_date:
                _datetime_in_str = str_date.split('T')[0]
                _result = datetime.datetime.strptime(_datetime_in_str, '%Y-%m-%d').strftime('%m/%d/%Y')
            # Handling the 'MM/DD/YYYY' format directly
            elif '/' in str_date:
                _result = datetime.datetime.strptime(str_date, '%m/%d/%Y').strftime('%m/%d/%Y')
            # Handling the 'YYYY-MM-DD' format
            else:
                _result = datetime.datetime.strptime(str_date, '%Y-%m-%d').strftime('%m/%d/%Y')
    except ValueError as _ve:
        logging.exception(constant.VALUE_ERROR_EXCEPTION_RAISED, _ve)

    if _result is not None:
        _result += ' 00:00:00'

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
def str_to_float(value):
    """Convert string to Float, if possible"""
    _result = 0
    try:
        if (value is not None and value != ''):
            _exp_result = re.sub('[^\d\.]', '', value)
            _result = (float(_exp_result))

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
    name = None

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
    if rcv_clz in (2, 3):
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
    """"Returns regional district name matching with the given key in regional district dictionary"""
    name = constant.REGIONAL_DISTRICT_NAME_DIC.get(key)
    if name is not None:
        return name
    else:
        return key

def convert_source_site_use_to_name(key):
    """Returns source site use name matching with the given key in source site use dictionary"""
    name = constant.SOURCE_SITE_USE_NAME_DIC.get(key)
    if name is not None:
        return name
    else:
        return key

def convert_receiving_site_use_to_name(key):
    """
    Returns receiving site use name matching with the given key in
    receiving site use dictionary
    """
    name = constant.RECEIVING_SITE_USE_NAME_DIC.get(key)
    if name is not None:
        return name
    else:
        return key

def convert_soil_quality_to_name(key):
    """
    Returns soil quality name matching with the given key in
    soil quality dictionary
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
    _value = chefs_dic.get(field)
    if _value:
        if isinstance(_value, list) and len(_value) > 0:
            _regional_district = convert_regional_district_to_name(_value[0])
        elif isinstance(_value, str): # changed to only allow one region selection on newer form
            _regional_district = convert_regional_district_to_name(_value)
    return _regional_district

def convert_land_ownership_to_name(key):
    """
    Returns land ownership name matching with the given key in
    land ownership dictionary
    """
    name = constant.LAND_OWNERSHIP_NAME_DIC.get(key)
    if name is not None:
        return name
    else:
        return key

def convert_soil_exemption_to_name(key):
    """
    Returns source site protocol 19 excemptions name matching with the given key in
    soil exemption dictionary
    """
    name = constant.SOIL_EXEMPTION_NAME_DIC.get(key)
    if name is not None:
        return name
    else:
        return key

def create_source_site_protocol_19_exemptions(chefs_dic, field):
    """
    Extract "source site protocol 19 exemptions" value from form
    (in case of multiple data, they are joined with comma)
    """
    _exemptions = []
    for _key, _value in chefs_dic[field].items():
        if is_not_none_true(_value):
            _exemptions.append(convert_soil_exemption_to_name(_key))
    if len(_exemptions) > 0:
        _exemptions = "\"" + ",".join(_exemptions) + "\""
    return _exemptions

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
     Extract all "PID and description" or "PIN and description" values from form and join them with a comma
    """
    _pid_list = []
    _desc_list = []

    if chefs_dic.get(data_grid_field) is not None and len(chefs_dic[data_grid_field]) > 0:
        for item in chefs_dic[data_grid_field]:
            pid_value = item.get(pid_pin_field)
            desc_value = item.get(desc_field)

            if pid_value is not None and pid_value.strip() != '':
                _pid_list.append(pid_value.strip())

            if desc_value is not None and desc_value.strip() != '':
                _desc_list.append(desc_value.strip())

    _pid = ','.join(_pid_list) if _pid_list else None
    _desc = ','.join(_desc_list) if _desc_list else None

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
                    _soil_volume = str_to_float(_soil_volume)

                _soil_volume = str_to_double(_soil_volume)
                _soil_claz = _dg9.get("B1-soilClassificationSource")

                if is_not_none_true(_soil_claz.get("urbanParkLandUsePl")):
                    working_dic['urbanParkSoilVol'] = working_dic['urbanParkSoilVol'] + _soil_volume if working_dic['urbanParkSoilVol'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("commercialLandUseCl")):
                    working_dic['commercialSoilVol'] = working_dic['commercialSoilVol'] + _soil_volume if working_dic['commercialSoilVol'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("industrialLandUseIl")):
                    working_dic['industrialSoilVol'] = working_dic['industrialSoilVol'] + _soil_volume if working_dic['industrialSoilVol'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("agriculturalLandUseAl")):
                    working_dic['agriculturalSoilVol'] = working_dic['agriculturalSoilVol'] + _soil_volume if working_dic['agriculturalSoilVol'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("wildlandsNaturalLandUseWln")):
                    working_dic['wildlandsNaturalSoilVol'] = working_dic['wildlandsNaturalSoilVol'] + _soil_volume if working_dic['wildlandsNaturalSoilVol'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("wildlandsRevertedLandUseWlr")):
                    working_dic['wildlandsRevertedSoilVol'] = working_dic['wildlandsRevertedSoilVol'] + _soil_volume if working_dic['wildlandsRevertedSoilVol'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("residentialLandUseLowDensityRlld")):
                    working_dic['residentLowDensitySoilVol'] = working_dic['residentLowDensitySoilVol'] + _soil_volume if working_dic['residentLowDensitySoilVol'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("residentialLandUseHighDensityRlhd")):
                    working_dic['residentHighDensitySoilVol'] = working_dic['residentHighDensitySoilVol'] + _soil_volume if working_dic['residentHighDensitySoilVol'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume
                elif is_not_none_true(_soil_claz.get("potentialToCauseMetalsLeachingAcidRockDrainageMlArd")):
                    working_dic['mdardSoilVol'] = working_dic['mdardSoilVol'] + _soil_volume if working_dic['mdardSoilVol'] is not None else _soil_volume
                    _total_soil_volume += _soil_volume

        if _total_soil_volume != 0:
            working_dic['totalSoilVolume'] = _total_soil_volume

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
    if _site_dic['confirmationId'] is not None and _site_dic['confirmationId'].strip() != '':
        return _site_dic['confirmationId']

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
    if _submission.get('Submit'):
        logging.debug("Mapping sourece site ...")
        for src_header in constant.SOURCE_SITE_HEADERS:
            _src_dic[src_header] = None

        _src_dic['updateToPreviousForm'] = convert_to_yes_no(_submission.get(chefs_src_param('updateToPreviousForm')))
        _src_dic['previousConfirmCode'] = _submission.get(chefs_src_param('previousConfirmCode'))
        _src_dic['ownerCompany'] = _submission.get(chefs_src_param('ownerCompany'))
        _src_dic['owner2Company'] = _submission.get(chefs_src_param('owner2Company'))
        _src_dic['contactCompany'] = _submission.get(chefs_src_param('contactCompany'))
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
        _src_dic['reserveNameAndNumber'] = _submission.get(chefs_src_param('reserveNameAndNumber'))

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

        _src_dic['highVolumeSite'] = convert_to_yes_no(_submission.get(chefs_src_param('highVolumeSite')))
        _src_dic['soilRelocationPurpose'] = _submission.get(chefs_src_param('soilRelocationPurpose'))
        _src_dic['soilStorageType'] = _submission.get(chefs_src_param('soilStorageType'))

        if _submission.get(chefs_src_param('exemptionFromProtocol19Apply')) is not None:
            if convert_to_yes_no(_submission.get(chefs_src_param('exemptionFromProtocol19Apply'))) == 'Yes':
                if _submission.get(chefs_src_param('protocol19AppliedExemptions')) is not None:
                    _src_dic['protocol19Exemptions'] = create_source_site_protocol_19_exemptions(_submission, chefs_src_param('protocol19AppliedExemptions'))
            else:
                _src_dic['protocol19Exemptions'] = 'No'

        create_soil_volumes(
            _submission,
            chefs_src_param('soilVolumeDataGrid'),
            chefs_src_param('soilVolume'),
            chefs_src_param('soilClassificationSource'),
            _src_dic)

        _src_dic['vapourExemption'] = convert_to_yes_no(_submission.get(chefs_src_param('vapourExemption')))
        _src_dic['vapourExemptionDesc'] = _submission.get(chefs_src_param('vapourExemptionDesc'))
        _src_dic['soilRelocationStartDate'] = convert_simple_datetime_format_in_str(_submission.get(chefs_src_param('soilRelocationStartDate')))
        _src_dic['soilRelocationCompletionDate'] = convert_simple_datetime_format_in_str(_submission.get(chefs_src_param('soilRelocationCompletionDate')))
        _src_dic['relocationMethod'] = _submission.get(chefs_src_param('relocationMethod'))
        _src_dic['qualifiedProfessionalOrganization'] = _submission.get(chefs_src_param('qualifiedProfessionalOrganization'))
        _src_dic['createAt'] = get_create_date(_submission, chefs_src_param('form'), chefs_src_param('createdAt'))
        _src_dic['confirmationId'] = _confirmation_id
    return _src_dic

def map_rcv_site(_submission, rcv_clz):
    """Mapping receiving site"""
    _rcv_dic = {}
    _confirmation_id = get_confirm_id(_submission,chefs_rcv_param('form', rcv_clz),chefs_rcv_param('confirmationId', rcv_clz))
    if (validate_additional_rcv_site(_submission, rcv_clz)
        and _submission.get('Submit')
    ):
        for rcv_header in constant.RECEIVING_SITE_HEADERS:
            _rcv_dic[rcv_header] = None

        _rcv_dic['previousConfirmCode'] = _submission.get(chefs_rcv_param('previousConfirmCode', rcv_clz))
        _rcv_dic['ownerCompany'] = _submission.get(chefs_rcv_param('ownerCompany', rcv_clz))
        _rcv_dic['owner2Company'] = _submission.get(chefs_rcv_param('owner2Company', rcv_clz))
        _rcv_dic['contactCompany'] = _submission.get(chefs_rcv_param('contactCompany', rcv_clz))
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

        _rcv_dic['crownLandFileNumbers'] = create_land_file_numbers(_submission,chefs_rcv_param('crownLandFileNumbers', rcv_clz))
        _rcv_dic['reserveNameAndNumber'] = _submission.get(chefs_rcv_param('reserveNameAndNumber', rcv_clz))
        _rcv_dic['receivingSiteLandUse'] = create_receiving_site_lan_uses(_submission,chefs_rcv_param('receivingSiteLandUse', rcv_clz))

        create_soil_volumes(
            _submission,
            chefs_rcv_param('soilVolumeDataGrid', rcv_clz),
            chefs_rcv_param('soilVolume', rcv_clz),
            chefs_rcv_param('soilClassificationSource', rcv_clz),
            _rcv_dic)

        _rcv_dic['CSRFactors'] = _submission.get(chefs_rcv_param('CSRFactors', rcv_clz))
        _rcv_dic['relocatedSoilUse'] = _submission.get(chefs_rcv_param('relocatedSoilUse', rcv_clz))
        _rcv_dic['highVolumeSite'] = convert_to_yes_no(_submission.get(chefs_rcv_param('highVolumeSite', rcv_clz)))
        _rcv_dic['soilDepositIsALR'] = convert_to_yes_no(_submission.get(chefs_rcv_param('soilDepositIsALR', rcv_clz)))
        _rcv_dic['soilDepositIsReserveLands'] = convert_to_yes_no(_submission.get(chefs_rcv_param('soilDepositIsReserveLands', rcv_clz)))
        _rcv_dic['soilRelocationStartDate'] = convert_simple_datetime_format_in_str(_submission.get(chefs_rcv_param('soilRelocationStartDate', rcv_clz)))
        _rcv_dic['soilRelocationCompletionDate'] = convert_simple_datetime_format_in_str(_submission.get(chefs_rcv_param('soilRelocationCompletionDate', rcv_clz)))
        _rcv_dic['qualifiedProfessionalOrganization'] = _submission.get(chefs_rcv_param('qualifiedProfessionalOrganization', rcv_clz))
        _rcv_dic['createAt'] = get_create_date(
                                _submission,
                                chefs_rcv_param('form', rcv_clz),
                                chefs_rcv_param('createdAt', rcv_clz))
        _rcv_dic['confirmationId'] = _confirmation_id
        _rcv_dic['receivingSiteClass'] = str(rcv_clz) # contaning string 1, 2, or 3 for receiving site classfication
    return _rcv_dic

def map_hv_site(_hvs):
    """Mapping HV Site"""
    _hv_dic = {}
    _confirmation_id = get_confirm_id(_hvs,chefs_hv_param('form'),chefs_hv_param('confirmationId'))
    if _hvs.get('Submit'):
        logging.debug("Mapping high volume site ...")
        for hv_header in constant.HV_SITE_HEADERS:
            _hv_dic[hv_header] = None

        _hv_dic['ownerCompany'] = _hvs.get(chefs_hv_param('ownerCompany'))
        _hv_dic['owner2Company'] = _hvs.get(chefs_hv_param('owner2Company'))
        _hv_dic['contactCompany'] = _hvs.get(chefs_hv_param('contactCompany'))
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
        _hv_dic['reserveNameAndNumber'] = _hvs.get(chefs_hv_param('reserveNameAndNumber'))
        _hv_dic['receivingSiteLandUse'] = create_receiving_site_lan_uses(_hvs, chefs_hv_param('receivingSiteLandUse'))
        _hv_dic['hvsConfirmation'] = convert_to_yes_no(_hvs.get(chefs_hv_param('hvsConfirmation')))
        _hv_dic['dateSiteBecameHighVolume'] = convert_simple_datetime_format_in_str(_hvs.get(chefs_hv_param('dateSiteBecameHighVolume')))
        _hv_dic['howRelocatedSoilWillBeUsed'] = _hvs.get(chefs_hv_param('howRelocatedSoilWillBeUsed'))
        _hv_dic['soilDepositIsALR'] = convert_to_yes_no(_hvs.get(chefs_hv_param('soilDepositIsALR')))
        _hv_dic['soilDepositIsReserveLands'] = convert_to_yes_no(_hvs.get(chefs_hv_param('soilDepositIsReserveLands')))
        _hv_dic['qualifiedProfessionalOrganization'] = _hvs.get(chefs_hv_param('qualifiedProfessionalOrganization'))
        _hv_dic['createAt'] = get_create_date(_hvs, chefs_hv_param('form'), chefs_hv_param('createdAt'))
        _hv_dic['confirmationId'] = _confirmation_id
    return _hv_dic

def map_source_receiving_site(_source_sites, _receiving_sites):
    """Mapping additional work between source site and receiving sites(address and regional district)"""
    for _src_site in _source_sites:
        for _rcv_site in _receiving_sites:
            if _rcv_site.get('confirmationId') == _src_site.get('confirmationId'):
                # adding receiving site addresses into source site
                if _rcv_site.get('receivingSiteClass') == '1':
                    _src_site['receivingSite1Address'] = _rcv_site.get('legallyTitledSiteAddress')
                    _src_site['receivingSite1City'] = _rcv_site.get('legallyTitledSiteCity')
                    _src_site['receivingSite1RegionalDistrict'] = _rcv_site.get('regionalDistrict')
                elif _rcv_site.get('receivingSiteClass') == '2':
                    _src_site['receivingSite2Address'] = _rcv_site.get('legallyTitledSiteAddress')
                    _src_site['receivingSite2City'] = _rcv_site.get('legallyTitledSiteCity')
                    _src_site['receivingSite2RegionalDistrict'] = _rcv_site.get('regionalDistrict')
                elif _rcv_site.get('receivingSiteClass') == '3':
                    _src_site['receivingSite3Address'] = _rcv_site.get('legallyTitledSiteAddress')
                    _src_site['receivingSite3City'] = _rcv_site.get('legallyTitledSiteCity')
                    _src_site['receivingSite3RegionalDistrict'] = _rcv_site.get('regionalDistrict')
                # adding source site address and regional district into receiving sites
                _rcv_site['sourceSiteAddress'] = _src_site.get('legallyTitledSiteAddress')
                _rcv_site['sourceSiteCity'] = _src_site.get('legallyTitledSiteCity')
                _rcv_site['sourceSiteRegionalDistrict'] = _src_site.get('regionalDistrict')
    return _source_sites, _receiving_sites
def get_boolean_env_var(env_var):
    """Returns boolean value of the given environment variable, handles None and case-insensitive values"""
    if env_var is not None:
        return os.getenv(env_var, 'false').lower() in ['true', '1']
    return False

def convert_to_yes_no(argument):
    """
    Convert the argument to 'Yes' or 'No'.
    If the argument is 'yes', 'true', True (case-insensitive), return 'Yes'.
    If the argument is 'no', 'false', False (case-insensitive), return 'No'.
    Otherwise, return the original argument.
    """
    # Convert boolean to string
    if isinstance(argument, bool):
        argument = str(argument)
    
    # Convert argument to lowercase if it is a string
    if isinstance(argument, str):
        argument_lower = argument.lower()

        if argument_lower in ['yes', 'true']:
            return 'Yes'
        elif argument_lower in ['no', 'false']:
            return 'No'

    # Return the original argument if it doesn't match any criteria
    return argument