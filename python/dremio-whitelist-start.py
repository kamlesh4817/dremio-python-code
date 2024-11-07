import requests, os, socket, logging, subprocess, re

# If a start up script throws and error / exits with code != 0 it causes the pod to go into a crashloop
# This can happen on inital cluster start up if the executor goes through it's init containsers faster than the master pod.
# Therefore all potential errors are caught and logged out to ${DREMIO_LOG_DIR}/whitelist_start.log with the script exiting with code 0.
# During exspected operation of this script the master will be up. All the REST calls are well defined and know to work.

requests.packages.urllib3.disable_warnings()
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'

def dremio_login(uid, pwd, dremio_endpoint):
    logging.info("Dremio login")
    headers = {"Content-Type": "application/json"}
    payload = '{"userName": "' + uid + '","password": "' + pwd + '"}'
    payload = payload.encode(encoding='utf-8')
    try:
        response = requests.request("POST", dremio_endpoint + "/apiv2/login", data=payload, headers=headers, timeout=None, verify=False)
    except Exception as err:
        logging.error(err)
        os._exit(0)
    if response.status_code != 200:
        logging.error("Authentication Error " + str(response.status_code))
        os._exit(0)
    return response

def check_and_reset_blacklist(auth, dremio_endpoint, executor_fqdn):
    logging.info("Checking and reseting blacklist status")
    authtoken = '_dremio' + auth.json()['token']
    headers = {"Accept": "application/json", "Authorization": authtoken}
    try:
        blacklistResponse = requests.request("GET", dremio_endpoint + "/api/v3/nodeCollections/blacklist", headers=headers, timeout=None, verify=False)
    except Exception as err:
        logging.error(err)
        os._exit(0)
    blacklisted = blacklistResponse.json()
    blacklisted_new = list(filter(lambda b: executor_fqdn != b, blacklisted))
    try:
        requests.post(dremio_endpoint + "/api/v3/nodeCollections/blacklist", json=blacklisted_new, headers=headers, timeout=None, verify=False)
    except Exception as err:
        logging.error(err)
        os._exit(0)


if __name__ == '__main__':
    output = str(subprocess.run('ps -ef | grep dremio', shell=True, check=True, executable='/bin/bash', stdout=subprocess.PIPE).stdout)
    re_out = re.search(' -Ddremio.log.path=(.+?) ', output)
    if re_out:
        logpath = re_out.group(1)
    else:
        logpath = os.environ["DREMIO_LOG_DIR"]
    try:
        logging.basicConfig(filename=f'{logpath}/whitelist_start.log', encoding='utf-8', level=logging.INFO, format='%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s')
        print(f'logs in {logpath}/whitelist_start.log')
    except Exception as err:
        print(f'first time executor mount')
        logpath = os.environ["DREMIO_LOG_DIR"]
        logging.basicConfig(filename=f'{logpath}/whitelist_start.log', encoding='utf-8', level=logging.INFO, format='%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s')
        print(f'logs in {logpath}/whitelist_start.log')
    logging.info("Getting environment vars and fully qualified domain")
    dremio_endpoint = os.environ['DREMIO_ENDPOINT']
    uid = os.environ['DREMIO_USERNAME']
    pwd = os.environ['DREMIO_PASSWORD']
    executor_fqdn = socket.getfqdn()
    auth = dremio_login(uid, pwd, dremio_endpoint)
    check_and_reset_blacklist(auth, dremio_endpoint, executor_fqdn)
    logging.info("If the executor was blacklisted that status has been removed")
