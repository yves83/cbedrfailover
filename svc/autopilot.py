#!/usr/bin/python3
import requests
import json
import os
import time
import sys
import datetime
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
sys.path.append(os.path.join(parent_dir,"lib"))

from ServiceController import *
from System import *
from State import *
from EdrController import *
from Utils import *
        
config_file=os.path.join(parent_dir,"conf","system.conf")
lstate_file=os.path.join(parent_dir,"run","local_state.conf")
rstate_file=os.path.join(parent_dir,"run","remote_state.conf")

sysinfo=SystemConfig(config_file)
utils = Utils()
logger = utils.create_logger(self.__name__, sysinfo.get('log_file'))

lstate=StateClass(lstate_file)
rstate=StateClass(rstate_file)

efwd = ServiceController('cb-event-forwarder')
kalive = ServiceController('keepalived')

# Main
# 1. Check whether the clusterole is auto
clusterole=sysinfo.get_value("clusterole")
netdown_grace_peroid=sysinfo.get_value("netdown_grace_peroid")
lstatus=lstate.get_all()
rstatus=rstate.get_all()

# Initialize the EDR object
#1. Initialize the local node status
edr = EdrController(config_file, lstate_file)
#edr_svc = EdrServiceController()
#efwd = ServiceController('cb-event-forwarder')
#kalive = ServiceController('keepalived')                      # Keep alive service
#edr_hb_svc = ServiceController('edr-state-server')            # Defined the EDR Heart Beat Service and poll the service stauts
diskmgt = DiskController(sysinfo['device'], sysinfo['mount_point'])            # Load the Disk Controller 


print(f"Cluster Role: {clusterole}")
if clusterole == "auto" or clusterole == "master":
    # Calculate the duration since the VIP bind
    # convert to datetime objects
    dtobj_now = datetime.datetime.now()
     
    try:
        dtobj_vip_bind_dt = datetime.datetime.strptime(lstatus["vip_bind_dt"], '%Y-%m-%d %H:%M:%S')
        print("VIP Bind DT: %s" % (dtobj_vip_bind_dt))
    except Exception as e:
        dtobj_vip_bind_dt = dtobj_now
        print(e)

    time_diff = dtobj_now - dtobj_vip_bind_dt

    print(f'Time difference: {time_diff.seconds} seconds, threshold {netdown_grace_peroid}')


    if (lstatus["network_state"] == "UP" and 
        lstatus["service_state"] == "STOPPED" and 
        time_diff.seconds > netdown_grace_peroid and 
        lstatus["vip_state"] == "BIND"):
        
        remote_last_update_drift = rstate.last_update_drift()
 
        print(f'Remote last update drift {remote_last_update_drift}')

        if remote_last_update_drift > netdown_grace_peroid: 
            # Mount partition and validate the lock file
            rmount_state=edr.check_remote_disk_mount_state()
            print ("Checked remote mount state with lock file: " + rmount_state)
            if rmount_state == "UNMOUNTED":
                print ('Cluster role transform to master')
                clusterole="master"
            else:
                print ('Error: Remote is still mouting the disk')
        elif remote_last_update_drift < netdown_grace_peroid and rstatus["disk_state"] == "UNMOUNTED":
            #Set the clusterole as master and start the service will start automatically
            print ('Cluster role transform to master')
            clusterole="master"
        else:
            print("Nothing happen")
    else:
        print(f'Condition not match. Network State {lstatus["network_state"]}, Service Statue {lstatus["service_state"]}, VIP State: {lstatus["vip_state"]}')
    
    if (lstatus["vip_state"] == "UNBIND" or lstatus["network_state"] == "DOWN") and time_diff.seconds > netdown_grace_peroid:
        #Set the clusterole as backup and stop the service will start automatically
        print('Cluster role transform to backup')
        clusterole="backup"


if clusterole == "master":
    print ("Transforming to Master state")
    edr.activate_service()

if (clusterole == "backup" or clusterole == "stop"):
    print (f'Transforming to {clusterole} state')
    edr.deactivate_service()
