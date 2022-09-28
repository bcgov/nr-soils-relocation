import json, csv, copy, os
import urllib.parse
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
import helper
import datetime
import pytz
from pytz import timezone

#### to track the version of forms (Sept/26/2022)
# CHEFS generates new vresion of forms when changes of data fields, manages data by each version
# 1.soil relocation form version: v9
# 2.high volume submission version v7
# 3.subscriber form version: v9

config = helper.read_config()
MAPHUB_URL = config['AGOL']['MAPHUB_URL']
WEBMAP_POPUP_URL = config['AGOL']['WEBMAP_POPUP_URL']
SOURCE_CSV_FILE = config['CSV']['SOURCE_CSV_FILE']
RECEIVE_CSV_FILE = config['CSV']['RECEIVE_CSV_FILE']
HIGH_VOLUME_CSV_FILE = config['CSV']['HIGH_VOLUME_CSV_FILE']
SRC_CSV_ID = config['AGOL_ITEMS']['SRC_CSV_ID']
SRC_LAYER_ID = config['AGOL_ITEMS']['SRC_LAYER_ID']
RCV_CSV_ID = config['AGOL_ITEMS']['RCV_CSV_ID']
RCV_LAYER_ID = config['AGOL_ITEMS']['RCV_LAYER_ID']
HV_CSV_ID = config['AGOL_ITEMS']['HV_CSV_ID']
HV_LAYER_ID = config['AGOL_ITEMS']['HV_LAYER_ID']
WEB_MAP_APP_ID = config['AGOL_ITEMS']['WEB_MAP_APP_ID']


REGIONAL_DISTRICT_NAME_DIC = dict(regionalDistrictOfBulkleyNechako='Regional District of Bulkley-Nechako'
                                , caribooRegionalDistrict='Cariboo Regional District'
                                , regionalDistrictOfFraserFortGeorge='Regional District of Fraser-Fort George'
                                , regionalDistrictOfKitimatStikine='Regional District of Kitimat-Stikine'
                                , peaceRiverRegionalDistrict='Peace River Regional District'
                                , northCoastRegionalDistrict='North Coast Regional District'
                                , regionalDistrictOfCentralOkanagan='Regional District of Central Okanagan'
                                , fraserValleyRegionalDistrict='Fraser Valley Regional District'
                                , metroVancouverRegionalDistrict='Metro Vancouver Regional District'
                                , regionalDistrictOfOkanaganSimilkameen='Regional District of Okanagan-Similkameen'
                                , squamishLillooetRegionalDistrict='Squamish-Lillooet Regional District'
                                , thompsonNicolaRegionalDistrict='Thompson-Nicola Regional District'
                                , regionalDistrictOfCentralKootenay='Regional District of Central Kootenay'
                                , columbiaShuswapRegionalDistrict='Columbia-Shuswap Regional District'
                                , regionalDistrictOfEastKootenay='Regional District of East Kootenay'
                                , regionalDistrictOfKootenayBoundary='Regional District of Kootenay Boundary'
                                , regionalDistrictOfNorthOkanagan='Regional District of North Okanagan'
                                , regionalDistrictOfAlberniClayoquot='Regional District of Alberni-Clayoquot'
                                , capitalRegionalDistrict='Capital Regional District'
                                , centralCoastRegionalDistrict='Central Coast Regional District'
                                , comoxValleyRegionalDistrict='Comox Valley Regional District'
                                , cowichanValleyRegionalDistrict='Cowichan Valley Regional District'
                                , regionalDistrictOfNanaimo='Regional District of Nanaimo'
                                , regionalDistrictOfMountWaddington='Regional District of Mount Waddington'
                                , qathetRegionalDistrict='qathet Regional District'
                                , sunshineCoastRegionalDistrict='Sunshine Coast Regional District'
                                , strathconaRegionalDistrict='Strathcona Regional District'
                                , stikineRegionUnincorporated='Stikine Region (Unincorporated)')

SOURCE_SITE_USE_NAME_DIC = dict(a1='A1. adhesives manufacturing, bulk storage, shipping or handling'
                                , a2='A2. chemical manufacturing, bulk storage, shipping or handling'
                                , a3='A3. explosives or ammunition manufacturing, bulk storage, shipping or handling'
                                , a4='A4. fire retardant manufacturing, bulk storage, shipping or handling'
                                , a5='A5. fertilizer manufacturing, bulk storage, shipping or handling'
                                , a6='A6. ink or dye manufacturing, bulk storage, shipping or handling'
                                , a7='A7. leather or hides tanning'
                                , a8='A8. paint, lacquer or varnish manufacturing, formulation, recycling, bulk storage, shipping or handling, not including retail stores'
                                , a9='A9. pharmaceutical products, or controlled substances as defined in the Controlled Drugs and Substances Act (Canada), manufacturing or operations'
                                , a10='A10. plastic products (foam or expanded plastic) manufacturing or repurposing'
                                , none='None'
                                , a11='A11. textile dyeing'
                                , a12='A12. pesticide manufacturing, formulation, bulk storage, shipping or handling'
                                , a13='A13. resin or plastic monomer manufacturing, formulation, bulk storage, shipping or handling'
                                , b1='B1. battery manufacturing, recycling, bulk storage, shipping or handling'
                                , b2='B2. facilities using equipment that contains PCBs greater than or equal to 50 ppm'
                                , b3='B3. electrical equipment manufacturing, refurbishing, bulk storage, shipping or handling'
                                , b4='B4. electrical transmission or distribution substations'
                                , b5='B5. electronic equipment manufacturing'
                                , b6='B6. transformer oil manufacturing, processing, bulk storage, shipping or handling'
                                , b7='B7. electrical power generating operations fuelled by coal or petroleum hydrocarbons that supply electricity to a community or commercial or industrial operation, excluding emergency generators'
                                , c1='C1. foundries'
                                , c2='C2. galvanizing'
                                , c3='C3. metal plating or finishing'
                                , c4='C4. metal salvage operations'
                                , c5='C5. metal smelting or refining'
                                , c6='C6. welding or machine shops (repair or fabrication)'
                                , d1='D1. asbestos mining, milling, bulk storage, shipping or handling'
                                , d2='D2. coal coke manufacture, bulk storage, shipping or handling'
                                , d3='D3. coal or lignite mining, milling, bulk storage, shipping or handling'
                                , d4='D4. milling reagent manufacture, bulk storage, shipping or handling'
                                , d5='D5. metal concentrate bulk storage, shipping or handling'
                                , d6='D6. metal ore mining or milling'
                                , e1='E1. appliance, equipment or engine maintenance, repair, reconditioning, cleaning or salvage'
                                , e2='E2. ash deposit from boilers, incinerators or other thermal facilities'
                                , e3='E3. asphalt and asphalt tar manufacture, storage and distribution, including stationary asphalt batch plants'
                                , e4='E4. coal gasification (manufactured gas production)'
                                , e5='E5. medical, chemical, radiological or biological laboratories'
                                , e6='E6. outdoor firearm shooting ranges'
                                , e7='E7. road salt or brine storage'
                                , e8='E8. measuring instruments (containing mercury) manufacture, repair or bulk storage'
                                , e9='E9. dry cleaning facilities or operations and dry cleaning chemical storage, excluding locations at which clothing is deposited but no dry cleaning process occurs'
                                , e10='E10. contamination or likely contamination of land by substances migrating from an industrial or commercial site'
                                , e11='E11. fire training facilities at which fire retardants are used'
                                , e12='E12. single or cumulative spills to the environment greater than the reportable quantities of substances listed in the Spill Reporting Regulation'
                                , f1='F1. petroleum or natural gas drilling'
                                , f2='F2. petroleum or natural gas production facilities'
                                , f3='F3. natural gas processing'
                                , f4='F4. petroleum coke manufacture, bulk storage, shipping or handling'
                                , f5='F5. petroleum product, other than compressed gas, dispensing facilities, including service stations and card locks'
                                , f6='F6. petroleum, natural gas or sulfur pipeline rights of way excluding rights of way for pipelines used to distribute natural gas to consumers in a community'
                                , f7='F7. petroleum product (other than compressed gas), or produced water storage in non-mobile above ground or underground tanks, except tanks associated with emergency generators or with secondary containment'
                                , f8='F8. petroleum product, other than compressed gas, bulk storage or distribution'
                                , f9='F9. petroleum refining'
                                , f10='F10. solvent manufacturing, bulk storage, shipping or handling'
                                , f11='F11. sulfur handling, processing or bulk storage and distribution'
                                , g1='G1. aircraft maintenance, cleaning or salvage'
                                , g2='G2. automotive, truck, bus, subway or other motor vehicle maintenance, repair, salvage or wrecking'
                                , g3='G3. dry docks, marinas, ship building or boat repair and maintenance, including paint removal from hulls'
                                , g4='G4. marine equipment salvage'
                                , g5='G5. rail car or locomotive maintenance, cleaning, salvage or related uses, including railyards'
                                , h1='H1. antifreeze bulk storage, recycling, shipping or handling'
                                , h2='H2. barrel, drum or tank reconditioning or salvage'
                                , h3='H3. biomedical waste disposal'
                                , h4='H4. bulk manure stockpiling and high rate land application or disposal (nonfarm applications only)'
                                , h5='H5. landfilling of construction demolition material, including without limitation asphalt and concrete'
                                , h6='H6. contaminated soil or sediment storage, treatment, deposit or disposal'
                                , h7l='H7. dry cleaning waste disposal'
                                , h8='H8. electrical equipment recycling'
                                , h9='H9. industrial waste lagoons or impoundments'
                                , h10='H10. industrial waste storage, recycling or landfilling'
                                , h11='H11. industrial woodwaste (log yard waste, hogfuel) disposal'
                                , h12='H12. mine tailings waste disposal'
                                , h13='H13. municipal waste storage, recycling, composting or landfilling'
                                , h14='H14. organic or petroleum material landspreading (landfarming)'
                                , h15='H15. sandblasting operations or sandblasting waste disposal'
                                , h16='H16. septic tank pumpage storage or disposal'
                                , h7='H17. sewage lagoons or impoundments'
                                , h18='H18. hazardous waste storage, treatment or disposal'
                                , h19='H19. sludge drying or composting'
                                , h20='H20. municipal or provincial road snow removal dumping or yard snow removal dumping'
                                , h21='H21. waste oil reprocessing, recycling or bulk storage'
                                , h22='H22. wire reclaiming operations'
                                , i1='I1. particle or wafer board manufacturing'
                                , i2='I2. pulp mill operations'
                                , i3='I3. pulp and paper manufacturing'
                                , i4='I4. treated wood storage at the site of treatment'
                                , i5='I5. veneer or plywood manufacturing'
                                , i6='I6. wood treatment (antisapstain or preservation)'
                                , i7='I7. wood treatment chemical manufacturing, bulk storage')

RECEIVING_SITE_USE_NAME_DIC = dict(industrialLandUseIl='Industrial Land Use (IL)'
                                  , commercialLandUseCl='Commercial Land Use (CL)'
                                  , residentialLandUseHighDensityRlhd='Residential Land Use High Density (RLHD)'
                                  , residentialLandUseLowDensityRlld='Residential Land Use Low Density (RLLD)'
                                  , urbanParkLandUsePl='Urban Park Land Use (PL)'
                                  , agriculturalLandUseAl='Agricultural Land Use (AL)'
                                  , wildlandsNaturalLandUseWln='Wildlands Natural Land Use (WLN)'
                                  , wildlandsRevertedLandUseWlr='Wildlands Reverted Land Use (WLR)')

SOIL_QUALITY_NAME_DIC = dict(industrialLandUseIl='Industrial Land Use (IL)'
                            , commercialLandUseCl='Commercial Land Use (CL)'
                            , residentialLandUseHighDensityRlhd='Residential Land Use High Density (RLHD)'
                            , residentialLandUseLowDensityRlld='Residential Land Use Low Density (RLLD)'
                            , urbanParkLandUsePl='Urban Park Land Use (PL)'
                            , agriculturalLandUseAl='Agricultural Land Use (AL)'
                            , wildlandsNaturalLandUseWln='Wildlands Natural Land Use (WLN)'
                            , wildlandsRevertedLandUseWlr='Wildlands Reverted Land Use (WLR)')

LAND_OWNERSHIP_NAME_DIC = dict(titled='Legally Titled, registered property'
                            , untitled='Untitled Crown Land'
                            , untitledMunicipalLand='Untitled Municipal Land')

SOURCE_SITE_HEADERS = [
  "updateToPreviousForm",
  "ownerFirstName",
  "ownerLastName",
  "ownerCompany",
  "ownerAddress",
  "ownerCity",
  "ownerProvince",
  "ownerCountry",
  "ownerPostalCode",
  "ownerPhoneNumber",
  "ownerEmail",
  "owner2FirstName",
  "owner2LastName",
  "owner2Company",
  "owner2Address",
  "owner2City",
  "owner2Province",
  "owner2Country",
  "owner2PostalCode",
  "owner2PhoneNumber",
  "owner2Email",
  "additionalOwners",
  "contactFirstName",
  "contactLastName",
  "contactCompany",
  "contactAddress",
  "contactCity",
  "contactProvince",
  "contactCountry",
  "contactPostalCode",
  "contactPhoneNumber",
  "contactEmail",
  "SID",
  "latitude",
  "longitude",
  "regionalDistrict",
  "landOwnership",
  "legallyTitledSiteAddress",
  "legallyTitledSiteCity",
  "legallyTitledSitePostalCode",
  "PID",
  "legalLandDescription",
  "PIN",
  "crownLandFileNumbers",
  "sourceSiteLandUse",
  "highVolumeSite",
  "soilRelocationPurpose",
  "soilStorageType",
  "soilVolume",
  "soilQuality",
  "soilCharacterMethod",
  "vapourExemption",
  "vapourExemptionDesc",
  "vapourCharacterMethodDesc",
  "soilRelocationStartDate",
  "soilRelocationCompletionDate",
  "relocationMethod",
  "qualifiedProfessionalFirstName",
	"qualifiedProfessionalLastName",
	"qualifiedProfessionalType",
	"professionalLicenceRegistration",
	"qualifiedProfessionalOrganization",
	"qualifiedProfessionalAddress",
	"qualifiedProfessionalCity",
	"qualifiedProfessionalProvince",
	"qualifiedProfessionalCountry",
	"qualifiedProfessionalPostalCode",
	"qualifiedProfessionalPhoneNumber",
	"qualifiedProfessionalEmail",
  "signaturerFirstAndLastName",
  "dateSigned",
  "createAt",
  "confirmationId"
]

RECEIVING_SITE_HEADERS = [
  "ownerFirstName",
  "ownerLastName",
  "ownerCompany",
  "ownerAddress",
  "ownerCity",
  "ownerProvince",
  "ownerCountry",
  "ownerPostalCode",
  "ownerPhoneNumber",
  "ownerEmail",
  "owner2FirstName",
  "owner2LastName",
  "owner2Company",
  "owner2Address",
  "owner2City",
  "owner2Province",
  "owner2Country",
  "owner2PostalCode",  
  "owner2PhoneNumber",
  "owner2Email",
  "additionalOwners",
  "contactFirstName",
  "contactLastName",
  "contactCompany",
  "contactAddress",
  "contactCity",
  "contactProvince",
  "contactCountry",
  "contactPostalCode",  
  "contactPhoneNumber",
  "contactEmail",
  "SID",
  "latitude",
  "longitude",
  "regionalDistrict",
  "landOwnership",
  "legallyTitledSiteAddress",
  "legallyTitledSiteCity",
  "legallyTitledSitePostalCode",
  "PID",
  "legalLandDescription",
  "PIN",
  "crownLandFileNumbers",  
  "receivingSiteLandUse",
  "CSRFactors",
  "relocatedSoilUse",
  "highVolumeSite",
  "soilDepositIsALR",
  "soilDepositIsReserveLands",
  "dateSigned",
  "createAt",
  "confirmationId"
]  

HV_SITE_HEADERS = [
  "ownerFirstName",
  "ownerLastName",
  "ownerCompany",
  "ownerAddress",
  "ownerCity",
  "ownerProvince",
  "ownerCountry",
  "ownerPostalCode",
  "ownerPhoneNumber",
  "ownerEmail",
  "owner2FirstName",
  "owner2LastName",
  "owner2Company",
  "owner2Address",
  "owner2City",
  "owner2Province",
  "owner2Country",
  "owner2PostalCode",
  "owner2PhoneNumber",
  "owner2Email",
  "additionalOwners",
  "contactFirstName",
  "contactLastName",
  "contactCompany",
  "contactAddress",
  "contactCity",
  "contactProvince",
  "contactCountry",
  "contactPostalCode",
  "contactPhoneNumber",
  "contactEmail",
  "SID",
  "latitude",
  "longitude",
  "regionalDistrict",  
  "landOwnership",
  "legallyTitledSiteAddress",
  "legallyTitledSiteCity",
  "legallyTitledSitePostalCode",
  "PID",
  "legalLandDescription",
  "PIN",
  "crownLandFileNumbers",
  "receivingSiteLandUse",
  "hvsConfirmation",
  "dateSiteBecameHighVolume",
  "howRelocatedSoilWillBeUsed",
  "soilDepositIsALR",
  "soilDepositIsReserveLands",
  "qualifiedProfessionalFirstName",
  "qualifiedProfessionalLastName",
  "qualifiedProfessionalType",
  "professionalLicenceRegistration",
  "qualifiedProfessionalOrganization",
  "qualifiedProfessionalAddress",
  "qualifiedProfessionalCity",
  "qualifiedProfessionalProvince",
  "qualifiedProfessionalCountry",
  "qualifiedProfessionalPostalCode",
  "qualifiedProfessionalPhoneNumber",
  "qualifiedProfessionalEmail",
  "signaturerFirstAndLastName",
  "dateSigned",
  "createAt",
  "confirmationId"
]

DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'



def convert_regional_district_to_name(id):
  name = REGIONAL_DISTRICT_NAME_DIC.get(id)
  if name is not None:
    return name
  else:
    return id

def convert_source_site_use_to_name(id):
  name = SOURCE_SITE_USE_NAME_DIC.get(id)
  if name is not None:
    return name
  else:
    return id

def convert_receiving_site_use_to_name(id):
  name = RECEIVING_SITE_USE_NAME_DIC.get(id)
  if name is not None:
    return name
  else:
    return id

def convert_soil_quality_to_name(id):
  name = SOIL_QUALITY_NAME_DIC.get(id)
  if name is not None:
    return name
  else:
    return id

def convert_land_ownership_to_name(id):
  name = LAND_OWNERSHIP_NAME_DIC.get(id)
  if name is not None:
    return name
  else:
    return id

def create_popup_link_body(_site_dic):
  _link_body = ''

  if _site_dic['SID'] is not None and _site_dic['SID'].strip() != '':
    _link_body = urllib.parse.quote(_site_dic['SID']) #Site ID
  elif _site_dic['PID'] is not None and _site_dic['PID'].strip() != '':
    _link_body = urllib.parse.quote(_site_dic['PID']) #PID
  elif _site_dic['PIN'] is not None and _site_dic['PIN'].strip() != '':
    _link_body = urllib.parse.quote(_site_dic['PIN']) #PIN
  elif _site_dic['latitude'] is not None and _site_dic['longitude'] is not None:
    _link_body = urllib.parse.quote(str(_site_dic['latitude'])+','+str(_site_dic['latitude'])) #Site lat/lon
  elif _site_dic['ownerAddress'] is not None and _site_dic['ownerAddress'].strip() != '':
    _link_body = urllib.parse.quote(_site_dic['ownerAddress']) #Site Owner Address
  elif _site_dic['ownerCompany'] is not None and _site_dic['ownerCompany'].strip() != '':
    _link_body = urllib.parse.quote(_site_dic['ownerCompany'])  #Site Owner Company  

  return _link_body

# create links to popup on Map using receiving sites searching keywords
def create_popup_links(sites, site_type):
  _popup_links = '' 

  if sites is not None:
    for _site_dic in sites:
      _link_body = create_popup_link_body(_site_dic)

      # create popup link
      if _link_body != '' and (site_type  == 'SR' or site_type  == 'HV'): #SR: for Soil Relocation Notication, HV: High Volume Receiving Notification
        _link = '<a href=' + WEBMAP_POPUP_URL + '?id=' + WEB_MAP_APP_ID + '&find=' 
        _link += _link_body
        if site_type  == 'SR':
          _link += '>Link to new submission</a><br/>'
        elif site_type  == 'HV':
          _link += '>Link to new high volume receiving site registration</a><br/>'

      _popup_links += _link
  return _popup_links

def create_land_file_numbers(cefs_dic, field):
  _land_file_numbers = []
  if cefs_dic.get(field) is not None : 
    for _item in cefs_dic[field]:
      for _v in _item.values():
        if _v != '':
          _land_file_numbers.append(_v)

  if len(_land_file_numbers) > 0: 
    _land_file_numbers = "\"" + ",".join(_land_file_numbers) + "\""   # could be more than one    

  return _land_file_numbers if len(_land_file_numbers) > 0 else None

def create_receiving_site_lan_uses(cefs_dic, field):
  _land_uses = []
  for _k, _v in cefs_dic[field].items():
    if _v == True:
      _land_uses.append(convert_receiving_site_use_to_name(_k))
  if len(_land_uses) > 0:
    _land_uses = "\"" + ",".join(_land_uses) + "\""
  return _land_uses

def create_regional_district(cefs_dic, field):
  _regional_districts = []

  if cefs_dic.get(field) is not None and len(cefs_dic[field]) > 0 : 
    for _item in cefs_dic[field]:
      _regional_districts.append(convert_regional_district_to_name(_item))
    
    if len(_regional_districts) > 0:
      _regional_districts = "\"" + ",".join(_regional_districts) + "\"" 

  return _regional_districts if len(_regional_districts)  > 0  else None

def create_land_ownership(cefs_dic, field):
  _land_ownership = None
  if cefs_dic.get(field) is not None : 
    _land_ownership = convert_land_ownership_to_name(cefs_dic[field])
  return _land_ownership

def create_site_relocation_email_msg(regional_district, popup_links):
  msg = '<p>Soil Relocation Notifications are received by the ministry under section 55 of the <i>Environmental Management Act</i>. For more information on soil relocation from commercial and industrial sites in BC, please visit our <a href=https://soil-relocation-information-system-governmentofbc.hub.arcgis.com/>webpage</a>.</p>'
  msg += '<p>This email is to notify you that soil is being relocated in the Regional District: <span style=font-weight:bold;color:red;>' 
  msg += regional_district
  msg += '</span></p>'

  if popup_links != "" and popup_links is not None:
    msg += '<p>The following new submission(s) were received.<p/>\
            <p font-style:italic>'
    msg += popup_links
    msg += '</p><br/>'
    msg += '<p><hr style=height:1px;border-top:dotted;color:#1c1b1b;background-color:#1c1b1b;/></p>\
            <p><b>To search the <a href=https://soil-relocation-information-system-governmentofbc.hub.arcgis.com/>Soil Relocation Information System</a> (SRIS):</b></p>\
            <p>Click on the link above to access the web page containing information on soil movement from commercial and industrial sites in BC.</p>\
            Click &#8216;view&#8217; under the <b>Soil Relocation Dashboard</b> and follow the search instructions below:\
            <ul>\
            <li>click on the small arrow on the left of the screen  to open search options</li>\
            <li>Filter by site address, regional district, high volume sites, and more.</li>\
            <li>On the map, you can zoom to the area you interested in and click on a single location. This will bring up information on that site including the address, volume of soil being moved, start date and finish date of the soil movement.</li>\
            <li>On the map, you can also select a rectangular area and view data in csv format for all sites within that rectangle.</li>\
            </ul>\
            <p>You can also search for information on the <b>Soil Relocation Site Map</b> by clicking on &#8216;view&#8217; under the Soil relocation site map on the main page.'
    msg += '<hr style=height:1px;border:none;color:#1c1b1b;background-color:#1c1b1b;/></p><br/><br/><br/>'
    msg += '<hr style=height:4px;border:none;color:#4da6ff;background-color:#4da6ff;/>'
    msg += '<span style=font-style:italic;color:#4da6ff;>You are receiving this email because you subscribed to receive email notifications of soil relocation or high-volume site registrations in select Regional Districts in BC.  If you wish to stop receiving these email notifications, please select &#8216;unsubscribe&#8217; on the subscription <a href=https://chefs.nrs.gov.bc.ca/app/form/submit?f=' + CHEFS_MAIL_FORM_ID + '>form</a></span>.<br/>'
    msg += '<hr style=height:4px;border:none;color:#4da6ff;background-color:#4da6ff;/>'
  return msg

def create_hv_site_email_msg(regional_district, popup_links):
  msg = '<p>High Volume Receiving Site Registrations are received by the ministry under section 55.1 of the <i>Environmental Management Act</i>. For more information on soil relocation from commercial and industrial sites in BC, please visit our <a href=https://soil-relocation-information-system-governmentofbc.hub.arcgis.com/>webpage</a>.</p>'
  msg += '<p>This email is to notify you that a registration for a high volume site has been received in Regional District: <span style=font-weight:bold;color:red;>'
  msg += regional_district
  msg += '</span></p>'


  if popup_links != "" and popup_links is not None:  
    msg += '<p>The following new high volume receiving site registration(s) were received.<p/>\
            <p font-style:italic>'
    msg += popup_links
    msg += '</p><br/>'


  msg += '<p><hr style=height:1px;border-top:dotted;color:#1c1b1b;background-color:#1c1b1b;/></p>\
            <p><b>To search the <a href=https://soil-relocation-information-system-governmentofbc.hub.arcgis.com/>Soil Relocation Information System</a> (SRIS):</b></p>\
            <p>Click on the link above to access the web page containing information on soil movement from commercial and industrial sites in BC.</p>\
            Click &#8216;view&#8217; under the <b>Soil Relocation Dashboard</b> and follow the search instructions below:\
            <ul>\
            <li>click on the small arrow on the left of the screen to open search options</li>\
            <li>Filter by site address, regional district, high volume sites, and more.</li>\
            <li>On the map, you can zoom to the area you interested in and click on a single location. This will bring up information on that site including the address, volume of soil being moved, start date and finish date of the soil movement</li>\
            <li>On the map, you can also select a rectangular area and view data in csv format for all sites within that rectangle.</li>\
            </ul>\
            <p>You can also search for information on the <b>Soil Relocation Site Map</b> by clicking on &#8216;view&#8217; under the Soil relocation site map on the main page.'
  msg += '<hr style=border-top:dotted;/></p><br/><br/><br/>'
  msg += '<hr style=height:4px;border:none;color:#4da6ff;background-color:#4da6ff;/>'
  msg += '<span style=font-style:italic;color:#4da6ff;>You are receiving this email because you subscribed to receive email notifications of soil relocation or high-volume site registrations in select Regional Districts in BC. If you wish to stop receiving these email notifications, please select &#8216;unsubscribe&#8217; on the subscription <a href=https://chefs.nrs.gov.bc.ca/app/form/submit?f=' + CHEFS_MAIL_FORM_ID + '>form</a></span>.<br/>'
  msg += '<hr style=height:4px;border:none;color:#4da6ff;background-color:#4da6ff;/>'

  return msg

def create_pid_and_desc(chefs_dic, data_grid_field, pid_field, desc_field):
  _pid = None
  _desc = None
  if chefs_dic.get(data_grid_field) is not None and len(chefs_dic[data_grid_field]) > 0: 
    _pids = []
    _descs= []
    for _dg in chefs_dic[data_grid_field]:
      if _dg.get(pid_field) is not None and _dg.get(pid_field) != '':
        _pids.append(_dg.get(pid_field))
        if _dg.get(desc_field) is not None and _dg.get(desc_field).strip() != '':
          if len(chefs_dic[data_grid_field]) > 1:
            _descs.append(_dg.get(pid_field) + ':' + _dg.get(desc_field))
          else:
            _descs.append(_dg.get(desc_field))
    if len(_pids) > 1: 
      _pid = "\"" + ",".join(_pids) + "\""
    elif len(_pids) == 1:
      _pid = _pids[0]

    if len(_descs) > 1:
      _desc = "\"" + ",".join(_descs) + "\""
    elif len(_descs) == 1:
      _desc = _descs[0]
  return _pid, _desc

def create_pin_and_desc(chefs_dic, data_grid_field, pin_field, desc_field):
  _pin = None
  _desc = None
  if chefs_dic.get(data_grid_field) is not None and len(chefs_dic[data_grid_field]) > 0: 
    _pins = []
    _descs= []
    for _dg in chefs_dic[data_grid_field]:
      if _dg.get(pin_field) is not None and _dg.get(pin_field) != '':
        _pins.append(_dg.get(pin_field))
        if _dg.get(desc_field) is not None and _dg.get(desc_field).strip() != '':
          if len(chefs_dic[data_grid_field]) > 1:
            _descs.append(_dg.get(pin_field) + ':' + _dg.get(desc_field))
          else:
            _descs.append(_dg.get(desc_field))
    if len(_pins) > 1: 
      _pin = "\"" + ",".join(_pins) + "\""
    elif len(_pins) == 1:
      _pin = _pins[0]

    if len(_descs) > 1:
      _desc = "\"" + ",".join(_descs) + "\""
    elif len(_descs) == 1:
      _desc = _descs[0]
  return _pin, _desc

def create_untitled_municipal_land_desc(chefs_dic, parent_field, desc_field):
  _desc = None
  if chefs_dic.get(parent_field) is not None and len(chefs_dic.get(parent_field)) > 0: 
    _descs= []
    for _uml in chefs_dic[parent_field]:
      if _uml.get(desc_field) is not None and _uml.get(desc_field).strip() != '':
        _descs.append(_uml.get(desc_field))

    if len(_descs) > 1:
      _desc = "\"" + ",".join(_descs) + "\""
    elif len(_descs) == 1:
      _desc = _descs[0]

  return _desc


def map_source_site(submission):
  _src_dic = {}
  _confirmation_id = helper.get_confirm_id(submission)
  if (helper.validate_lat_lon(submission.get("A3-SourceSiteLatitude-Degrees"), submission.get("A3-SourceSiteLatitude-Minutes"), submission.get("A3-SourceSiteLatitude-Seconds"), 
                              submission.get("A3-SourceSiteLongitude-Degrees"), submission.get("A3-SourceSiteLongitude-Minutes"), submission.get("A3-SourceSiteLongitude-Seconds"),
                              _confirmation_id, 'Soil Relocation Notification Form-Source Site')
  ):  
    #print("Mapping sourece site ...")

    #initialize
    for src_header in SOURCE_SITE_HEADERS:
      _src_dic[src_header] = None

    _src_dic['updateToPreviousForm'] = submission.get("Intro-New_form_or_update")
    _src_dic['ownerFirstName'] = submission.get("A1-FIRSTName")
    _src_dic['ownerLastName'] = submission.get("A1-LASTName")
    _src_dic['ownerCompany'] = submission.get("A1-Company")
    _src_dic['ownerAddress'] = submission.get("A1-Address")
    _src_dic['ownerCity'] = submission.get("A1-City")
    _src_dic['ownerProvince'] = submission.get("A1-ProvinceState")
    _src_dic['ownerCountry'] = submission.get("A1-Country")
    _src_dic['ownerPostalCode'] = submission.get("A1-PostalZipCode")
    _src_dic['ownerPhoneNumber'] = submission.get("A1-Phone")
    _src_dic['ownerEmail'] = submission.get("A1-Email")
    _src_dic['owner2FirstName'] = submission.get("A1-additionalownerFIRSTName")
    _src_dic['owner2LastName'] = submission.get("A1-additionalownerLASTName1")
    _src_dic['owner2Company'] = submission.get("A1-additionalownerCompany1")
    _src_dic['owner2Address'] = submission.get("A1-additionalownerAddress1")
    _src_dic['owner2City'] = submission.get("A1-additionalownerCity1")
    _src_dic['owner2Province'] = submission.get("A1-additionalownerProvinceState2")
    _src_dic['owner2Country'] = submission.get("A1-additionalownerCountry2")
    _src_dic['owner2PostalCode'] = submission.get("A1-additionalownerPostalZipCode1")
    _src_dic['owner2PhoneNumber'] = submission.get("A1-additionalownerPhone1")
    _src_dic['owner2Email'] = submission.get("A1-additionalownerEmail1")
    _src_dic['additionalOwners'] = submission.get("areThereMoreThanTwoOwnersIncludeTheirInformationBelow")
    _src_dic['contactFirstName'] = submission.get("A2-SourceSiteContactFirstName")
    _src_dic['contactLastName'] = submission.get("A2-SourceSiteContactLastName")
    _src_dic['contactCompany'] = submission.get("A2-SourceSiteContactCompany")
    _src_dic['contactAddress'] = submission.get("A2-SourceSiteContactAddress")
    _src_dic['contactCity'] = submission.get("A2-SourceSiteContactCity")
    _src_dic['contactProvince'] = submission.get("A1-sourcesitecontactProvinceState3")
    _src_dic['contactCountry'] = submission.get("A1-sourcesitecontactpersonCountry3")
    _src_dic['contactPostalCode'] = submission.get("A1-sourcesitecontactpersonPostalZipCode2")
    _src_dic['contactPhoneNumber'] = submission.get("SourceSiteContactphoneNumber")
    _src_dic['contactEmail'] = submission.get("A2-SourceSiteContactEmail")
    _src_dic['SID'] = submission.get("A3-SourcesiteIdentificationNumberSiteIdIfAvailable")

    _src_dic['latitude'], _src_dic['longitude'] = helper.convert_deciaml_lat_long(
      submission["A3-SourceSiteLatitude-Degrees"], submission["A3-SourceSiteLatitude-Minutes"], submission["A3-SourceSiteLatitude-Seconds"], 
      submission["A3-SourceSiteLongitude-Degrees"], submission["A3-SourceSiteLongitude-Minutes"], submission["A3-SourceSiteLongitude-Seconds"])

    _src_dic['landOwnership'] = create_land_ownership(submission, 'SourcelandOwnership-checkbox')
    _src_dic['regionalDistrict'] = create_regional_district(submission, 'SourceSiteregionalDistrict')
    _src_dic['legallyTitledSiteAddress'] = submission.get("A-LegallyTitled-AddressSource")
    _src_dic['legallyTitledSiteCity'] = submission.get("A-LegallyTitled-CitySource")
    _src_dic['legallyTitledSitePostalCode'] = submission.get("A-LegallyTitled-PostalZipCodeSource")
    _src_dic['crownLandFileNumbers'] = create_land_file_numbers(submission, 'A-UntitledCrownLand-FileNumberColumnSource')
    #PIN, PIN, description
    _src_dic['PID'], _src_dic['legalLandDescription'] = create_pid_and_desc(submission, 'dataGrid', 'A-LegallyTitled-PID', 'legalLandDescriptionSource')  #PID
    if (_src_dic['PID'] is None or _src_dic['PID'].strip() == ''): #PIN
      _src_dic['PIN'], _src_dic['legalLandDescription'] = create_pin_and_desc(submission, 'dataGrid1', 'A-UntitledPINSource', 'legalLandDescriptionUntitledSource')
    if ((_src_dic['PID'] is None or _src_dic['PID'].strip() == '')
        and (_src_dic['PIN'] is None or _src_dic['PIN'].strip() == '')): #Description when selecting 'Untitled Municipal Land'
      _src_dic['legalLandDescription'] = create_untitled_municipal_land_desc(submission, 'A-UntitledMunicipalLand-PIDColumnSource', 'legalLandDescriptionUntitledMunicipalSource')

    if submission.get("A4-schedule2ReferenceSourceSite") is not None and len(submission.get("A4-schedule2ReferenceSourceSite")) > 0 : 
      _source_site_land_uses = []
      for _ref_source_site in submission.get("A4-schedule2ReferenceSourceSite"):
        _source_site_land_uses.append(convert_source_site_use_to_name(_ref_source_site))
      _src_dic['sourceSiteLandUse'] = "\"" + ",".join(_source_site_land_uses) + "\""

    _src_dic['highVolumeSite'] = submission.get("isTheSourceSiteHighRisk")
    _src_dic['soilRelocationPurpose'] = submission.get("A5-PurposeOfSoilExcavationSource")
    _src_dic['soilStorageType'] = submission.get("B4-currentTypeOfSoilStorageEGStockpiledInSitu1Source")

    if submission.get("dataGrid9") is not None and len(submission["dataGrid9"]) > 0: 
      _dg9 = submission["dataGrid9"][0] # could be more than one, but take only one
      if _dg9.get("B1-soilVolumeToBeRelocationedInCubicMetresM3Source") is not None: 
        # Soil Volume field is double data type, but on the source site CHEFS form,
        # it could be entried string value(e.g xxx) as there is no validation on the form
        _soil_volume = _dg9["B1-soilVolumeToBeRelocationedInCubicMetresM3Source"]
        if not helper.isfloat(_soil_volume):
          _soil_volume = helper.extract_floating_from_string(_soil_volume)
        _src_dic['soilVolume'] = _soil_volume
      if _dg9.get("B1-soilClassificationSource") is not None and len(_dg9.get("B1-soilClassificationSource")) > 0 : 
        for _k, _v in _dg9.get("B1-soilClassificationSource").items():
          if _v == True:
              _src_dic['soilQuality'] = convert_soil_quality_to_name(_k)
              break

    _src_dic['soilCharacterMethod'] = submission.get("B2-describeSoilCharacterizationMethod1")
    _src_dic['vapourExemption'] = submission.get("B3-yesOrNoVapourexemptionsource")
    _src_dic['vapourExemptionDesc'] = submission.get("B3-ifExemptionsApplyPleaseDescribe")
    _src_dic['vapourCharacterMethodDesc'] = submission.get("B3-describeVapourCharacterizationMethod")
    _src_dic['soilRelocationStartDate'] = helper.convert_simple_datetime_format_in_str(submission.get("B4-soilRelocationEstimatedStartDateMonthDayYear"))
    _src_dic['soilRelocationCompletionDate'] = helper.convert_simple_datetime_format_in_str(submission.get("B4-soilRelocationEstimatedCompletionDateMonthDayYear"))
    _src_dic['relocationMethod'] = submission.get("B4-RelocationMethod")
    _src_dic['qualifiedProfessionalFirstName'] = submission.get("D1-FirstNameQualifiedProfessional")
    _src_dic['qualifiedProfessionalLastName'] = submission.get("LastNameQualifiedProfessional")
    _src_dic['qualifiedProfessionalType'] = submission.get("D1-TypeofQP1")
    _src_dic['professionalLicenceRegistration'] = submission.get("D1-professionalLicenseRegistrationEGPEngRpBio")
    _src_dic['qualifiedProfessionalOrganization'] = submission.get("D1-organization1QualifiedProfessional")
    _src_dic['qualifiedProfessionalAddress'] = submission.get("D1-streetAddress1QualifiedProfessional")
    _src_dic['qualifiedProfessionalCity'] = submission.get("D1-city1QualifiedProfessional")
    _src_dic['qualifiedProfessionalProvince'] = submission.get("D1-provinceState3QualifiedProfessional")
    _src_dic['qualifiedProfessionalCountry'] = submission.get("D1-canadaQualifiedProfessional")
    _src_dic['qualifiedProfessionalPostalCode'] = submission.get("D1-postalZipCode3QualifiedProfessional")
    _src_dic['qualifiedProfessionalPhoneNumber'] = submission.get("simplephonenumber1QualifiedProfessional")
    _src_dic['qualifiedProfessionalEmail'] = submission.get("EmailAddressQualifiedProfessional")
    _src_dic['signaturerFirstAndLastName'] = submission.get("sig-firstAndLastNameQualifiedProfessional")
    _src_dic['dateSigned'] = helper.convert_simple_datetime_format_in_str(submission.get("simpledatetime"))
    _src_dic['createAt'] = helper.get_create_date(submission)
    _src_dic['confirmationId'] = _confirmation_id

  return _src_dic

def map_rcv_1st_rcver(submission):
  _rcv_dic = {}
  _confirmation_id = helper.get_confirm_id(submission)
  if (helper.validate_lat_lon(submission.get("C2-Latitude-DegreesReceivingSite"), submission.get("C2-Latitude-MinutesReceivingSite"), submission.get("Section2-Latitude-Seconds1ReceivingSite"), 
                              submission.get("C2-Longitude-DegreesReceivingSite"), submission.get("C2-Longitude-MinutesReceivingSite"), submission.get("C2-Longitude-SecondsReceivingSite"),
                              _confirmation_id, 'Soil Relocation Notification Form-Receiving Site')
  ):  
    #print("Mapping 1st receiver ...")

    for rcv_header in RECEIVING_SITE_HEADERS:
      _rcv_dic[rcv_header] = None

    if submission.get("C1-FirstNameReceivingSiteOwner") is not None : _rcv_dic['ownerFirstName'] = submission["C1-FirstNameReceivingSiteOwner"]
    if submission.get("C1-LastNameReceivingSiteOwner") is not None : _rcv_dic['ownerLastName'] = submission["C1-LastNameReceivingSiteOwner"]
    if submission.get("C1-CompanyReceivingSiteOwner") is not None : _rcv_dic['ownerCompany'] = submission["C1-CompanyReceivingSiteOwner"]
    if submission.get("C1-AddressReceivingSiteOwner") is not None : _rcv_dic['ownerAddress'] = submission["C1-AddressReceivingSiteOwner"]
    if submission.get("C1-CityReceivingSiteOwner") is not None : _rcv_dic['ownerCity'] = submission["C1-CityReceivingSiteOwner"]
    if submission.get("A1-receivingsiteownerProvinceState4") is not None : _rcv_dic['ownerProvince'] = submission["A1-receivingsiteownerProvinceState4"]    
    if submission.get("A1-receivingsiteownerCountry4") is not None : _rcv_dic['ownerCountry'] = submission["A1-receivingsiteownerCountry4"]
    if submission.get("A1-receivingsiteownerPostalCode3") is not None : _rcv_dic['ownerPostalCode'] = submission["A1-receivingsiteownerPostalCode3"]
    if submission.get("C1-PhoneRecevingSiteOwner") is not None : _rcv_dic['ownerPhoneNumber'] = submission["C1-PhoneRecevingSiteOwner"]
    if submission.get("C1-EmailReceivingSiteOwner") is not None : _rcv_dic['ownerEmail'] = submission["C1-EmailReceivingSiteOwner"]

    if submission.get("C1-FirstName1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2FirstName'] = submission["C1-FirstName1ReceivingSiteAdditionalOwners"]
    if submission.get("C1-LastName1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2LastName'] = submission["C1-LastName1ReceivingSiteAdditionalOwners"]
    if submission.get("C1-Company1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2Company'] = submission["C1-Company1ReceivingSiteAdditionalOwners"]
    if submission.get("C1-Address1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2Address'] = submission["C1-Address1ReceivingSiteAdditionalOwners"]
    if submission.get("C1-City1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2City'] = submission["C1-City1ReceivingSiteAdditionalOwners"]
    if submission.get("A1-additionareceivingsiteownerProvinceState5") is not None : _rcv_dic['owner2Province'] = submission["A1-additionareceivingsiteownerProvinceState5"]
    if submission.get("A1-additionareceivingsiteownerCountry5") is not None : _rcv_dic['owner2Country'] = submission["A1-additionareceivingsiteownerCountry5"]
    if submission.get("A1-additionalreceivingsiteownerPostalCode4") is not None : _rcv_dic['owner2PostalCode'] = submission["A1-additionalreceivingsiteownerPostalCode4"]    
    if submission.get("C1-Phone1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2PhoneNumber'] = submission["C1-Phone1ReceivingSiteAdditionalOwners"]
    if submission.get("C1-Email1ReceivingSiteAdditionalOwners") is not None : _rcv_dic['owner2Email'] = submission["C1-Email1ReceivingSiteAdditionalOwners"]

    if submission.get("haveMoreThatTwoOwnersEnterTheirInformationBelow") is not None : _rcv_dic['additionalOwners'] = submission["haveMoreThatTwoOwnersEnterTheirInformationBelow"]
    if submission.get("C2-RSC-FirstName") is not None : _rcv_dic['contactFirstName'] = submission["C2-RSC-FirstName"]
    if submission.get("C2-RSC-LastName") is not None : _rcv_dic['contactLastName'] = submission["C2-RSC-LastName"]
    if submission.get("C2-RSC-Company") is not None : _rcv_dic['contactCompany'] = submission["C2-RSC-Company"]
    if submission.get("C2-RSC-Address") is not None : _rcv_dic['contactAddress'] = submission["C2-RSC-Address"]
    if submission.get("C2-RSC-City") is not None : _rcv_dic['contactCity'] = submission["C2-RSC-City"]
    if submission.get("A1-additionareceivingsitecontactpersonProvinceState6") is not None : _rcv_dic['contactProvince'] = submission["A1-additionareceivingsitecontactpersonProvinceState6"]
    if submission.get("A1-additionareceivingsitecontactpersonCountry6") is not None : _rcv_dic['contactCountry'] = submission["A1-additionareceivingsitecontactpersonCountry6"]
    if submission.get("A1-additionalreceivingsitecontactpersonPostalCode5") is not None : _rcv_dic['contactPostalCode'] = submission["A1-additionalreceivingsitecontactpersonPostalCode5"]
    if submission.get("C2-RSCphoneNumber1") is not None : _rcv_dic['contactPhoneNumber'] = submission["C2-RSCphoneNumber1"]
    if submission.get("C2-RSC-Email") is not None : _rcv_dic['contactEmail'] = submission["C2-RSC-Email"]
    if submission.get("C2-siteIdentificationNumberSiteIdIfAvailableReceivingSite") is not None : _rcv_dic['SID'] = submission["C2-siteIdentificationNumberSiteIdIfAvailableReceivingSite"]

    _rcv_lat, _rcv_lon = helper.convert_deciaml_lat_long(
      submission["C2-Latitude-DegreesReceivingSite"], submission["C2-Latitude-MinutesReceivingSite"], submission["Section2-Latitude-Seconds1ReceivingSite"], 
      submission["C2-Longitude-DegreesReceivingSite"], submission["C2-Longitude-MinutesReceivingSite"], submission["C2-Longitude-SecondsReceivingSite"])
    _rcv_dic['latitude'] = _rcv_lat
    _rcv_dic['longitude'] = _rcv_lon

    _rcv_dic['regionalDistrict'] = create_regional_district(submission, 'ReceivingSiteregionalDistrict')
    _rcv_dic['landOwnership'] = create_land_ownership(submission, 'C2-receivinglandOwnership-checkbox')

    if submission.get("C2-LegallyTitled-AddressReceivingSite") is not None : _rcv_dic['legallyTitledSiteAddress'] = submission["C2-LegallyTitled-AddressReceivingSite"]
    if submission.get("C2-LegallyTitled-CityReceivingSite") is not None : _rcv_dic['legallyTitledSiteCity'] = submission["C2-LegallyTitled-CityReceivingSite"]
    if submission.get("C2-LegallyTitled-PostalReceivingSite") is not None : _rcv_dic['legallyTitledSitePostalCode'] = submission["C2-LegallyTitled-PostalReceivingSite"]

    if submission.get("dataGrid2") is not None and len(submission["dataGrid2"]) > 0: 
      _dg2 = submission["dataGrid2"][0] # could be more than one, but take only one
      if _dg2.get("A-LegallyTitled-PIDReceivingSite") is not None: _rcv_dic['PID'] = _dg2["A-LegallyTitled-PIDReceivingSite"]
      if _dg2.get("legalLandDescriptionReceivingSite") is not None: _rcv_dic['legalLandDescription'] = _dg2["legalLandDescriptionReceivingSite"]
    if (submission.get("dataGrid5") is not None and len(submission["dataGrid5"]) > 0 
        and (_rcv_dic['PID'] is None or _rcv_dic['PID'].strip() == '')): 
      _dg5 = submission["dataGrid5"][0] # could be more than one, but take only one
      if _dg5.get("A-LegallyTitled-PID") is not None: _rcv_dic['PIN'] = _dg5["A-LegallyTitled-PID"]
      if _dg5.get("legalLandDescriptionUntitledCrownLandReceivingSite") is not None: _rcv_dic['legalLandDescription'] = _dg5["legalLandDescriptionUntitledCrownLandReceivingSite"]
    if (submission.get("A-UntitledMunicipalLand-PIDColumn1") is not None and len(submission["A-UntitledMunicipalLand-PIDColumn1"]) > 0 
        and (_rcv_dic['PID'] is None or _rcv_dic['PID'].strip() == '') 
        and (_rcv_dic['PIN'] is None or _rcv_dic['PIN'].strip() == '')):
      _untitled_municipal_land = submission["A-UntitledMunicipalLand-PIDColumn1"][0]
      if _untitled_municipal_land.get("legalLandDescription") is not None:
        _rcv_dic['legalLandDescription'] = _untitled_municipal_land["legalLandDescription"]

    _rcv_dic['crownLandFileNumbers'] = create_land_file_numbers(submission, 'A-UntitledCrownLand-FileNumberColumn1')
    _rcv_dic['receivingSiteLandUse'] = create_receiving_site_lan_uses(submission, 'C3-soilClassification1ReceivingSite')

    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule31ReceivingSite") is not None : _rcv_dic['CSRFactors'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule31ReceivingSite"]
    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule32ReceivingSite") is not None : _rcv_dic['relocatedSoilUse'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule32ReceivingSite"]
    if submission.get("C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime3") is not None : _rcv_dic['highVolumeSite'] = submission["C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime3"]
    if submission.get("D2-receivingsitesoilDepositIsInTheAgriculturalLandReserveAlr1") is not None : _rcv_dic['soilDepositIsALR'] = submission["D2-receivingsitesoilDepositIsInTheAgriculturalLandReserveAlr1"]
    if submission.get("D2-receivingsitesoilDepositIsInTheReserveLands1") is not None : _rcv_dic['soilDepositIsReserveLands'] = submission["D2-receivingsitesoilDepositIsInTheReserveLands1"]
    _rcv_dic['dateSigned'] = helper.convert_simple_datetime_format_in_str(submission.get("simpledatetime"))    
    _rcv_dic['createAt'] = helper.get_create_date(submission)
    _rcv_dic['confirmationId'] = _confirmation_id
  return _rcv_dic

def map_rcv_2nd_rcver(submission):
  _rcv_dic = {}
  _confirmation_id = helper.get_confirm_id(submission)
  if (submission.get('additionalReceivingSites').get('firstAdditionalReceivingSiteInformation') == True and
      helper.validate_lat_lon(submission.get("C2-Latitude-Degrees1FirstAdditionalReceivingSite"), submission.get("C2-Latitude-Minutes1FirstAdditionalReceivingSite"), submission.get("Section2-Latitude-Seconds2FirstAdditionalReceivingSite"), 
                              submission.get("C2-Longitude-Degrees1FirstAdditionalReceivingSite"), submission.get("C2-Longitude-Minutes1FirstAdditionalReceivingSite"), submission.get("C2-Longitude-Seconds1FirstAdditionalReceivingSite"),
                              _confirmation_id, 'Soil Relocation Notification Form-Receiving Site')
  ):  
    #print("Mapping 2nd receiver ...")

    for rcv_header in RECEIVING_SITE_HEADERS:
      _rcv_dic[rcv_header] = None

    if submission.get("C1-FirstName2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerFirstName'] = submission["C1-FirstName2FirstAdditionalReceivingSite"]
    if submission.get("C1-LastName2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerLastName'] = submission["C1-LastName2FirstAdditionalReceivingSite"]
    if submission.get("C1-Company2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerCompany'] = submission["C1-Company2FirstAdditionalReceivingSite"]
    if submission.get("C1-Address2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerAddress'] = submission["C1-Address2FirstAdditionalReceivingSite"]
    if submission.get("C1-City2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerCity'] = submission["C1-City2FirstAdditionalReceivingSite"]
    if submission.get("A1-firstadditionalreceivingsiteownerProvinceState7") is not None : _rcv_dic['ownerProvince'] = submission["A1-firstadditionalreceivingsiteownerProvinceState7"]    
    if submission.get("A1-firstadditionalreceivingsiteownerCountry7") is not None : _rcv_dic['ownerCountry'] = submission["A1-firstadditionalreceivingsiteownerCountry7"]
    if submission.get("A1-firstadditionalreceivingsiteownerPostalCode6") is not None : _rcv_dic['ownerPostalCode'] = submission["A1-firstadditionalreceivingsiteownerPostalCode6"]
    if submission.get("phoneNumber4FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerPhoneNumber'] = submission["phoneNumber4FirstAdditionalReceivingSite"]
    if submission.get("C1-Email2FirstAdditionalReceivingSite") is not None : _rcv_dic['ownerEmail'] = submission["C1-Email2FirstAdditionalReceivingSite"]

    if submission.get("C1-FirstName3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2FirstName'] = submission["C1-FirstName3AdditionalReceivingSiteOwner"]
    if submission.get("C1-LastName3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2LastName'] = submission["C1-LastName3AdditionalReceivingSiteOwner"]
    if submission.get("C1-Company3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2Company'] = submission["C1-Company3AdditionalReceivingSiteOwner"]
    if submission.get("C1-Address3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2Address'] = submission["C1-Address3AdditionalReceivingSiteOwner"]
    if submission.get("C1-City3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2City'] = submission["C1-City3AdditionalReceivingSiteOwner"]
    if submission.get("A1-firstadditionalreceivingmoreownersProvinceState8") is not None : _rcv_dic['owner2Province'] = submission["A1-additionareceivingsiteownerProvinceState5"]
    if submission.get("A1-firstadditionalreceivingmoreownersCountry8") is not None : _rcv_dic['owner2Country'] = submission["A1-firstadditionalreceivingmoreownersCountry8"]
    if submission.get("A1-firstadditionalreceivingmoreownersPostalCode7") is not None : _rcv_dic['owner2PostalCode'] = submission["A1-firstadditionalreceivingmoreownersPostalCode7"]    
    if submission.get("phoneNumber2AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2PhoneNumber'] = submission["phoneNumber2AdditionalReceivingSiteOwner"]
    if submission.get("C1-Email3AdditionalReceivingSiteOwner") is not None : _rcv_dic['owner2Email'] = submission["C1-Email3AdditionalReceivingSiteOwner"]

    if submission.get("C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow2ReceivingSite") is not None : _rcv_dic['additionalOwners'] = submission["C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow2ReceivingSite"]
    if submission.get("C2-RSC-FirstName1AdditionalReceivingSite") is not None : _rcv_dic['contactFirstName'] = submission["C2-RSC-FirstName1AdditionalReceivingSite"]
    if submission.get("C2-RSC-LastName1AdditionalReceivingSite") is not None : _rcv_dic['contactLastName'] = submission["C2-RSC-LastName1AdditionalReceivingSite"]
    if submission.get("C2-RSC-Company1AdditionalReceivingSite") is not None : _rcv_dic['contactCompany'] = submission["C2-RSC-Company1AdditionalReceivingSite"]
    if submission.get("C2-RSC-Address1AdditionalReceivingSite") is not None : _rcv_dic['contactAddress'] = submission["C2-RSC-Address1AdditionalReceivingSite"]
    if submission.get("C2-RSC-City1AdditionalReceivingSite") is not None : _rcv_dic['contactCity'] = submission["C2-RSC-City1AdditionalReceivingSite"]
    if submission.get("A1-firstadditionalreceivingsitecontactProvinceState9") is not None : _rcv_dic['contactProvince'] = submission["A1-firstadditionalreceivingsitecontactProvinceState9"]
    if submission.get("A1-firstadditionalreceivingsitecontactCountry9") is not None : _rcv_dic['contactCountry'] = submission["A1-firstadditionalreceivingsitecontactCountry9"]
    if submission.get("A1-firstadditionalreceivingsitecontactPostalCode8") is not None : _rcv_dic['contactPostalCode'] = submission["A1-firstadditionalreceivingsitecontactPostalCode8"]
    if submission.get("phoneNumber3AdditionalReceivingSite") is not None : _rcv_dic['contactPhoneNumber'] = submission["phoneNumber3AdditionalReceivingSite"]
    if submission.get("C2-RSC-Email1AdditionalReceivingSite") is not None : _rcv_dic['contactEmail'] = submission["C2-RSC-Email1AdditionalReceivingSite"]
    if submission.get("C2-siteIdentificationNumberSiteIdIfAvailable1FirstAdditionalReceivingSite") is not None : _rcv_dic['SID'] = submission["C2-siteIdentificationNumberSiteIdIfAvailable1FirstAdditionalReceivingSite"]

    _rcv_lat, _rcv_lon = helper.convert_deciaml_lat_long(
      submission["C2-Latitude-Degrees1FirstAdditionalReceivingSite"], submission["C2-Latitude-Minutes1FirstAdditionalReceivingSite"], submission["Section2-Latitude-Seconds2FirstAdditionalReceivingSite"], 
      submission["C2-Longitude-Degrees1FirstAdditionalReceivingSite"], submission["C2-Longitude-Minutes1FirstAdditionalReceivingSite"], submission["C2-Longitude-Seconds1FirstAdditionalReceivingSite"])
    _rcv_dic['latitude'] = _rcv_lat
    _rcv_dic['longitude'] = _rcv_lon

    _rcv_dic['regionalDistrict'] = create_regional_district(submission, 'FirstAdditionalReceivingSiteregionalDistrict1')
    _rcv_dic['landOwnership'] = create_land_ownership(submission, 'Firstadditionalreceiving-landOwnership-checkbox1')

    if submission.get("C2-LegallyTitled-Address1FirstAdditionalReceivingSite") is not None : _rcv_dic['legallyTitledSiteAddress'] = submission["C2-LegallyTitled-Address1FirstAdditionalReceivingSite"]
    if submission.get("C2-LegallyTitled-City1FirstAdditionalReceivingSite") is not None : _rcv_dic['legallyTitledSiteCity'] = submission["C2-LegallyTitled-City1FirstAdditionalReceivingSite"]
    if submission.get("C2-LegallyTitled-PostalZipCode1FirstAdditionalReceivingSite") is not None : _rcv_dic['legallyTitledSitePostalCode'] = submission["C2-LegallyTitled-PostalZipCode1FirstAdditionalReceivingSite"]

    if submission.get("dataGrid3") is not None and len(submission["dataGrid3"]) > 0: 
      _dg3 = submission["dataGrid3"][0] # could be more than one, but take only one
      if _dg3.get("A-LegallyTitled-PIDFirstAdditionalReceivingSite") is not None: _rcv_dic['PID'] = _dg3["A-LegallyTitled-PIDFirstAdditionalReceivingSite"]
      if _dg3.get("legalLandDescriptionFirstAdditionalReceivingSite") is not None: _rcv_dic['legalLandDescription'] = _dg3["legalLandDescriptionFirstAdditionalReceivingSite"]
    if (submission.get("dataGrid6") is not None and len(submission["dataGrid6"]) > 0 
        and (_rcv_dic['PID'] is None or _rcv_dic['PID'].strip() == '')): 
      _dg6 = submission["dataGrid6"][0] # could be more than one, but take only one
      if _dg6.get("A-UntitledCrown-PINFirstAdditionalReceivingSite") is not None: _rcv_dic['PIN'] = _dg6["A-UntitledCrown-PINFirstAdditionalReceivingSite"]
      if _dg6.get("legalLandDescriptionUntitledCrownFirstAdditionalReceivingSite") is not None: _rcv_dic['legalLandDescription'] = _dg6["legalLandDescriptionUntitledCrownFirstAdditionalReceivingSite"]
    if (submission.get("A-UntitledMunicipalLand-PIDColumn2") is not None and len(submission["A-UntitledMunicipalLand-PIDColumn2"]) > 0 
        and (_rcv_dic['PID'] is None or _rcv_dic['PID'].strip() == '')
        and (_rcv_dic['PIN'] is None or _rcv_dic['PIN'].strip() == '')):
      _untitled_municipal_land = submission["A-UntitledMunicipalLand-PIDColumn2"][0]
      if _untitled_municipal_land.get("legalLandDescriptionUntitledMunicipalFirstAdditionalReceivingSite") is not None:
        _rcv_dic['legalLandDescription'] = _untitled_municipal_land["legalLandDescriptionUntitledMunicipalFirstAdditionalReceivingSite"]

    _rcv_dic['crownLandFileNumbers'] = create_land_file_numbers(submission, 'A-UntitledCrownLand-FileNumberColumn2')
    _rcv_dic['receivingSiteLandUse'] = create_receiving_site_lan_uses(submission, 'C3-soilClassification2FirstAdditionalReceivingSite')

    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule33FirstAdditionalReceivingSite") is not None : _rcv_dic['CSRFactors'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule33FirstAdditionalReceivingSite"]
    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule34FirstAdditionalReceivingSite") is not None : _rcv_dic['relocatedSoilUse'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule34FirstAdditionalReceivingSite"]
    if submission.get("C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1") is not None : _rcv_dic['highVolumeSite'] = submission["C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime1"]
    if submission.get("D2-firstaddtlreceivingsitesoilDepositIsInTheAgriculturalLandReserveAlr2") is not None : _rcv_dic['soilDepositIsALR'] = submission["D2-firstaddtlreceivingsitesoilDepositIsInTheAgriculturalLandReserveAlr2"]
    if submission.get("D2-firstaddtlreceivingsitesoilDepositIsInTheReserveLands2") is not None : _rcv_dic['soilDepositIsReserveLands'] = submission["D2-firstaddtlreceivingsitesoilDepositIsInTheReserveLands2"]
    _rcv_dic['dateSigned'] = helper.convert_simple_datetime_format_in_str(submission.get("simpledatetime"))       
    _rcv_dic['createAt'] = helper.get_create_date(submission)
    _rcv_dic['confirmationId'] = _confirmation_id
  return _rcv_dic

def map_rcv_3rd_rcver(submission):
  _rcv_dic = {}
  _confirmation_id = helper.get_confirm_id(submission)
  if (submission.get('secondadditionalReceivingSites1').get('secondAdditionalReceivingSiteInformation') == True and
      helper.validate_lat_lon(submission.get("C2-Latitude-Degrees3SecondAdditionalreceivingSite"), submission.get("C2-Latitude-Minutes3SecondAdditionalreceivingSite"), submission.get("Section2-Latitude-Seconds4SecondAdditionalreceivingSite"), 
                              submission.get("C2-Longitude-Degrees3SecondAdditionalreceivingSite"), submission.get("C2-Longitude-Minutes3SecondAdditionalreceivingSite"), submission.get("C2-Longitude-Seconds3SecondAdditionalreceivingSite"),
                              _confirmation_id, 'Soil Relocation Notification Form-Receiving Site')
  ):  
    #print("Mapping 3rd receiver ...")

    for rcv_header in RECEIVING_SITE_HEADERS:
      _rcv_dic[rcv_header] = None

    if submission.get("C1-FirstName6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerFirstName'] = submission["C1-FirstName6SecondAdditionalreceivingSite"]
    if submission.get("C1-LastName6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerLastName'] = submission["C1-LastName6SecondAdditionalreceivingSite"]
    if submission.get("C1-Company6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerCompany'] = submission["C1-Company6SecondAdditionalreceivingSite"]
    if submission.get("C1-Address6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerAddress'] = submission["C1-Address6SecondAdditionalreceivingSite"]
    if submission.get("C1-City6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerCity'] = submission["C1-City6SecondAdditionalreceivingSite"]
    if submission.get("A1-secondadditionalreceivingsiteownerProvinceState10") is not None : _rcv_dic['ownerProvince'] = submission["A1-secondadditionalreceivingsiteownerProvinceState10"]    
    if submission.get("A1-secondadditionalreceivingsiteownerCountry10") is not None : _rcv_dic['ownerCountry'] = submission["A1-secondadditionalreceivingsiteownerCountry10"]
    if submission.get("A1-secondadditionalreceivingsiteownerPostalCode9") is not None : _rcv_dic['ownerPostalCode'] = submission["A1-secondadditionalreceivingsiteownerPostalCode9"]
    if submission.get("phoneNumber7SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerPhoneNumber'] = submission["phoneNumber7SecondAdditionalreceivingSite"]
    if submission.get("C1-Email6SecondAdditionalreceivingSite") is not None : _rcv_dic['ownerEmail'] = submission["C1-Email6SecondAdditionalreceivingSite"]

    if submission.get("C1-FirstName7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2FirstName'] = submission["C1-FirstName7SecondAdditionalreceivingSite"]
    if submission.get("C1-LastName7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2LastName'] = submission["C1-LastName7SecondAdditionalreceivingSite"]
    if submission.get("C1-Company7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2Company'] = submission["C1-Company7SecondAdditionalreceivingSite"]
    if submission.get("C1-Address7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2Address'] = submission["C1-Address7SecondAdditionalreceivingSite"]
    if submission.get("C1-City7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2City'] = submission["C1-City7SecondAdditionalreceivingSite"]
    if submission.get("A1-secondadditionalreceivingsiteadditionalownerProvinceState11") is not None : _rcv_dic['owner2Province'] = submission["A1-secondadditionalreceivingsiteadditionalownerProvinceState11"]
    if submission.get("A1-secondadditionalreceivingsiteadditionalownerCountry11") is not None : _rcv_dic['owner2Country'] = submission["A1-secondadditionalreceivingsiteadditionalownerCountry11"]
    if submission.get("A1-secondadditionalreceivingsiteadditionalownerPostalCode10") is not None : _rcv_dic['owner2PostalCode'] = submission["A1-secondadditionalreceivingsiteadditionalownerPostalCode10"]    
    if submission.get("phoneNumber5SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2PhoneNumber'] = submission["phoneNumber5SecondAdditionalreceivingSite"]
    if submission.get("C1-Email7SecondAdditionalreceivingSite") is not None : _rcv_dic['owner2Email'] = submission["C1-Email7SecondAdditionalreceivingSite"]

    if submission.get("C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow4SecondAdditionalreceivingSite") is not None : _rcv_dic['additionalOwners'] = submission["C1-haveMoreThanTwoOwnersIncludeTheirInformationBelow4SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-FirstName3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactFirstName'] = submission["C2-RSC-FirstName3SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-LastName3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactLastName'] = submission["C2-RSC-LastName3SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-Company3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactCompany'] = submission["C2-RSC-Company3SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-Address3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactAddress'] = submission["C2-RSC-Address3SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-City3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactCity'] = submission["C2-RSC-City3SecondAdditionalreceivingSite"]
    if submission.get("A1-secondadditionalreceivingsitecontactProvinceState12") is not None : _rcv_dic['contactProvince'] = submission["A1-firstadditionalreceivingsitecontactProvinceState9"]
    if submission.get("A1-secondadditionalreceivingsitecontactrCountry12") is not None : _rcv_dic['contactCountry'] = submission["A1-secondadditionalreceivingsitecontactrCountry12"]
    if submission.get("A1-secondadditionalreceivingsitecontactPostalCode11") is not None : _rcv_dic['contactPostalCode'] = submission["A1-secondadditionalreceivingsitecontactPostalCode11"]

    if submission.get("phoneNumber6SecondAdditionalreceivingSite") is not None : _rcv_dic['contactPhoneNumber'] = submission["phoneNumber6SecondAdditionalreceivingSite"]
    if submission.get("C2-RSC-Email3SecondAdditionalreceivingSite") is not None : _rcv_dic['contactEmail'] = submission["C2-RSC-Email3SecondAdditionalreceivingSite"]
    if submission.get("C2-siteIdentificationNumberSiteIdIfAvailable3SecondAdditionalreceivingSite") is not None : _rcv_dic['SID'] = submission["C2-siteIdentificationNumberSiteIdIfAvailable3SecondAdditionalreceivingSite"]

    _rcv_lat, _rcv_lon = helper.convert_deciaml_lat_long(
      submission["C2-Latitude-Degrees3SecondAdditionalreceivingSite"], submission["C2-Latitude-Minutes3SecondAdditionalreceivingSite"], submission["Section2-Latitude-Seconds4SecondAdditionalreceivingSite"], 
      submission["C2-Longitude-Degrees3SecondAdditionalreceivingSite"], submission["C2-Longitude-Minutes3SecondAdditionalreceivingSite"], submission["C2-Longitude-Seconds3SecondAdditionalreceivingSite"])
    _rcv_dic['latitude'] = _rcv_lat
    _rcv_dic['longitude'] = _rcv_lon

    _rcv_dic['regionalDistrict'] = create_regional_district(submission, 'SecondAdditionalReceivingSiteregionalDistrict')
    _rcv_dic['landOwnership'] = create_land_ownership(submission, 'Secondadditionalreceiving-landOwnership-checkbox3')

    if submission.get("C2-LegallyTitled-Address3SecondAdditionalreceivingSite") is not None : _rcv_dic['legallyTitledSiteAddress'] = submission["C2-LegallyTitled-Address3SecondAdditionalreceivingSite"]
    if submission.get("C2-LegallyTitled-City3SecondAdditionalreceivingSite") is not None : _rcv_dic['legallyTitledSiteCity'] = submission["C2-LegallyTitled-City3SecondAdditionalreceivingSite"]
    if submission.get("C2-LegallyTitled-PostalZipCode3SecondAdditionalreceivingSite") is not None : _rcv_dic['legallyTitledSitePostalCode'] = submission["C2-LegallyTitled-PostalZipCode3SecondAdditionalreceivingSite"]

    if submission.get("dataGrid4") is not None and len(submission["dataGrid4"]) > 0: 
      _dg4 = submission["dataGrid4"][0] # could be more than one, but take only one
      if _dg4.get("A-LegallyTitled-PIDSecondAdditionalreceivingSite") is not None: _rcv_dic['PID'] = _dg4["A-LegallyTitled-PIDSecondAdditionalreceivingSite"]
      if _dg4.get("legalLandDescriptionSecondAdditionalreceivingSite") is not None: _rcv_dic['legalLandDescription'] = _dg4["legalLandDescriptionSecondAdditionalreceivingSite"]
    if (submission.get("dataGrid7") is not None and len(submission["dataGrid7"]) > 0 
        and (_rcv_dic['PID'] is None or _rcv_dic['PID'].strip() == '')):
      _dg7 = submission["dataGrid7"][0] # could be more than one, but take only one
      if _dg7.get("A-UntitledCrownLand-PINSecondAdditionalreceivingSite") is not None: _rcv_dic['PIN'] = _dg7["A-UntitledCrownLand-PINSecondAdditionalreceivingSite"]
      if _dg7.get("UntitledCrownLandLegalLandDescriptionSecondAdditionalreceivingSite") is not None: _rcv_dic['legalLandDescription'] = _dg7["UntitledCrownLandLegalLandDescriptionSecondAdditionalreceivingSite"]
    if (submission.get("A-UntitledMunicipalLand-PIDColumn3") is not None and len(submission["A-UntitledMunicipalLand-PIDColumn3"]) > 0 
        and (_rcv_dic['PID'] is None or _rcv_dic['PID'].strip() == '')
        and (_rcv_dic['PIN'] is None or _rcv_dic['PIN'].strip() == '')):
      _untitled_municipal_land = submission["A-UntitledMunicipalLand-PIDColumn3"][0]
      if _untitled_municipal_land.get("legalLandDescriptionUntitledMunicipalSecondAdditionalreceivingSite") is not None:
        _rcv_dic['legalLandDescription'] = _untitled_municipal_land["legalLandDescriptionUntitledMunicipalSecondAdditionalreceivingSite"]

    _rcv_dic['crownLandFileNumbers'] = create_land_file_numbers(submission, 'A-UntitledCrownLand-FileNumberColumn2')        
    _rcv_dic['receivingSiteLandUse'] = create_receiving_site_lan_uses(submission, 'C3-soilClassification4SecondAdditionalreceivingSite')

    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule37SecondAdditionalreceivingSite") is not None : _rcv_dic['CSRFactors'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule37SecondAdditionalreceivingSite"]
    if submission.get("C3-applicableSiteSpecificFactorsForCsrSchedule38SecondAdditionalreceivingSite") is not None : _rcv_dic['relocatedSoilUse'] = submission["C3-applicableSiteSpecificFactorsForCsrSchedule38SecondAdditionalreceivingSite"]
    if submission.get("C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime3") is not None : _rcv_dic['highVolumeSite'] = submission["C3-receivingSiteIsAHighVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime3"]
    if submission.get("D2-secondaddtlreceivingsitesoilDepositIsInTheAgriculturalLandReserveAlr3") is not None : _rcv_dic['soilDepositIsALR'] = submission["D2-secondaddtlreceivingsitesoilDepositIsInTheAgriculturalLandReserveAlr3"]
    if submission.get("D2-secondaddtlreceivingsitesoilDepositIsInTheReserveLands3") is not None : _rcv_dic['soilDepositIsReserveLands'] = submission["D2-secondaddtlreceivingsitesoilDepositIsInTheReserveLands3"]
    _rcv_dic['dateSigned'] = helper.convert_simple_datetime_format_in_str(submission.get("simpledatetime"))       
    _rcv_dic['createAt'] = helper.get_create_date(submission)
    _rcv_dic['confirmationId'] = _confirmation_id
  return _rcv_dic

def map_hv_site(hvs):
  _hv_dic = {}
  _confirmation_id = helper.get_confirm_id(hvs)
  if (helper.validate_lat_lon(hvs.get("Section3-Latitude-Degrees"), hvs.get("Section3-Latitude-Minutes"), hvs.get("Section3-Latitude-Seconds"), 
                              hvs.get("Section3-Longitude-Degrees"), hvs.get("Section3-Longitude-Minutes"), hvs.get("Section3-Longitude-Seconds"),
                              _confirmation_id, 'High Volume Receiving Site Form')
  ):
    #print("Mapping high volume site ...")

    # initialize
    for hv_header in HV_SITE_HEADERS:
      _hv_dic[hv_header] = None

    _hv_dic['ownerFirstName'] = hvs.get("Section1-FirstNameReceivingSiteOwner")
    _hv_dic['ownerLastName'] = hvs.get("Section1-LastNameReceivingSiteOwner")
    _hv_dic['ownerCompany'] = hvs.get("Section1-CompanyReceivingSiteOwner")
    _hv_dic['ownerAddress'] = hvs.get("Section1-AddressReceivingSiteOwner")
    _hv_dic['ownerCity'] = hvs.get("Section1-CityReceivingSiteOwner")
    _hv_dic['ownerProvince'] = hvs.get("Section1-provinceStateReceivingSiteOwner")
    _hv_dic['ownerCountry'] = hvs.get("Section1-countryReceivingSiteOwner")
    _hv_dic['ownerPostalCode'] = hvs.get("Section1-postalZipCodeReceivingSiteOwner")
    _hv_dic['ownerPhoneNumber'] = hvs.get("Section1-PhoneReceivingSiteOwner")
    _hv_dic['ownerEmail'] = hvs.get("Section1-EmailReceivingSiteOwner")
    _hv_dic['owner2FirstName'] = hvs.get("Section1a-FirstNameAdditionalOwner")
    _hv_dic['owner2LastName'] = hvs.get("Section1A-LastNameAdditionalOwner")
    _hv_dic['owner2Company'] = hvs.get("Section1A-CompanyAdditionalOwner")
    _hv_dic['owner2Address'] = hvs.get("Section1A-AddressAdditionalOwner")
    _hv_dic['owner2City'] = hvs.get("Section1A-CityAdditionalOwner")
    _hv_dic['owner2Province'] = hvs.get("Section1A-ProvinceStateAdditionalOwner")
    _hv_dic['owner2Country'] = hvs.get("Section1A-CountryAdditionalOwner")
    _hv_dic['owner2PostalCode'] = hvs.get("Section1A-PostalZipCodeAdditionalOwner")
    _hv_dic['owner2PhoneNumber'] = hvs.get("Section1A-PhoneAdditionalOwner")
    _hv_dic['owner2Email'] = hvs.get("Section1A-EmailAdditionalOwner")
    _hv_dic['additionalOwners'] = hvs.get("areThereMoreThanTwoOwnersIncludeTheirInformationBelow")
    _hv_dic['contactFirstName'] = hvs.get("Section2-firstNameRSC")
    _hv_dic['contactLastName'] = hvs.get("Section2-lastNameRSC")
    _hv_dic['contactCompany'] = hvs.get("Section2-organizationRSC")
    _hv_dic['contactAddress'] = hvs.get("Section2-streetAddressRSC")
    _hv_dic['contactCity'] = hvs.get("Section2-cityRSC")
    _hv_dic['contactProvince'] = hvs.get("Section2-provinceStateRSC")
    _hv_dic['contactCountry'] = hvs.get("Section2-countryRSC")
    _hv_dic['contactPostalCode'] = hvs.get("Section2-postalZipCodeRSC")
    _hv_dic['contactPhoneNumber'] = hvs.get("section2phoneNumberRSC")
    _hv_dic['contactEmail'] = hvs.get("Section2-simpleemailRSC")
    _hv_dic['SID'] = hvs.get("Section3-siteIdIncludeAllRelatedNumbers")

    _hv_dic['latitude'], _hv_dic['longitude'] = helper.convert_deciaml_lat_long(
      hvs["Section3-Latitude-Degrees"], hvs["Section3-Latitude-Minutes"], hvs["Section3-Latitude-Seconds"], 
      hvs["Section3-Longitude-Degrees"], hvs["Section3-Longitude-Minutes"], hvs["Section3-Longitude-Seconds"])

    _hv_dic['regionalDistrict'] = create_regional_district(hvs, 'ReceivingSiteregionalDistrict')
    _hv_dic['landOwnership'] = create_land_ownership(hvs, 'landOwnership-checkbox')
    _hv_dic['legallyTitledSiteAddress'] = hvs.get("Section3-LegallyTitled-Address")
    _hv_dic['legallyTitledSiteCity'] = hvs.get("Section3-LegallyTitled-City")
    _hv_dic['legallyTitledSitePostalCode'] = hvs.get("Section3-LegallyTitled-PostalZipCode")
    #PIN, PIN, description
    _hv_dic['PID'], _hv_dic['legalLandDescription'] = create_pid_and_desc(hvs, 'dataGrid', 'A-LegallyTitled-PID', 'legalLandDescription') #PID
    if (_hv_dic['PID'] is None or _hv_dic['PID'].strip() == ''): #PIN
      _hv_dic['PIN'], _hv_dic['legalLandDescription'] = create_pin_and_desc(hvs, 'dataGrid1', 'A-LegallyTitled-PID', 'legalLandDescription')      
    if ((_hv_dic['PID'] is None or _hv_dic['PID'].strip() == '')
        and (_hv_dic['PIN'] is None or _hv_dic['PIN'].strip() == '')): #Description when selecting 'Untitled Municipal Land'
      _hv_dic['legalLandDescription'] = create_untitled_municipal_land_desc(hvs, 'A-UntitledMunicipalLand-PIDColumn', 'legalLandDescription')

    _hv_dic['crownLandFileNumbers'] = create_land_file_numbers(hvs, 'A-UntitledCrownLand-FileNumberColumn')
    _hv_dic['receivingSiteLandUse'] = create_receiving_site_lan_uses(hvs, 'primarylanduse')
    _hv_dic['hvsConfirmation'] = hvs.get("highVolumeSite20000CubicMetresOrMoreDepositedOnTheSiteInALifetime")
    _hv_dic['dateSiteBecameHighVolume'] = helper.convert_simple_datetime_format_in_str(hvs["dateSiteBecameHighVolume"])
    _hv_dic['howRelocatedSoilWillBeUsed'] = hvs.get("howrelocatedsoilwillbeused")
    _hv_dic['soilDepositIsALR'] = hvs.get("soilDepositIsInTheAgriculturalLandReserveAlr1")
    _hv_dic['soilDepositIsReserveLands'] = hvs.get("receivingSiteIsOnReserveLands1")
    _hv_dic['qualifiedProfessionalFirstName'] = hvs.get("Section5-FirstNameQualifiedProfessional")
    _hv_dic['qualifiedProfessionalLastName'] = hvs.get("Section5-LastName1QualifiedProfessional")
    _hv_dic['qualifiedProfessionalType'] = hvs.get("Section5-TypeofQP")
    _hv_dic['qualifiedProfessionalOrganization'] = hvs.get("Section5-organizationQualifiedProfessional")
    _hv_dic['professionalLicenceRegistration'] = hvs.get("Section5-professionalLicenseRegistrationEGPEngRpBio")
    _hv_dic['qualifiedProfessionalAddress'] = hvs.get("Section5-streetAddressQualifiedProfessional")
    _hv_dic['qualifiedProfessionalCity'] = hvs.get("Section5-cityQualifiedProfessional")
    _hv_dic['qualifiedProfessionalProvince'] = hvs.get("Section5-provinceStateQualifiedProfessional")
    _hv_dic['qualifiedProfessionalCountry'] = hvs.get("Section5-countryQualifiedProfessional")
    _hv_dic['qualifiedProfessionalPostalCode'] = hvs.get("Section5-postalZipCodeQualifiedProfessional")
    _hv_dic['qualifiedProfessionalPhoneNumber'] = hvs.get("simplephonenumber1QualifiedProfessional")
    _hv_dic['qualifiedProfessionalEmail'] = hvs.get("simpleemail1QualifiedProfessional")
    _hv_dic['signaturerFirstAndLastName'] = hvs.get("firstAndLastNameQualifiedProfessional")
    _hv_dic['dateSigned'] = helper.convert_simple_datetime_format_in_str(hvs["simpledatetime"])
    _hv_dic['createAt'] = helper.get_create_date(hvs)
    _hv_dic['confirmationId'] = _confirmation_id
  return _hv_dic

# add Regional Districts in site forms to dictionary - key:regional district string / value:site data dictionary
def add_regional_district_dic(site_dic, reg_dist_dic):
  if 'regionalDistrict' in site_dic and site_dic['regionalDistrict'] is not None: # could be none regional district key
    _dic_copy = {}
    _dic_copy = copy.deepcopy(site_dic)
    _rd_str = site_dic['regionalDistrict'] # could be more than one
    if _rd_str is not None:
      _rd_str = _rd_str.strip('\"')
      _rds = []
      _rds = _rd_str.split(",")
      for _rd in _rds:
        # reverse-convert name to id for searching key
        _rd_key = [k for k, v in REGIONAL_DISTRICT_NAME_DIC.items() if v == _rd]
        if len(_rd_key) > 0:
          if _rd_key[0] in reg_dist_dic:
            reg_dist_dic[_rd_key[0]].append(_dic_copy)
          else:
            reg_dist_dic[_rd_key[0]] = [_dic_copy]






CHEFS_SOILS_FORM_ID = os.getenv('CHEFS_SOILS_FORM_ID')
CHEFS_SOILS_API_KEY = os.getenv('CHEFS_SOILS_API_KEY')
CHEFS_HV_FORM_ID = os.getenv('CHEFS_HV_FORM_ID')
CHEFS_HV_API_KEY = os.getenv('CHEFS_HV_API_KEY')
CHEFS_MAIL_FORM_ID = os.getenv('CHEFS_MAIL_FORM_ID')
CHEFS_MAIL_API_KEY = os.getenv('CHEFS_MAIL_API_KEY')
MAPHUB_USER = os.getenv('MAPHUB_USER')
MAPHUB_PASS = os.getenv('MAPHUB_PASS')

"""
print(f"Value of env variable key='CHEFS_SOILS_FORM_ID': {CHEFS_SOILS_FORM_ID}")
print(f"Value of env variable key='CHEFS_SOILS_API_KEY': {CHEFS_SOILS_API_KEY}")
print(f"Value of env variable key='CHEFS_HV_FORM_ID': {CHEFS_HV_FORM_ID}")
print(f"Value of env variable key='CHEFS_HV_API_KEY': {CHEFS_HV_API_KEY}")
print(f"Value of env variable key='CHEFS_MAIL_FORM_ID': {CHEFS_MAIL_FORM_ID}")
print(f"Value of env variable key='CHEFS_MAIL_API_KEY': {CHEFS_MAIL_API_KEY}")

print(f"Value of env variable key='MAPHUB_USER': {MAPHUB_USER}")
print(f"Value of env variable key='MAPHUB_PASS': {MAPHUB_PASS}")
"""


# Fetch all submissions from chefs API
print('Loading Submissions List...')
submissionsJson = helper.site_list(CHEFS_SOILS_FORM_ID, CHEFS_SOILS_API_KEY)
#print(submissionsJson)
print('Loading Submission attributes and headers...')
soilsAttributes = helper.fetch_columns(CHEFS_SOILS_FORM_ID, CHEFS_SOILS_API_KEY)
#print(soilsAttributes)

print('Loading High Volume Sites list...')
hvsJson = helper.site_list(CHEFS_HV_FORM_ID, CHEFS_HV_API_KEY)
#print(hvsJson)
print('Loading High Volume Sites attributes and headers...')
hvsAttributes = helper.fetch_columns(CHEFS_HV_FORM_ID, CHEFS_HV_API_KEY)
# print(hvsAttributes)

# Fetch subscribers list
print('Loading submission subscribers list...')
subscribersJson = helper.site_list(CHEFS_MAIL_FORM_ID, CHEFS_MAIL_API_KEY)
#print(subscribersJson)
print('Loading submission subscribers attributes and headers...')
subscribeAttributes = helper.fetch_columns(CHEFS_MAIL_FORM_ID, CHEFS_MAIL_API_KEY)
# print(subscribeAttributes)


print('Creating source site, receiving site records...')
sourceSites = []
receivingSites = []
rcvRegDistDic = {}
for submission in submissionsJson:
  #print('Mapping submission data to the source site...')
  _srcDic = map_source_site(submission)
  if _srcDic:
    sourceSites.append(_srcDic)

  #print('Mapping submission data to the receiving site...')  
  _1rcvDic = map_rcv_1st_rcver(submission)
  if _1rcvDic:
    receivingSites.append(_1rcvDic)
    add_regional_district_dic(_1rcvDic, rcvRegDistDic)

  _2rcvDic = map_rcv_2nd_rcver(submission)
  if _2rcvDic:
    receivingSites.append(_2rcvDic)
    add_regional_district_dic(_2rcvDic, rcvRegDistDic)

  _3rcvDic = map_rcv_3rd_rcver(submission)
  if _3rcvDic:
    receivingSites.append(_3rcvDic)
    add_regional_district_dic(_3rcvDic, rcvRegDistDic)  

print('Creating high volume site records records...')
hvSites = []
hvRegDistDic = {}
for hvs in hvsJson:
  #print('Mapping hv data to the hv site...')  
  _hvDic = map_hv_site(hvs)
  if _hvDic:
    hvSites.append(_hvDic)
    add_regional_district_dic(_hvDic, hvRegDistDic)  



print('Creating soil source site CSV...')
print('>> current directory:' + os.getcwd())
with open(SOURCE_CSV_FILE, 'w', encoding='UTF8', newline='') as f:
  writer = csv.DictWriter(f, fieldnames=SOURCE_SITE_HEADERS)
  writer.writeheader()
  writer.writerows(sourceSites)

print('Creating soil receiving site CSV...')
with open(RECEIVE_CSV_FILE, 'w', encoding='UTF8', newline='') as f:
  writer = csv.DictWriter(f, fieldnames=RECEIVING_SITE_HEADERS)
  writer.writeheader()
  writer.writerows(receivingSites)

print('Creating soil high volume site CSV...')
with open(HIGH_VOLUME_CSV_FILE, 'w', encoding='UTF8', newline='') as f:
  writer = csv.DictWriter(f, fieldnames=HV_SITE_HEADERS)
  writer.writeheader()
  writer.writerows(hvSites)



print('Connecting to AGOL GIS...')
# connect to GIS
_gis = GIS(MAPHUB_URL, username=MAPHUB_USER, password=MAPHUB_PASS)

print('Updating Soil Relocation Soruce Site CSV...')
_srcCsvItem = _gis.content.get(SRC_CSV_ID)
if _srcCsvItem is None:
  print('Error: Source Site CSV Item ID is invalid!')
else:
  _srcCsvUpdateResult = _srcCsvItem.update({}, SOURCE_CSV_FILE)
  print('Updated Soil Relocation Source Site CSV sucessfully: ' + str(_srcCsvUpdateResult))

  print('Updating Soil Relocation Soruce Site Feature Layer...')
  _srcLyrItem = _gis.content.get(SRC_LAYER_ID)
  if _srcLyrItem is None:
    print('Error: Source Site Layter Item ID is invalid!')
  else:
    _srcFlc = FeatureLayerCollection.fromitem(_srcLyrItem)
    _srcLyrOverwriteResult = _srcFlc.manager.overwrite(SOURCE_CSV_FILE)
    print('Updated Soil Relocation Source Site Feature Layer sucessfully: ' + json.dumps(_srcLyrOverwriteResult))


print('Updating Soil Relocation Receiving Site CSV...')
_rcvCsvItem = _gis.content.get(RCV_CSV_ID)
if _rcvCsvItem is None:
  print('Error: Receiving Site CSV Item ID is invalid!')
else:
  _rcvCsvUpdateResult = _rcvCsvItem.update({}, RECEIVE_CSV_FILE)
  print('Updated Soil Relocation Receiving Site CSV sucessfully: ' + str(_rcvCsvUpdateResult))

  print('Updating Soil Relocation Receiving Site Feature Layer...')
  _rcvLyrItem = _gis.content.get(RCV_LAYER_ID)
  if _rcvLyrItem is None:
    print('Error: Receiving Site Layer Item ID is invalid!')
  else:    
    _rcvFlc = FeatureLayerCollection.fromitem(_rcvLyrItem)
    _rcvLyrOverwriteResult = _rcvFlc.manager.overwrite(RECEIVE_CSV_FILE)
    print('Updated Soil Relocation Receiving Site Feature Layer sucessfully: ' + json.dumps(_rcvLyrOverwriteResult))


print('Updating High Volume Receiving Site CSV...')
_hvCsvItem = _gis.content.get(HV_CSV_ID)
if _hvCsvItem is None:
  print('Error: High Volume Receiving Site CSV Item ID is invalid!')
else:
  _hvCsvUpdateResult = _hvCsvItem.update({}, HIGH_VOLUME_CSV_FILE)
  print('Updated High Volume Receiving Site CSV sucessfully: ' + str(_hvCsvUpdateResult))

  print('Updating High Volume Receiving Site Feature Layer...')
  _hvLyrItem = _gis.content.get(HV_LAYER_ID)
  if _hvLyrItem is None:
    print('Error: High Volume Receiving Site Layer Item ID is invalid!')
  else:      
    _hvFlc = FeatureLayerCollection.fromitem(_hvLyrItem)
    _hvLyrOverwriteResult = _hvFlc.manager.overwrite(HIGH_VOLUME_CSV_FILE)
    print('Updated High Volume Receiving Site Feature Layer sucessfully: ' + json.dumps(_hvLyrOverwriteResult))




print('Sending subscriber emails...')
# iterate through the submissions and send an email
# Only send emails for sites that are new (don't resend for old sites)
# For new/old submissions, you'll have to compare the submission create date against the current script runtime. 
# This may require finding a way to store a "last run time" for the script, or running the script once per day, 
# and only sending submissions for where a create-date is within the last 24 hours.

EMAIL_SUBJECT_SOIL_RELOCATION = 'SRIS Subscription Service - New Notification(s) Received (Soil Relocation)'
EMAIL_SUBJECT_HIGH_VOLUME = 'SRIS Subscription Service - New Registration(s) Received (High Volume Receiving Site)'

today = datetime.datetime.now(tz=pytz.timezone('Canada/Pacific'))
# print(today)

notifySoilRelocSubscriberDic = {}
notifyHVSSubscriberDic = {}
unSubscribersDic = {}

for _subscriber in subscribersJson:
  #print(_subscriber)
  _subscriberEmail = None
  _subscriberRegionalDistrict = [] # could be more than one
  _unsubscribe = False
  _notifyHVS = None
  _notifySoilReloc = None
  _subscription_created_at = None
  _subscription_confirm_id = None

  if _subscriber.get("emailAddress") is not None : _subscriberEmail = _subscriber["emailAddress"]
  if _subscriber.get("regionalDistrict") is not None : _subscriberRegionalDistrict = _subscriber["regionalDistrict"] 
  if _subscriber.get("unsubscribe") is not None :
    if (_subscriber["unsubscribe"]).get("unsubscribe") is not None :
       if helper.is_boolean(_subscriber["unsubscribe"]["unsubscribe"]):
          _unsubscribe = _subscriber["unsubscribe"]["unsubscribe"]

  if _subscriber.get("notificationSelection") is not None : 
    _noticeSelection = _subscriber["notificationSelection"]
    if _noticeSelection.get('notifyOnHighVolumeSiteRegistrationsInSelectedRegionalDistrict') is not None:
      if helper.is_boolean(_noticeSelection['notifyOnHighVolumeSiteRegistrationsInSelectedRegionalDistrict']):
        _notifyHVS = _noticeSelection['notifyOnHighVolumeSiteRegistrationsInSelectedRegionalDistrict']
    if _noticeSelection.get('notifyOnSoilRelocationsInSelectedRegionalDistrict') is not None:
      if helper.is_boolean(_noticeSelection['notifyOnSoilRelocationsInSelectedRegionalDistrict']):
        _notifySoilReloc = _noticeSelection['notifyOnSoilRelocationsInSelectedRegionalDistrict']

  _subscription_created_at = helper.get_create_date(_subscriber)
  _subscription_confirm_id = helper.get_confirm_id(_subscriber)  

  if (_subscriberEmail is not None and _subscriberEmail.strip() != '' and
      _subscriberRegionalDistrict is not None and len(_subscriberRegionalDistrict) > 0 and
      _unsubscribe == False and 
      (
        _notifyHVS == True or
        _notifySoilReloc == True
      )):

    # Notification of soil relocation in selected Regional District(s)  =========================================================
    if _notifySoilReloc == True:
      for _srd in _subscriberRegionalDistrict:

        # finding if subscriber's regional district in receiving site registration
        _rcvSitesInRD = rcvRegDistDic.get(_srd)

        if _rcvSitesInRD is not None:
          for _receivingSiteDic in _rcvSitesInRD:

            #print('today:',today,',created at:',_receivingSiteDic['createAt'],'confirm Id:',_receivingSiteDic['confirmationId'])
            _diff = helper.get_difference_datetimes_in_hour(today, _receivingSiteDic['createAt'])
            if (_diff is not None and _diff <= 24):  #within the last 24 hours.
              _rcvPopupLinks = create_popup_links(_rcvSitesInRD, 'SR')
              _regDisName = convert_regional_district_to_name(_srd)
              _emailMsg = create_site_relocation_email_msg(_regDisName, _rcvPopupLinks)

              # create soil relocation notification substriber dictionary
              # key-Tuple of email address, RegionalDistrict Tuple, value=Tuple of email maessage, subscription create date, subscription confirm id
              if (_subscriberEmail,_srd) not in notifySoilRelocSubscriberDic:
                notifySoilRelocSubscriberDic[(_subscriberEmail,_srd)] = (_emailMsg, _subscription_created_at, _subscription_confirm_id)
                #print("notifySoilRelocSubscriberDic added email:" + _subscriberEmail+ ', region:' + _srd + ', confirm id:' 
                #      + str(_subscription_confirm_id) + ', subscription created at:' + str(_subscription_created_at))
              else:
                _subscrb_created = notifySoilRelocSubscriberDic.get((_subscriberEmail,_srd))[1]
                if (_subscription_created_at is not None and _subscription_created_at > _subscrb_created):
                  notifySoilRelocSubscriberDic.update({(_subscriberEmail,_srd):(_emailMsg, _subscription_created_at, _subscription_confirm_id)})
                  #print("notifySoilRelocSubscriberDic updated email:" + _subscriberEmail+ ', region:' + _srd + ', confirm id:' 
                  #      + str(_subscription_confirm_id) + ', subscription created at:' + str(_subscription_created_at))

    # Notification of high volume site registration in selected Regional District(s) ============================================
    if _notifyHVS == True:
      for _srd in _subscriberRegionalDistrict:

        # finding if subscriber's regional district in high volume receiving site registration
        _hvSitesInRD = hvRegDistDic.get(_srd)

        if _hvSitesInRD is not None:
          for _hvSiteDic in _hvSitesInRD:

            #print('today:',today,',created at:',_hvSiteDic['createAt'],'confirm Id:',_hvSiteDic['confirmationId'])
            _diff = helper.get_difference_datetimes_in_hour(today, _hvSiteDic['createAt'])
            if (_diff is not None and _diff <= 24):  #within the last 24 hours.
              _hvPopupLinks = create_popup_links(_hvSitesInRD, 'HV')
              _hvRegDis = convert_regional_district_to_name(_srd)
              _hvEmailMsg = create_hv_site_email_msg(_hvRegDis, _hvPopupLinks)

              # create high volume relocation notification substriber dictionary
              # key-Tuple of email address, RegionalDistrict Tuple, value=Tuple of email maessage, subscription create date, subscription confirm id
              if (_subscriberEmail,_srd) not in notifyHVSSubscriberDic:
                notifyHVSSubscriberDic[(_subscriberEmail,_srd)] = (_hvEmailMsg, _subscription_created_at, _subscription_confirm_id)
                #print("notifyHVSSubscriberDic added email:" + _subscriberEmail+ ', region:' + _srd + ', confirm id:' 
                #      + str(_subscription_confirm_id) + ', subscription created at:' + str(_subscription_created_at))
              else:
                _subscrb_created = notifyHVSSubscriberDic.get((_subscriberEmail,_srd))[1]
                if (_subscription_created_at is not None and _subscription_created_at > _subscrb_created):
                  notifyHVSSubscriberDic.update({(_subscriberEmail,_srd):(_hvEmailMsg, _subscription_created_at, _subscription_confirm_id)})
                  #print("notifyHVSSubscriberDic updated email:" + _subscriberEmail+ ', region:' + _srd + ', confirm id:' 
                  #    + str(_subscription_confirm_id) + ', subscription created at:' + str(_subscription_created_at))

  elif (_subscriberEmail is not None and _subscriberEmail.strip() != '' and
        _subscriberRegionalDistrict is not None and len(_subscriberRegionalDistrict) > 0 and  
        _unsubscribe == True):
    # create unSubscriber list
    for _srd in _subscriberRegionalDistrict:
      if (_subscriberEmail,_srd) not in unSubscribersDic:
        unSubscribersDic[(_subscriberEmail,_srd)] = _subscription_created_at
        #print("unSubscribersDic added email:" + _subscriberEmail+ ', region:' + _srd + ', confirm id:' 
        #      + str(_subscription_confirm_id) + ', unsubscription created at:' + str(_subscription_created_at))
      else:  
        _unsubscrb_created = unSubscribersDic.get((_subscriberEmail,_srd))
        if (_subscription_created_at is not None and _subscription_created_at > _unsubscrb_created):
          unSubscribersDic.update({(_subscriberEmail,_srd):_subscription_created_at})
          #print("unSubscribersDic updated email:" + _subscriberEmail+ ', region:' + _srd + ', confirm id:' 
          #    + str( _subscription_confirm_id) + ', unsubscription created at:' + str(_subscription_created_at))

print('Removing unsubscribers from notifyHVSSubscriberDic and notifySoilRelocSubscriberDic ...')
# Processing of data subscribed and unsubscribed by the same email in the same region -
# This is processed based on the most recent submission date.
for (_k1_subscriberEmail,_k2_srd), _unsubscribe_create_at in unSubscribersDic.items():
  if (_k1_subscriberEmail,_k2_srd) in notifySoilRelocSubscriberDic:
    _subscribe_create_at = notifySoilRelocSubscriberDic.get((_k1_subscriberEmail,_k2_srd))[1]
    _subscribe_confirm_id = notifySoilRelocSubscriberDic.get((_k1_subscriberEmail,_k2_srd))[2]    
    if (_unsubscribe_create_at is not None and _subscribe_create_at is not None and _unsubscribe_create_at > _subscribe_create_at):
      notifySoilRelocSubscriberDic.pop(_k1_subscriberEmail,_k2_srd)
      #print("remove subscription from notifySoilRelocSubscriberDic - email:" + _k1_subscriberEmail+ ', region:' 
      #      + _k2_srd + ', confirm id:' +str( _subscription_confirm_id) + ', unsubscription created at:' + str(_unsubscribe_create_at))

  if (_k1_subscriberEmail,_k2_srd) in notifyHVSSubscriberDic:
    _subscribe_create_at = notifyHVSSubscriberDic.get((_k1_subscriberEmail,_k2_srd))[1]
    _subscribe_confirm_id = notifyHVSSubscriberDic.get((_k1_subscriberEmail,_k2_srd))[2]        
    if (_unsubscribe_create_at is not None and _subscribe_create_at is not None and _unsubscribe_create_at > _subscribe_create_at):
      notifyHVSSubscriberDic.pop((_k1_subscriberEmail,_k2_srd))
      #print("remove subscription from notifyHVSSubscriberDic - email:" + _k1_subscriberEmail+ ', region:' 
      #      + _k2_srd + ', confirm id:' +str( _subscribe_confirm_id) + ', unsubscription created at:' + str(_unsubscribe_create_at))


print('Sending Notification of soil relocation in selected Regional District(s) ...')
for _k, _v in notifySoilRelocSubscriberDic.items():
  _ches_response = helper.send_mail(_k[0], EMAIL_SUBJECT_SOIL_RELOCATION, _v[0])
  print("CHEFS response: " + str(_ches_response.status_code) + ", subscriber email: " + _subscriberEmail)

print('Sending Notification of high volume site registration in selected Regional District(s) ...')
for _k, _v in notifyHVSSubscriberDic.items():
  _ches_response = helper.send_mail(_k[0], EMAIL_SUBJECT_SOIL_RELOCATION, _v[0])
  print("CHEFS response: " + str(_ches_response.status_code) + ", subscriber email: " + _subscriberEmail)


print('Completed Soils data publishing')