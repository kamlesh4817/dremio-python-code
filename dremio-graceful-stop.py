import requests, socket, time, os, logging, subprocess, re
from prometheus_client.parser import text_string_to_metric_families

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
        raise RuntimeError(err)
    if response.status_code != 200:
        raise RuntimeError("Authentication Error " + str(response.status_code))
    return response

def black_list_executor(auth, dremio_endpoint, executor_fqdn):
    logging.info("Setting terminating executor to drain if not already")
    authtoken = '_dremio' + auth.json()['token']
    headers = {"Accept": "application/json", "Authorization": authtoken}
    try:
        blacklistResponse = requests.request("GET", dremio_endpoint + "/api/v3/nodeCollections/blacklist", headers=headers, timeout=10, verify=False)
    except Exception as err:
        raise RuntimeError(err)
    blacklisted = blacklistResponse.json()
    if executor_fqdn not in blacklisted:
        blacklisted.append(executor_fqdn)
        try:
            requests.post(dremio_endpoint + "/api/v3/nodeCollections/blacklist", json=blacklisted, headers=headers, timeout=10, verify=False)
        except Exception as err:
            raise RuntimeError(err)

def ckeck_for_running_fragments(prometheus_endpoint):
    logging.info("Starting loop to check for running fragments, will timeout based on the pods terminationGracePeriodSeconds")
    num_running_fragments = 1
    while num_running_fragments > 0:
        num_running_fragments = 0
        try:
            response = requests.request("GET", prometheus_endpoint, timeout=5, verify=False)
        except Exception as err:
            raise RuntimeError(err)
        for family in text_string_to_metric_families(response.content.decode('utf-8')):
            if family.name == 'metrics_fragments_active_Number':
                for sample in family.samples:
                    num_running_fragments += sample.value
                logging.info("Running fragments: " + str(num_running_fragments))
                print("Running fragments: " + str(num_running_fragments))
        time.sleep(5)
    print("No running fragments exiting loop")
    logging.info("No running fragments exiting loop")


if __name__ == '__main__':
    output = str(subprocess.run('ps -ef | grep dremio', shell=True, check=True, executable='/bin/bash', stdout=subprocess.PIPE).stdout)
    re_out = re.search(' -Ddremio.log.path=(.+?) ', output)
    if re_out: 
        logpath = re_out.group(1)
    else:
        logpath = os.environ["DREMIO_LOG_DIR"]
    try:
        logging.basicConfig(filename=f'{logpath}/graceful_stop.log', encoding='utf-8', level=logging.INFO, format='%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s')
        print(f'logs in {logpath}/graceful_stop.log')
    except:
        print(f'first time executor mount')
        logpath = os.environ["DREMIO_LOG_DIR"]
        logging.basicConfig(filename=f'{logpath}/graceful_stop.log', encoding='utf-8', level=logging.INFO, format='%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s')
        print(f'logs in {logpath}/graceful_stop.log')
    logging.info("Getting environment vars and fully qualified domain")
    dremio_endpoint = os.environ['DREMIO_ENDPOINT']
    uid = os.environ['DREMIO_USERNAME']
    pwd = os.environ['DREMIO_PASSWORD']
    prometheus_endpoint = os.environ['PROMETHEUS_ENDPOINT']
    executor_fqdn = socket.getfqdn()
    auth = dremio_login(uid, pwd, dremio_endpoint)
    black_list_executor(auth, dremio_endpoint, executor_fqdn)
    ckeck_for_running_fragments(prometheus_endpoint)
