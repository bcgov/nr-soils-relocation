import configparser
import re
import json
import requests
from requests.auth import HTTPBasicAuth
import os
import datetime
from pytz import timezone
import constant

CHES_API_KEY = os.getenv('CHES_API_KEY')

def read_config():
    config = configparser.ConfigParser()
    config.read('configurations.ini')
    return config

config = read_config()
AUTH_URL = config['CHEFS']['AUTH_URL']
CHEFS_URL = config['CHEFS']['CHEFS_URL']
CHEFS_API_URL = config['CHEFS']['CHEFS_API_URL']

def convert_deciaml_lat_long(lat_deg, lat_min, lat_sec, lon_deg, lon_min, lon_sec):
    _lat_dd = 0
    _lon_dd = 0
    try:
        # Convert to DD in mapLatitude and mapLongitude
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
                _lon_dd = - (float(_lon_deg[0]) + float(_lon_min[0])/60 + float(_lon_sec[0])/(60*60))

            if _lon_dd > 0: _lon_dd = - _lon_dd # longitude degrees should be minus in BC bouding box

    except ValueError as ve:
        print(constant.VALUE_ERROR_EXCEPTION_RAISED, ve)

    return _lat_dd, _lon_dd

def validate_lat_lon(lat_deg, lat_min, lat_sec, lon_deg, lon_min, lon_sec, confirmation_id, form_name):
    _lat_dd, _lon_dd = convert_deciaml_lat_long(lat_deg, lat_min, lat_sec, lon_deg, lon_min, lon_sec)

    if (_lat_dd is not None and _lat_dd != 0 and
        _lon_dd is not None and _lon_dd != 0 and
        _lat_dd >= 48.30 and _lat_dd <= 60.00 and
        _lon_dd >=-139.06 and _lon_dd <= -114.02):
        return True
    print("[INFO] Can't publish data to AGOL due to Invalidate site coordinates - Latitude(deg/min/sec):",_lat_dd,"(",lat_deg,"/",lat_min,"/",lat_sec,"), Longitude(deg/min/sec):",_lon_dd,"(",lon_deg,"/",lon_min,"/",lon_sec,"), Confirm ID:",confirmation_id,", Form:",form_name)    
    return False

# check if boolen type is
def is_boolean(obj):
  return True if isinstance(obj, bool) else False

def send_mail(to_email, subject, message):
  ches_response = None
  try:
    auth_pay_load = 'grant_type=client_credentials'
    auth_headers = {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Authorization': 'Basic ' + CHES_API_KEY
    }
    auth_response = requests.request("POST", AUTH_URL + '/auth/realms/jbd6rnxw/protocol/openid-connect/token', headers=auth_headers, data=auth_pay_load)
    auth_response_json = json.loads(auth_response.content)
    if auth_response_json.get('access_token'):
      access_token = auth_response_json['access_token']

      from_email = "noreply@gov.bc.ca"
      ches_pay_load = "{\n \"bodyType\": \"html\",\n \"body\": \""+message+"\",\n \"delayTS\": 0,\n \"encoding\": \"utf-8\",\n \"from\": \""+from_email+"\",\n \"priority\": \"normal\",\n  \"subject\": \""+subject+"\",\n  \"to\": [\""+to_email+"\"]\n }\n"
      ches_headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + access_token
      }
      ches_response = requests.request("POST", CHEFS_URL + '/api/v1/email', headers=ches_headers, data=ches_pay_load)
    else:
      raise KeyError(auth_response_json.get('error_description') + ", " + auth_response_json.get('error') + ", status code:" + str(auth_response.status_code) + ", reason:"+ auth_response.reason)
  except KeyError as ke:
      print("[ERROR] The email could not be sent due to an authorization issue. (" , ke , ")")
  return ches_response

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

def get_difference_datetimes_in_hour(datetime1, datetime2):
    _diff = None
    if datetime1 is not None and datetime2 is not None:
        _diff = (datetime1 - datetime2).total_seconds() / 60 / 60 #difference in hour
        #print('difference datetimes in hour:',_diff)
    return _diff

def get_create_date(cefs_dic):
  _created_at = None
  if cefs_dic.get('form') is not None : 
    _created_at = cefs_dic.get('form').get('createdAt')
    if _created_at is not None:
      #print('the supported timezones by the pytz module:', pytz.all_timezones, '\n')
      _created_at = datetime.datetime.strptime(_created_at, '%Y-%m-%dT%H:%M:%S.%f%z') #convert string to datetime with timezone(UTC)
      _created_at = _created_at.astimezone(timezone('Canada/Pacific'))  #convert to PST
  return _created_at

def get_confirm_id(cefs_dic):
  _confirmation_id = None
  if cefs_dic.get('form') is not None : 
    _confirmation_id = cefs_dic.get('form').get('confirmationId')
  return _confirmation_id  

# str_date: '2022-09-22T00:00:00-07:00' or '09/02/2022' format
# return: 'MM/DD/YYYY' string format
def convert_simple_datetime_format_in_str(str_date):
    _result = None
    try:
        if str_date is not None and str_date != '':
            _datetime_in_str = str_date.split('T')
            if len(_datetime_in_str) > 1:
                _result = datetime.datetime.strptime(_datetime_in_str[0], '%Y-%m-%d').strftime('%m/%d/%Y')
    except ValueError as ve:
        print(constant.VALUE_ERROR_EXCEPTION_RAISED, ve)
    return _result if _result is not None else str_date

def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def extract_floating_from_string(value):
    _result = 0
    try:
        if (value is not None and value != ''):
          # extract floating number from text
          _exp_result = re.findall(constant.EXP_EXTRACT_FLOATING, value)
          if isinstance(_exp_result, list) and len(_exp_result) > 0:
            _result = _exp_result[0]

    except ValueError as ve:
        print(constant.VALUE_ERROR_EXCEPTION_RAISED, ve)

    return _result
def str_to_double(obj):
  return float(obj) if isinstance(obj, str) else obj

def is_not_none_true(val):
  if val is not None and is_boolean(val):
    return val
  else:
    return False