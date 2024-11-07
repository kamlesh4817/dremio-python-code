import time, math, json, urllib.parse, requests as r, pandas as pd
host = '<DremioMaster>'
UiPort = '<DremioMasterUIPort>'
uid = '<Username>'
pwd = '<UserPassword>'
SSL_enabled = <TrueorFalse>
saveLocation = <saveLocation>
sql = 'SELECT CONCAT(TABLE_SCHEMA, \'.\', TABLE_NAME) as vds FROM INFORMATION_SCHEMA.\\"TABLES\\" WHERE TABLE_TYPE = \'VIEW\' AND \\"LEFT\\"(TABLE_SCHEMA,1) != (\'@\')'''
rows_list = []
def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper
def get_parents(b, h, c, i):
    try:
        graph = r.request('GET', b + '/api/v3/catalog/' + c + '/graph', headers=h)
        gj = graph.json()
        if gj['parents']:
            for item in gj['parents']:
                if item['datasetType'] != 'VIRTUAL':
                    row = {}
                    row['VDS'] = i
                    row['PDS'] = '.'.join(item['path'])
                    rows_list.append(row)
                else:
                    get_parents(b, h, item['id'], i)
    except:
        print('The VDS lineage for ' + i + 'has broken. Please check this dataset')
if SSL_enabled:
    BASE_URL = 'https://' + host + ':' + UiPort
else:
    BASE_URL = 'http://' + host + ':' + UiPort
headers = {'Content-Type': 'application/json'}
data = '{"userName": "' + uid + '","password": "' + pwd + '"}'
response = r.post(BASE_URL + '/apiv2/login', headers=headers, data=data, verify=False)
authorization_code = '_dremio' + response.json()['token']
auth_header = {
    'Authorization': authorization_code,
    'Content-Type': 'application/json'}
response = r.request('GET', BASE_URL + '/api/v3/catalog', headers=auth_header)
catalog = response.json()['data']
data = '{\n    "sql": "' + sql + '",\n    "context":[]\n}'
response = r.post(BASE_URL + '/api/v3/sql', headers=auth_header, data=data)
job_id = response.json()['id']
job_status = r.request("GET", BASE_URL + "/api/v3/job/" + job_id, headers=auth_header).json()['jobState']
while job_status != 'COMPLETED':
    time.sleep(1)
    job_status = r.request("GET", BASE_URL + "/api/v3/job/" + job_id, headers=auth_header).json()['jobState']
response = r.request("GET", BASE_URL + "/api/v3/job/" + job_id + "/results?limit=500", headers=auth_header)
batchcount = truncate(float(response.json()['rowCount'])/500, 0) + 1
dicts = []
batchno = 0
while batchno < int(batchcount):
    response = r.request("GET", BASE_URL + "/api/v3/job/" + job_id + "/results?offset=" + str(batchno*500) + "&limit=500", headers=auth_header)
    data = json.loads(response.text)
    for result in data['rows']:
        row = {}
        row['vds'] = result['vds']
        if row not in dicts:
            dicts.append(row)
    batchno = batchno + 1
df = pd.DataFrame(dicts)
for i in df['vds']:
    response = r.request('GET', BASE_URL + '/api/v3/catalog/by-path/' + urllib.parse.quote(i.replace('.', '/')), headers=auth_header)
    catalogID = response.json()['id']
    graph = r.request('GET', BASE_URL + '/api/v3/catalog/' + catalogID + '/graph', headers=auth_header)
    try:
        if graph.json()['parents']:
            get_parents(BASE_URL, auth_header, catalogID, i)
    except:
        print('VDS ' + i + ' was not found in the graph API. Please check the definition of this VDS and resave')
lineage = pd.DataFrame(rows_list)
lineage.to_parquet(saveLocation)