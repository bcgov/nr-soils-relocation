# pylint: disable=line-too-long
"""
Map submission data from CHEFS the pre-defined submision dictionaries by sites
"""
import os
import logging
import helper

LOGLEVEL = os.getenv('LOGLEVEL')

logging.basicConfig(level=LOGLEVEL, format='%(asctime)s [%(levelname)s] %(message)s')

def map_sites(submissions_json, hvs_json):
    """Map submission data from CHEFS the pre-defined submision dictionaries by sites"""
    source_sites = []
    src_reg_dist_dic = {}
    receiving_sites = []
    rcv_reg_dist_dic = {}
    hv_sites = []
    hv_reg_dist_dic = {}
    for submission in submissions_json:
        logging.debug('Mapping submission data to the source site...')
        _src_dic = helper.map_source_site(submission)
        if _src_dic:
            source_sites.append(_src_dic)
            helper.add_regional_district_dic(_src_dic, src_reg_dist_dic)

        logging.debug('Mapping submission data to the receiving site...')
        _1rcv_dic = helper.map_rcv_site(submission, 1)
        if _1rcv_dic:
            receiving_sites.append(_1rcv_dic)
            helper.add_regional_district_dic(_1rcv_dic, rcv_reg_dist_dic)

        _2rcv_dic = helper.map_rcv_site(submission, 2)
        if _2rcv_dic:
            receiving_sites.append(_2rcv_dic)
            helper.add_regional_district_dic(_2rcv_dic, rcv_reg_dist_dic)

        _3rcv_dic = helper.map_rcv_site(submission, 3)
        if _3rcv_dic:
            receiving_sites.append(_3rcv_dic)
            helper.add_regional_district_dic(_3rcv_dic, rcv_reg_dist_dic)

    logging.debug('Adding receiving site addresses into source site and source site address into receiving sites...')
    source_sites, receiving_sites = helper.map_source_receiving_site_address(source_sites, receiving_sites)

    logging.info('Creating high volume site records records...')
    for hvs in hvs_json:
        logging.debug('Mapping hv data to the hv site...')
        _hv_dic = helper.map_hv_site(hvs)
        if _hv_dic:
            hv_sites.append(_hv_dic)
            helper.add_regional_district_dic(_hv_dic, hv_reg_dist_dic)

    return source_sites, src_reg_dist_dic, receiving_sites, rcv_reg_dist_dic, hv_sites, hv_reg_dist_dic
