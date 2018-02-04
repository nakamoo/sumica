import subprocess
import time
import json
import datetime
import requests
import traceback
import logging
import traceback
import sys
from utils.speechrecognition import confirm

class Manager:
    def __init__(self, user, server_ip):
        logging.debug("connecting to any Hue devices...")
        out = subprocess.check_output(['node', './utils/hue.js', 'connect'])
        out = out.decode('utf-8')
        self.server_ip = server_ip
        self.user = user
        self.send = True

        if out.split("\n")[-2] != "ok":
            self.connected = False
            logging.warn("failed to connect Hue; internet connection or press button?")
        else:
            self.connected = True
            logging.debug("connected to Hue.")

    def start(self):
        if not self.connected:
            print("HUE NOT CONNECTED")
            return

        while True:
            try:
                out = subprocess.check_output(['node', './utils/hue.js', 'get_state'])
                state = json.loads(out.decode('utf-8').split("\n")[-2])

                data = dict()
                data["lights"] = json.dumps(state["lights"])
                data["time"] = time.time()
                data["user_name"] = self.user

                if self.send:
                    requests.post(self.server_ip + "/data/hue", data=data, verify=False)
                    logging.debug("sent hue info to server")

            except requests.exceptions.ConnectionError:
                logging.error("could not connect to server")


if __name__ == "__main__":
    pass
