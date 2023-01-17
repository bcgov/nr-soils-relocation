"""
Write source, receive, high volume receiving site CSV files
"""
import csv
import os
import logging
import constant

LOGLEVEL = os.getenv('LOGLEVEL')

logging.basicConfig(level=LOGLEVEL, format='%(asctime)s [%(levelname)s] %(message)s')

def site_csv_writer(source_sites, receiving_sites, hv_sites):
    """Create source, receive, high volume receiving CSV file"""
    logging.info('Creating soil source site CSV...')
    with open(constant.SOURCE_CSV_FILE, 'w', encoding='UTF8', newline='') as source_file:
        writer = csv.DictWriter(source_file, fieldnames=constant.SOURCE_SITE_HEADERS, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(source_sites)

    logging.info('Creating soil receiving site CSV...')
    with open(constant.RECEIVE_CSV_FILE, 'w', encoding='UTF8', newline='') as receive_file:
        writer = csv.DictWriter(receive_file, fieldnames=constant.RECEIVING_SITE_HEADERS, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(receiving_sites)

    logging.info('Creating soil high volume site CSV...')
    with open(constant.HIGH_VOLUME_CSV_FILE, 'w', encoding='UTF8', newline='') as high_volume_file:
        writer = csv.DictWriter(high_volume_file, fieldnames=constant.HV_SITE_HEADERS, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(hv_sites)
