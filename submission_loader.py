# pylint: disable=line-too-long
"""
Load all site submissions from CHEFS
"""
import os
import logging
import helper


CHEFS_SOILS_FORM_ID = os.getenv('CHEFS_SOILS_FORM_ID')
CHEFS_SOILS_API_KEY = os.getenv('CHEFS_SOILS_API_KEY')
CHEFS_HV_FORM_ID = os.getenv('CHEFS_HV_FORM_ID')
CHEFS_HV_API_KEY = os.getenv('CHEFS_HV_API_KEY')
CHEFS_MAIL_FORM_ID = os.getenv('CHEFS_MAIL_FORM_ID')
CHEFS_MAIL_API_KEY = os.getenv('CHEFS_MAIL_API_KEY')
LOGLEVEL = os.getenv('LOGLEVEL')

logging.basicConfig(level=LOGLEVEL, format='%(asctime)s [%(levelname)s] %(message)s')

def load_submissions():
    """Load all site submissions from CHEFS"""
    logging.info('Loading Submissions List...')
    submissions_json = helper.site_list(CHEFS_SOILS_FORM_ID, CHEFS_SOILS_API_KEY)
    # if int(submissionsJson.get('status')) > 201:
    #     logging.error("Loading Submissions List failed: %s %s, %s", submissionsJson['status'], submissionsJson['title'], submissionsJson['detail'])
    logging.info("%s Submissions are retrived.", len(submissions_json))
    logging.debug(submissions_json)
    # logging.info('Loading Submission attributes and headers...')
    # soilsAttributes = helper.fetch_columns(CHEFS_SOILS_FORM_ID, CHEFS_SOILS_API_KEY)

    logging.info('Loading High Volume Sites list...')
    hvs_json = helper.site_list(CHEFS_HV_FORM_ID, CHEFS_HV_API_KEY)
    # if int(hvsJson.get('status')) > 201:
    #     logging.error("Loading High Volume Sites list failed: %s %s, %s", hvsJson['status'], hvsJson['title'], hvsJson['detail'])
    logging.info("%s High Volume Sites are retrived.", len(hvs_json))
    logging.debug(hvs_json)
    # logging.info('Loading High Volume Sites attributes and headers...')
    # hvsAttributes = helper.fetch_columns(CHEFS_HV_FORM_ID, CHEFS_HV_API_KEY)

    logging.info('Loading submission subscribers list...')
    subscribers_json = helper.site_list(CHEFS_MAIL_FORM_ID, CHEFS_MAIL_API_KEY)
    # if int(subscribersJson.get('status')) > 201:
    #     logging.error("Loading submission subscribers list failed: %s %s, %s", subscribersJson['status'], subscribersJson['title'], subscribersJson['detail'])
    logging.info("%s Submission Subscribers are retrived.", len(subscribers_json))
    logging.debug(subscribers_json)
    # logging.info('Loading submission subscribers attributes and headers...')
    # subscribeAttributes = helper.fetch_columns(CHEFS_MAIL_FORM_ID, CHEFS_MAIL_API_KEY)

    return submissions_json, hvs_json, subscribers_json
