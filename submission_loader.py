# pylint: disable=line-too-long
# pylint: disable=simplifiable-if-expression
"""
Load all site submissions from CHEFS
"""
import os
import logging
import helper

CHEFS_SOILS_FORM_ID = os.getenv('CHEFS_SOILS_FORM_ID')
CHEFS_SOILS_API_KEY = os.getenv('CHEFS_SOILS_API_KEY')
CHEFS_SOILS_FORM_VERSION = os.getenv('CHEFS_SOILS_FORM_VERSION')
CHEFS_HV_FORM_ID = os.getenv('CHEFS_HV_FORM_ID')
CHEFS_HV_API_KEY = os.getenv('CHEFS_HV_API_KEY')
CHEFS_HV_FORM_VERSION = os.getenv('CHEFS_HV_FORM_VERSION')
CHEFS_MAIL_FORM_ID = os.getenv('CHEFS_MAIL_FORM_ID')
CHEFS_MAIL_API_KEY = os.getenv('CHEFS_MAIL_API_KEY')
CHEFS_MAIL_FORM_VERSION = os.getenv('CHEFS_MAIL_FORM_VERSION')
LOGLEVEL = os.getenv('LOGLEVEL')

logging.basicConfig(level=LOGLEVEL, format='%(asctime)s [%(levelname)s] %(message)s')

def load_submissions():
    """Load all site submissions from CHEFS"""
    chefs_loaded = True
    submission_loaded = True
    submissions_json = helper.site_list(CHEFS_SOILS_FORM_ID, CHEFS_SOILS_API_KEY, CHEFS_SOILS_FORM_VERSION)
    if isinstance(submissions_json, dict) and int(submissions_json.get('status')) > 201:
        logging.error("Loading Submissions List failed: %s %s, %s", submissions_json['status'], submissions_json['title'], submissions_json['detail'])
        submission_loaded = False
    elif submissions_json is None:
        logging.error("Loading Submissions List failed - CHEFS returned none")
        submission_loaded = False

    if submission_loaded:
        logging.info("%s Submissions are retrived.", len(submissions_json))
    logging.debug(submissions_json)

    logging.info('Loading High Volume Sites list...')
    hvs_loaded = True
    hvs_json = helper.site_list(CHEFS_HV_FORM_ID, CHEFS_HV_API_KEY, CHEFS_HV_FORM_VERSION)
    if isinstance(hvs_json, dict) and int(hvs_json.get('status')) > 201:
        logging.error("Loading High Volume Sites list failed: %s %s, %s", hvs_json['status'], hvs_json['title'], hvs_json['detail'])
        hvs_loaded = False
    elif hvs_json is None:
        logging.error("Loading High Volume Sites List failed - CHEFS returned none")
        hvs_loaded = False

    if hvs_loaded:
        logging.info("%s High Volume Sites are retrived.", len(hvs_json))
    logging.debug(hvs_json)

    logging.info('Loading submission subscribers list...')
    subscribers_loaded = True
    subscribers_json = helper.site_list(CHEFS_MAIL_FORM_ID, CHEFS_MAIL_API_KEY, CHEFS_MAIL_FORM_VERSION)
    if isinstance(subscribers_json, dict) and int(subscribers_json.get('status')) > 201:
        logging.error("Loading submission subscribers list failed: %s %s, %s", subscribers_json['status'], subscribers_json['title'], subscribers_json['detail'])
        subscribers_loaded = False
    elif subscribers_json is None:
        logging.error("Loading submission subscribers List failed - CHEFS returned none")
        subscribers_loaded = False

    if subscribers_loaded:
        logging.info("%s Submission Subscribers are retrived.", len(subscribers_json))
    logging.debug(subscribers_json)

    chefs_loaded = True if submission_loaded and hvs_loaded and subscribers_loaded else False
    return submissions_json, hvs_json, subscribers_json, chefs_loaded
