#!/usr/bin/python3
import requests
import json
import os
import time
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
sys.path.append(os.path.join(parent_dir,"lib"))

from ServiceController import *
from EdrConfig import *
from State import *
from EdrController import *
from EdrUtils import *

utils = EdrUtils()
log_file=f'state-monitor.log'
logger = utils.create_logger(log_file)

config_file=os.path.join(parent_dir,"conf","system.conf")
lstate_file=os.path.join(parent_dir,"run","local_state.conf")
rstate_file=os.path.join(parent_dir,"run","remote_state.conf")

logger.debug(f"Load Configure file: {config_file}")
sysinfo=EdrConfig(config_file)

logger.debug(f"Load Local State file: {lstate_file}")
lstate=State(lstate_file)

logger.debug(f"Load Remote State file: {rstate_file}")
rstate=State(rstate_file)

logger.debug(f"Initialize Cb Event Forwarder Service Controller")
efwd = ServiceController('cb-event-forwarder')

logger.debug(f"Initialize Keepalived Service Controller")
kalive = ServiceController('keepalived')

# Refresh the local service and network status
try:
    logger.debug(f"Initialize EDR Controller")
    edr = EdrController(config_file, lstate_file, logger)
    
    logger.debug(f"Refreshgin the overall EDR status")
    edr.refresh_status()
    #edr.update_lock_file() #Only Active Node will take effect

    logger.debug(f"Save the EDR status in locate state file")
    edr.save()
    
except Exception as e:
    print(f'Exception: ' + str(e))
    logger.debug(f'Exception: ' + str(e))

    
# Refresh the remote service and network status
url = "http://%s:%s" % (sysinfo.get("peer_ip"),sysinfo.get("server_port"))

try:
    logger.debug(f"Polling remote server state file from URL: {url}")
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()
    with open(rstate_file, "w") as outfile:
        json.dump(data, outfile)
        logger.debug(f"Save Remote Server State to {rstate_file}")

except requests.exceptions.HTTPError as http_error:
    logger.error(f"HTTP error occurred: {http_error}")
except requests.exceptions.RequestException as request_error:
    logger.error(f"An error occurred while making the request: {request_error}")
except json.JSONDecodeError as json_error:
    logger.error(f"Error decoding JSON: {json_error}")
except Exception as error:
    logger.error(f"An unexpected error occurred: {error}")
