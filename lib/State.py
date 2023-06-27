import json
import datetime
from EdrUtils import *

class State:
    # vip_last_flip: record the earliest vip obtained date time
    keys=("network_state", "disk_state", "vip_state", "service_state", "vip_bind_dt", "last_update")
    values={"network_state": "", "disk_state": "", "vip_state": "", "service_state": ""}

    def __init__(self, fullpath):
        self.statefile = fullpath
        self.utils = EdrUtils()
        self.data = self._load_data()


    
    def _load_data(self):
        data = self.utils.read_json_file(self.statefile)
        res={}
        for k in self.keys:
            if k in self.values.keys():
                res[k] = self.values[k]
            else:
                res[k] = ""
            
            if k in data.keys():
                res[k] = data[k]
        return res
    
    def get(self, key):
        if key in self.keys:
            return self.data[key]
        return "" 
        
    def get_all(self):
        return self.data
    
    def set(self, key, value):
        if key in self.keys:
            if key == "vip_state" and self.data[key]=="UNBIND" and value=="BIND":
                now=datetime.datetime.now()
                self.data["vip_bind_dt"] = now.strftime('%Y-%m-%d %H:%M:%S')
                print ("vip_bind_dt: " + now.strftime('%Y-%m-%d %H:%M:%S'))

            if key != "vip_bind_dt":
                self.data[key] = value
    
    def save(self):
        now=datetime.datetime.now()
        self.data["last_update"] = now.strftime('%Y-%m-%d %H:%M:%S')
        self.utils.write_json_file(self.data, self.statefile)


    def last_update_drift(self):
        try:
            if self.data["last_update"]:
                now=datetime.datetime.now()
                last_update=datetime.datetime.strptime(self.data["last_update"], '%Y-%m-%d %H:%M:%S')
                return (now - last_update).seconds
        except Exception as e:
            print(e)
        return 0

