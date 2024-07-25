# pylint: disable=line-too-long
# pylint: disable=no-member
# pylint: disable=too-many-locals
"""
Update source / receiving / high volume site CSV and Layer in AGOL
"""
import json
import os
import logging
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
import constant
import helper

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

helper.load_env()

logging.basicConfig(level=LOGLEVEL, format='%(asctime)s [%(levelname)s] %(message)s')

def agol_items_overwrite():
    """Update source / receiving / high volume site CSV and Layer in AGOL"""
    logging.info('Connecting to AGOL GIS...')
    _gis = GIS(MAPHUB_URL, username=MAPHUB_USER, password=MAPHUB_PASS)

    logging.info('Updating Soil Relocation Soruce Site CSV...')
    _src_csv_item = _gis.content.get(SRC_CSV_ID)
    if _src_csv_item is None:
        logging.error('Source Site CSV Item ID is invalid!')
    else:
        _src_csv_update_result = _src_csv_item.update({}, constant.SOURCE_CSV_FILE)
        logging.info("Updated Soil Relocation Source Site CSV successfully:%s", str(_src_csv_update_result))

        logging.info('Updating Soil Relocation Soruce Site Feature Layer...')
        _src_lyr_item = _gis.content.get(SRC_LAYER_ID)
        if _src_lyr_item is None:
            logging.error('Source Site Layter Item ID is invalid!')
        else:
            _src_flc = FeatureLayerCollection.fromitem(_src_lyr_item)
            _src_lyr_overwrite_result = _src_flc.manager.overwrite(constant.SOURCE_CSV_FILE)
            logging.info("Updated Soil Relocation Source Site Feature Layer successfully:%s", json.dumps(_src_lyr_overwrite_result))


    logging.info('Updating Soil Relocation Receiving Site CSV...')
    _rcv_csv_item = _gis.content.get(RCV_CSV_ID)
    if _rcv_csv_item is None:
        logging.error('Receiving Site CSV Item ID is invalid!')
    else:
        _rcv_csv_update_result = _rcv_csv_item.update({}, constant.RECEIVE_CSV_FILE)
        logging.info("Updated Soil Relocation Receiving Site CSV successfully:%s", str(_rcv_csv_update_result))

        logging.info('Updating Soil Relocation Receiving Site Feature Layer...')
        _rcv_lyr_item = _gis.content.get(RCV_LAYER_ID)
        if _rcv_lyr_item is None:
            logging.error('Receiving Site Layer Item ID is invalid!')
        else:
            _rcv_flc = FeatureLayerCollection.fromitem(_rcv_lyr_item)
            _rcv_lyr_overwrite_result = _rcv_flc.manager.overwrite(constant.RECEIVE_CSV_FILE)
            logging.info("Updated Soil Relocation Receiving Site Feature Layer successfully:%s", json.dumps(_rcv_lyr_overwrite_result))


    logging.info('Updating High Volume Receiving Site CSV...')
    _hv_csv_item = _gis.content.get(HV_CSV_ID)
    if _hv_csv_item is None:
        logging.error('High Volume Receiving Site CSV Item ID is invalid!')
    else:
        _hv_csv_update_result = _hv_csv_item.update({}, constant.HIGH_VOLUME_CSV_FILE)
        logging.info("Updated High Volume Receiving Site CSV successfully: %s", str(_hv_csv_update_result))

        logging.info('Updating High Volume Receiving Site Feature Layer...')
        _hv_lyr_item = _gis.content.get(HV_LAYER_ID)
        if _hv_lyr_item is None:
            logging.error('High Volume Receiving Site Layer Item ID is invalid!')
        else:
            _hv_flc = FeatureLayerCollection.fromitem(_hv_lyr_item)
            _hv_lyr_overwrite_result = _hv_flc.manager.overwrite(constant.HIGH_VOLUME_CSV_FILE)
            logging.info("Updated High Volume Receiving Site Feature Layer successfully:%s", json.dumps(_hv_lyr_overwrite_result))
