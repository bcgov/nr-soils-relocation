![Lifecycle:Experimental](https://img.shields.io/badge/Lifecycle-Experimental-339999)
# Soil Relocation Information System
Soil Relocation Information System manages soil relocation notifications and high volume receiving site registration and gives access to Indigenous Nations, municipalities, and other interested parties to access information on soil relocation through a mapping application. Interested parties can subscribe to be automatically notified of soil relocation or high volume receiving site registrations in their areas.

### Process
1. Users in BC submit the information about soil relocation using CHEFS Forms.
2. The Python script, present in this repo, is run on a schedule through openshift cronjobs.
3. The Script pulls data from CHEF forms and upload csv to AGOL and also triggers emails to people who subscribed(CHEF forms) to be notified for soil movement.
4. The frontend to display all these details are shown AGOL.

The Project uses OpenShift CronJobs(https://docs.openshift.com/container-platform/4.10/nodes/jobs/nodes-nodes-jobs.html#nodes-nodes-jobs-creating-cron_nodes-nodes-jobs)

The openshift template for cronjob is present here(https://raw.githubusercontent.com/bcgov/nr-soils-relocation/main/openshift/sris-schedule-job.yml)

The workflow file for build and deploy is located here(https://raw.githubusercontent.com/bcgov/nr-soils-relocation/main/.github/workflows/ci-openshift-prod.yaml).

_Due to the fact that both source and destination have only prod environment, the deployment happens to prod directly._

The secrets in GitHub are passed as env variables to application through config-map.

The CHES API Key is generated from postman, by providing the username(client_id) and (client_secret) and that is added as env variable(CHES_API_OAUTH_SECRET) in the pipeline.

The cron time are in UTC as the OpenShift servers are in UTC.
