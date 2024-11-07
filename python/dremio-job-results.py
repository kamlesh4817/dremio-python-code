import requests as r, re, json, time, pandas as pd, urllib3
urllib3.disable_warnings()

# Authentication
username = '<Username>'
password = '<Password>'
cluster = '<ClusterDNS/IP>'
port = '<UIPort>'
SSL_enabled = False #True or False
datasetURI = '<DATASET>'

if SSL_enabled:
    BASE_URL = 'https://' + cluster + ':' + port
else:
    BASE_URL = 'http://' + cluster + ':' + port

headers = {
    'Content-Type': 'application/json',
}

data = '{"userName": "' + username + '","password": "' + password + '"}'
response = r.post(BASE_URL + '/apiv2/login', headers=headers, data=data, verify=False)

authorization_code = '_dremio' + response.json()['token']

auth_header = {
    'Authorization': authorization_code,
    'Content-Type': 'application/json',
}

data = '{\n    "sql": "SELECT * FROM ' + datasetURI.replace('"', '\\"') + ' LIMIT 1000",\n    "context":[]\n}'
response = r.post(BASE_URL + '/api/v3/sql', headers=auth_header, data=data, verify=False)
job_id = response.json()['id']

if not(response.status_code is 200):
    print('Job creation failed.')

# Get status of the previous job
job_status = r.get(BASE_URL + "/api/v3/job/" +job_id, headers=auth_header).json()['jobState']

while job_status != 'COMPLETED':
    time.sleep(1)
    job_status = r.get(BASE_URL + "/api/v3/job/" +job_id, headers=auth_header, verify=False).json()['jobState']
response = r.get(BASE_URL + "/api/v3/job/"+job_id+"/results?limit=500", headers=auth_header, verify=False)

totalrows = float(response.json()['rowCount'])

rows = []
rowno = 0
while rowno < totalrows:
    response = r.get(BASE_URL + "/api/v3/job/"+job_id+"/results?offset=" + str(rowno) + "&limit=500", headers=auth_header, verify=False)
    data = json.loads(response.text)
    for result in data['rows']:
        rows.append(result)
        rowno = rowno + 1
df = pd.DataFrame(rows)
df
