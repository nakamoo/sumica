# create ID
# discover hardware (e.g. discover cameras)
# send sensor data
# receive commands and act

import threading
import json
import os, importlib
import requests

SERVER_IP = ""

fs = ['sensors.{}'.format(f[:-3]) for f in os.listdir('sensors') if f.endswith('.py')]
sensor_mods = [m.Manager(SERVER_IP) for m in map(importlib.import_module, fs)]

import actions

# hard-code for now
ID = "noguchi"

for inp in sensor_mods:
    thread_stream = threading.Thread(target=inp.start())    
    thread_stream.daemon = True
    thread_stream.start()

while True:
    r = requests.post(SERVER_IP, data={'id': ID})
    action_data = json.loads(r.text)
    actions.act(action_data)