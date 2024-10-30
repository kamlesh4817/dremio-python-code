import json
import requests
import os
import configparser
import sys
import logging
from datetime import date


headers = {'content-type':'application/json'}
server_status = '/apiv2/server_status/'
sql_endpoint = '/api/v3/sql'
job_status_endpoint = '/api/v3/job/'
catalog_endpoint = '/api/v3/catalog/by-path/'
payload = "{\n\t\"sql\": \"alter pds dremiomonitor.dremiomonitor refresh metadata force update\"\n}"
dremio_pds = 'dremiomonitor'+'//' +'dremiomonitor'

# Get the LofFile name
today = date.today()
logfile = "dremio" + today.strftime("%d-%b-%Y") + ".log"
logging.basicConfig(filename=logfile, filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s() -  %(lineno)04d - | %(message)s', level=logging.INFO)

def main():

  try:  
    optionsFile   = sys.argv[1]
    dremioCluster = sys.argv[2]


  # Get the Dremio username and password from environment varibales
    username      = os.environ.get('DREMIO_USER')
    password      = os.environ.get('DREMIO_PASSWORD')
  

	# Parse options from the file
    configdata    = configParser(optionsFile, dremioCluster)
    api_timeout   = int(configdata['api_timeout'])
    dremioServer = configdata['dremioserver']
    path = configdata['path']
    jmxPort = configdata['jmxport']
    jdbcPort = configdata['jdbcport']
    jdbcJar = configdata['jdbcjar']
    verifySsl = configdata['verifyssl']
    webPort = configdata['webport']
    awsregion = configdata['awsregion']
    awsbucket = configdata['awsbucket']
    awsbucketfolder = configdata['awsbucketfolder']

    dremioWebURL = 'http://' + dremioServer + ':' + webPort
    headers = login(username,password,dremioWebURL)

     #Get the Object ID
    #response = requests.request("GET", dremioWebUrl + sql_endpoint, headers=headers, timeout=api_timeout, verify=verifySsl)
    response = requests.request("GET",dremioWebURL + catalog_endpoint + dremio_pds, headers=headers,verify=verifySsl)
    pds_info = json.loads(response.text)
    print(headers)
    if response.status_code != 200:
        raise RuntimeError("API Error " + str(response.status_code)+ " - " + response.status_code)
    print(pds_info['id'])
    #Trigger the refresh based on the ID
    dremio_refresh_url = dremioWebURL +'/api/v3/catalog/' + pds_info['id'] + '/refresh'
    response = requests.request("POST",dremio_refresh_url, headers=headers,verify=verifySsl)
  except Exception as e:
    logging.info('Failed to refresh reflection. Error meesage: ' + repr(e))



def login(username, password,dremioWebURL):
  # we login using the old api for now
  loginData = {'userName': username, 'password': password}
  response = requests.post(dremioWebURL + "/apiv2/login", headers=headers, data=json.dumps(loginData), verify=False)
  data = json.loads(response.text)
  # retrieve the login token
  token = data['token']
  logging.info('Successfully completed login function from refresh reflection code....')
  return {'content-type':'application/json', 'Authorization':'_dremio{authToken}'.format(authToken=token)}

   

def configParser(configFile, section):
  config = configparser.ConfigParser()
  config.read(configFile)
  configDict = {}
  options = config.options(section)
  for option in options:
    try:
      configDict[option] = config.get(section, option)
    except Exception as e:
      logging.info('Unable to parse config: ' + repr(e))
      configDict[option] = None
  return configDict

if __name__ == "__main__":
  main()