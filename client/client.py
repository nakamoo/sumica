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

import coloredlogs, logging
coloredlogs.install(level="DEBUG")

SERVER_IP = "https://homeai.ml:{}".format(sys.argv[2])

ID = sys.argv[1]
logging.info("id: {}".format(ID))

actions = Actions(ID, SERVER_IP)

fs = ['managers.{}'.format(f[:-3]) for f in os.listdir('managers') if f.endswith('.py')]
sensor_mods = []
mods = []
for f in fs:
    try:
        mods.append(importlib.import_module(f))
    except:
        logging.warn("couldn't import {}".format(f))

for m in mods:
    try:
        sensor_mods.append(m.Manager(ID, SERVER_IP, actions))
    except:
        logging.warn("couldn't initialize {}".format(m))

# start all sensor modules
for inp in sensor_mods:
    thread_stream = threading.Thread(target=inp.start) 
    thread_stream.daemon = False
    thread_stream.start()

# TODO: clean
def act_list2(acts):
    for inp in sensor_mods:
        try:
            inp.execute(acts)
        except:
            #traceback.print_exc()
            pass

while True:
    try:
        time.sleep(1)
        logging.debug("getting commands")

        try:
            # fetch actions
            r = requests.post(SERVER_IP + "/controllers/execute", data={'user_name': ID}, verify=False)
        except Exception as e:
            logging.warn(e)

        try:
            action_data = json.loads(r.text)
        except Exception as e:
            logging.warn(e)
            logging.warn(r.text)

        logging.debug("action data: {}".format(action_data))
        act_list2(action_data)
        actions.act_list(action_data)
           
    except KeyboardInterrupt:
        for inp in sensor_mods:
            try:
                inp.close()
            except Exception as e:
                logging.debug("shutting down")
                exit()

