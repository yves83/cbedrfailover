from EdrUtils import *
from EdrConfig import *
from Network import *
from EdrServiceController import *
from ServiceController import *
from DiskController import *
from State import *

class EdrController:
    keys=("network_state","disk_state","vip_state","service_state")
    default_values={}

    def __init__(self, system_file, state_file, logger):        
        # Initialize Networking Class
        self.logger = logger # Set the logger instance
        self.logger.debug(f'Initializing EdrController Class')

        self.system = EdrConfig(system_file)       # Load the configuration file class
        self.state = State(state_file)          # Load the State management class

        gwip = self.system.get('gateway_ip')
        peerip = self.system.get('peer_ip')
        vip = self.system.get('virtual_ip')
        
        self.network = Network(gwip, peerip, vip, logger)                # Load the Network class
        
        # Initialize Disk Class
        device_name=self.system.get('device')
        mount_point=self.system.get('mount_point')
        filesystem_type=self.system.get('fs_type')
        self.disk = DiskController(device_name, mount_point, filesystem_type)        # Load the Disk Controller 
        
        self.edrSvc = EdrServiceController(logger)    # Load the EDR Service Controller

        self.logger.debug(f'Initializing EdrController Class is completed')

        
    # Return the EDR service status
    def get(self, key):
        return self.state.get(key)
    
    # Save the EDR service status into file
    def save(self):
        self.state.save()


    def refresh_status(self):
        # Update Networking
        self.network.refresh_network_state()
        network_state='DOWN'
        if self.network.IsGatewayAlive():
            self.logger.debug(f'Gateway is reachable')
            network_state='UP'
        if len(self.system.get('peer_ip').strip()) > 0 and self.network.IsPeerAlive():
            self.logger.debug(f'Peer is reachable')
            network_state='UP'
            
        self.logger.info(f'EDR Server Network State is {network_state}')
        self.state.set('network_state',network_state)


        # Update VIP Binding Status
        if self.network.IsVipMapped():
            self.logger.info(f'The Virtual IP address is bind to this server')
            self.state.set('vip_state','BINDED')
        else:
            self.logger.info(f'The Virtual IP address is NOT bind to this server')
            self.state.set('vip_state','NOT BINDED')


        # Update Partition Mount Status
        if self.disk.ismounted():
            self.logger.info(f'The Data Partition is Mounted')
            self.state.set('disk_state','MOUNTED')
        else:
            self.logger.info(f'The Data Partition is NOT Mounted')
            self.state.set('disk_state','NOT MOUNTED')


        # Update EDR Service Status
        svcState=self.edrSvc.status()
        self.logger.info(f'The EDR service is {svcState}')
        self.state.set('service_state', svcState)


    def zip_edr_cronjob():
        command1=['gzip','-f','/etc/cron.d/cb'] 
        try:
            self.utils.exec_cmd(command1)
        except Exception as e:
            self.logger.error('Failed to compress the EDR Cronjob file. ' + str(e))


    def unzip_edr_cronjob():
        command1=['gzip','-d','/etc/cron.d/cb.gz']
        try:
            self.utils.exec_cmd(command1)
        except Exception as e:
            self.logger.error('Failed to decompress the EDR Cronjob file. ' + str(e))
     

    def activate_service(self):
        # Mount Partition
        self.logger.info(f'Activating EDR Service:')

        self.logger.info(f'   Start mounting data disk')
        self.disk.mount()
        if self.disk.ismounted():
            self.logger.info(f'   Mounting data disk success')
        else:
            self.logger.warn(f'   Mounting data disk failed')
            return False


        # Start EDR Service
        self.logger.info(f'   Start EDR services')
        self.edrSvc.start()
        running_state=self.edrSvc.status()
        if running_state == "RUNNING":
            self.logger.info(f'   EDR services are RUNNING')
        else:
            self.logger.warn(f'   EDR services are {running_state}')
            return False

        # Start Event Forwarder Service
        efw = ServiceController('cb-event-forwarder')
        eft.start()
        
        # Unzip cronjob
        self.zip_edr_cronjob()
         

    def deactivate_service(self):
        # Zip Cronjob 
        self.unzip_edr_cronjob()

        # Stop Event Forarder Service 
        efw = ServiceController('cb-event-forwarder')
        eft.stop() 

        # Stop EDR Service
        self.logger.info(f'   Stop EDR services')
        self.edrSvc.stop()
        running_state=self.edrSvc.status()
        if running_state == "STOPPED":
            self.logger.info(f'   EDR services are STOPPED')
        else:
            self.logger.warn(f'   EDR services are {running_state}')

        # Unmount Partition 
        self.self.logger.info(f'Deactivating EDR Service:')

        self.logger.info(f'   Stop mounting data disk')
        self.disk.mount()
        if self.disk.ismounted():
            self.logger.info(f'   Unmounting data disk is failed')
        else:
            self.logger.warn(f'   Unmounting data disk is success')



    # Test lock file availibility
    # Return True when lock file is available. Here is the rules:
    # 1. The Lock file is create by same server
    # 2. The Lock file was not updated for a certain of peroid
    # A cronjob should run regularly to keep update the lock file.
    def validate_lockfile(self, lockf):
        try:
            unlock_grace_peroid = self.system.get_value('unlock_grace_peroid')
            my_ip=self.system.get_value('my_ip')
            
            # Return True and exist when the lock file does not exist
            if not os.path.exists(lockf):
                return True

            # When the file content is empty, unlock the file
            lock_info = read_json_file(lockf)

            if len(lock_info)==0:
                return True

            lock_ts_delta = time.time() - lock_info['lock_ts']

            if lock_info['my_ip'] == my_ip:
                # IP Address Match
                return True
            elif lock_ts_delta > unlock_grace_peroid:
                # File lock expired
                return True
            
        except Exception as e:
            self.logger.debug(e)
            print(e)

        return False
    
    # This function will mount the cb data partion as read only when it is not mounted
    # and check the partition mount status in remoute host through testing the lock file availability 
    def check_remote_disk_mount_state(self):

        # This is the return value which indicated that whether the remote host mounted the partition
        partion_maybe_mounted='UNMOUNTED'

        #Refresh the Mount Point status
        self.refresh_disk_state()

        # Whatif the partition was mount occationally
        if self.state.get_value('disk_state') == "MOUNTED":
            mount_point=self.system.get_value('mount_point')
            lock_file=os.path.join(mount_point, self.system.get_value('lock_file'))

            # The lock file is free to update(return true). Partition was unmount.
            if self.validate_lockfile(lock_file):
                partion_maybe_mounted='UNMOUNTED'
            else:
                partion_maybe_mounted='MOUNTED'

        else: 
            try:
                dev = self.system.get_value('device')
                mpreadonly = self.system.get_value('mount_point_readonly')

                command1 = ['mount', '-t', 'gfs2', '-o', 'ro', dev,  mpreadonly]
                response = subprocess.run(command1, stdout=subprocess.PIPE)

                # When mount success
                if response.returncode == 0:
                    mount_point=self.system.get_value('mount_point_readonly')
                    lock_file=os.path.join(mount_point, self.system.get_value('lock_file'))
            
                    # The lock file is free to update(return true). Partition was unmount.
                    if self.validate_lockfile(lock_file):
                        partion_maybe_mounted='UNMOUNTED'
                    else:
                        partion_maybe_mounted='MOUNTED'
         
                    command1 = ['umount', mpreadonly]
                    response = subprocess.run(command1, stdout=subprocess.PIPE)
            except Exception as e:
                print(e)

        return partion_maybe_mounted


    def update_lock_file(self):
        try:
            #Refresh the Mount Point status
            self.refresh_disk_state()
            
            # Update the lock file when the partition is mount
            if self.state.get_value('disk_state') == "MOUNTED":
                mount_point=self.system.get_value('mount_point')
                lock_file=os.path.join(mount_point, self.system.get_value('lock_file'))

                if(self.validate_lockfile(lock_file)):
                    res={}
                    res['my_ip']=self.system.get_value('my_ip')
                    res['lock_ts']=time.time()
                    lock_file = self.system.get_value('mount_point') + "/cb-lock"
                    write_json_file(res,lock_file)
        except Exception as e:
            print(e)
            self.logger.debug(e)


    # Display the EDR Service Status
    def status(self):
        svc_running_state=self.state.get_value('service_state')
        print ("Overall Service Running State: " + svc_running_state)

        if svc_running_state=="STOPPED":
            return 

        print ("Individual Service Running State: ")
        svc_state = self.list_services_state()
        for state in svc_state.keys():
            for svc in svc_state[state]:
                print (svc + " ... ... " + state)

