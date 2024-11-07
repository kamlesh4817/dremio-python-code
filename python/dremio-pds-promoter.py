#!/usr/bin/python
import pandas as pd
from sys import argv
import os
import json
import requests
import time
import urllib3
#urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings() 
#************* Input Dremio Crendentials ********
dremioServer = "http://host:9047"
username = "user"
password = "paswd"
#***********************************************
def apiGet(endpoint):
    return json.loads(
        requests.get(
            "{server}/api/v3/{endpoint}".format(server=dremioServer, endpoint=endpoint),
            headers=headers,verify = False 
        ).text
    )

def apiPost(endpoint, body=None, headers=None):
    text = requests.post(
        dremioServer + "/api/v3/" + endpoint, headers=headers,verify=False, data=json.dumps(body)
    ).text
    # a post may return no data
    if text:
        return json.loads(text)
    else:
        return None


def login(username, password):
    # we login using the old api for now
    loginData = {"userName": username, "password": password}
    response = requests.post(
        dremioServer + "/apiv2/login", headers=headers, verify=False,data=json.dumps(loginData)
    )
    data = json.loads(response.text)
    # retrieve the login token
    token = data["token"]
    return {
        "content-type": "application/json",
        "Authorization": "{authToken}".format(authToken=token),
    }

def querySQL(query, headers):
    queryResponse = apiPost("sql", body={"sql": query}, headers=headers)
    jobid = queryResponse["id"]
    return jobid
#print(headers)

def ex():
    print("    Usage: \n"
                  "          auto_refresh.py <PDS> OR \n" +
                  "          auto_refresh.py -f <File with list of PDSs > \n"+   
                  "          auto_refresh.py -f <File with list of PDSs> +R (Reflection Refresh)") 
    quit()

headers = {"content-type": "application/json"}

if len(argv) < 2:
    ex()        
def ref(dataset):
    url = dremioServer + "/api/v3/catalog/by-path/" + dataset.replace(".","/")
    payload = ""

    response = requests.request("GET", url, data=payload, headers=headers,verify=False)
    dataout= json.loads(response.text)
    id_num = dataout["id"]

    url2= dremioServer+ "/api/v3/catalog/"+id_num + "/refresh"
    ref_now= requests.request("POST", url2, headers=headers,verify=False,data="")
    return()
epoch=int(time.time())
suff=time.strftime("%m-%d-%Y-%H%M%S", time.localtime(epoch))
if len(argv) == 2 and argv[1] != '-f':
    headers = login(username, password)
    query = 'ALTER TABLE '+ argv[1].replace("/",".")+" REFRESH METADATA"
    jobid = querySQL(query, headers)
    print("Processing... " +query)
    time.sleep(2)
    results = apiGet('job/{id}/results?offset={offset}&limit={limit}'.format(id=jobid, offset=0, limit=1))
    #print(results[0].value)
    #for key, value in results.items():
    #    print(key,value)
    if 'errorMessage' in results.keys():
        #print(results["errorMessage"]+"  Error Processing "+ query)
        print("Error Processing... "+ query)
# Refresh Reflections  
    ref(argv[1].replace(".","/"))
    print("Dependant Reflections Refresh submitted")
elif(argv[1] == '-f' and len(argv) ==3):
    headers = login(username, password)
    fr = open(argv[2], "r")
# Uncomment the following line to write different logs for repeat runs and comment the next
#    fwname="refresh_err"+suff+".log"
    fwname="refresh_err.log"
    fw = open(fwname, "w")
    for line in fr:
       query = 'ALTER TABLE '+ line.strip().replace("/",".")+" REFRESH METADATA"
       jobid = querySQL(query, headers)
       print("Processing... " +query)
       time.sleep(.5)
       results = apiGet('job/{id}/results?offset={offset}&limit={limit}'.format(id=jobid, offset=0, limit=1))
       if 'errorMessage' in results.keys():
           print("Error Processing... "+ query)
           fw.write("Error Processing PDS.... " + line )

    fr.close() 
    fw.close()
    print("All Done ..")
elif(argv[1] == '-f' and argv[3] == '+R'and len(argv) ==4):
    headers = login(username, password)
    fr = open(argv[2], "r")
# Uncomment the following line to write different logs for repeat runs and comment the next
#    fwname="refresh_err"+suff+".log"
    fwname="refresh_err.log"
    fw = open(fwname, "w")
    for line in fr:
       query = 'ALTER TABLE '+ line.strip().replace("/",".")+" REFRESH METADATA"
       jobid = querySQL(query, headers)
       print("Processing... " +query)
       time.sleep(.5)
       results = apiGet('job/{id}/results?offset={offset}&limit={limit}'.format(id=jobid, offset=0, limit=1))
       if 'errorMessage' in results.keys():
 #          print("Error Processing... "+ query)
           fw.write("Error Processing PDS.... " + line )
# Refresh Reflections
       ref(line.strip().replace(".","/"))
       print("Dependant Reflections Refresh submitted")

    fr.close() 
    fw.close()
    print("All Done ..")
else:
    ex()
    #results = apiGet('job/{id}/results?offset={offset}&limit={limit}'.format(id=jobid, offset=0, limit=100))
    #print(results)
