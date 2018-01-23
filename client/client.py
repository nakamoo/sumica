import threading
import json
import os, importlib
import requests
import time
import sys
import traceback
requests.packages.urllib3.disable_warnings()
import coloredlogs, logging
coloredlogs.install(level="DEBUG")
from modulemanager import ModuleManager

SERVER_IP = "https://homeai.ml:{}".format(sys.argv[2])
ID = sys.argv[1]
logging.info("id: {}".format(ID))

modules = ModuleManager(ID, SERVER_IP)
modules.start_sensor_mods()

while True:
    try:
        time.sleep(1)

        try:
            # fetch actions
            r = requests.post(SERVER_IP + "/controllers/execute", data={'user_name': ID}, verify=False)
            logging.debug("fetched execution commands (actions) from server")
            action_data = json.loads(r.text)
            logging.debug("action data: {}".format(action_data))
            modules.execute_actor_mods(action_data)
        except requests.exceptions.ConnectionError as e:
            logging.error('could not connect to server')
        except Exception as e:
            traceback.print_exc()

    except KeyboardInterrupt:
        for inp in modules.sensor_mods:
            try:
                inp.close()
            except Exception as e:
                logging.debug("shutting down")
                exit()

