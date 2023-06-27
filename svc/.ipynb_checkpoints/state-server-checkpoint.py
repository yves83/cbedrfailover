import http.server
import json
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
sys.path.append(os.path.join(parent_dir,"lib"))
from EdrConfig import *

port=10443

class MyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
        state_file = os.path.join(parent_dir, 'run/local_state.conf')
        
        try:
            with open(state_file, 'r') as f:
                json_data = json.load(f)
                e=json.dumps(json_data)
                self.wfile.write(e.encode())
        except Exception as e:
            print('Exception: ' + e)

        return

system_file=os.path.join(parent_dir,"conf","system.conf")
sysinfo = EdrConfig(system_file)       # Load the configuration file class
port=sysinfo.get('server_port')
httpd = http.server.HTTPServer(('0.0.0.0', port), MyHandler)
print('Server running on port %s...' % port)
httpd.serve_forever()