# Get Catalog

import sys
import requests                         # pip install requests
import json                             # builtin, no install required

def flatten(p):
    q = []
    for r in p:
        if '.' in r or ' ' in r:
            t = '"' + r + '"'
            q.append (t)
        else:
            q.append(r)
    r = ".".join(q)
    return r

def search(item):
    id = item['id']
    if item['type'] == 'CONTAINER' and item['containerType'] == 'FOLDER' and id.startswith('dremio:'):
        return
    if item['type'] == 'FILE':
        return
    if item['type'] == 'DATASET':
        print(flatten(item['path']))
        return
    item_url = url + '/' + id
    r = requests.get(item_url, headers = queryHeader)
    if r.status_code != 200: 
        exit('Cannot get child catalog')
    children = r.json()['children'] 
    for c in children:
        search(c)

# User inputs
project_id = '6dac13c8-c1b0-4be5-9d59-cbfa607be820'
pat = 'U/soDX8PR3y+wapSa21KeGbJvSeN3CHHX3yvTaXHN7PEnpbLslFkk3cl+HmKZQ==' # generated on 10/30/24

auth = 'Bearer ' + pat
url = 'https://api.dremio.cloud/v0/projects/' + project_id + '/catalog'
source_url = url  + '/by-path/Samples' 
queryHeader = {'content-type': 'application/json', 'Authorization' : auth}
r = requests.get(source_url, headers = queryHeader)
if r.status_code != 200: 
    exit('Cannot get source catalog')
search(r.json()) 

