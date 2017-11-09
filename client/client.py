# create ID
# discover hardware (e.g. discover cameras)
# send sensor data
# receive commands and act

import threading
import json
import os, importlib
import requests
import time
import sys
import traceback

from utils.actions import Actions
requests.packages.urllib3.disable_warnings()

SERVER_IP = "https://homeai.ml:{}".format(sys.argv[2])

ID = sys.argv[1]
print("id:", ID)

actions = Actions()

fs = ['managers.{}'.format(f[:-3]) for f in os.listdir('managers') if f.endswith('.py')]
sensor_mods = []
mods = []
for f in fs:
    try:
        mods.append(importlib.import_module(f))
    except:
        print("couldn't import {}".format(f))

for m in mods:
    try:
        sensor_mods.append(m.Manager(ID, SERVER_IP, actions))
    except:
        traceback.print_exc()

# start all sensor modules
for inp in sensor_mods:
    thread_stream = threading.Thread(target=inp.start) 
    thread_stream.daemon = True
    thread_stream.start()

# TODO: clean
def act_list2(acts):
    for inp in sensor_mods:
        try:
            inp.execute(acts)
        except:
            traceback.print_exc()

while True:
    try:
        time.sleep(1)

        try:
            # fetch actions
            r = requests.post(SERVER_IP + "/controllers/execute", data={'user_name': ID}, verify=False)
            action_data = json.loads(r.text)
            print(action_data)
            act_list2(action_data)
            actions.act_list(action_data)
            time.sleep(0.5)
        except Exception as e:
            time.sleep(1)
            traceback.print_exc()

    except KeyboardInterrupt:
        for inp in sensor_mods:
            try:
                inp.close()
            except Exception as e:
                traceback.print_exc()
                exit()

