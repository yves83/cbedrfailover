from EdrUtils import *

class Network:
    def __init__(self, gateway, peer_ip, virtual_ip, logger):
        self.logger = logger # Set the logger instance
        self.logger.debug('Initializing Network Class')
        
        self.gateway=gateway
        self.peer = peer_ip
        self.vip = virtual_ip
        self.utils = EdrUtils()
        self.gateway_is_alive=False
        self.peer_is_alive=False
        self.vip_is_mapped=False


    def refresh_network_state(self):
        self.logger.debug('Refreshing the networking status on current host')
        
        # Check the VIP mapping status
        command1 = ['/usr/sbin/ip','addr']
        response = self.utils.exec_cmd(command1)
        target=f' {self.vip}/'
        
        if response:
            self.logger.debug('Obtained IP address list from system')
            if target.encode('UTF-8') in response.stdout:
                self.logger.info('VIP is found')
                self.vip_is_mapped=True
            else:
                self.logger.info('VIP is not found')
            
            if self.utils.ping_cmd(self.gateway):
                self.logger.info(f'Ping gateway {self.gateway} is success')
                self.gateway_is_alive=True
            else:
                self.logger.info(f'Ping gateway {self.gateway} is failed')
    
            if self.utils.ping_cmd(self.peer):
                self.logger.info(f'Ping peer {self.peer} is success')
                self.peer_is_alive=True
            else:
                self.logger.info(f'Ping peer {self.peer} is failed')


    def IsGatewayAlive(self):
        return self.gateway_is_alive


    def IsPeerAlive(self):
        return self.peer_is_alive


    def IsVipMapped(self):
        return self.vip_is_mapped
