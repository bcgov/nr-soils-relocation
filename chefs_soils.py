# pylint: disable=line-too-long
# pylint: disable=no-member
"""
Retrieve CHEFS form data, overwrite it into AGOL CSVs and Layers,
send notification email to subscribers who want to get information for the soil relocation
"""
import os
import logging
import helper
import csvwriter
import agol
import email_sender

CHEFS_SOILS_FORM_ID = os.getenv('CHEFS_SOILS_FORM_ID')
CHEFS_SOILS_API_KEY = os.getenv('CHEFS_SOILS_API_KEY')
CHEFS_HV_FORM_ID = os.getenv('CHEFS_HV_FORM_ID')
CHEFS_HV_API_KEY = os.getenv('CHEFS_HV_API_KEY')
CHEFS_MAIL_FORM_ID = os.getenv('CHEFS_MAIL_FORM_ID')
CHEFS_MAIL_API_KEY = os.getenv('CHEFS_MAIL_API_KEY')
LOGLEVEL = os.getenv('LOGLEVEL')

logging.basicConfig(level=LOGLEVEL, format='%(asctime)s [%(levelname)s] %(message)s')

logging.info('Loading Submissions List...')
submissionsJson = helper.site_list(CHEFS_SOILS_FORM_ID, CHEFS_SOILS_API_KEY)
# if int(submissionsJson.get('status')) > 201:
#     logging.error("Loading Submissions List failed: %s %s, %s", submissionsJson['status'], submissionsJson['title'], submissionsJson['detail'])
logging.info("%s Submissions are retrived.", len(submissionsJson))
logging.debug(submissionsJson)
logging.info('Loading Submission attributes and headers...')
soilsAttributes = helper.fetch_columns(CHEFS_SOILS_FORM_ID, CHEFS_SOILS_API_KEY)

logging.info('Loading High Volume Sites list...')
hvsJson = helper.site_list(CHEFS_HV_FORM_ID, CHEFS_HV_API_KEY)
# if int(hvsJson.get('status')) > 201:
#     logging.error("Loading High Volume Sites list failed: %s %s, %s", hvsJson['status'], hvsJson['title'], hvsJson['detail'])
logging.info("%s High Volume Sites are retrived.", len(hvsJson))
logging.debug(hvsJson)
logging.info('Loading High Volume Sites attributes and headers...')
hvsAttributes = helper.fetch_columns(CHEFS_HV_FORM_ID, CHEFS_HV_API_KEY)

logging.info('Loading submission subscribers list...')
subscribersJson = helper.site_list(CHEFS_MAIL_FORM_ID, CHEFS_MAIL_API_KEY)
# if int(subscribersJson.get('status')) > 201:
#     logging.error("Loading submission subscribers list failed: %s %s, %s", subscribersJson['status'], subscribersJson['title'], subscribersJson['detail'])
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


logging.debug('Adding receiving site addresses into source site and source site address into receiving sites...')
sourceSites, receivingSites = helper.map_source_receiving_site_address(sourceSites, receivingSites)

logging.info('Creating high volume site records records...')
hvSites = []
hvRegDistDic = {}
for hvs in hvsJson:
    logging.debug('Mapping hv data to the hv site...')
    _hvDic = helper.map_hv_site(hvs)
    if _hvDic:
        hvSites.append(_hvDic)
        helper.add_regional_district_dic(_hvDic, hvRegDistDic)


logging.info('Creating soil source / receiving / high volume site CSV...')
csvwriter.site_csv_writer(sourceSites, receivingSites, hvSites)

logging.info('Updating source / receiving / high volume site CSV and Layer in AGOL...')
agol.agol_updater()

logging.info('Sending notification emails to subscribers...')
email_sender.email_to_subscribers(subscribersJson, srcRegDistDic, rcvRegDistDic, hvRegDistDic)

logging.info('Completed Soils data publishing')

#### to track the version of forms (Jan/12/2023)
# CHEFS generates new vresion of forms when changes of data fields, manages data by each version
# 1.soil relocation form version: v11
# 2.high volume submission version v8
# 3.subscriber form version: v9
