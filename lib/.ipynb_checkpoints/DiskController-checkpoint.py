from EdrUtils import *

class DiskController:
    def __init__(self, device_name, mount_point, fstype='gfs2', readonly=False):
        #self.logger = logger # Set the logger instance
        #self.logger.debug(f'Initializing EdrController Class')
        
        self.device_name = device_name
        self.mount_point = mount_point
        self.file_system_type = fstype
        self.readonly = readonly
        self.utils = EdrUtils()


    # Turn on the service
    def mount(self):
        if self.readonly:
            command1 = ['mount','-o','ro','-t',self.file_system_type,self.device_name,self.mount_point]
        else:
            command1 = ['mount','-t',self.file_system_type,self.device_name,self.mount_point]
   
        response = self.utils.exec_cmd(command1)
        return response
        #if response:
        #    if response.returncode == 0:
        #        return True
        #return False


    # Turn off the service
    def unmount(self):
        command1 = ['umount',self.mount_point]
        response = self.utils.exec_cmd(command1)
        return response
        #if response:
        #    if response.returncode == 0:
        #        return True
        #return False


    # Turn off the service
    def ismounted(self):
        command1 = ['mount']
        response = self.utils.exec_cmd(command1)

        target=f'{self.device_name} on {self.mount_point} type {self.file_system_type} (rw'
        if self.readonly:
            target=f'{self.device_name} on {self.mount_point} type {self.file_system_type} (ro'
            
        if response:
            #print(response.stdout)
            if target.encode('UTF-8') in response.stdout:
                return True
        return False

