#!/usr/bin/python3
###########
# Objective:
#    This script is used to configure the server state manually.
#    Here are the available operations:
#    - Set Local Cluster State: Auto / Master / Backup / Stop
#    - Mount Partiton: Mount / Umount
#    - Cb Services: Start / Stop / Status
#    - Cb Event Forwrder Services: Start / Stop / Status
# 

import sys
import os
import json
import subprocess
import time
import requests
import argparse
from termcolor import colored

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
sys.path.append(os.path.join(parent_dir,"lib"))

from DiskController import *
from EdrController import *
from EdrServiceController import *
from Network import *
from ServiceController import *
from State import *
from EdrConfig import *
from EdrUtils import *


##################################
# Variable Definition
##################################
config_file=os.path.join(parent_dir,"conf","system.conf")
lstate_file=os.path.join(parent_dir,"run","local_state.conf")
rstate_file=os.path.join(parent_dir,"run","remote_state.conf")

# Read System Configure
edrConf=EdrConfig(config_file)
sysinfo=edrConf.get_all()


##################################
# Main Program
##################################

#1. Initialize the local node status
utils = EdrUtils()
log_file=f'cluster-operation.log'
logger = utils.create_logger(log_file)

edr = EdrController(config_file, lstate_file, logger)
edr_svc = EdrServiceController(logger)
efwd = ServiceController('cb-event-forwarder')
kalive = ServiceController('keepalived')                      # Keep alive service
edr_hb_svc = ServiceController('edr-state-server')            # Defined the EDR Heart Beat Service and poll the service stauts
diskmgt = DiskController(sysinfo['device'], sysinfo['mount_point'])            # Load the Disk Controller 

netdown_grace_peroid=sysinfo["netdown_grace_peroid"]

# Load the Cached State Files
lstate=State(lstate_file)
lstatus=lstate.get_all()

rstate=State(rstate_file)
rstatus=rstate.get_all()

# Create an argument parser object
parser = argparse.ArgumentParser(description='This script can be used to manage the VMware EDR HA stauts.')

# Add arguments to the parser
parser.add_argument('--clusterole', required=False, choices=['auto','master','backup','stop'],
                    help='Set EDR Cluster role. When clusterole=auto, the master and backup role will switch automatically. When clusterrole=master, the service will start. When clusterole=backup, the service will stop. When clusterole=stop, the service will always stop.')
parser.add_argument('--datapart', required=False, choices=['mount','umount'],
                    help='Mount or Unmount EDR data partition')
parser.add_argument('--edr', required=False, choices=['start','stop'],
                    help='Start or Stop EDR services')
parser.add_argument('--event', required=False, choices=['start','stop'],
                    help='Start or Stop EDR Event Forwarder services')
parser.add_argument('--keepalive', required=False, choices=['start','stop'], 
                    help='Start or Stop Keepalive services')
parser.add_argument('--status', required=False, action='store_true', help='Check the EDR Cluster Status')

# Parse the arguments
args = parser.parse_args()

if args.status:
 
    # Define the values to be printed
    basic_info = {
        'BCP Site Role': colored(sysinfo['current_site'], 'green'),
        'Cluster Role': sysinfo['clusterole'],
        'Virtual IP': colored(sysinfo['virtual_ip'], 'yellow'),
        'My IP': sysinfo['my_ip'],
        'Gateway IP': sysinfo['gateway_ip'],
        'Data Disk Device': sysinfo['device'],
        'Data Disk Mount Point': sysinfo['mount_point'],
        'Heartbeat Listening Port': sysinfo['server_port'],
        'Network Down Grace Period': str(sysinfo['netdown_grace_peroid']) + ' seconds',
        'Lock File Unlock Grace Period': str(sysinfo['unlock_grace_peroid']) +' seconds',
        'Lock File': sysinfo['mount_point']+"/"+sysinfo['lock_file'] + " OR " + sysinfo['mount_point_readonly']+"/"+sysinfo['lock_file'],
        'Log Location': sysinfo['log_file']
    }


    default_color = {
        'vip_state':'red',
        'disk_state':'red',
        'edr_svc':'red',
        'efwd_svc':'red',
        'kalive_svc':'red',
        'edr_hb_svc':'red'
    }

    edr.refresh_status()
    efwd_svc_status = efwd.status()
    kalive_svc_status = kalive.status()
    edr_hb_svc_status = edr_hb_svc.status()
    

    if edr.get('vip_state') == "BINDED":
         default_color['vip_state']='green'
    
    if edr.get('disk_state') == "MOUNTED":
         default_color['disk_state']='green'
    
    if edr.get('service_state') == "RUNNING":
         default_color['edr_svc']='green'

    if efwd_svc_status == "RUNNING":
         default_color['efwd_svc']='green'

    if kalive_svc_status == "RUNNING":
         default_color['kalive_svc']='green'
 
    if edr_hb_svc_status == "RUNNING":
         default_color['edr_hb_svc']='green'

    local_state = {
        'Virtual IP Binding State': colored(edr.get('vip_state'), default_color['vip_state']),
        'Data Disk Mount State': colored(edr.get('disk_state'), default_color['disk_state']),
        'EDR Service State': colored(edr.get('service_state'), default_color['edr_svc']),
        'Event Forwarder Service State': colored(efwd_svc_status, default_color['efwd_svc']),
        'Keepalive Service State': colored(kalive_svc_status, default_color['kalive_svc']),
        'EDR Heartbeat Service State': colored(edr_hb_svc_status, default_color['edr_hb_svc'])
    }
    

    # Print the formatted output
    print(colored('Basic Information:\n','cyan'))
    for key, value in basic_info.items():
        print('{:<50}{}'.format(key,':  '+value))

    print(colored('\n\nLocal Running State:\n','cyan'))
    for key, value in local_state.items():
        print('{:<50}{}'.format(key,':  '+value))

    print('\n\n\n')


elif args.clusterole == "master":
    print ("Transforming to Master")
    
    #Save the clusterole state
    edrConf.set("clusterole",args.clusterole)
    edrConf.save()
    edr.activate_service()
   
elif args.clusterole == "backup" or args.clusterole == "stop":
    #Save the clusterole state
    edrConf.set("clusterole",args.clusterole)
    edrConf.save()
    edr.deactivate_service()

elif  args.clusterole == "auto":
    #Save the clusterole state
    edrConf.set("clusterole",args.clusterole)
    edrConf.save()

elif args.datapart=="mount":
    print ("Mount EDR Data partition")
    diskmgt.mount()

elif args.datapart=="umount":
    print ("Unmount EDR Data partition")
    diskmgt.unmount()
    
elif args.edr=="start":
    print ("Start the EDR services")
    edr_svc.start()

elif args.edr=="stop":
    print ("Stop the EDR services")
    edr_svc.stop()

elif args.event=="start":
    print ("Start the EDR Event Forwarder services")
    efwd.start()
    
elif args.event=="stop":
    print ("Stop the EDR Event Forwarder services")
    efwd.stop()

elif args.keepalive=="start":
    print ("Start the Keep Alive services")
    kalive.start()

elif args.keepalive=="stop":
    print ("Stop the Keep Alive services")
    kalive.stop()

else:
    parser.print_help()   
