import argparse
import requests
import time
import json

BASE_URL = "http://localhost:9047/api/v3"

# Job wait timeout in seconds
JOB_TIMEOUT = 5

# Job status polling frequency in seconds
JOB_STATUS_POLL_FREQUENCY = 0.2

# terminal job states
TERMINAL_JOB_STATES = ["COMPLETED", "CANCELED", "FAILED"]

def getAuthenToken(url, user, passwd):
    headers = {'Content-Type': 'application/json'}
    payload = '{"userName": "%s", "password": "%s"}' % (user, passwd)
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code != 200:
        print("Error getting authentication token")
        return NONE
    token = json.loads(response.text)['token']
    return token

# function to create a space
def create_space(space_name):
    headers = {
        "Authorization": f"{API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "entityType": "space",
        "name": space_name
    }
    response = requests.post(f"{BASE_URL}/catalog", headers=headers, json=data)
    if response.status_code == 200:
        print(f"Space '{space_name}' created successfully.")
    elif response.status_code == 409:
        print(f"Space '{space_name}' already exists, skipping.")
    else:
        print(f"Error creating space '{space_name}': {response.text}")

# function to create a folder
def create_folder(space_id, folder_path):
    headers = {
        "Authorization": f"{API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "path": folder_path,
        "entityType": "folder",
    }
    response = requests.post(f"{BASE_URL}/catalog", headers=headers, json=data)
    if response.status_code == 200:
        print(f"Folder '{folder_path}' created successfully.")
    elif response.status_code == 409:
        print(f"Folder '{folder_path}' already exists, skipping.")
    else:
        print(f"Error creating folder '{folder_path}': {response.text}")

# function to run queries, returns job ID
def run_sql(sql):
    headers = {
        "Authorization": f"{API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "sql": sql,
        "context": ["repo"]
    }
    response = requests.post(f"{BASE_URL}/sql", headers=headers, json=data)
    if response.status_code != 200:
        print(f"ERROR {response.status_code}!")
    return response.json()["id"]

# get job status
def get_job_status(job_id):
    headers = {
        "Authorization": f"{API_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(f"{BASE_URL}/job/{job_id}", headers=headers)
    if response.status_code != 200:
        print(f"Error code {response.status_code} getting job: {job_id}")
    return response.json()["jobState"]
    
# Parse command line arguments
parser = argparse.ArgumentParser(description="Script to create spaces and folders in your local Dremio instance.")
parser.add_argument("-host", type=str, help="Dremio host", default="localhost")
parser.add_argument("-port", type=str, help="Dremio port", default="9047")
parser.add_argument("-user", type=str, help="Dremio username", default="dremio")
parser.add_argument("-password", type=str, help="Dremio password", default="dremio123")
parser.add_argument("-folder", type=str, help="Path to repro tool output. e.g., /path/to/dx-12345/")
parser.add_argument("--createall", action=argparse.BooleanOptionalAction, help="Create PDSs VDSs and reflections or not (default false)")
parser.set_defaults(createall=False)
args = parser.parse_args()

API_TOKEN = getAuthenToken(f'http://{args.host}:{args.port}/apiv2/login', args.user, args.password)
FOLDER_PATH = args.folder
NAMESPACES_PATH = args.folder + "namespace.sql"
PDS_PATH = args.folder + "pds.sql"
MISSING_DATASETS_PATH = args.folder + "missing_datasets.sql"
VDS_PATH = args.folder + "vds.sql"
REFLECTIONS_PATH = args.folder + "reflections.sql"

# read namespaces.sql
with open(NAMESPACES_PATH, "r") as namespaces:
    namespaces_lines = namespaces.readlines()

# spaces and folder creation phases:
#         0 - skip over sources
#         1 - create spaces folders
#         2 - create versioned folders
#         3 - create versioned refs
current_phase = 0
for line in namespaces_lines:
    # skip blank lines
    if not line.strip():
        continue

    # skip sources
    if current_phase == 0:
        if line.startswith("SPACES FOLDERS"):
            current_phase += 1
        continue

    # creating spaces and folders
    if current_phase == 1:
        if line.startswith("VERSIONED FOLDERS"):
            current_phase += 1
            continue
        # split the line into space and folders
        parts = line.strip().split(".")
        space_name = parts[0].strip('"')
        folders = [folder.strip('"') for folder in parts[0:]]

        # check if space already exists using the get space by path API
        space_path = '.'.join([space_name] + folders)
        response = requests.get(f"{BASE_URL}/catalog/by-path/{space_name}", headers={"Authorization": f"{API_TOKEN}"})

        if response.status_code == 404:
            create_space(space_name)
        elif response.status_code != 200:
            print(f"Error getting space by path '{space_path}': {response.text}")
            continue
        
        response = requests.get(f"{BASE_URL}/catalog/by-path/{space_name}", headers={"Authorization": f"{API_TOKEN}"})
        space_id = response.json()["id"]
        
        # create folders
        for i in range(1, len(folders)):
            create_folder(space_id, folders[0:i+1])

    # creating versioned folders and refs
    if current_phase == 2:
        if line.startswith("VERSIONED REFS"):
            continue
        run_sql(line)

if args.createall:
    # create PDSs. We need to pause between each statement so each PDS finishes being made before trying to insert any rows
    with open(PDS_PATH, "r") as pds:
        print("Creating PDSs...")
        pds_script = pds.read()
        statements = pds_script.split(";")
        for statement in statements:
            if statement.strip():
                job_id = run_sql(statement)
                start_time = current_time = time.time()
                while True:
                    current_time = time.time()
                    elapsed_time = current_time - start_time

                    if elapsed_time > JOB_TIMEOUT:
                        print(f"Maximum wait ({JOB_TIMEOUT} sec) reached for job {job_id}.")
                        break

                    status = get_job_status(job_id)

                    if status in TERMINAL_JOB_STATES:
                        print(f"Job {job_id} finished with status {status}")
                        break
                    else:
                        time.sleep(JOB_STATUS_POLL_FREQUENCY)
    
    # if there are missing datasets, issue a warning before continuing, because there will be errors
    with open(MISSING_DATASETS_PATH, "r") as missing:
        missing_script = missing.read()
        if missing_script.strip():
            proceed = input("Missing dataset(s) in repro. Proceeding will produce VDS/reflection creation errors. Continue? (y/n)")
        else:
            proceed = "y"
    if proceed != "y":
        exit()
        
    # create VDSs
    with open(VDS_PATH, "r") as vds:
        print("Creating VDSs...")
        vds_script = vds.read()
        statements = vds_script.split(";")
        for statement in statements:
            if statement.strip():
                job_id = run_sql(statement)
                start_time = current_time = time.time()
                while True:
                    current_time = time.time()
                    elapsed_time = current_time - start_time

                    if elapsed_time > JOB_TIMEOUT:
                        print(f"Maximum wait ({JOB_TIMEOUT} sec) reached for job {job_id}.")
                        break

                    status = get_job_status(job_id)

                    if status in TERMINAL_JOB_STATES:
                        print(f"Job {job_id} finished with status {status}")
                        break
                    else:
                        time.sleep(JOB_STATUS_POLL_FREQUENCY)

    # create reflections
    with open(REFLECTIONS_PATH, "r") as reflections:
        print("Creating reflections...")
        reflections_script = reflections.read()
        statements = reflections_script.split(";")
        for statement in statements:
            if statement.strip():
                run_sql(statement)

print("Repro setup complete. Please check the jobs UI for any failures/errors!")
