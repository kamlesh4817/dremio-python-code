# Submit a query through the Dremio Cloud REST API

import sys
import requests                         # pip install requests
import json                             # no install required

# Inputs 
project_id = '6dac13c8-c1b0-4be5-9d59-cbfa607be820'
pat = 'U/soDX8PR3y+wapSa21KeGbJvSeN3CHHX3yvTaXHN7PEnpbLslFkk3cl+HmKZQ==' # generated on 10/30/24

auth = 'Bearer ' + pat
base_url = 'https://api.dremio.cloud/v0'
url = base_url + '/projects/' + project_id + '/sql'
query_header = {'content-type': 'application/json', 'Authorization' : auth}
query = 'select * from Samples."samples.dremio.com"."NYC-taxi-trips"'
payload = { 'sql' : query }

r = requests.post(url, headers = query_header, json = payload)
if r.status_code != 200:
    exit('status code not 200')
d = r.json()
id = d['id']
print(id)

