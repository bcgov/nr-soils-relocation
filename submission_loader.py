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

helper.load_env()

logging.basicConfig(level=LOGLEVEL, format='%(asctime)s [%(levelname)s] %(message)s')

def get_versions(chefs_soils_form_version):
    """
    Parse the CHEFS_SOILS_FORM_VERSION string and return a list of trimmed version strings.

    This function takes a string of versions separated by commas, trims any surrounding whitespace
    from each version, and returns a list of the resulting version strings. If the input string
    does not contain any commas, it trims the string and returns it as a single-element list.

    Args:
        chefs_soils_form_version (str): The version string to be parsed.

    Returns:
        list: A list of trimmed version strings.
    """
    if ',' in chefs_soils_form_version:
        return [version.strip() for version in chefs_soils_form_version.split(',')]
    else:
        return [chefs_soils_form_version.strip()]

def load_submissions():
    """Load all site submissions from CHEFS"""
    chefs_loaded = True

    logging.info('Loading Submissions List...')
    submission_loaded = False
    soils_form_versions = []
    submissions_json = []

    if CHEFS_SOILS_FORM_VERSION:
        soils_form_versions = get_versions(CHEFS_SOILS_FORM_VERSION)

    logging.debug("soils_form_versions:%s", soils_form_versions)

    if soils_form_versions:
        for version in soils_form_versions:
            submission_loaded = False
            response = helper.site_list(CHEFS_SOILS_FORM_ID, CHEFS_SOILS_API_KEY, version)
            if isinstance(response, dict) and int(response.get('status')) > 201:
                logging.error("Loading Submissions List failed: %s %s, %s", response['status'], response['title'], response['detail'])
            elif response is None:
                logging.error("Loading Submissions List failed - CHEFS returned none")
            else:
                if isinstance(response, list):
                    submissions_json.extend(response)
                else:
                    submissions_json.append(response)
                submission_loaded = True

            if submission_loaded:
                logging.info("%s submissions from version %s have been loaded.", len(response), version)
            else:
                logging.error("Submissions in version %s failed to load.", version)
            logging.debug(response)

        if len(soils_form_versions) > 1:
            if len(submissions_json) > 0:
                logging.info("%s submissions from version %s have been loaded.", len(submissions_json), soils_form_versions)
            else:
                logging.error("Submissions in version %s failed to load.", soils_form_versions)
    else:
        logging.error("Failed to load env CHEFS_SOILS_FORM_VERSION")

    logging.info('Loading High Volume Sites list...')
    hvs_loaded = False
    hv_form_versions = []
    hvs_json = []

    if CHEFS_HV_FORM_VERSION:
        hv_form_versions = get_versions(CHEFS_HV_FORM_VERSION)

    logging.debug("hv_form_versions:%s", hv_form_versions)

    if hv_form_versions:
        for version in hv_form_versions:
            hvs_loaded = False
            response = helper.site_list(CHEFS_HV_FORM_ID, CHEFS_HV_API_KEY, version)
            if isinstance(response, dict) and int(response.get('status')) > 201:
                logging.error("Loading High Volume Sites list failed: %s %s, %s", response['status'], response['title'], response['detail'])
            elif response is None:
                logging.error("Loading High Volume Sites List failed - CHEFS returned none")
            else:
                if isinstance(response, list):
                    hvs_json.extend(response)
                else:
                    hvs_json.append(response)
                hvs_loaded = True

            if hvs_loaded:
                logging.info("%s High Volume Sites from version %s have been loaded.", len(response), version)
            else:
                logging.error("High Volume Sites in version %s failed to load.", version)
            logging.debug(response)

        if len(hv_form_versions) > 1:
            if len(hvs_json) > 0:
                logging.info("%s High Volume Sites from version %s have been loaded.", len(hvs_json), hv_form_versions)
            else:
                logging.error("High Volume Sites in version %s failed to load.", hv_form_versions)
    else:
        logging.error("Failed to load env CHEFS_HV_FORM_VERSION")

    logging.info('Loading submission subscribers list...')
    subscribers_loaded = False
    mail_form_versions = []
    subscribers_json = []

    if CHEFS_MAIL_FORM_VERSION:
        mail_form_versions = get_versions(CHEFS_MAIL_FORM_VERSION)

    logging.debug("mail_form_versions:%s", mail_form_versions)

    if mail_form_versions:
        for version in mail_form_versions:
            subscribers_loaded = False
            response = helper.site_list(CHEFS_MAIL_FORM_ID, CHEFS_MAIL_API_KEY, version)
            if isinstance(response, dict) and int(response.get('status')) > 201:
                logging.error("Loading submission subscribers list failed: %s %s, %s", response['status'], response['title'], response['detail'])
            elif response is None:
                logging.error("Loading submission subscribers List failed - CHEFS returned none")
            else:
                if isinstance(response, list):
                    subscribers_json.extend(response)
                else:
                    subscribers_json.append(response)
                subscribers_loaded = True

            if subscribers_loaded:
                logging.info("%s Submission Subscribers from version %s have been loaded.", len(response), version)
            logging.debug(response)

        if len(mail_form_versions) > 1:
            if len(subscribers_json) > 0:
                logging.info("%s Submission Subscribers from version %s have been loaded.", len(subscribers_json), mail_form_versions)
            else:
                logging.error("Submission Subscribers in version %s failed to load.", mail_form_versions)
    else:
        logging.error("Failed to load env CHEFS_MAIL_FORM_VERSION")

    chefs_loaded = True if submission_loaded and hvs_loaded and subscribers_loaded else False
    return submissions_json, hvs_json, subscribers_json, chefs_loaded
