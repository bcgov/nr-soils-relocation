# pylint: disable=line-too-long
"""
Retrieve CHEFS form data, overwrite it into AGOL CSVs and Layers,
send notification email to subscribers who want to get information for the soil relocation
"""
import json
import csv
import os
import datetime
import pytz
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
from jinja2 import Environment, select_autoescape, FileSystemLoader
import constant
import helper

CHEFS_SOILS_FORM_ID = os.getenv('CHEFS_SOILS_FORM_ID')
CHEFS_SOILS_API_KEY = os.getenv('CHEFS_SOILS_API_KEY')
CHEFS_HV_FORM_ID = os.getenv('CHEFS_HV_FORM_ID')
CHEFS_HV_API_KEY = os.getenv('CHEFS_HV_API_KEY')
CHEFS_MAIL_FORM_ID = os.getenv('CHEFS_MAIL_FORM_ID')
CHEFS_MAIL_API_KEY = os.getenv('CHEFS_MAIL_API_KEY')
MAPHUB_USER = os.getenv('MAPHUB_USER')
MAPHUB_PASS = os.getenv('MAPHUB_PASS')

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
    _confirmation_id = helper.get_confirm_id(_submission, helper.chefs_src_param('form'), helper.chefs_src_param('confirmationId'))
    if (helper.validate_lat_lon(_submission.get(helper.chefs_src_param('latitudeDegrees')), _submission.get(helper.chefs_src_param('latitudeMinutes')), _submission.get(helper.chefs_src_param('latitudeSeconds')), 
                                _submission.get(helper.chefs_src_param('longitudeDegrees')), _submission.get(helper.chefs_src_param('longitudeMinutes')), _submission.get(helper.chefs_src_param('longitudeSeconds')),
                                _confirmation_id, 'Soil Relocation Notification Form-Source Site')
    ):
        #print("Mapping sourece site ...")
        for src_header in constant.SOURCE_SITE_HEADERS:
            _src_dic[src_header] = None

        _src_dic['updateToPreviousForm'] = _submission.get(helper.chefs_src_param('updateToPreviousForm'))
        _src_dic['ownerFirstName'] = _submission.get(helper.chefs_src_param('ownerFirstName'))
        _src_dic['ownerLastName'] = _submission.get(helper.chefs_src_param('ownerLastName'))
        _src_dic['ownerCompany'] = _submission.get(helper.chefs_src_param('ownerCompany'))
        _src_dic['ownerAddress'] = _submission.get(helper.chefs_src_param('ownerAddress'))
        _src_dic['ownerCity'] = _submission.get(helper.chefs_src_param('ownerCity'))
        _src_dic['ownerProvince'] = _submission.get(helper.chefs_src_param('ownerProvince'))
        _src_dic['ownerCountry'] = _submission.get(helper.chefs_src_param('ownerCountry'))
        _src_dic['ownerPostalCode'] = _submission.get(helper.chefs_src_param('ownerPostalCode'))
        _src_dic['ownerPhoneNumber'] = _submission.get(helper.chefs_src_param('ownerPhoneNumber'))
        _src_dic['ownerEmail'] = _submission.get(helper.chefs_src_param('ownerEmail'))
        _src_dic['owner2FirstName'] = _submission.get(helper.chefs_src_param('owner2FirstName'))
        _src_dic['owner2LastName'] = _submission.get(helper.chefs_src_param('owner2LastName'))
        _src_dic['owner2Company'] = _submission.get(helper.chefs_src_param('owner2Company'))
        _src_dic['owner2Address'] = _submission.get(helper.chefs_src_param('owner2Address'))
        _src_dic['owner2City'] = _submission.get(helper.chefs_src_param('owner2City'))
        _src_dic['owner2Province'] = _submission.get(helper.chefs_src_param('owner2Province'))
        _src_dic['owner2Country'] = _submission.get(helper.chefs_src_param('owner2Country'))
        _src_dic['owner2PostalCode'] = _submission.get(helper.chefs_src_param('owner2PostalCode'))
        _src_dic['owner2PhoneNumber'] = _submission.get(helper.chefs_src_param('owner2PhoneNumber'))
        _src_dic['owner2Email'] = _submission.get(helper.chefs_src_param('owner2Email'))
        _src_dic['additionalOwners'] = _submission.get(helper.chefs_src_param('additionalOwners'))
        _src_dic['contactFirstName'] = _submission.get(helper.chefs_src_param('contactFirstName'))
        _src_dic['contactLastName'] = _submission.get(helper.chefs_src_param('contactLastName'))
        _src_dic['contactCompany'] = _submission.get(helper.chefs_src_param('contactCompany'))
        _src_dic['contactAddress'] = _submission.get(helper.chefs_src_param('contactAddress'))
        _src_dic['contactCity'] = _submission.get(helper.chefs_src_param('contactCity'))
        _src_dic['contactProvince'] = _submission.get(helper.chefs_src_param('contactProvince'))
        _src_dic['contactCountry'] = _submission.get(helper.chefs_src_param('contactCountry'))
        _src_dic['contactPostalCode'] = _submission.get(helper.chefs_src_param('contactPostalCode'))
        _src_dic['contactPhoneNumber'] = _submission.get(helper.chefs_src_param('contactPhoneNumber'))
        _src_dic['contactEmail'] = _submission.get(helper.chefs_src_param('contactEmail'))
        _src_dic['SID'] = _submission.get(helper.chefs_src_param('SID'))

        _src_dic['latitude'], _src_dic['longitude'] = helper.convert_deciaml_lat_long(
          _submission[helper.chefs_src_param('latitudeDegrees')],
          _submission[helper.chefs_src_param('latitudeMinutes')],
          _submission[helper.chefs_src_param('latitudeSeconds')],
          _submission[helper.chefs_src_param('longitudeDegrees')],
          _submission[helper.chefs_src_param('longitudeMinutes')],
          _submission[helper.chefs_src_param('longitudeSeconds')])

        _src_dic['landOwnership'] = helper.create_land_ownership(_submission, helper.chefs_src_param('landOwnership'))
        _src_dic['regionalDistrict'] = helper.create_regional_district(_submission, helper.chefs_src_param('regionalDistrict'))
        _src_dic['legallyTitledSiteAddress'] = _submission.get(helper.chefs_src_param('legallyTitledSiteAddress'))
        _src_dic['legallyTitledSiteCity'] = _submission.get(helper.chefs_src_param('legallyTitledSiteCity'))
        _src_dic['legallyTitledSitePostalCode'] = _submission.get(helper.chefs_src_param('legallyTitledSitePostalCode'))
        _src_dic['crownLandFileNumbers'] = helper.create_land_file_numbers(_submission,helper.chefs_src_param('crownLandFileNumbers'))

        _src_dic['PID'], _src_dic['legalLandDescription'] = helper.create_pid_pin_and_desc(_submission,helper.chefs_src_param('pidDataGrid'),helper.chefs_src_param('pid'),helper.chefs_src_param('pidDesc'))  #PID
        if (_src_dic['PID'] is None or _src_dic['PID'].strip() == ''): #PIN
            _src_dic['PIN'], _src_dic['legalLandDescription'] = helper.create_pid_pin_and_desc(_submission, helper.chefs_src_param('pinDataGrid'), helper.chefs_src_param('pin'), helper.chefs_src_param('pinDesc'))
        if ((_src_dic['PID'] is None or _src_dic['PID'].strip() == '')
            and (_src_dic['PIN'] is None or _src_dic['PIN'].strip() == '')):
            #Description when selecting 'Untitled Municipal Land'
            _src_dic['legalLandDescription'] = helper.create_untitled_municipal_land_desc(_submission, helper.chefs_src_param('untitledMunicipalLand'), helper.chefs_src_param('untitledMunicipalLandDesc'))

        if _submission.get(helper.chefs_src_param('sourceSiteLandUse')) is not None and len(_submission.get(helper.chefs_src_param('sourceSiteLandUse'))) > 0 :
            _source_site_land_uses = []
            for _ref_source_site in _submission.get(helper.chefs_src_param('sourceSiteLandUse')):
                _source_site_land_uses.append(helper.convert_source_site_use_to_name(_ref_source_site))
            _src_dic['sourceSiteLandUse'] = "\"" + ",".join(_source_site_land_uses) + "\""

        _src_dic['highVolumeSite'] = _submission.get(helper.chefs_src_param('highVolumeSite'))
        _src_dic['soilRelocationPurpose'] = _submission.get(helper.chefs_src_param('soilRelocationPurpose'))
        _src_dic['soilStorageType'] = _submission.get(helper.chefs_src_param('soilStorageType'))

        helper.create_soil_volumes(_submission, helper.chefs_src_param('soilVolumeDataGrid'), helper.chefs_src_param('soilVolume'), helper.chefs_src_param('soilClassificationSource'), _src_dic)

        _src_dic['soilCharacterMethod'] = _submission.get(helper.chefs_src_param('soilCharacterMethod'))
        _src_dic['vapourExemption'] = _submission.get(helper.chefs_src_param('vapourExemption'))
        _src_dic['vapourExemptionDesc'] = _submission.get(helper.chefs_src_param('vapourExemptionDesc'))
        _src_dic['vapourCharacterMethodDesc'] = _submission.get(helper.chefs_src_param('vapourCharacterMethodDesc'))
        _src_dic['soilRelocationStartDate'] = helper.convert_simple_datetime_format_in_str(_submission.get(helper.chefs_src_param('soilRelocationStartDate')))
        _src_dic['soilRelocationCompletionDate'] = helper.convert_simple_datetime_format_in_str(_submission.get(helper.chefs_src_param('soilRelocationCompletionDate')))
        _src_dic['relocationMethod'] = _submission.get(helper.chefs_src_param('relocationMethod'))
        _src_dic['qualifiedProfessionalFirstName'] = _submission.get(helper.chefs_src_param('qualifiedProfessionalFirstName'))
        _src_dic['qualifiedProfessionalLastName'] = _submission.get(helper.chefs_src_param('qualifiedProfessionalLastName'))
        _src_dic['qualifiedProfessionalType'] = _submission.get(helper.chefs_src_param('qualifiedProfessionalType'))
        _src_dic['professionalLicenceRegistration'] = _submission.get(helper.chefs_src_param('professionalLicenceRegistration'))
        _src_dic['qualifiedProfessionalOrganization'] = _submission.get(helper.chefs_src_param('qualifiedProfessionalOrganization'))
        _src_dic['qualifiedProfessionalAddress'] = _submission.get(helper.chefs_src_param('qualifiedProfessionalAddress'))
        _src_dic['qualifiedProfessionalCity'] = _submission.get(helper.chefs_src_param('qualifiedProfessionalCity'))
        _src_dic['qualifiedProfessionalProvince'] = _submission.get(helper.chefs_src_param('qualifiedProfessionalProvince'))
        _src_dic['qualifiedProfessionalCountry'] = _submission.get(helper.chefs_src_param('qualifiedProfessionalCountry'))
        _src_dic['qualifiedProfessionalPostalCode'] = _submission.get(helper.chefs_src_param('qualifiedProfessionalPostalCode'))
        _src_dic['qualifiedProfessionalPhoneNumber'] = _submission.get(helper.chefs_src_param('qualifiedProfessionalPhoneNumber'))
        _src_dic['qualifiedProfessionalEmail'] = _submission.get(helper.chefs_src_param('qualifiedProfessionalEmail'))
        _src_dic['signaturerFirstAndLastName'] = _submission.get(helper.chefs_src_param('signaturerFirstAndLastName'))
        _src_dic['dateSigned'] = helper.convert_simple_datetime_format_in_str(_submission.get(helper.chefs_src_param('dateSigned')))
        _src_dic['createAt'] = helper.get_create_date(_submission, helper.chefs_src_param('form'), helper.chefs_src_param('createdAt'))
        _src_dic['confirmationId'] = _confirmation_id
    return _src_dic

def map_rcv_site(_submission, rcv_clz):
    """Mapping receiving site"""
    _rcv_dic = {}
    _confirmation_id = helper.get_confirm_id(
      _submission,
      helper.chefs_rcv_param('form', rcv_clz),
      helper.chefs_rcv_param('confirmationId', rcv_clz))
    if (helper.validate_additional_rcv_site(_submission, rcv_clz) and
        helper.validate_lat_lon(
          _submission.get(helper.chefs_rcv_param('latitudeDegrees', rcv_clz)),
          _submission.get(helper.chefs_rcv_param('latitudeMinutes', rcv_clz)),
          _submission.get(helper.chefs_rcv_param('latitudeSeconds', rcv_clz)),
          _submission.get(helper.chefs_rcv_param('longitudeDegrees', rcv_clz)),
          _submission.get(helper.chefs_rcv_param('longitudeMinutes', rcv_clz)),
          _submission.get(helper.chefs_rcv_param('longitudeSeconds', rcv_clz)),
          _confirmation_id,
          'Soil Relocation Notification Form-Receiving Site')
    ):
        for rcv_header in constant.RECEIVING_SITE_HEADERS:
            _rcv_dic[rcv_header] = None

        _rcv_dic['ownerFirstName'] = _submission.get(helper.chefs_rcv_param('ownerFirstName', rcv_clz))
        _rcv_dic['ownerLastName'] = _submission.get(helper.chefs_rcv_param('ownerLastName', rcv_clz))
        _rcv_dic['ownerCompany'] = _submission.get(helper.chefs_rcv_param('ownerCompany', rcv_clz))
        _rcv_dic['ownerAddress'] = _submission.get(helper.chefs_rcv_param('ownerAddress', rcv_clz))
        _rcv_dic['ownerCity'] = _submission.get(helper.chefs_rcv_param('ownerCity', rcv_clz))
        _rcv_dic['ownerProvince'] = _submission.get(helper.chefs_rcv_param('ownerProvince', rcv_clz))
        _rcv_dic['ownerCountry'] = _submission.get(helper.chefs_rcv_param('ownerCountry', rcv_clz))
        _rcv_dic['ownerPostalCode'] = _submission.get(helper.chefs_rcv_param('ownerPostalCode', rcv_clz))
        _rcv_dic['ownerPhoneNumber'] = _submission.get(helper.chefs_rcv_param('ownerPhoneNumber', rcv_clz))
        _rcv_dic['ownerEmail'] = _submission.get(helper.chefs_rcv_param('ownerEmail', rcv_clz))
        _rcv_dic['owner2FirstName'] = _submission.get(helper.chefs_rcv_param('owner2FirstName', rcv_clz))
        _rcv_dic['owner2LastName'] = _submission.get(helper.chefs_rcv_param('owner2LastName', rcv_clz))
        _rcv_dic['owner2Company'] = _submission.get(helper.chefs_rcv_param('owner2Company', rcv_clz))
        _rcv_dic['owner2Address'] = _submission.get(helper.chefs_rcv_param('owner2Address', rcv_clz))
        _rcv_dic['owner2City'] = _submission.get(helper.chefs_rcv_param('owner2City', rcv_clz))
        _rcv_dic['owner2Province'] = _submission.get(helper.chefs_rcv_param('owner2Province', rcv_clz))
        _rcv_dic['owner2Country'] = _submission.get(helper.chefs_rcv_param('owner2Country', rcv_clz))
        _rcv_dic['owner2PostalCode'] = _submission.get(helper.chefs_rcv_param('owner2PostalCode', rcv_clz))
        _rcv_dic['owner2PhoneNumber'] = _submission.get(helper.chefs_rcv_param('owner2PhoneNumber', rcv_clz))
        _rcv_dic['owner2Email'] = _submission.get(helper.chefs_rcv_param('owner2Email', rcv_clz))
        _rcv_dic['additionalOwners'] = _submission.get(helper.chefs_rcv_param('additionalOwners', rcv_clz))
        _rcv_dic['contactFirstName'] = _submission.get(helper.chefs_rcv_param('contactFirstName', rcv_clz))
        _rcv_dic['contactLastName'] = _submission.get(helper.chefs_rcv_param('contactLastName', rcv_clz))
        _rcv_dic['contactCompany'] = _submission.get(helper.chefs_rcv_param('contactCompany', rcv_clz))
        _rcv_dic['contactAddress'] = _submission.get(helper.chefs_rcv_param('contactAddress', rcv_clz))
        _rcv_dic['contactCity'] = _submission.get(helper.chefs_rcv_param('contactCity', rcv_clz))
        _rcv_dic['contactProvince'] = _submission.get(helper.chefs_rcv_param('contactProvince', rcv_clz))
        _rcv_dic['contactCountry'] = _submission.get(helper.chefs_rcv_param('contactCountry', rcv_clz))
        _rcv_dic['contactPostalCode'] = _submission.get(helper.chefs_rcv_param('contactPostalCode', rcv_clz))
        _rcv_dic['contactPhoneNumber'] = _submission.get(helper.chefs_rcv_param('contactPhoneNumber', rcv_clz))
        _rcv_dic['contactEmail'] = _submission.get(helper.chefs_rcv_param('contactEmail', rcv_clz))
        _rcv_dic['SID'] = _submission.get(helper.chefs_rcv_param('SID', rcv_clz))

        _rcv_lat, _rcv_lon = helper.convert_deciaml_lat_long(
          _submission.get(helper.chefs_rcv_param('latitudeDegrees', rcv_clz)),
          _submission.get(helper.chefs_rcv_param('latitudeMinutes', rcv_clz)),
          _submission.get(helper.chefs_rcv_param('latitudeSeconds', rcv_clz)),
          _submission.get(helper.chefs_rcv_param('longitudeDegrees', rcv_clz)),
          _submission.get(helper.chefs_rcv_param('longitudeMinutes', rcv_clz)),
          _submission.get(helper.chefs_rcv_param('longitudeSeconds', rcv_clz)))
        _rcv_dic['latitude'] = _rcv_lat
        _rcv_dic['longitude'] = _rcv_lon

        _rcv_dic['regionalDistrict'] = helper.create_regional_district(_submission, helper.chefs_rcv_param('regionalDistrict', rcv_clz))
        _rcv_dic['landOwnership'] = helper.create_land_ownership(_submission, helper.chefs_rcv_param('landOwnership', rcv_clz))

        _rcv_dic['legallyTitledSiteAddress'] = _submission.get(helper.chefs_rcv_param('legallyTitledSiteAddress', rcv_clz))
        _rcv_dic['legallyTitledSiteCity'] = _submission.get(helper.chefs_rcv_param('legallyTitledSiteCity', rcv_clz))
        _rcv_dic['legallyTitledSitePostalCode'] = _submission.get(helper.chefs_rcv_param('legallyTitledSitePostalCode', rcv_clz))

        _rcv_dic['PID'], _rcv_dic['legalLandDescription'] = helper.create_pid_pin_and_desc(
          _submission,
          helper.chefs_rcv_param('pidDataGrid', rcv_clz),
          helper.chefs_rcv_param('pid', rcv_clz),
          helper.chefs_rcv_param('pidDesc', rcv_clz))  #PID
        if (_rcv_dic['PID'] is None or _rcv_dic['PID'].strip() == ''): #PIN
            _rcv_dic['PIN'], _rcv_dic['legalLandDescription'] = helper.create_pid_pin_and_desc(
                _submission,
                helper.chefs_rcv_param('pinDataGrid', rcv_clz),
                helper.chefs_rcv_param('pin', rcv_clz),
                helper.chefs_rcv_param('pinDesc', rcv_clz))
        if ((_rcv_dic['PID'] is None or _rcv_dic['PID'].strip() == '')
            and (_rcv_dic['PIN'] is None or _rcv_dic['PIN'].strip() == '')):
                  #Description when selecting 'Untitled Municipal Land'
            _rcv_dic['legalLandDescription'] = helper.create_untitled_municipal_land_desc(
                  _submission,
                  helper.chefs_rcv_param('untitledMunicipalLand', rcv_clz),
                  helper.chefs_rcv_param('untitledMunicipalLandDesc', rcv_clz))

        _rcv_dic['crownLandFileNumbers'] = helper.create_land_file_numbers(
            _submission,
            helper.chefs_rcv_param('crownLandFileNumbers', rcv_clz))
        _rcv_dic['receivingSiteLandUse'] = helper.create_receiving_site_lan_uses(
            _submission,
            helper.chefs_rcv_param('receivingSiteLandUse', rcv_clz))

        _rcv_dic['CSRFactors'] = _submission.get(helper.chefs_rcv_param('CSRFactors', rcv_clz))
        _rcv_dic['relocatedSoilUse'] = _submission.get(helper.chefs_rcv_param('relocatedSoilUse', rcv_clz))
        _rcv_dic['highVolumeSite'] = _submission.get(helper.chefs_rcv_param('highVolumeSite', rcv_clz))
        _rcv_dic['soilDepositIsALR'] = _submission.get(helper.chefs_rcv_param('soilDepositIsALR', rcv_clz))
        _rcv_dic['soilDepositIsReserveLands'] = _submission.get(helper.chefs_rcv_param('soilDepositIsReserveLands', rcv_clz))
        _rcv_dic['dateSigned'] = helper.convert_simple_datetime_format_in_str(_submission.get(helper.chefs_rcv_param('dateSigned', rcv_clz)))
        _rcv_dic['createAt'] = helper.get_create_date(
          _submission,
          helper.chefs_rcv_param('form', rcv_clz),
          helper.chefs_rcv_param('createdAt', rcv_clz))
        _rcv_dic['confirmationId'] = _confirmation_id
    return _rcv_dic

def map_hv_site(_hvs):
    """Mapping HV Site"""
    _hv_dic = {}
    _confirmation_id = helper.get_confirm_id(
      _hvs,
      helper.chefs_hv_param('form'),
      helper.chefs_hv_param('confirmationId'))
    if (helper.validate_lat_lon(
      _hvs.get(helper.chefs_hv_param('latitudeDegrees')),
      _hvs.get(helper.chefs_hv_param('latitudeMinutes')),
      _hvs.get(helper.chefs_hv_param('latitudeSeconds')),
      _hvs.get(helper.chefs_hv_param('longitudeDegrees')),
      _hvs.get(helper.chefs_hv_param('longitudeMinutes')),
      _hvs.get(helper.chefs_hv_param('longitudeSeconds')),
      _confirmation_id,
      'High Volume Receiving Site Form')
    ):
        #print("Mapping high volume site ...")
        for hv_header in constant.HV_SITE_HEADERS:
            _hv_dic[hv_header] = None

        _hv_dic['ownerFirstName'] = _hvs.get(helper.chefs_hv_param('ownerFirstName'))
        _hv_dic['ownerLastName'] = _hvs.get(helper.chefs_hv_param('ownerLastName'))
        _hv_dic['ownerCompany'] = _hvs.get(helper.chefs_hv_param('ownerCompany'))
        _hv_dic['ownerAddress'] = _hvs.get(helper.chefs_hv_param('ownerAddress'))
        _hv_dic['ownerCity'] = _hvs.get(helper.chefs_hv_param('ownerCity'))
        _hv_dic['ownerProvince'] = _hvs.get(helper.chefs_hv_param('ownerProvince'))
        _hv_dic['ownerCountry'] = _hvs.get(helper.chefs_hv_param('ownerCountry'))
        _hv_dic['ownerPostalCode'] = _hvs.get(helper.chefs_hv_param('ownerPostalCode'))
        _hv_dic['ownerPhoneNumber'] = _hvs.get(helper.chefs_hv_param('ownerPhoneNumber'))
        _hv_dic['ownerEmail'] = _hvs.get(helper.chefs_hv_param('ownerEmail'))
        _hv_dic['owner2FirstName'] = _hvs.get(helper.chefs_hv_param('owner2FirstName'))
        _hv_dic['owner2LastName'] = _hvs.get(helper.chefs_hv_param('owner2LastName'))
        _hv_dic['owner2Company'] = _hvs.get(helper.chefs_hv_param('owner2Company'))
        _hv_dic['owner2Address'] = _hvs.get(helper.chefs_hv_param('owner2Address'))
        _hv_dic['owner2City'] = _hvs.get(helper.chefs_hv_param('owner2City'))
        _hv_dic['owner2Province'] = _hvs.get(helper.chefs_hv_param('owner2Province'))
        _hv_dic['owner2Country'] = _hvs.get(helper.chefs_hv_param('owner2Country'))
        _hv_dic['owner2PostalCode'] = _hvs.get(helper.chefs_hv_param('owner2PostalCode'))
        _hv_dic['owner2PhoneNumber'] = _hvs.get(helper.chefs_hv_param('owner2PhoneNumber'))
        _hv_dic['owner2Email'] = _hvs.get(helper.chefs_hv_param('owner2Email'))
        _hv_dic['additionalOwners'] = _hvs.get(helper.chefs_hv_param('additionalOwners'))
        _hv_dic['contactFirstName'] = _hvs.get(helper.chefs_hv_param('contactFirstName'))
        _hv_dic['contactLastName'] = _hvs.get(helper.chefs_hv_param('contactLastName'))
        _hv_dic['contactCompany'] = _hvs.get(helper.chefs_hv_param('contactCompany'))
        _hv_dic['contactAddress'] = _hvs.get(helper.chefs_hv_param('contactAddress'))
        _hv_dic['contactCity'] = _hvs.get(helper.chefs_hv_param('contactCity'))
        _hv_dic['contactProvince'] = _hvs.get(helper.chefs_hv_param('contactProvince'))
        _hv_dic['contactCountry'] = _hvs.get(helper.chefs_hv_param('contactCountry'))
        _hv_dic['contactPostalCode'] = _hvs.get(helper.chefs_hv_param('contactPostalCode'))
        _hv_dic['contactPhoneNumber'] = _hvs.get(helper.chefs_hv_param('contactPhoneNumber'))
        _hv_dic['contactEmail'] = _hvs.get(helper.chefs_hv_param('contactEmail'))
        _hv_dic['SID'] = _hvs.get(helper.chefs_hv_param('SID'))

        _hv_dic['latitude'], _hv_dic['longitude'] = helper.convert_deciaml_lat_long(
          _hvs[helper.chefs_hv_param('latitudeDegrees')],
          _hvs[helper.chefs_hv_param('latitudeMinutes')],
          _hvs[helper.chefs_hv_param('latitudeSeconds')],
          _hvs[helper.chefs_hv_param('longitudeDegrees')],
          _hvs[helper.chefs_hv_param('longitudeMinutes')],
          _hvs[helper.chefs_hv_param('longitudeSeconds')])

        _hv_dic['regionalDistrict'] = helper.create_regional_district(_hvs, helper.chefs_hv_param('regionalDistrict'))
        _hv_dic['landOwnership'] = helper.create_land_ownership(_hvs, helper.chefs_hv_param('landOwnership'))
        _hv_dic['legallyTitledSiteAddress'] = _hvs.get(helper.chefs_hv_param('legallyTitledSiteAddress'))
        _hv_dic['legallyTitledSiteCity'] = _hvs.get(helper.chefs_hv_param('legallyTitledSiteCity'))
        _hv_dic['legallyTitledSitePostalCode'] = _hvs.get(helper.chefs_hv_param('legallyTitledSitePostalCode'))

        _hv_dic['PID'], _hv_dic['legalLandDescription'] = helper.create_pid_pin_and_desc(
          _hvs,
          helper.chefs_hv_param('pidDataGrid'),
          helper.chefs_hv_param('pid'),
          helper.chefs_hv_param('pidDesc')) #PID
        if (_hv_dic['PID'] is None or _hv_dic['PID'].strip() == ''): #PIN
            _hv_dic['PIN'], _hv_dic['legalLandDescription'] = helper.create_pid_pin_and_desc(
                _hvs,
                helper.chefs_hv_param('pinDataGrid'),
                helper.chefs_hv_param('pin'),
                helper.chefs_hv_param('pinDesc'))
        if ((_hv_dic['PID'] is None or _hv_dic['PID'].strip() == '')
            and (_hv_dic['PIN'] is None or _hv_dic['PIN'].strip() == '')):
            #Description when selecting 'Untitled Municipal Land'
            _hv_dic['legalLandDescription'] = helper.create_untitled_municipal_land_desc(
                _hvs,
                helper.chefs_hv_param('untitledMunicipalLand'),
                helper.chefs_hv_param('untitledMunicipalLandDesc'))

        _hv_dic['crownLandFileNumbers'] = helper.create_land_file_numbers(_hvs, helper.chefs_hv_param('crownLandFileNumbers'))
        _hv_dic['receivingSiteLandUse'] = helper.create_receiving_site_lan_uses(_hvs, helper.chefs_hv_param('receivingSiteLandUse'))
        _hv_dic['hvsConfirmation'] = _hvs.get(helper.chefs_hv_param('hvsConfirmation'))
        _hv_dic['dateSiteBecameHighVolume'] = helper.convert_simple_datetime_format_in_str(_hvs.get(helper.chefs_hv_param('dateSiteBecameHighVolume')))
        _hv_dic['howRelocatedSoilWillBeUsed'] = _hvs.get(helper.chefs_hv_param('howRelocatedSoilWillBeUsed'))
        _hv_dic['soilDepositIsALR'] = _hvs.get(helper.chefs_hv_param('soilDepositIsALR'))
        _hv_dic['soilDepositIsReserveLands'] = _hvs.get(helper.chefs_hv_param('soilDepositIsReserveLands'))
        _hv_dic['qualifiedProfessionalFirstName'] = _hvs.get(helper.chefs_hv_param('qualifiedProfessionalFirstName'))
        _hv_dic['qualifiedProfessionalLastName'] = _hvs.get(helper.chefs_hv_param('qualifiedProfessionalLastName'))
        _hv_dic['qualifiedProfessionalType'] = _hvs.get(helper.chefs_hv_param('qualifiedProfessionalType'))
        _hv_dic['qualifiedProfessionalOrganization'] = _hvs.get(helper.chefs_hv_param('qualifiedProfessionalOrganization'))
        _hv_dic['professionalLicenceRegistration'] = _hvs.get(helper.chefs_hv_param('professionalLicenceRegistration'))
        _hv_dic['qualifiedProfessionalAddress'] = _hvs.get(helper.chefs_hv_param('qualifiedProfessionalAddress'))
        _hv_dic['qualifiedProfessionalCity'] = _hvs.get(helper.chefs_hv_param('qualifiedProfessionalCity'))
        _hv_dic['qualifiedProfessionalProvince'] = _hvs.get(helper.chefs_hv_param('qualifiedProfessionalProvince'))
        _hv_dic['qualifiedProfessionalCountry'] = _hvs.get(helper.chefs_hv_param('qualifiedProfessionalCountry'))
        _hv_dic['qualifiedProfessionalPostalCode'] = _hvs.get(helper.chefs_hv_param('qualifiedProfessionalPostalCode'))
        _hv_dic['qualifiedProfessionalPhoneNumber'] = _hvs.get(helper.chefs_hv_param('qualifiedProfessionalPhoneNumber'))
        _hv_dic['qualifiedProfessionalEmail'] = _hvs.get(helper.chefs_hv_param('qualifiedProfessionalEmail'))
        _hv_dic['signaturerFirstAndLastName'] = _hvs.get(helper.chefs_hv_param('signaturerFirstAndLastName'))
        _hv_dic['dateSigned'] = helper.convert_simple_datetime_format_in_str(_hvs.get(helper.chefs_hv_param('dateSigned')))
        _hv_dic['createAt'] = helper.get_create_date(_hvs, helper.chefs_hv_param('form'), helper.chefs_hv_param('createdAt'))
        _hv_dic['confirmationId'] = _confirmation_id
    return _hv_dic

def send_email_subscribers():
    """
    iterate through the submissions and send an email
    only send emails for sites that are new (don't resend for old sites)
    """
    _today = datetime.datetime.now(tz=pytz.timezone('Canada/Pacific'))

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

        if _subscriber.get("emailAddress") is not None:
            _subscriber_email = _subscriber["emailAddress"]
        if _subscriber.get("regionalDistrict") is not None:
            _subscriber_regional_district = _subscriber["regionalDistrict"]
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

            # Notification of soil relocation in selected Regional District(s)  ============
            if _notify_soil_reloc:
                for _srd in _subscriber_regional_district:

                    # finding if subscriber's regional district in receiving site registration
                    _rcv_sites_in_rd = rcvRegDistDic.get(_srd)

                    if _rcv_sites_in_rd is not None:
                        for _receiving_site_dic in _rcv_sites_in_rd:

                            #print('today:',today,',created at:',_receivingSiteDic['createAt'],
                            #'confirm Id:',_receivingSiteDic['confirmationId'])
                            #comparing the submission create date against the current
                            #script runtime.
                            _diff = helper.get_difference_datetimes_in_hour(_today, _receiving_site_dic['createAt'])
                            if (_diff is not None and _diff <= 24):  #within the last 24 hours.
                                _rcv_popup_links = create_popup_links(_rcv_sites_in_rd)
                                _reg_dis_name = helper.convert_regional_district_to_name(_srd)
                                _email_msg = create_site_relocation_email_msg(_reg_dis_name, _rcv_popup_links)

                                # create soil relocation notification substriber dictionary
                                # key-Tuple of email address, RegionalDistrict Tuple,
                                # value=Tuple of email maessage, subscription create date,
                                # subscription confirm id
                                if (_subscriber_email,_srd) not in notify_soil_reloc_subscriber_dic:
                                    notify_soil_reloc_subscriber_dic[(_subscriber_email,_srd)] = (_email_msg, _subscription_created_at, _subscription_confirm_id)
                                    #print("notifySoilRelocSubscriberDic added email:" + 
                                    # _subscriberEmail+ 
                                    # ', region:' + _srd + ', confirm id:'
                                    #      + str(_subscription_confirm_id) + ', 
                                    # subscription created at:' 
                                    # + str(_subscription_created_at))
                                else:
                                    _subscrb_created = notify_soil_reloc_subscriber_dic.get((_subscriber_email,_srd))[1]
                                    if (_subscription_created_at is not None and _subscription_created_at > _subscrb_created):
                                        notify_soil_reloc_subscriber_dic.update({(_subscriber_email,_srd):(_email_msg, _subscription_created_at, _subscription_confirm_id)})
                                        #print("notifySoilRelocSubscriberDic updated email:" + 
                                        # _subscriberEmail+ ', region:' + _srd + ', confirm id:'
                                        #      + str(_subscription_confirm_id) + ', subscription 
                                        # created at:' + str(_subscription_created_at))

            # Notification of high volume site registration
            # in selected Regional District(s) ============================================
            if _notify_hvs:
                for _srd in _subscriber_regional_district:

                    # finding if subscriber's regional district
                    # in high volume receiving site registration
                    _hv_sites_in_rd = hvRegDistDic.get(_srd)

                    if _hv_sites_in_rd is not None:
                        for _hv_site_dic in _hv_sites_in_rd:

                            #print('today:',today,',created at:',_hvSiteDic['createAt'],'
                            # confirm Id:',_hvSiteDic['confirmationId'])
                            # comparing the submission create date against the
                            # current script runtime.
                            _diff = helper.get_difference_datetimes_in_hour(_today, _hv_site_dic['createAt'])
                            if (_diff is not None and _diff <= 24):  #within the last 24 hours.
                                _hv_popup_links = create_popup_links(_hv_sites_in_rd)
                                _hv_reg_dis = helper.convert_regional_district_to_name(_srd)
                                _hv_email_msg = create_hv_site_email_msg(_hv_reg_dis,_hv_popup_links)

                                # create high volume relocation notification substriber dictionary
                                # key-Tuple of email address, RegionalDistrict Tuple, value=Tuple
                                # of email maessage, subscription create date,
                                # subscription confirm id
                                if (_subscriber_email,_srd) not in notify_hvs_subscriber_dic:
                                    notify_hvs_subscriber_dic[(_subscriber_email,_srd)] = (_hv_email_msg, _subscription_created_at, _subscription_confirm_id)
                                    #print("notifyHVSSubscriberDic added email:" +
                                    # _subscriberEmail+ ',
                                    # region:' + _srd + ', confirm id:'
                                    #      + str(_subscription_confirm_id) + ',
                                    # subscription created at:' + str(_subscription_created_at))
                                else:
                                    _subscrb_created = notify_hvs_subscriber_dic.get((_subscriber_email,_srd))[1]
                                    if (_subscription_created_at is not None and _subscription_created_at > _subscrb_created):
                                        notify_hvs_subscriber_dic.update({(_subscriber_email,_srd):(_hv_email_msg, _subscription_created_at, _subscription_confirm_id)})
                                        #print("notifyHVSSubscriberDic updated email:" +
                                        # _subscriberEmail+ ', region:' + _srd + ', confirm id:'
                                        #    + str(_subscription_confirm_id) + ', subscription
                                        # created at:' + str(_subscription_created_at))

        elif (_subscriber_email is not None and _subscriber_email.strip() != '' and
              _subscriber_regional_district is not None and len(_subscriber_regional_district) > 0 and
              _unsubscribe):
            # create unSubscriber list
            for _srd in _subscriber_regional_district:
                if (_subscriber_email,_srd) not in unsubscribers_dic:
                    unsubscribers_dic[(_subscriber_email,_srd)] = _subscription_created_at
                    #print("unSubscribersDic added email:" + _subscriberEmail+ ',
                    # region:' + _srd + ', confirm id:'
                    #      + str(_subscription_confirm_id) + ',
                    # unsubscription created at:' + str(_subscription_created_at))
                else:
                    _unsubscrb_created = unsubscribers_dic.get((_subscriber_email,_srd))
                    if (_subscription_created_at is not None and _subscription_created_at > _unsubscrb_created):
                        unsubscribers_dic.update({(_subscriber_email,_srd):_subscription_created_at})
                        #print("unSubscribersDic updated email:" + _subscriberEmail+ ',
                        # region:' + _srd + ', confirm id:'
                        #    + str( _subscription_confirm_id) + ',
                        # unsubscription created at:' + str(_subscription_created_at))

    print('Removing unsubscribers from notifyHVSSubscriberDic and notifySoilRelocSubscriberDic ...')
    # Processing of data subscribed and unsubscribed by the same email in the same region -
    # This is processed based on the most recent submission date.
    for (_k1_subscriber_email,_k2_srd), _unsubscribe_create_at in unsubscribers_dic.items():
        if (_k1_subscriber_email,_k2_srd) in notify_soil_reloc_subscriber_dic:
            _subscribe_create_at = notify_soil_reloc_subscriber_dic.get((_k1_subscriber_email,_k2_srd))[1]
            _subscribe_confirm_id = notify_soil_reloc_subscriber_dic.get((_k1_subscriber_email,_k2_srd))[2]
            if (_unsubscribe_create_at is not None and _subscribe_create_at is not None and _unsubscribe_create_at > _subscribe_create_at):
                notify_soil_reloc_subscriber_dic.pop((_k1_subscriber_email,_k2_srd))
                #print("remove subscription from notifySoilRelocSubscriberDic
                #  - email:" + _k1_subscriberEmail+ ', region:'
                #      + _k2_srd + ', confirm id:' +str( _subscription_confirm_id) + ',
                #  unsubscription created at:' + str(_unsubscribe_create_at))

        if (_k1_subscriber_email,_k2_srd) in notify_hvs_subscriber_dic:
            _subscribe_create_at = notify_hvs_subscriber_dic.get((_k1_subscriber_email,_k2_srd))[1]
            _subscribe_confirm_id = notify_hvs_subscriber_dic.get((_k1_subscriber_email,_k2_srd))[2]
            if (_unsubscribe_create_at is not None and _subscribe_create_at is not None and _unsubscribe_create_at > _subscribe_create_at):
                notify_hvs_subscriber_dic.pop((_k1_subscriber_email,_k2_srd))
                #print("remove subscription from notifyHVSSubscriberDic - email:" +
                # _k1_subscriberEmail+ ', region:'
                #      + _k2_srd + ', confirm id:' +str( _subscribe_confirm_id) + ',
                # unsubscription created at:' + str(_unsubscribe_create_at))

    print('Sending Notification of soil relocation in selected Regional District(s) ...')
    for _k, _v in notify_soil_reloc_subscriber_dic.items():
        #key:(subscriber email, regional district),
        #value:email message, subscription create date, subscription confirm id)
        _ches_response = helper.send_mail(_k[0], constant.EMAIL_SUBJECT_SOIL_RELOCATION, _v[0])
        if _ches_response is not None and _ches_response.status_code is not None:
            print("[INFO] CHEFS Email response: " + str(_ches_response.status_code) + ", subscriber email: " + _k[0])

    print('Sending Notification of high volume site registration in selected Regional District(s) ...')
    for _k, _v in notify_hvs_subscriber_dic.items():
        #key:(subscriber email, regional district),
        #value:email message, subscription create date, subscription confirm id)
        _ches_response = helper.send_mail(_k[0], constant.EMAIL_SUBJECT_HIGH_VOLUME, _v[0])
        if _ches_response is not None and _ches_response.status_code is not None:
            print("[INFO] CHEFS Email response: " + str(_ches_response.status_code) + ", subscriber email: " + _k[0])


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
    _1rcvDic = map_rcv_site(submission, 1)
    if _1rcvDic:
        receivingSites.append(_1rcvDic)
        helper.add_regional_district_dic(_1rcvDic, rcvRegDistDic)

    _2rcvDic = map_rcv_site(submission, 2)
    if _2rcvDic:
        receivingSites.append(_2rcvDic)
        helper.add_regional_district_dic(_2rcvDic, rcvRegDistDic)

    _3rcvDic = map_rcv_site(submission, 3)
    if _3rcvDic:
        receivingSites.append(_3rcvDic)
        helper.add_regional_district_dic(_3rcvDic, rcvRegDistDic)

print('Creating high volume site records records...')
hvSites = []
hvRegDistDic = {}
for hvs in hvsJson:
    #print('Mapping hv data to the hv site...')
    _hvDic = map_hv_site(hvs)
    if _hvDic:
        hvSites.append(_hvDic)
        helper.add_regional_district_dic(_hvDic, hvRegDistDic)



print('Creating soil source site CSV...')
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
send_email_subscribers()


print('Completed Soils data publishing')

#### to track the version of forms (Sept/26/2022)
# CHEFS generates new vresion of forms when changes of data fields, manages data by each version
# 1.soil relocation form version: v9
# 2.high volume submission version v7
# 3.subscriber form version: v9
