#!/usr/bin/env python3
#
#
# Name         : dremiomonitor.py
# Description  : Script to push jmx & SQL metrics for Dremio to AWS S3
# Author       : Dremio
# Date         : Oct 19, 2022
# Version      : 1.0
# Notes        : Needs boto3 for uploading to S3: Install client using "python -m pip install boto3"
#                Uses JDBC driver : Visit https://docs.dremio.com/drivers/dremio-jdbc-driver.html for details
#                Uses Python JDBC Module: Install client using "python -m pip install JayDeBeApi"
#                Export evironment variables DREMIO_USER, DREMIO_PASSWORD, AWS_KEY, AWS_SECRET (Ex: export DREMIO_USER="localadmin" )
#                To run the program: python dremiomonitor.py <config_file> <section_in_config_file> 
#                Example: python metricsToS3.py monitorconfig.txt PROD
# CHANGE LOG   :
#  Version 1.x :
#          Date: Oct XX, 20XX
#   Description: XXXXXXXXXXXXXXXXXXXXXX
#



import json
import logging
import requests
import os
import time
import jaydebeapi
import configparser
import sys
import boto3
import datetime
from datetime import date
from datetime import timezone




headers = {'content-type':'application/json'}
metrics_header_file = '_dremiometricsheader.txt'
metrics_file = '_dremiometrics.txt'
dremio_status_file = '_dremiostatus.txt'
epoch = round(time.time()) 
utc_time = datetime.datetime.now(timezone.utc)
utc_time_string =  utc_time.strftime('%Y-%m-%d %H:%M:%S') 
year = utc_time.strftime('%Y')
month = utc_time.strftime('%m')
day = utc_time.strftime('%d')
hour = utc_time.strftime('%H')
server_status = '/apiv2/server_status'

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
  
   # Get the AWS Access Key and Secret from environment varibales
    awskey = os.environ.get('AWS_KEY')
    awssecret = os.environ.get('AWS_SECRET')

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
    dremioMetricsURL = 'http://' + dremioServer + ':' + jmxPort + '/metrics'
  
# Check Server Status via API call. Proceed to collect metrics if server is active
    response = requests.get(dremioWebURL + server_status, timeout=api_timeout, verify=verifySsl)
    if(response.text == '"OK"'):
      out_header_file = open(path + '/' + dremioCluster + metrics_header_file, "w")
      out_metrics_file = open(path + '/' + dremioCluster + metrics_file, "w")
      out_status_file = open(path + '/' + dremioCluster + dremio_status_file, "w")
      logging.info("Calling Dremio Server for Metrics .....")
      appendJMXMetrics(dremioMetricsURL,out_header_file,out_metrics_file,out_status_file,dremioCluster,dremioWebURL,username,password)
      appendSQLMetrics(dremioServer, jdbcPort, jdbcJar,out_metrics_file,username,password,dremioCluster)
      out_status_file.write("OK" + "\n")
      logging.info("Finished writing to AWS for Metrics .....")
    else:
      print(response.text)
      out_status_file.write("INACTIVE")
      logging.error("Dremio Server is unavailable. Program Quitting.....")
    out_header_file.close()
    out_metrics_file.close()
    out_status_file.close()
    writeToS3(awskey,awssecret,awsregion,awsbucket,awsbucketfolder,path,dremioCluster)
  except Exception as e:
    logging.error('Failed to write metrics to S3. Error meesage: ' + repr(e))
  


def login(username, password,dremioWebURL):
  # we login using the old api for now
  loginData = {'userName': username, 'password': password}
  response = requests.post(dremioWebURL + "/apiv2/login", headers=headers, data=json.dumps(loginData), verify=False)
  data = json.loads(response.text)
  # retrieve the login token
  token = data['token']
  logging.info('Successfully completed login function....')
  return {'content-type':'application/json', 'Authorization':'_dremio{authToken}'.format(authToken=token)}

def appendJMXMetrics(dremioMetricsURL,out_header_file,out_metrics_file,out_status_file,dremiocluster,dremioWebURL,username,password):
  headers = login(username,password,dremioWebURL)
  response = requests.get(dremioMetricsURL,headers=headers,verify=False)
  metricSource = 'JMX'
  node = 'Co-ordiantor'
  if (response.status_code == 200):
    for x in response.text.splitlines():
      if ('#' in x):
        out_header_file.write(x + "\n")
      else:
        temp = x.split(" ")
        out_metrics_file.write(utc_time_string + "," + year + "," + month + "," + day + "," + hour + "," + dremiocluster +  "," + node + "," + metricSource + "," +temp[0] + "," +  temp[1] + "\n")
    logging.info('Successfully completed appendJMXMetrics....')
  else:
    out_status_file.write("JMX_INACTIVE")
  
 

def  appendSQLMetrics(dremioServer, jdbcPort, jdbcJar,out_metrics_file,username, password,dremiocluster):
  jdbcUrl = "jdbc:dremio:direct=" + dremioServer+ ":" + str(jdbcPort)
  cnxn = jaydebeapi.connect("com.dremio.jdbc.Driver", jdbcUrl, [username, password], jdbcJar)
  cursor = cnxn.cursor()
  metricSource = 'SQL'
  node = 'Co-ordiantor'

# Executor count
  query = 'select hostname, count(*) from sys.nodes group by hostname'
  cursor.execute(query)
  result = cursor.fetchall()
  for row in result:
    executorNode = row[0]
    executorCount = row[1]
    out_metrics_file.write(utc_time_string + "," + year + "," + month + "," + day + "," + hour + "," + dremiocluster +  "," + node + "," + metricSource + "," + 'sql_executor_count' + "," + str(executorCount) + "\n")

# Thread count
  query = 'select hostname, count(*) from sys.threads where thread_state in (\'WAITING\') group by hostname'
  cursor.execute(query)
  result = cursor.fetchall()
  for row in result:
    executorNode = row[0]
    threadCount = row[1]
    out_metrics_file.write(utc_time_string + "," + year + "," + month + "," + day + "," + hour + "," + dremiocluster +  "," + node + "," + metricSource + "," + 'sql_threads_waiting_value' + "," + str(threadCount)+ "\n")

# Direct Memory
  query = 'select hostname, direct_max, direct_current, heap_max, heap_current from sys.memory'
  cursor.execute(query)
  result = cursor.fetchall()
  memorydict = {}
  for row in result:
    executorNode = row[0]
    out_metrics_file.write(utc_time_string + "," + year + "," + month + "," + day + "," + hour + "," + dremiocluster +  "," + node + "," + metricSource + "," + 'sql_memory_metric_directmax' + "," + str(row[1])+ "\n")
    out_metrics_file.write(utc_time_string + "," + year + "," + month + "," + day + "," + hour + "," + dremiocluster +  "," + node + "," + metricSource + "," + 'sql_memory_metric_directcurrent' + "," + str(row[2])+ "\n")
    out_metrics_file.write(utc_time_string + "," + year + "," + month + "," + day + "," + hour + "," + dremiocluster +  "," + node + "," + metricSource + "," + 'sql_memory_metric_heapmax' + "," + str(row[3])+ "\n")
    out_metrics_file.write(utc_time_string + "," + year + "," + month + "," + day + "," + hour + "," + dremiocluster +  "," + node + "," + metricSource + "," + 'sql_memory_metric_heapcurrent'+ "," + str(row[4])+ "\n")
        

# VDS Count
  query = 'select count(*) from information_schema."TABLES" where table_type = \'VIEW\' and table_schema not like \'@%\''
  cursor.execute(query)
  vdsCount = 0
  result = cursor.fetchall()
  for row in result:
    vdsCount = str(row[0])
    out_metrics_file.write(utc_time_string + "," + year + "," + month + "," + day + "," + hour + "," + dremiocluster +  "," + node + "," + metricSource + "," + 'sql_vds_count_value'+ "," + vdsCount + "\n")
  cursor.close()
  logging.info('Successfully completed appendSQLMetrics function....')

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

def writeToS3(awskey, awssecret, awsregion,bucket,folder,path,dremioCluster):
  s3 = boto3.resource('s3', region_name=awsregion,aws_access_key_id=awskey,aws_secret_access_key=awssecret)
  localfile = path + '/' + dremioCluster +  metrics_file
  remotefile = folder + '/' + dremioCluster +'_dremiometrics_' + str(epoch) + '.txt'
  #with open(localfile) as f:
  s3.Bucket(bucket).upload_file(localfile,remotefile)
  #f.close()
  logging.info('Successfully wrote metrics to S3....')

def writeToIceberg(dremioServer, jdbcPort, jdbcJar,path, metrics_file,username, password,dremiocluster):
  jdbcUrl = "jdbc:dremio:direct=" + dremioServer+ ":" + str(jdbcPort)
  cnxn = jaydebeapi.connect("com.dremio.jdbc.Driver", jdbcUrl, [username, password], jdbcJar)
  cursor = cnxn.cursor()
  metricSource = 'SQL'
  node = 'Co-ordiantor'
  metrics_file = open(path + metrics_file, "r")
  query_string = metrics_file.read()
  length = len(query_string)
  query = query_string[:length-1]
  cursor.execute(query)
  result = cursor.fetchall()
  for row in result:
    rows_written = row[0]
  logging.info('Successfully wrote ' + str(rows_written) + ' metrics to Iceberg....')   


if __name__ == "__main__":
  main()