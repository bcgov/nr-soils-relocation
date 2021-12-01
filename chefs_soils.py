import requests
from requests.auth import HTTPBasicAuth
import json
import csv
# ArcGis Online
from arcgis.gis import GIS

# Move these to a secrets/configuration file
chefsUrl = 'https://chefs.nrs.gov.bc.ca/app/api/v1'
chefsFormId = <form ID>
chefsApiKey = <api key>
submissionListEndpoint = '/forms/' + chefsFormId + '/export?format=json&type=submissions'
# If we don't want to export everything and do incrementals, add a minDate=<YYYY>-<MM>-<DD>T08:00:00Z (and maxDate?)
# This way we can pull everything from "The last import" and just process that data. That said, unless we're talking about
# 10's of thousands of records, it shouldn't matter too much.
csvLocation = 'Soils_Export_Testing.csv'
maphubUrl = r'https://governmentofbc.maps.arcgis.com'
maphubUser = <maphub username>
maphubPass = <maphub pwd>

# Fetch all submissions from chefs API
print('Loading Submissions...')
submissionsRequest = requests.get(chefsUrl + submissionListEndpoint, auth=HTTPBasicAuth(chefsFormId, chefsApiKey), headers={'Content-type': 'application/json'})
print('Parsing JSON response')
submissionsRaw = submissionsRequest.content
submissions = json.loads(submissionsRaw)

# testing variables. We'll replace this with the real attributes from the soils form
csvHeaders = ['latitude', 'longitude', 'data', 'submittedBy', 'submittedAt']
# Parse information, format for CSV
with open(csvLocation, 'w', encoding='UTF8', newline='') as f:
  print('Creating CSV @ ' + csvLocation)
  writer = csv.writer(f)
  writer.writerow(csvHeaders)

  print('Parsing ' + str(len(submissions)) + ' submissions (Not all submissions will be valid')
  count = 0
  for submission in submissions:
    # Export as CSV to dropbox location (note, we can extract a csv from the forms endpoint, but we may want to massage the data)
    # simple test for valid, replace with something useful once we have the soils dataset from the form
    if "latitude" in submission:
      data = [submission['latitude'], submission['longitude'], submission['simpleselect'][0], submission['form']['fullName'], submission['form']['createdAt']]
      writer.writerow(data)
      count = count + 1
    else:
      print("Failed to parse attributes from submission: ")
      print(submission)

  print('Successfully processed ' + str(count) + ' submissions')

  if count > 0:
    print('Starting publish to AGOL...')
    # seems to not like my username/password?
    gis = GIS(maphubUrl, username=maphubUser, password=maphubPass)

    # Replace the layer name when we have a real dataset name (add to config?)
    featureLayerName = 'Soils_Export_Testing'
    featureLayerTags = ['Test', 'Soils']

    csvProperties = {
      'title': featureLayerName,
      'tags': featureLayerTags,
      'type': 'csv'
    }

    layer = gis.content.add(csvProperties, data=csvLocation)

    featureLayer = layer.publish()

    print(featureLayer.url)
    print('published ' + featureLayerName + ' successfully')

print('Completed Soils data publishing')
