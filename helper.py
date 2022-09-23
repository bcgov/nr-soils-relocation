import configparser
import re

def read_config():
    config = configparser.ConfigParser()
    config.read('configurations.ini')
    return config

def convert_deciaml_lat_long(lat_deg, lat_min, lat_sec, lon_deg, lon_min, lon_sec):
  _lat_dd = 0
  _lon_dd = 0
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
  return _lat_dd, _lon_dd
