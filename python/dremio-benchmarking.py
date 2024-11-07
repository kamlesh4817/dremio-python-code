import os, re, time, math, json, urllib.parse, requests as r, pandas as pd, getpass, urllib3, datetime, numpy as np
from datetime import date
urllib3.disable_warnings()

# Authentication
username = '<USERNAME>'
password = getpass.getpass(prompt='Password: ')
cluster = '<CLUSTER_NAME>'
port = '<PORT>'
SSL_enabled = False #True or False
directory = "<LOCATION_OF_SQL_SCRIPTS>"
saveAnalysisParquet='<LOCATION_TO_SAVE_RESULTS>'
noRuns=1
context = '""'

data = []
for filename in os.listdir(directory):
    if filename.endswith(".sql"):
        d_row = {}
        with open(directory + '/' + filename, 'r') as file:
            d_row['queryNo'] = filename[:-4]
            d_row['query'] = file.read().replace('\n', ' ')
            data.append(d_row)
dt = pd.DataFrame(data)
noqueries=len(dt)


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

allFail=True
queries = []
qs=[]
run=1
while run<=noRuns:
    for i in dt['query']:
        data = '{\n    "sql": "' + i.replace('"', '\\"') + '",\n    "context":['+context+']\n}'
        response = r.post(BASE_URL + '/api/v3/sql', headers=auth_header, data=data, verify=False)
        try:
            job_id = response.json()['id']
            q = {}
            if not(response.status_code is 200):
                print('Job creation failed.')
            else:
                queries.append(job_id)
                q['run']=run
                q['query']=i
                q['query_id']=job_id
                qs.append(q)
                allFail=False
        except:
            print('Job creation failed.')
    run=run+1
    dt = dt.iloc[np.random.permutation(len(dt))]
    dt.reset_index(drop=True)
df_q=pd.DataFrame(qs)

queryresults=[]
completed=False
if allFail!=True:
    while completed!=True:
        if len(queries)==0:
            completed=True
        for job in queries:
            job_status = r.get(BASE_URL + "/api/v3/job/"+job, headers=auth_header).json()
            queryresult={}
            if job_status['jobState'] == 'COMPLETED':
                queryresult['query_id'] = job
                queryresult['time'] = datetime.datetime.strptime(job_status['endedAt'], '%Y-%m-%dT%H:%M:%S.%fZ') - datetime.datetime.strptime(job_status['startedAt'], '%Y-%m-%dT%H:%M:%S.%fZ')
                queryresults.append(queryresult)
                queries.remove(job)
        time.sleep(1)
df_r=pd.DataFrame(queryresults)
df = pd.merge(df_q, df_r, left_on='query_id', right_on='query_id', how='inner')
df
df['time'] = (df['time'] / np.timedelta64(1, 'ms'))/1000
df.to_parquet( saveAnalysisParquet + str(date.today()) + '.parquet', compression='snappy')
