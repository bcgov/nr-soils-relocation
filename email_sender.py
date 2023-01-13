# pylint: disable=line-too-long
# pylint: disable=no-member
"""
Retrieve CHEFS form data, overwrite it into AGOL CSVs and Layers,
send notification email to subscribers who want to get information for the soil relocation
"""
import os
import datetime
import logging
import pytz
import constant
import helper

LOGLEVEL = os.getenv('LOGLEVEL')

config = helper.read_config()
MAPHUB_URL = config['AGOL']['MAPHUB_URL']

logging.basicConfig(level=LOGLEVEL, format='%(asctime)s [%(levelname)s] %(message)s')

def send_email_subscribers(subscribers_json, src_reg_dist_dic, rcv_reg_dist_dic, hv_reg_dist_dic):
    """
    iterate through the submissions and send an email
    only send emails for sites that are new (don't resend for old sites)
    """
    _today = datetime.datetime.now(tz=pytz.timezone('Canada/Pacific'))

    notify_soil_reloc_subscriber_dic = {}
    notify_hvs_subscriber_dic = {}
    unsubscribers_dic = {}

    for _subscriber in subscribers_json:
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
                    _src_sites_in_rd = src_reg_dist_dic.get(_srd)

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
                    _rcv_sites_in_rd = rcv_reg_dist_dic.get(_srd)

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
                    _hv_sites_in_rd = hv_reg_dist_dic.get(_srd)

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

def email_to_subscribers(subscribers_json, src_reg_dist_dic, rcv_reg_dist_dic, hv_reg_dist_dic):
    """Send notification emails to subscribers"""
    logging.info('Checking CHES Health...')
    helper.check_ches_health()

    logging.info('Sending subscriber emails...')
    send_email_subscribers(subscribers_json, src_reg_dist_dic, rcv_reg_dist_dic, hv_reg_dist_dic)
