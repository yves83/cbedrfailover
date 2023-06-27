import json
from EdrUtils import *

class EdrConfig:
    keys=("gateway_ip","my_ip","peer_ip","virtual_ip","current_site","mount_point","server_port", "netdown_grace_peroid","lock_file","unlock_grace_peroid","clusterole", "log_file","mount_point_readonly","device","fs_type")
    values={"mount_point":"/var/cb", "server_port":10443, "netdown_grace_peroid":300, "unlock_grace_peroid":300, "lock_file":"/var/cbmon/cb-lock", "clusterole":"auto", "log_file":"/var/log/cb/cluster-state.log", "mount_point_readonly":"/var/cbmon", "device":"/dev/mapper/cluster-disk","fs_type":"gfs2"}

    def __init__(self, filename, log_file='edrConfig.log'):
        self.filename = filename
        self.utils = EdrUtils()
        self.data = self._load_data()
    

    def _load_data(self):
        data = self.utils.read_json_file(self.filename)
        res = {}
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
    

    def set(self, key, value):
        if key in self.keys:
            self.data[key] = value
    

    def save(self):
        self.utils.write_json_file(self.data, self.filename)

    
    def get_all(self):
        return self.data