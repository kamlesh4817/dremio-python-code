import pymongo
import json
from pymongo import MongoClient, InsertOne

client = pymongo.MongoClient({CONNECTION_STRING})
db = client.hr
requesting = []
folder_location = {LOCATION OF HR FILES}
collections = {
    "countries": db.countries,
    "departments": db.departments,
    "employees": db.employees,
    "job_history": db.job_history,
    "jobs": db.jobs,
    "locations": db.locations,
    "regions": db.regions
    }

for key in collections:
    requesting = []
    filename = folder_location + key + ".json"
    with open(filename, "r") as f:
        for jsonObj in f:
            myDict = json.loads(jsonObj)
            requesting.append(InsertOne(myDict))

    result = collections[key].bulk_write(requesting)
    
client.close()
