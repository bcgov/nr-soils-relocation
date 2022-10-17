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

### How To Deploy (The below steps are to be followed to deploy into openshift PROD)
**_Note: This Application is the middle layer between CHEFS forms and AGOL. Both these tools does not have different environments. 
Once the application is moved to PROD and available to public users future enhancements needs to be thought through and different deployment approach might be needed._**

1. Once the code coding is done in a specific branch(ex: feature/abc) then create a Pull Request and ask for a reviewer on the code base.
2. Once the code is reviewed and approved, merge it to main branch.
3. Go to Actions tab and click on the `Build And Add Job to Openshift Prod` and trigger a build.
   1. It would ask for a tag number, please check the releases/tag branch and increase as per the code changes done, before prod release, just update the minor version like, 0.0.5 to 0.0.6. Make sure the tag does not exist otherwise build would fail.
   2. Click on Run workflow button.
4. The workflow will do 3 things.
   1. Build the Docker Image and push it to GHCR and tag it to the tag you just entered above. All the images are available here(https://github.com/bcgov/nr-soils-relocation/pkgs/container/nr-soils-relocation%2Fsris)
   2. Create a TAG in GitHub as release/$TAG, here $TAG refers to the TAG number entered during the build.
   3. Deploy the latest code changes and config map changes to openshift.
5. Once it is deployed, the cronjob is created in the PROD environment. The image in the cronjob refers to the image in image stream with specific TAG.
6. The Environment variables are supplied to the container through config-map.
7. The Config Map is populated from GitHub Secrets. Any updates to the environment variables should happen at GitHub Secrets level to maintain the source of truth.
8. Currently, the cron Schedule is set to run at 1AM daily at Pacific Time.
9. if there is a need to run a one time job to test the changes that was made, rather than waiting for the scheduled process, a one time job can be created. please follow the one time job section below for more details.

#### One Time Job
There are certain instances where waiting for the schedule job to test the changes are not possible, in that case a one time job could be created. Please follow the steps below to achieve that.
1. Go to(https://console.apps.silver.devops.gov.bc.ca/k8s/ns/f0431b-prod/cronjobs/sris-cron-job/yaml).
2. Copy the Spec-> Spec -> Containers section from the yaml(the whole containers section including the containers: tag)
3. Go to Jobs menu in the same namespace and click on Create Job on the right hand side.
4. In the name section just give `sris-1-of-job-$name` replace $name with your name and replace the containers section with copied section from step number 2, and click on create.
5. It should spin up a new pod instantly and execute it. Verify your changes.
6. Finally, delete this one off job you just created.


