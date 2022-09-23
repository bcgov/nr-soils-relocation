import configparser
import re
import json
import requests
from requests.auth import HTTPBasicAuth
import os
import datetime
from pytz import timezone

CHES_API_KEY = os.getenv('CHES_API_KEY')
print(f"Value of env variable key='CHES_API_KEY': {CHES_API_KEY}")

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
        EXP_EXTRACT_FLOATING = r'[-+]?\d*\.\d+|\d+'
        # Convert to DD in mapLatitude and mapLongitude
        if (lat_deg is not None and lat_deg != '' and
            lat_min is not None and lat_min != '' and
            lat_sec is not None and lat_sec != '' and
            lon_deg is not None and lon_deg != '' and
            lon_min is not None and lon_min != '' and
            lon_sec is not None and lon_sec != ''
        ):
            # extract floating number from text
            _lat_deg = re.findall(EXP_EXTRACT_FLOATING, lat_deg)
            _lat_min = re.findall(EXP_EXTRACT_FLOATING, lat_min)
            _lat_sec = re.findall(EXP_EXTRACT_FLOATING, lat_sec)
            _lon_deg = re.findall(EXP_EXTRACT_FLOATING, lon_deg)
            _lon_min = re.findall(EXP_EXTRACT_FLOATING, lon_min)
            _lon_sec = re.findall(EXP_EXTRACT_FLOATING, lon_sec)

            if (len(_lat_deg) > 0 and len(_lat_min) > 0 and len(_lat_sec) > 0 
                and len(_lon_deg) > 0 and len(_lon_min) > 0 and len(_lon_sec) > 0):
                _lat_dd = (float(_lat_deg[0]) + float(_lat_min[0])/60 + float(_lat_sec[0])/(60*60))
                _lon_dd = - (float(_lon_deg[0]) + float(_lon_min[0])/60 + float(_lon_sec[0])/(60*60))

            if _lon_dd > 0: _lon_dd = - _lon_dd # longitude degrees should be minus in BC bouding box

    except ValueError as ve:
        print('ValueError Raised:', ve)

    return _lat_dd, _lon_dd

def validate_lat_lon(lat_deg, lat_min, lat_sec, lon_deg, lon_min, lon_sec):
    _lat_dd, _lon_dd = convert_deciaml_lat_long(lat_deg, lat_min, lat_sec, lon_deg, lon_min, lon_sec)

    if (_lat_dd is not None and _lat_dd != 0 and
        _lon_dd is not None and _lon_dd != 0 and
        _lat_dd >= 48.30 and _lat_dd <= 60.00 and
        _lon_dd >=-139.06 and _lon_dd <= -114.02):
        return True
    return False

# check if boolen type is
def is_boolean(_v):
  _result = False
  if type(_v) == bool: 
    _result = True
  return _result

def send_mail(to_email, subject, message):
  auth_pay_load = 'grant_type=client_credentials'
  auth_haders = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': 'Basic ' + CHES_API_KEY
  }
  auth_response = requests.request("POST", AUTH_URL + '/auth/realms/jbd6rnxw/protocol/openid-connect/token', headers=auth_haders, data=auth_pay_load)
  auth_response_json = json.loads(auth_response.content)
  access_token = auth_response_json['access_token']

  from_email = "noreply@gov.bc.ca"
  ches_pay_load = "{\n \"bodyType\": \"html\",\n \"body\": \""+message+"\",\n \"delayTS\": 0,\n \"encoding\": \"utf-8\",\n \"from\": \""+from_email+"\",\n \"priority\": \"normal\",\n  \"subject\": \""+subject+"\",\n  \"to\": [\""+to_email+"\"]\n }\n"
  ches_headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer ' + access_token
  }
  ches_response = requests.request("POST", CHEFS_URL + '/api/v1/email', headers=ches_headers, data=ches_pay_load)
  #_ches_content = json.loads(ches_response.content)
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

def get_create_date_and_confirm_id(cefs_dic):
  _created_at = None
  _confirmation_id = None
  if cefs_dic.get('form') is not None : 
    _created_at = cefs_dic.get('form').get('createdAt')
    _confirmation_id = cefs_dic.get('form').get('confirmationId')
    if _created_at is not None:
      #print('the supported timezones by the pytz module:', pytz.all_timezones, '\n')
      _created_at = datetime.datetime.strptime(_created_at, '%Y-%m-%dT%H:%M:%S.%f%z') #convert string to datetime with timezone(UTC)
      _created_at = _created_at.astimezone(timezone('Canada/Pacific'))  #convert to PST
  return _created_at, _confirmation_id

# str_date: '2022-09-22T00:00:00-07:00' or '09/02/2022' format
# return: 'MM/DD/YYYY' string format
def convert_simple_datetime_format_in_str(str_date):
    _result = None
    try:
        if str_date is not None:
            _datetime_in_str = str_date.split('T')
            if len(_datetime_in_str) > 1:
                _result = datetime.datetime.strptime(_datetime_in_str[0], '%Y-%m-%d').strftime('%m/%d/%Y')
    except ValueError as ve:
        print('ValueError Raised:', ve)
    return _result if _result is not None else str_date