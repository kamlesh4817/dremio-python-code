# Enable an engine through the Dremio REST API

import sys
import requests                         # pip install requests
import json                             # builtin, no install required

# User inputs
project_id = '6dac13c8-c1b0-4be5-9d59-cbfa607be820'
pat = 'U/soDX8PR3y+wapSa21KeGbJvSeN3CHHX3yvTaXHN7PEnpbLslFkk3cl+HmKZQ==' # generated on 10/30/24
target_engine_name = ''

auth = 'Bearer ' + pat
base_url = 'https://api.dremio.cloud/v0'
url = base_url + '/projects/' + project_id + '/engines'
queryHeader = {'content-type': 'application/json', 'Authorization' : auth}

r = requests.get(url, headers = queryHeader)
if r.status_code != 200: 
    exit('Cannot get engine list')

engines = r.json()
for e in engines:
    if e['name'] == target_engine_name:  
        if e['state'] == 'DISABLED': 
            put_url = url + '/' + e['id'] + '/enable'
            r = requests.put(put_url, headers = queryHeader)
            if r.status_code != 200:
                exit('Could not change engine status')
            else:
                exit('Successfully changed engine status')
        exit('Engine is already enabled')
print ('Could not find the engine')

