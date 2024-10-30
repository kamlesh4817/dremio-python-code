import json
import requests

username = 'dremio'
password = 'dremio123'
headers = {'content-type':'application/json'}
dremioServer = 'http://localhost:9047'

def apiGet(endpoint):
  return json.loads(requests.get('{server}/api/v3/{endpoint}'.format(server=dremioServer, endpoint=endpoint), headers=headers).text)

def apiPost(endpoint, body=None):
  text = requests.post('{server}/api/v3/{endpoint}'.format(server=dremioServer, endpoint=endpoint), headers=headers, data=json.dumps(body)).text

  # a post may return no data
  if (text):
    return json.loads(text)
  else:
    return None

def apiPut(endpoint, body=None):
  return requests.put('{server}/api/v3/{endpoint}'.format(server=dremioServer, endpoint=endpoint), headers=headers, data=json.dumps(body)).text

def apiDelete(endpoint):
  return requests.delete('{server}/api/v3/{endpoint}'.format(server=dremioServer, endpoint=endpoint), headers=headers)

def login(username, password):
  # we login using the old api for now
  loginData = {'userName': username, 'password': password}
  response = requests.post('http://demo.drem.io:9047/apiv2/login', headers=headers, data=json.dumps(loginData))
  data = json.loads(response.text)

  # retrieve the login token
  token = data['token']
  return {'content-type':'application/json', 'authorization':'_ dremio{authToken}'.format(authToken=token)}

headers = login(username, password)
