# pylint: disable=line-too-long
# pylint: disable=no-member
"""
Retrieve CHEFS form data, overwrite it into AGOL CSVs and Layers,
send notification email to subscribers who want to get information for the soil relocation
"""
import os
import logging
import submission_loader
import submission_mapper
import csv_writer
import agol_updater
import email_sender

LOGLEVEL = os.getenv('LOGLEVEL')
logging.basicConfig(level=LOGLEVEL, format='%(asctime)s [%(levelname)s] %(message)s')

logging.info('Loading Submissions List...')
submissionsJson, hvsJson, subscribersJson = submission_loader.load_submissions()

logging.info('Creating source site, receiving site records...')
sourceSites, srcRegDistDic, receivingSites, rcvRegDistDic, hvSites, hvRegDistDic = submission_mapper.map_sites(submissionsJson, hvsJson)

logging.info('Creating soil source / receiving / high volume site CSV...')
csv_writer.site_csv_writer(sourceSites, receivingSites, hvSites)

logging.info('Updating source / receiving / high volume site CSV and Layer in AGOL...')
agol_updater.agol_items_overwrite()

logging.info('Sending notification emails to subscribers...')
email_sender.email_to_subscribers(subscribersJson, srcRegDistDic, rcvRegDistDic, hvRegDistDic)

logging.info('Completed Soils data publishing')

#### to track the version of forms (Jan/12/2023)
# CHEFS generates new vresion of forms when changes of data fields, manages data by each version
# 1.soil relocation form version: v11
# 2.high volume submission version v8
# 3.subscriber form version: v9
