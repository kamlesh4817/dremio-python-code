import requests as r, re, json, time, pandas as pd, urllib3, getpass
urllib3.disable_warnings()

# Authentication
username = '<Username>'
password = getpass.getpass(prompt='Password: ')
cluster = '<ClusterDNS/IP>'
port = '<UIPort>'
SSL_enabled = False #True or False
dataset = 'expected_cflow_keys_df'
dataSource = 'test'
CTASlocation = 'TestFiles.RenRe'

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

data = '{\n    "sql": "SELECT key FROM \\"@' + username + '\\".' + dataset + '",\n    "context":[]\n}'
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

for i in df['key']:
    ar = i.split('/')
    ar = ar[1:]
    i = '"' + '"."'.join(ar) + '"'
    ic = CTASlocation + '.' + i.replace('.csv', '')
    data = '{\n    "sql": "CREATE TABLE ' + ic.replace('"', '\\"') + ' AS SELECT * FROM ' + dataSource + '.' + i.replace('"', '\\"') + '",\n    "context":[]\n}'
    response = r.post(BASE_URL + '/api/v3/sql', headers=auth_header, data=data, verify=False)
    job_id = response.json()['id']

    if not(response.status_code is 200):
        print('Job creation failed.')
