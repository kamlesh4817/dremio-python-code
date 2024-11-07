#!/usr/bin/env python3 
#
# Script to get Admin API resources. 
# Needs python client for Prometheus: Install client using "pip3 install prometheus_client"
# Needs ODBC drivers : Install by visiting https://docs.dremio.com/drivers/odbc-linux.html
#
# Name         : dremioMetrics.py
# Description  : Script to push Prometheus metrics for Dremio clusters via Push Gateway
# Author       : Dremio
# Date         : May 5, 2020
# Version      : 1.0
# Notes        : Needs python client for Prometheus: Install client using "pip3 install prometheus_client"
#                Uses JDBC driver : Visit https://docs.dremio.com/drivers/dremio-jdbc-driver.html for details
# CHANGE LOG   :
#


import sys
import configparser
import os.path
import requests
import json
import jaydebeapi
from prometheus_client import CollectorRegistry, Gauge, pushadd_to_gateway

# Configuration
debug = False
api_timeout = 2
verify_ssl = False

# Push Gateway URL
pgwendpoint = "http://dremio-master:9091"

# Metrics
api_up_metric = 'dremio_api_up'
api_coordinator_status_metric = 'dremio_api_coordinator_up'
api_cluster_status_metric = 'dremio_api_cluster_up'
api_total_executor_metric = 'dremio_api_total_executors_Value'
api_current_executor_metric = 'dremio_api_current_executors_Value'
api_cluster_memory_allocated_metric = 'dremio_api_cluster_allocated_memory_Value'
api_cluster_memory_used_metric = 'dremio_api_cluster_used_memory_Value'
sql_executor_metric = 'dremio_sql_executors_Value'
sql_direct_max_value = 'dremio_sql_executor_direct_max_Value'
sql_direct_current_value = 'dremio_sql_executor_direct_current_Value'
sql_threads_waiting_value = 'dremio_sql_threads_waiting_Value'
sql_datasource_count_value = 'dremio_sql_datasource_count_Value'

# API endpoints
server_status = '/apiv2/server_status'
login_url = '/apiv2/login'
cluster_url = '/apiv2/provision/clusters'
pgw_api_url = '/api/v1/metrics'

def main():
	
	if len(sys.argv) < 3:
		print_usage()
	else:
		optionsFile = sys.argv[1]
		dremioCluster = sys.argv[2]

		# Parse options from the file
		cluster = configParser(optionsFile, dremioCluster)
		masterCoordinator = cluster['mastercoordinator']
		standbyCoordinator = cluster['standbycoordinator']
		port = cluster['port']
		jmxPort = cluster['jmxport']
		username = cluster['username']
		password = cluster['password']
		jdbcPort = cluster['jdbcport']
		jdbcJar = cluster['jdbcjar']

		# URLs to hit
		masterUrl = "http://" + masterCoordinator + ":" + str(port)
		standbyUrl = "http://" + standbyCoordinator + ":" + str(port)
		masterJmxUrl = "http://" + masterCoordinator + ":" + str(jmxPort)
		standbyJmxUrl = "http://" + standbyCoordinator + ":" + str(jmxPort)

		# Check both Coordinators
		masterStatus, standbyStatus = 2, 2
		activeCoordinator = masterCoordinator
		try:
			role = 'Master'
			response = requests.get(masterUrl + server_status, timeout=api_timeout)
		except requests.ConnectionError:
			activeCoordinator = standbyCoordinator
			masterStatus = 1
			try:
				response = requests.get(masterJmxUrl, timeout=api_timeout)
			except requests.ConnectionError:
				masterStatus = 0

		# Push Master Coordinator Status
		push_api_coordinator_status_metric(dremioCluster, masterCoordinator, role, masterStatus)

		try:
			role = 'Standby'
			response = requests.get(standbyJmxUrl, timeout=api_timeout)
		except requests.ConnectionError:
			standbyStatus = 1
			try:
				response = requests.get(standbyUrl + server_status, timeout=api_timeout)
			except requests.ConnectionError:
				standbyStatus = 0

		# Push Standby Coordinator Status
		push_api_coordinator_status_metric(dremioCluster, standbyCoordinator, role, standbyStatus)

		if (masterStatus == 1 and standbyStatus == 0) or (masterStatus == 0 and standbyStatus == 0):
			# Both coordinators are down!
			if debug:
				print("Coordinators are Down! : ", dremioCluster)
			# Set all child clusters to down state. 
			# Get list of child clusters for this job from Push Gateway
			endpoint = pgwendpoint + pgw_api_url
			response = requests.get(endpoint)
			if response.status_code != 200:
				raise RuntimeError("API Error " + str(response.status_code)+ " - " + get_error_message(response))
			items = response.json()['data']
			for item in items:
				# Check if we have relevant metrics
				if api_cluster_status_metric in item or sql_direct_max_value in item:
					for record in item.items():
						if api_cluster_status_metric in record:
							metric = dict(dict(record[1])['metrics'][0])
							clusterName = metric['labels']['cluster']
							jobName = metric['labels']['job']
							if jobName == dremioCluster:
								push_api_coordinator_status_metric(dremioCluster, activeCoordinator, role, 0)
								push_api_cluster_status_metric(dremioCluster, clusterName, 0)
								push_api_total_executor_metric(dremioCluster, clusterName, 0)
								#push_api_current_executor_metric(dremioCluster, clusterName, 0)
								push_api_cluster_memory_allocated_metric(dremioCluster, clusterName, 0)
								push_api_cluster_memory_used_metric(dremioCluster, clusterName, 0)
		else:
			# Check Child Clusters
			endpoint = "http://" + activeCoordinator + ":" + str(port)
			headers = {"Content-Type": "application/json"}
			payload = '{"userName": "' + username + '","password": "' + password + '"}'
			response = requests.request("POST", endpoint + login_url, data=payload, headers=headers, timeout=api_timeout, verify=verify_ssl)
			if response.status_code != 200:
				raise RuntimeError("Authentication error." + str(response.status_code))
			authtoken = '_dremio' + response.json()['token']
			headers = {"Content-Type": "application/json", "Authorization": authtoken}
			# Get Cluster List
			response = requests.request("GET", endpoint + cluster_url, headers=headers, timeout=api_timeout, verify=verify_ssl)
			if response.status_code != 200:
				raise RuntimeError("API Error " + str(response.status_code)+ " - " + get_error_message(response))
			clusters = response.json()['clusterList']
			for cluster in clusters:
				clusterName = cluster['name']
				if cluster['currentState'] == "RUNNING":
					if debug:
						print("Cluster " + clusterName +" is UP")
					pendingCount = cluster['containers']['pendingCount']
					provisioningCount = cluster['containers']['provisioningCount']
					decommissioningCount = cluster['containers']['decommissioningCount']
					runningCount = len(cluster['containers']['runningList'])
					desiredExecutorCount = pendingCount + provisioningCount + runningCount - decommissioningCount
					runningContainers = cluster['containers']['runningList']
					if debug: 
						print("  Pending: ", pendingCount, "Provisioning: ", provisioningCount)
						print("  Provisioned Executors: ", desiredExecutorCount, "Running: ", runningCount)
					usedMemoryMB = 0
					executorCount = 0
					for container in runningContainers:
						propertyList = container['containerPropertyList']
						for item in propertyList:
							if item['key'] == "host":
								node = item['value']
							if item['key'] == "memoryMB":
								memoryMB = item['value']
						if debug:
							print("     Executor: ", node +  " Memory: ", memoryMB)
						usedMemoryMB = usedMemoryMB + int(memoryMB)
					yarnProps = cluster['yarnProps']
					yarnMemoryMB = runningCount * yarnProps['memoryMB']
					if debug:
						print("Total YARN Memory (GB): ", yarnMemoryMB/1024, "Used Memory(GB): ", usedMemoryMB/1024)

					# Push API Metrics
					push_api_cluster_status_metric(dremioCluster, clusterName, 1)
					push_api_total_executor_metric(dremioCluster, clusterName, desiredExecutorCount)
					push_api_current_executor_metric(dremioCluster, clusterName, runningCount)
					push_api_cluster_memory_allocated_metric(dremioCluster, clusterName, yarnMemoryMB)
					push_api_cluster_memory_used_metric(dremioCluster, clusterName, usedMemoryMB)	
				else:
					# Cluster is down!
					if debug:
						print("Cluster " + clusterName +" is DOWN!")
					push_api_cluster_status_metric(dremioCluster, clusterName, 0)
					push_api_total_executor_metric(dremioCluster, clusterName, 0)
					push_api_current_executor_metric(dremioCluster, clusterName, 0)
					push_api_cluster_memory_allocated_metric(dremioCluster, clusterName, 0)
					push_api_cluster_memory_used_metric(dremioCluster, clusterName, 0)

			# SQL Metrics
			# Connect to Dremio Node
			jdbcUrl = "jdbc:dremio:direct=" + activeCoordinator + ":" + str(jdbcPort)
			cnxn = jaydebeapi.connect("com.dremio.jdbc.Driver", jdbcUrl, [username, password], jdbcJar)
			cursor = cnxn.cursor()
			
			# Executor count
			query = 'select hostname, count(*) from sys.nodes group by hostname'
			cursor.execute(query)
			result = cursor.fetchall()
			for row in result:
				executorNode = row[0]
				executorCount = row[1]
				push_sql_metric(sql_executor_metric, dremioCluster, executorNode, executorCount)

			# Thread count
			query = 'select hostname, count(*) from sys.threads where threadState in (\'WAITING\') group by hostname'
			cursor.execute(query)
			result = cursor.fetchall()
			for row in result:
				executorNode = row[0]
				executorCount = row[1]
				push_sql_metric(sql_threads_waiting_value, dremioCluster, executorNode, executorCount)

			# Direct Memory
			query = 'select hostname, direct_max, direct_current, heap_max, heap_current from sys.memory'
			cursor.execute(query)
			result = cursor.fetchall()
			for row in result:
				executorNode = row[0]
				directMax = row[1]
				directCurrent = row[2]
				heapMax = row[3]
				heapCurrent = row[4]
				push_sql_metric(sql_direct_max_value, dremioCluster, executorNode, directMax)
				push_sql_metric(sql_direct_current_value, dremioCluster, executorNode, directCurrent)
			
			cursor.close()

def push_api_coordinator_status_metric(dremioCluster, activeCoordinator, intendedRole, status):
	# Push Coordinator Status
	registry = CollectorRegistry()
	metric = Gauge(api_coordinator_status_metric, "Coordinator status, pushed via Gateway",labelnames=['instance', 'role'], registry=registry)
	metric.labels(activeCoordinator, intendedRole).set_to_current_time()
	metric.labels(activeCoordinator, intendedRole).set(status)
	groupingKey = dict({"job": dremioCluster, "role": intendedRole})
	pushadd_to_gateway(pgwendpoint, job=dremioCluster, registry=registry, timeout=api_timeout, grouping_key=groupingKey)

def push_api_cluster_status_metric(dremioCluster, clusterName, status):
	# Push child cluster status metric
	registry = CollectorRegistry()
	metric = Gauge(api_cluster_status_metric, "Child cluster status, pushed via Gateway",labelnames=['cluster'], registry=registry)
	metric.labels(clusterName).set_to_current_time()
	metric.labels(clusterName).set(status)
	groupingKey = dict({"job": dremioCluster, "cluster": clusterName})
	pushadd_to_gateway(pgwendpoint, job=dremioCluster, registry=registry, timeout=api_timeout, grouping_key=groupingKey)

def push_api_total_executor_metric(dremioCluster, clusterName, desiredExecutorCount):
	# Push Total Executors provisioned metric
	registry = CollectorRegistry()
	metric = Gauge(api_total_executor_metric, "Total number of expected executors, pushed via Gateway",labelnames=['cluster'], registry=registry)
	metric.labels(clusterName).set_to_current_time()
	metric.labels(clusterName).set(desiredExecutorCount)
	groupingKey = dict({"job": dremioCluster, "cluster": clusterName})
	pushadd_to_gateway(pgwendpoint, job=dremioCluster, registry=registry, timeout=api_timeout, grouping_key=groupingKey)

def push_api_current_executor_metric(dremioCluster, clusterName, runningCount):
	# Push Current Executors provisioned metric
	registry = CollectorRegistry()
	metric = Gauge(api_current_executor_metric, "Current number of expected executors, pushed via Gateway",labelnames=['cluster'], registry=registry)
	metric.labels(clusterName).set_to_current_time()
	metric.labels(clusterName).set(runningCount)
	groupingKey = dict({"job": dremioCluster, "cluster": clusterName})
	pushadd_to_gateway(pgwendpoint, job=dremioCluster, registry=registry, timeout=api_timeout, grouping_key=groupingKey)

def push_api_cluster_memory_allocated_metric(dremioCluster, clusterName, yarnMemoryMB):
	# Push Memory metrics
	registry = CollectorRegistry()
	metric = Gauge(api_cluster_memory_allocated_metric, "Allocated memory (GB) to a child cluster, pushed via Gateway",labelnames=['cluster'], registry=registry)
	metric.labels(clusterName).set_to_current_time()
	metric.labels(clusterName).set(yarnMemoryMB/1024)
	groupingKey = dict({"job": dremioCluster, "cluster": clusterName})
	pushadd_to_gateway(pgwendpoint, job=dremioCluster, registry=registry, timeout=api_timeout, grouping_key=groupingKey)

def push_api_cluster_memory_used_metric(dremioCluster, clusterName,  usedMemoryMB):	
	# Push Memory metrics
	registry = CollectorRegistry()
	metric = Gauge(api_cluster_memory_used_metric, "Used memory (GB) for a child cluster, pushed via Gateway",labelnames=['cluster'], registry=registry)
	metric.labels(clusterName).set_to_current_time()
	metric.labels(clusterName).set(usedMemoryMB/1024)
	groupingKey = dict({"job": dremioCluster, "cluster": clusterName})
	pushadd_to_gateway(pgwendpoint, job=dremioCluster, registry=registry, timeout=api_timeout, grouping_key=groupingKey)

def push_sql_metric(metricName, dremioCluster, instance, metricValue):
	# Push SQL Metric
	registry = CollectorRegistry()
	metric = Gauge(metricName, "SQL Metric, pushed via Gateway",labelnames=['instance'], registry=registry)
	metric.labels(instance).set_to_current_time()
	metric.labels(instance).set(metricValue)
	pushadd_to_gateway(pgwendpoint, job=dremioCluster, registry=registry, timeout=api_timeout)

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

def get_error_message(self, response):
	message = ""
	try:
		if 'errorMessage' in response.json():
			message = message + " errorMessage: " + str(response.json()['errorMessage'])
		if 'moreInfo' in response.json():
			message = message + " moreInfo: " + str(response.json()['moreInfo'])
	except:
		message = message + " content: " + str(response.content)
	return message

def print_usage():
	prog = os.path.basename(__file__)
	print("USAGE: " + prog + " <Options File> <Dremio Cluster Name>")
	print("   Eg: " + prog + " /home/dremio/dremio.ini dremioCluster\n")

if __name__ == "__main__":
	main()
