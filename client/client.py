# creat ID
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

requests.packages.urllib3.disable_warnings()

import coloredlogs, logging
coloredlogs.install(level="DEBUG")

SERVER_IP = "https://homeai.ml:{}".format(sys.argv[2])
ID = sys.argv[1]
logging.info("id: {}".format(ID))

from managers.cvcamera import Manager as CameraManager
from managers.speech import Manager as SpeechManager
from managers.hue import Manager as HueManager

from actors.youtubeactor import YoutubeActor
from actors.hueactor import HueActor
from actors.generalactor import GeneralActor

camera_manager = CameraManager(ID, SERVER_IP)
speech_manager = SpeechManager(ID, SERVER_IP)
hue_manager = HueManager(ID, SERVER_IP)
# sensor_mods = [camera_manager, youtube_manager, speech_manager, hue_manager]
sensor_mods = []

youtube_actor = YoutubeActor(ID, SERVER_IP)
hue_actor = HueActor(ID, SERVER_IP)
general_actor = GeneralActor(ID, SERVER_IP)
actor_mods = [youtube_actor, hue_actor, general_actor]

# start all sensor modules
for inp in sensor_mods:
    thread_stream = threading.Thread(target=inp.start) 
    thread_stream.daemon = False
    thread_stream.start()

# TODO: clean
def act_list2(acts):
    for inp in actor_mods:
        try:
            inp.execute(acts)
        except:
            traceback.print_exc()
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

    except KeyboardInterrupt:
        for inp in sensor_mods:
            try:
                inp.close()
            except Exception as e:
                logging.debug("shutting down")
                exit()

