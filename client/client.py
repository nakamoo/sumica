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
import sys

SERVER_IP = "http://homeai.ml:5001"

ID = sys.argv[1]
print("id:", ID)

fs = ['managers.{}'.format(f[:-3]) for f in os.listdir('managers') if f.endswith('.py')]
sensor_mods = [m.Manager(ID, SERVER_IP) for m in map(importlib.import_module, fs)]

print(fs)
print('---')
print(sensor_mods)

for inp in sensor_mods:
    thread_stream = threading.Thread(target=inp.start) 
    thread_stream.daemon = True
    thread_stream.start()

while True:
    pass
#     try:
#         r = requests.post(SERVER_IP + "/controllers/execute", data={'user_name': ID})
#         action_data = json.loads(r.text)
#         print(action_data)
#         actions.act_list(action_data)
#         time.sleep(0.5)
#     except:
#         time.sleep(1)
#         print("connection error")
