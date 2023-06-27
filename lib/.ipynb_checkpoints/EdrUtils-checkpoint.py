import logging, logging.config
import json
import os
import subprocess

class EdrUtils:
    def create_logger(self, log_file_name):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))

        logging.config.fileConfig(os.path.join(parent_dir, 'conf', 'logging.ini'))

        log_file_path = os.path.join(parent_dir, 'logs', log_file_name)
         
        # Create a logger object
        logger = logging.getLogger(__name__)

        # Create a file handler
        file_handler = logging.FileHandler(log_file_path)
        formatter = logging.Formatter('%(asctime)s - %(pathname)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger


    # Read json file to dictionary
    def read_json_file(self, fullpath):
        with open(fullpath) as f:
            data = json.load(f)
        return data


    # Write json file to dictionary
    def write_json_file(self, dict,fullpath):
        with open(fullpath, 'w') as f:
            json.dump(dict, f, indent=4)


    # Run Linux Command
    def exec_cmd(self, cmd):
        return subprocess.run(cmd, stdout=subprocess.PIPE)


    def ping_cmd(self, target):
        try:
            with open('/dev/null', 'w') as devnull:
                response = subprocess.run(['ping', '-c', '4', target], stdout=devnull, stderr=devnull)

            if response.returncode == 0:
                return True
        except Exception:
            return False

        return False
