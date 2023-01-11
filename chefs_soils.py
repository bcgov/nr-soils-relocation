# pylint: disable=line-too-long
# pylint: disable=no-member
"""
Retrieve CHEFS form data, overwrite it into AGOL CSVs and Layers,
send notification email to subscribers who want to get information for the soil relocation
"""
import json
import csv
import os
import datetime
import logging
import pytz
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
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
SRC_CSV_ID = os.getenv('SRC_CSV_ID')
SRC_LAYER_ID = os.getenv('SRC_LAYER_ID')
RCV_CSV_ID = os.getenv('RCV_CSV_ID')
RCV_LAYER_ID = os.getenv('RCV_LAYER_ID')
HV_CSV_ID = os.getenv('HV_CSV_ID')
HV_LAYER_ID = os.getenv('HV_LAYER_ID')
LOGLEVEL = os.getenv('LOGLEVEL')

config = helper.read_config()
MAPHUB_URL = config['AGOL']['MAPHUB_URL']

logging.basicConfig(level=LOGLEVEL, format='%(asctime)s [%(levelname)s] %(message)s')

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
        logging.debug(_subscriber)
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

            # Notification of soil relocation in selected Regional District(s)  ================================================================================
            if _notify_soil_reloc:
                for _srd in _subscriber_regional_district:

                    # finding if subscriber's regional district in SOURCE SITE registration  ===================================================================
                    _src_sites_in_rd = srcRegDistDic.get(_srd)

                    if _src_sites_in_rd is not None:
                        for _source_site_dic in _src_sites_in_rd:
                            logging.debug("today:%s, created at:%s confirm Id:%s", _today, _source_site_dic['createAt'], _source_site_dic['confirmationId'])
                            #comparing the submission create date against the current script runtime.
                            _diff = helper.get_difference_datetimes_in_hour(_today, _source_site_dic['createAt'])
                            if (_diff is not None and _diff <= 24):  #within the last 24 hours.
                                _src_popup_links = helper.create_popup_links(_src_sites_in_rd)
                                _src_reg_dis_name = helper.convert_regional_district_to_name(_srd)
                                _src_email_msg = helper.create_site_relocation_email_msg(_src_reg_dis_name, _src_popup_links)

                                # create soil relocation notification substriber dictionary
                                # key-Tuple of email address, RegionalDistrict Tuple,
                                # value=Tuple of email maessage, subscription create date,
                                # subscription confirm id
                                if (_subscriber_email,_srd) not in notify_soil_reloc_subscriber_dic:
                                    notify_soil_reloc_subscriber_dic[(_subscriber_email,_srd)] = (_src_email_msg, _subscription_created_at, _subscription_confirm_id)
                                    logging.debug("notifySoilRelocSubscriberDic added email:%s, region:%s, confirm id:%s, subscription created at:%s",
                                        _subscriber_email, _srd, str(_subscription_confirm_id), str(_subscription_created_at))
                                else:
                                    _subscrb_created = notify_soil_reloc_subscriber_dic.get((_subscriber_email,_srd))[1]
                                    if (_subscription_created_at is not None and _subscription_created_at > _subscrb_created):
                                        notify_soil_reloc_subscriber_dic.update({(_subscriber_email,_srd):(_src_email_msg, _subscription_created_at, _subscription_confirm_id)})
                                        logging.debug("notifySoilRelocSubscriberDic updated email:%s, region:%s, confirm id:%s, subscription created at:%s",
                                            _subscriber_email, _srd, str(_subscription_confirm_id), str(_subscription_created_at))

                    # finding if subscriber's regional district in RECEIVING SITE registration  ===================================================================
                    _rcv_sites_in_rd = rcvRegDistDic.get(_srd)

                    if _rcv_sites_in_rd is not None:
                        for _receiving_site_dic in _rcv_sites_in_rd:
                            logging.debug("today:%s, created at:%s confirm Id:%s", _today, _receiving_site_dic['createAt'], _receiving_site_dic['confirmationId'])
                            #comparing the submission create date against the current script runtime.
                            _diff = helper.get_difference_datetimes_in_hour(_today, _receiving_site_dic['createAt'])
                            if (_diff is not None and _diff <= 24):  #within the last 24 hours.
                                _rcv_popup_links = helper.create_popup_links(_rcv_sites_in_rd)
                                _rcv_reg_dis_name = helper.convert_regional_district_to_name(_srd)
                                _rcv_email_msg = helper.create_site_relocation_email_msg(_rcv_reg_dis_name, _rcv_popup_links)

                                # create soil relocation notification substriber dictionary
                                # key-Tuple of email address, RegionalDistrict Tuple,
                                # value=Tuple of email maessage, subscription create date,
                                # subscription confirm id
                                if (_subscriber_email,_srd) not in notify_soil_reloc_subscriber_dic:
                                    notify_soil_reloc_subscriber_dic[(_subscriber_email,_srd)] = (_rcv_email_msg, _subscription_created_at, _subscription_confirm_id)
                                    logging.debug("notifySoilRelocSubscriberDic added email:%s, region:%s, confirm id:%s, subscription created at:%s", 
                                        _subscriber_email, _srd, str(_subscription_confirm_id), str(_subscription_created_at))
                                else:
                                    _subscrb_created = notify_soil_reloc_subscriber_dic.get((_subscriber_email,_srd))[1]
                                    if (_subscription_created_at is not None and _subscription_created_at > _subscrb_created):
                                        notify_soil_reloc_subscriber_dic.update({(_subscriber_email,_srd):(_rcv_email_msg, _subscription_created_at, _subscription_confirm_id)})
                                        logging.debug("notifySoilRelocSubscriberDic updated email:%s, region:%s, confirm id:%s, subscription created at:%s", 
                                            _subscriber_email, _srd, str(_subscription_confirm_id), str(_subscription_created_at))

            # Notification of high volume site registration in selected Regional District(s) ============================================
            if _notify_hvs:
                for _srd in _subscriber_regional_district:

                    # finding if subscriber's regional district
                    # in high volume receiving site registration
                    _hv_sites_in_rd = hvRegDistDic.get(_srd)

                    if _hv_sites_in_rd is not None:
                        for _hv_site_dic in _hv_sites_in_rd:
                            logging.debug("today:%s, created at:%s, confirm Id:%s", 
                                _today, _hv_site_dic['createAt'], _hv_site_dic['confirmationId'])
                            # comparing the submission create date against the current script runtime.
                            _diff = helper.get_difference_datetimes_in_hour(_today, _hv_site_dic['createAt'])
                            if (_diff is not None and _diff <= 24):  #within the last 24 hours.
                                _hv_popup_links = helper.create_popup_links(_hv_sites_in_rd)
                                _hv_reg_dis = helper.convert_regional_district_to_name(_srd)
                                _hv_email_msg = helper.create_hv_site_email_msg(_hv_reg_dis,_hv_popup_links)

                                # create high volume relocation notification substriber dictionary
                                # key-Tuple of email address, RegionalDistrict Tuple, value=Tuple
                                # of email maessage, subscription create date,
                                # subscription confirm id
                                if (_subscriber_email,_srd) not in notify_hvs_subscriber_dic:
                                    notify_hvs_subscriber_dic[(_subscriber_email,_srd)] = (_hv_email_msg, _subscription_created_at, _subscription_confirm_id)
                                    logging.debug("notifyHVSSubscriberDic added email:%s, region:%s, confirm id:%s ,subscription created at:%s", 
                                        _subscriber_email, _srd, str(_subscription_confirm_id), str(_subscription_created_at))
                                else:
                                    _subscrb_created = notify_hvs_subscriber_dic.get((_subscriber_email,_srd))[1]
                                    if (_subscription_created_at is not None and _subscription_created_at > _subscrb_created):
                                        notify_hvs_subscriber_dic.update({(_subscriber_email,_srd):(_hv_email_msg, _subscription_created_at, _subscription_confirm_id)})
                                        logging.debug("notifyHVSSubscriberDic updated email:%s, region:%s, confirm id:%s, subscription created at:%s", 
                                            _subscriber_email, _srd, str(_subscription_confirm_id), str(_subscription_created_at))

        elif (_subscriber_email is not None and _subscriber_email.strip() != '' and
              _subscriber_regional_district is not None and len(_subscriber_regional_district) > 0 and
              _unsubscribe):
            # create unSubscriber list
            for _srd in _subscriber_regional_district:
                if (_subscriber_email,_srd) not in unsubscribers_dic:
                    unsubscribers_dic[(_subscriber_email,_srd)] = _subscription_created_at
                    logging.debug("unSubscribersDic added email:%s, region:%s, confirm id:%s, unsubscription created at:%s", 
                        _subscriber_email, _srd, str(_subscription_confirm_id), str(_subscription_created_at))
                else:
                    _unsubscrb_created = unsubscribers_dic.get((_subscriber_email,_srd))
                    if (_subscription_created_at is not None and _subscription_created_at > _unsubscrb_created):
                        unsubscribers_dic.update({(_subscriber_email,_srd):_subscription_created_at})
                        logging.debug("unSubscribersDic updated email:%s, region:%s, confirm id:%s, unsubscription created at:%s", 
                            _subscriber_email, _srd, str( _subscription_confirm_id), str(_subscription_created_at))

    logging.info('Removing unsubscribers from notifyHVSSubscriberDic and notifySoilRelocSubscriberDic ...')
    # Processing of data subscribed and unsubscribed by the same email in the same region -
    # This is processed based on the most recent submission date.
    for (_k1_subscriber_email,_k2_srd), _unsubscribe_create_at in unsubscribers_dic.items():
        if (_k1_subscriber_email,_k2_srd) in notify_soil_reloc_subscriber_dic:
            _subscribe_create_at = notify_soil_reloc_subscriber_dic.get((_k1_subscriber_email,_k2_srd))[1]
            _subscribe_confirm_id = notify_soil_reloc_subscriber_dic.get((_k1_subscriber_email,_k2_srd))[2]
            if (_unsubscribe_create_at is not None and _subscribe_create_at is not None and _unsubscribe_create_at > _subscribe_create_at):
                notify_soil_reloc_subscriber_dic.pop((_k1_subscriber_email,_k2_srd))
                logging.debug("remove subscription from notifySoilRelocSubscriberDic - email:%s, region:%s, confirm id:%s, unsubscription created at:%s", 
                    _k1_subscriber_email, _k2_srd, str(_subscribe_confirm_id), str(_unsubscribe_create_at))

        if (_k1_subscriber_email,_k2_srd) in notify_hvs_subscriber_dic:
            _subscribe_create_at = notify_hvs_subscriber_dic.get((_k1_subscriber_email,_k2_srd))[1]
            _subscribe_confirm_id = notify_hvs_subscriber_dic.get((_k1_subscriber_email,_k2_srd))[2]
            if (_unsubscribe_create_at is not None and _subscribe_create_at is not None and _unsubscribe_create_at > _subscribe_create_at):
                notify_hvs_subscriber_dic.pop((_k1_subscriber_email,_k2_srd))
                logging.debug("remove subscription from notifyHVSSubscriberDic - email:%s, region:%s, confirm id:%s, unsubscription created at:%s", 
                    _k1_subscriber_email, _k2_srd, str(_subscribe_confirm_id), str(_unsubscribe_create_at))

    logging.info('Sending Notification of soil relocation in selected Regional District(s) ...')
    for _k, _v in notify_soil_reloc_subscriber_dic.items():
        #key:(subscriber email, regional district),
        #value:email message, subscription create date, subscription confirm id)
        _ches_response = helper.send_single_email(_k[0], constant.EMAIL_SUBJECT_SOIL_RELOCATION, _v[0])
        if _ches_response is not None and _ches_response.status_code is not None:
            logging.info("CHEFS Email response: %s, subscriber email: %s", str(_ches_response.status_code), _k[0])

    logging.info('Sending Notification of high volume site registration in selected Regional District(s) ...')
    for _k, _v in notify_hvs_subscriber_dic.items():
        #key:(subscriber email, regional district),
        #value:email message, subscription create date, subscription confirm id)
        _ches_response = helper.send_single_email(_k[0], constant.EMAIL_SUBJECT_HIGH_VOLUME, _v[0])
        if _ches_response is not None and _ches_response.status_code is not None:
            logging.info("CHEFS Email response: %s, subscriber email: %s", str(_ches_response.status_code), _k[0])


logging.info('Loading Submissions List...')
submissionsJson = helper.site_list(CHEFS_SOILS_FORM_ID, CHEFS_SOILS_API_KEY)
if int(submissionsJson['status']) > 201:
    logging.error("Loading Submissions List failed: %s %s, %s", submissionsJson['status'], submissionsJson['title'], submissionsJson['detail'])
logging.info("%s Submissions are retrived.", len(submissionsJson))
logging.debug(submissionsJson)
logging.info('Loading Submission attributes and headers...')
soilsAttributes = helper.fetch_columns(CHEFS_SOILS_FORM_ID, CHEFS_SOILS_API_KEY)

logging.info('Loading High Volume Sites list...')
hvsJson = helper.site_list(CHEFS_HV_FORM_ID, CHEFS_HV_API_KEY)
if int(hvsJson['status']) > 201:
    logging.error("Loading High Volume Sites list failed: %s %s, %s", hvsJson['status'], hvsJson['title'], hvsJson['detail'])
logging.info("%s High Volume Sites are retrived.", len(hvsJson))
logging.debug(hvsJson)
logging.info('Loading High Volume Sites attributes and headers...')
hvsAttributes = helper.fetch_columns(CHEFS_HV_FORM_ID, CHEFS_HV_API_KEY)

logging.info('Loading submission subscribers list...')
subscribersJson = helper.site_list(CHEFS_MAIL_FORM_ID, CHEFS_MAIL_API_KEY)
if int(subscribersJson['status']) > 201:
    logging.error("Loading submission subscribers list failed: %s %s, %s", subscribersJson['status'], subscribersJson['title'], subscribersJson['detail'])
logging.info("%s Submission Subscribers are retrived.", len(subscribersJson))
logging.debug(subscribersJson)
logging.info('Loading submission subscribers attributes and headers...')
subscribeAttributes = helper.fetch_columns(CHEFS_MAIL_FORM_ID, CHEFS_MAIL_API_KEY)


logging.info('Creating source site, receiving site records...')
sourceSites = []
receivingSites = []
srcRegDistDic = {}
rcvRegDistDic = {}
for submission in submissionsJson:
    logging.debug('Mapping submission data to the source site...')
    _srcDic = helper.map_source_site(submission)
    if _srcDic:
        sourceSites.append(_srcDic)
        helper.add_regional_district_dic(_srcDic, srcRegDistDic)

    logging.debug('Mapping submission data to the receiving site...')
    _1rcvDic = helper.map_rcv_site(submission, 1)
    if _1rcvDic:
        receivingSites.append(_1rcvDic)
        helper.add_regional_district_dic(_1rcvDic, rcvRegDistDic)

    _2rcvDic = helper.map_rcv_site(submission, 2)
    if _2rcvDic:
        receivingSites.append(_2rcvDic)
        helper.add_regional_district_dic(_2rcvDic, rcvRegDistDic)

    _3rcvDic = helper.map_rcv_site(submission, 3)
    if _3rcvDic:
        receivingSites.append(_3rcvDic)
        helper.add_regional_district_dic(_3rcvDic, rcvRegDistDic)

logging.info('Creating high volume site records records...')
hvSites = []
hvRegDistDic = {}
for hvs in hvsJson:
    logging.debug('Mapping hv data to the hv site...')
    _hvDic = helper.map_hv_site(hvs)
    if _hvDic:
        hvSites.append(_hvDic)
        helper.add_regional_district_dic(_hvDic, hvRegDistDic)

logging.info('Creating soil source site CSV...')
with open(constant.SOURCE_CSV_FILE, 'w', encoding='UTF8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=constant.SOURCE_SITE_HEADERS)
    writer.writeheader()
    writer.writerows(sourceSites)

logging.info('Creating soil receiving site CSV...')
with open(constant.RECEIVE_CSV_FILE, 'w', encoding='UTF8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=constant.RECEIVING_SITE_HEADERS)
    writer.writeheader()
    writer.writerows(receivingSites)

logging.info('Creating soil high volume site CSV...')
with open(constant.HIGH_VOLUME_CSV_FILE, 'w', encoding='UTF8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=constant.HV_SITE_HEADERS)
    writer.writeheader()
    writer.writerows(hvSites)


logging.info('Connecting to AGOL GIS...')
_gis = GIS(MAPHUB_URL, username=MAPHUB_USER, password=MAPHUB_PASS)

logging.info('Updating Soil Relocation Soruce Site CSV...')
_srcCsvItem = _gis.content.get(SRC_CSV_ID)
if _srcCsvItem is None:
    logging.error('Source Site CSV Item ID is invalid!')
else:
    _srcCsvUpdateResult = _srcCsvItem.update({}, constant.SOURCE_CSV_FILE)
    logging.info("Updated Soil Relocation Source Site CSV successfully:%s", str(_srcCsvUpdateResult))

    logging.info('Updating Soil Relocation Soruce Site Feature Layer...')
    _srcLyrItem = _gis.content.get(SRC_LAYER_ID)
    if _srcLyrItem is None:
        logging.error('Source Site Layter Item ID is invalid!')
    else:
        _srcFlc = FeatureLayerCollection.fromitem(_srcLyrItem)
        _srcLyrOverwriteResult = _srcFlc.manager.overwrite(constant.SOURCE_CSV_FILE)
        logging.info("Updated Soil Relocation Source Site Feature Layer successfully:%s", json.dumps(_srcLyrOverwriteResult))


logging.info('Updating Soil Relocation Receiving Site CSV...')
_rcvCsvItem = _gis.content.get(RCV_CSV_ID)
if _rcvCsvItem is None:
    logging.error('Receiving Site CSV Item ID is invalid!')
else:
    _rcvCsvUpdateResult = _rcvCsvItem.update({}, constant.RECEIVE_CSV_FILE)
    logging.info("Updated Soil Relocation Receiving Site CSV successfully:%s", str(_rcvCsvUpdateResult))

    logging.info('Updating Soil Relocation Receiving Site Feature Layer...')
    _rcvLyrItem = _gis.content.get(RCV_LAYER_ID)
    if _rcvLyrItem is None:
        logging.error('Receiving Site Layer Item ID is invalid!')
    else:
        _rcvFlc = FeatureLayerCollection.fromitem(_rcvLyrItem)
        _rcvLyrOverwriteResult = _rcvFlc.manager.overwrite(constant.RECEIVE_CSV_FILE)
        logging.info("Updated Soil Relocation Receiving Site Feature Layer successfully:%s", json.dumps(_rcvLyrOverwriteResult))


logging.info('Updating High Volume Receiving Site CSV...')
_hvCsvItem = _gis.content.get(HV_CSV_ID)
if _hvCsvItem is None:
    logging.error('High Volume Receiving Site CSV Item ID is invalid!')
else:
    _hvCsvUpdateResult = _hvCsvItem.update({}, constant.HIGH_VOLUME_CSV_FILE)
    logging.info("Updated High Volume Receiving Site CSV successfully: %s", str(_hvCsvUpdateResult))

    logging.info('Updating High Volume Receiving Site Feature Layer...')
    _hvLyrItem = _gis.content.get(HV_LAYER_ID)
    if _hvLyrItem is None:
        logging.error('High Volume Receiving Site Layer Item ID is invalid!')
    else:
        _hvFlc = FeatureLayerCollection.fromitem(_hvLyrItem)
        _hvLyrOverwriteResult = _hvFlc.manager.overwrite(constant.HIGH_VOLUME_CSV_FILE)
        logging.info("Updated High Volume Receiving Site Feature Layer successfully:%s", json.dumps(_hvLyrOverwriteResult))


logging.info('Checking CHES Health...')
helper.check_ches_health()

logging.info('Sending subscriber emails...')
send_email_subscribers()


logging.info('Completed Soils data publishing')

#### to track the version of forms (Oct/18/2022)
# CHEFS generates new vresion of forms when changes of data fields, manages data by each version
# 1.soil relocation form version: v10
# 2.high volume submission version v8
# 3.subscriber form version: v9
