# create ID
# discover hardware (e.g. discover cameras)
# send sensor data
# receive commands and act

import threading
import json
import os, importlib
import requests
import time
from utils import actions

SERVER_IP = "http://153.120.159.210:5002"

fs = ['managers.{}'.format(f[:-3]) for f in os.listdir('managers') if f.endswith('.py')]
sensor_mods = [m.Manager(SERVER_IP) for m in map(importlib.import_module, fs)]

# hard-code for now
ID = "noguchi"

for inp in sensor_mods:
    thread_stream = threading.Thread(target=inp.start) 
    thread_stream.daemon = True
    thread_stream.start()

time.sleep(1000)
#while True:
#    r = requests.post(SERVER_IP, data={'id': ID})
#    action_data = json.loads(r.text)
#    actions.act_list(action_data)
