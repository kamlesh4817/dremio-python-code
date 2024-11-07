#################################################################################
# Before starting the code make sure to run the following                       #
# export  DREMIO_SOURCE_USER='<source_user_id>'                                 #    
# export  DREMIO_SOURCE_PASSWORD='<source_password>'                            #
# Execution Steps:                                                              #
# Step1. Create a directory called "wlmtuning". Can be any name though          # 
# Step2: Copy the code "DremioWlmTuning.py" and "DremioWlmConfig.txt" into      #
#        the directory created in Step1                                         #    
# Step3: python DremioWlmMemoryGuardrails.py DremioWlmMemoryGuardrailsConfig.txt PROD DEMO                #
#        python DremioWlmMemoryGuardrails.py DremioWlmMemoryGuardrailsConfig.txt PROD RUN                 #
#
# Note:                                                                         #
#                                                                               #
#################################################################################


import json
import logging
import requests
import os
import configparser
import sys
import time
import jaydebeapi
from datetime import date
import json


headers = {'content-type':'application/json'}
# Get the LofFile name
today = date.today()
logfile = "dremio" + today.strftime("%d-%b-%Y") + ".log"
logging.basicConfig(filename=logfile, filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s() -  %(lineno)04d - | %(message)s', level=logging.INFO)
sql_endpoint = '/api/v3/sql'
queue_endpoint = '/api/v3/wlm/queue'
job_status_endpoint = '/api/v3/job/'
payload_directmemory = "{\n\t\"sql\": \"select node_tag, avg(direct_max) from sys.nodes a, sys.memory b where a.hostname = b.hostname AND a.is_executor = true group by node_tag\"\n}"
concurrency = { 'High Cost Reflections':2, 'High Cost User Queries':3,'Low Cost User Queries':20,'Low Cost Reflections':5,'UI Previews':100}
query_memoryfactor_pernode = { 'High Cost Reflections':0.75, 'High Cost User Queries':0.75,'Low Cost User Queries':0.4375,'Low Cost Reflections':0.4375,'UI Previews':0.5}
job_memoryfactor_pernode = { 'High Cost Reflections':0.5, 'High Cost User Queries':0.5,'Low Cost User Queries':0.1875,'Low Cost Reflections':0.1875,'UI Previews':0.5}
direct_memory = 0


def main():

  try:  
    environmentFile   = sys.argv[1]
    environment       = sys.argv[2]
    update_flag       = sys.argv[3]

  # Get the Dremio Source username and password from environment varibales
    username      = os.environ.get('DREMIO_SOURCE_USER')
    password      = os.environ.get('DREMIO_SOURCE_PASSWORD')
    #print(username + ',' + password)

   # Get the executor memory from Dremio

  	# Parse options from the file
    configdata            = configParser(environmentFile, environment)
    api_timeout           = int(configdata['api_timeout'])
    dremioServer          = configdata['dremioserver']
    webPort               = configdata['webport']
    jdbcPort              = configdata['jdbcport']
    verifySsl             = configdata['verifyssl']
    jdbcJar               = configdata['jdbcjar']
 
    dremioURL = 'http://' + dremioServer + ':' + webPort 
    #print(dremioURL)

    # Get the login auth token from Dremio
    authtoken = login(username,password,dremioURL)
    #print(authtoken)

    # Get the Average Direct Memory
    average_directmemory = getDirectMemory(dremioServer,jdbcPort,jdbcJar, username, password)
    memory_by_engine = {}
    for item in average_directmemory:
        memory_by_engine[item[0]] = item[1]
    print()
    print("**************** AVAILABLE AVERAGE DIRECT MEMORY BY ENGINE *******************")
    print(memory_by_engine)
    print()
    print()
    print("********************** CURRENT QUEUE CONFIGURATION ***************************")
    # Get all the queues
    allqueue = getAllQueue(dremioURL,authtoken)
    for x in allqueue['data']:
        print(json.dumps(x,indent=5))
    print('************************ UPDATED QUEUE CONFIGURATION *************************')
    # Update the queue data with right consurrency number
    updatedqueue = updateQueue(allqueue['data'],dremioURL,authtoken,memory_by_engine,update_flag)
    for x in updatedqueue:
       print(json.dumps(x,indent=5))

  except Exception as e:
    logging.error(' Error meesage: ' + repr(e))



def login(username, password,dremioWebURL):
  # we login using the old api for now
  loginData = {'userName': username, 'password': password}
  logging.info("Getting the Auth token")
  response = requests.post(dremioWebURL + "/apiv2/login", headers=headers, data=json.dumps(loginData), verify=False)
  data = json.loads(response.text)
  # retrieve the login token
  token = data['token']
  logging.info('Successfully completed login function....')
  return {'content-type':'application/json', 'Authorization':'_dremio{authToken}'.format(authToken=token)}


# Read the memory data from Server

def getDirectMemory(dremioServer, jdbcPort, jdbcJar, username, password):
    jdbcUrl = "jdbc:dremio:direct=" + dremioServer+ ":" + str(jdbcPort)
    cnxn = jaydebeapi.connect("com.dremio.jdbc.Driver", jdbcUrl, [username, password], jdbcJar)
    cursor = cnxn.cursor()
# Get Average Memory
    query = "select node_tag, avg(direct_max) as avg_memory from sys.nodes a, sys.memory b where a.hostname = b.hostname AND a.is_executor = true group by node_tag"
    cursor.execute(query)
    result = cursor.fetchall()
    return result


# Read the Memory
def configParser(configFile, section):
  config = configparser.ConfigParser()
  config.read(configFile)
  configDict = {}
  options = config.options(section)
  for option in options:
    try:
      configDict[option] = config.get(section, option)
    except:
      print("exception on %s!" % option)
      configDict[option] = None
  return configDict

# Get all the queues
def getAllQueue(dremioURL,authToken):
    response = requests.get(dremioURL + queue_endpoint, headers=authToken, verify=False) 
    data = json.loads(response.text)
    return data

def updateQueue(queuelist,dremioURL,authToken,memory_by_engine,update_flag):
    updatedqueue = []
# Update concurrency, maxmemory and job memory as per PS guidelines
    for item in queuelist:
# If 'engineid' is present, get the direct memory for that engine. If not, get the direct memory with engineid as ''
        if ('engineId' in item):
            direct_memory = round(memory_by_engine[item['engineId']])
        else:
            direct_memory = round(memory_by_engine[''])
        item['maxAllowedRunningJobs'] = concurrency[item['name']]
        item['maxMemoryPerNodeBytes'] = round(query_memoryfactor_pernode[item['name']] * direct_memory)
        if(item['name'] == 'Low Cost User Queries' or item['name'] == 'Low Cost Reflections' ):
            if (job_memoryfactor_pernode[item['name']] * direct_memory < 5368709120):
               item['maxQueryMemoryPerNodeBytes'] = round(job_memoryfactor_pernode[item['name']] * direct_memory)
            else:
                item['maxQueryMemoryPerNodeBytes'] = 5368709120
        else:
            item['maxQueryMemoryPerNodeBytes'] = round(job_memoryfactor_pernode[item['name']] * direct_memory)
        if(update_flag == 'RUN'):
            response = requests.put(dremioURL + "/api/v3/wlm/queue/" + item['id'], headers=authToken, data=json.dumps(item), verify=False)
            data = json.loads(response.text)
            updatedqueue.append(data)
        else:
            updatedqueue.append(item)

    return updatedqueue

if __name__ == "__main__":
   main()
