# Submit a query through the Dremio REST API

import boto3
import requests                         # pip install requests
import json                             # builtin, no install required
import time 


def await_job_completion(id):
    url = base_url + '/projects/' + project_id + '/job/' + id
    while 1:
        r = requests.get(url, headers = queryHeader)
        if r.status_code != 200:
            exit('status code not 200')
        d = r.json()
        jobState = d['jobState']
        print(jobState)
        if jobState == 'COMPLETED':
            break 
        elif jobState == 'FAILED' or jobState == 'CANCELED':
            exit('job failed')
        else:
            time.sleep(5) 


# User inputs
project_id = '6dac13c8-c1b0-4be5-9d59-cbfa607be820'
pat = 'U/soDX8PR3y+wapSa21KeGbJvSeN3CHHX3yvTaXHN7PEnpbLslFkk3cl+HmKZQ==' # generated on 10/30/24

auth = 'Bearer ' + pat
base_url = 'https://api.dremio.cloud/v0'
url = base_url + '/projects/' + project_id + '/sql'
queryHeader = {'content-type': 'application/json', 'Authorization' : auth}

# add new files to the datalake 
client = boto3.client("s3")
filename= '202302-citibike-tripdata.csv'
client.upload_file ('/home/@kamlesh.sharma@dremio.com/' + filename, 'aws-data', 'citibike/2023/' + filename )

# refresh table metadata
url = base_url + '/projects/' + project_id + '/sql'
query = 'alter table awsdata.citibike refresh metadata'
payload = { 'sql' : query } 
r = requests.post(url, headers = queryHeader, json = payload)
if r.status_code != 200:
    exit('status code not 200')
d = r.json()
job_id = d['id']
await_job_completion(job_id)

# refresh all dependent reflections
url = base_url + '/projects/' + project_id + '/catalog/by-path/awsdata/citibike'
r = requests.get(url, headers = queryHeader)
if r.status_code != 200: 
    exit('status code not 200')
d = r.json()
dataset_id = d['id']
print(dataset_id)
url = base_url + '/projects/' + project_id + '/catalog/' + dataset_id + '/refresh'
requests.post(url, headers = queryHeader)
print('refresh requested')



