from EdrUtils import *

class ServiceController:
    def __init__(self, svc_name, log_file='serviceController.log'):
        self.service_name=svc_name
        self.utils = EdrUtils()


    # Turn on the service
    def start(self):
        command1 = ['systemctl','start',self.service_name]
        response = self.utils.exec_cmd(command1)
        if response:
            if response.returncode == 0:
                return True
        return False


    # Turn off the service
    def stop(self):
        command1 = ['systemctl','stop',self.service_name]
        response = self.utils.exec_cmd(command1)
        if response:
            if response.returncode == 0:
                return True
        return False


    # Turn off the service
    def status(self):
        command1 = ['systemctl','status',self.service_name]
        response = self.utils.exec_cmd(command1)
        if response:
            if response.returncode == 0:
                return "RUNNING"
        return "STOPPED"


    # Kill cb thr process if it can't completely stopped
    # Try 3 times if the process can't kill
    def killall(self, user_name):
        for x in range(3):
            command1 = ['killall','-u',user_name]
              
            if response.returncode == 0:
                return True
            time.sleep(3)

        return False

