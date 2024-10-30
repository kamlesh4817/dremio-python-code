import requests as r, pandas as pd, urllib.parse, urllib3, re, getpass, time, json
urllib3.disable_warnings()
# Authentication
HOST = 'automaster'
PORT = '9047'
SSL = False
uid = 'dremio'
# pwd = getpass.getpass(prompt='Password: ')
pwd = 'dremio123'

datasource = 'hive'

data = '{"userName": "' + uid + '","password": "' + pwd + '"}'

if SSL:
    BASE_URL = 'https://' + HOST + ':' + PORT
else:
    BASE_URL = 'http://' + HOST + ':' + PORT

def parse_dataset_path(dataset_path):
    path=""
    dataset_path = re.findall('"[^"]*"|[^.]+', dataset_path)
    dataset_path = [dataset_path_part.replace('"', '') for dataset_path_part in dataset_path]
    dataset_path = [dataset_path_part.replace(' ', '%20') for dataset_path_part in dataset_path]
    for part in dataset_path:
        path=path+"/"+part
    return (path)

headers = {
    'Content-Type': 'application/json',
}

response = r.request('POST', BASE_URL + '/apiv2/login', headers=headers, data=data, verify=False)

authorization_code = '_dremio' + response.json()['token']
print(authorization_code)

if response.status_code == 200:
    print ('Successfully authenticated.')
else:
    print('Authentication failed.')

auth_header = {
    'Authorization': authorization_code,
    'Content-Type': 'application/json',
}

sql = 'SELECT * FROM INFORMATION_SCHEMA.\\"TABLES\\" WHERE TABLE_SCHEMA like \'hive%\''

# data = '{\n    "sql": "' + sql + '",\n    "context":["INFORMATION_SCHEMA"]\n}'

response = r.post(BASE_URL + '/api/v3/sql', headers=auth_header, data=data, verify=False)

# print(response.text)

try:
    job_id = response.json()['id']
    print(job_id)
    if not(response.status_code == 200):
        print('Job creation failed.')
    else:
        status = r.get(BASE_URL + "/api/v3/job/"+job_id+"/results?limit=500", headers=auth_header, verify=False).status_code
        while not(status == 200):
            time.sleep(1)
            status = r.get(BASE_URL + "/api/v3/job/"+job_id+"/results?limit=500", headers=auth_header, verify=False).status_code
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
        df['tbls']=df['TABLE_SCHEMA'] + '.' + df['TABLE_NAME']
        for rw,v in df.iterrows():
            try:
                response = r.get(BASE_URL + "/api/v3/catalog/by-path"+parse_dataset_path(v['tbls']), headers=auth_header, verify=False)
                datasetid = response.json()['id']
                response = r.post(BASE_URL + "/api/v3/catalog/"+datasetid+"/refresh", headers=auth_header, data='', verify=False)
            except:
                print('PDS failure. Please check ' + parse_dataset_path(v['tbls']))
except:
    print('Refresh job failed')

# import http.client

# conn = http.client.HTTPSConnection("localhost", 9047)
# payload = ''
# headers = {
#   'Authorization': '_dremiohltbgvmsogpu18cj6k429538sc'
# }
# conn.request("GET", "/api/v3/catalog/", payload, headers)
# res = conn.getresponse()
# data = res.read()
# print(data.decode("utf-8"))    