from EdrUtils import *

class EdrServiceController:
    def __init__(self, logger):
        self.utils = EdrUtils()
        self.logger = logger
        self.services=[]


    # Turn on the service
    def start(self):
        command1 = ['/etc/init.d/cb-enterprise','start']
        response = self.utils.exec_cmd(command1)


    # Turn off the service
    def stop(self):
        command1 = ['/etc/init.d/cb-enterprise','stop']
        response = self.utils.exec_cmd(command1)

        svc_list=('cb-enterprised', 'cb-allianceclient', 'cb-liveresponse', 'cb-sensorservices', 'cb-coreservices', 'cb-datastore', 'cb-nginx', 'cb-solr', 'cb-rabbitmq', 'cb-redis', 'cb-datagrid', 'cb-pgsql')
        for svc_name in svc_list:
            command1 = ['/usr/share/cb/cbservice',svc_name,'stop']
            response = subprocess.run(command1, stdout=subprocess.PIPE)

        self.killall()


    # Turn off the service
    def status(self):
        #Reset the Services Status
        command1 = ['/etc/init.d/cb-enterprise','status']
        response = self.utils.exec_cmd(command1)

        #Reset the Service State
        if(response):
            status_array=response.stdout.decode("UTF-8").split("\n")
            services={}
            for status in status_array:
                if len(status) < 10:
                    continue

                status=status.split(".")[0]
                s=status.split(" ")
                if s[-1].upper() in services.keys():
                    services[s[-1].upper()].append(s[0])
                else:
                    services[s[-1].upper()]=[]
                    services[s[-1].upper()].append(s[0])
            self.services=services
             
            k=services.keys()
            if "RUNNING" in k and "STOPPED" in k:
                return "FAILED"
            elif response.returncode == 0:
                return "RUNNING"

        return "STOPPED"


    def get_services_status(self):
        return self.services


    # Kill cb thr process if it can't completely stopped
    # Try 3 times if the process can't kill
    def killall(self, user_name='cb'):
        for x in range(3):
            command1 = ['killall','-u',user_name]
            response = self.utils.exec_cmd(command1) 
            if(response):
                if response.returncode == 0:
                    return True
            time.sleep(3)

        return False

