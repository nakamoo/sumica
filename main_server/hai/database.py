from pymongo import MongoClient
from _app import app
client = MongoClient('localhost', app.config['PORT_DB'])
mongo = client.hai
mongo.images.ensure_index('time')
mongo.hue.ensure_index('time')

import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)

import os
import traceback
import importlib

from controllers.detection import Detection
from controllers.chatbot import Chatbot
from controllers.hello import HelloController
from controllers.settings import Settings
from controllers.pose import Pose
from controllers.snapshot import Snapshot
from controllers.summarizer import Summarizer
from controllers.activity_test import ActivityTest
from controllers.activity_test3 import ActivityTest3
from controllers.tests.activity_test4 import ActivityTest4
from controllers.youtubeplayer import YoutubePlayer
from controllers.irkit import IRKit
from controllers.printtest import PrintTest
#from controllers.learner import Learner

import time
from _thread import start_new_thread

def load_controller_modules():
    fs = ['controllers.{}'.format(f[:-3]) for f in os.listdir('controllers') if f.endswith('.py')]
    mods = []
    for f in fs:
        try:
            m = importlib.import_module(f)
            if "on_global_event" in dir(m):
                mods.append(m)
        except Exception as e:
            print("failed to load", f, e)

    return mods

def standard_controllers(user_name):
    return [YoutubePlayer(user_name), IRKit(user_name), PrintTest(user_name), Pose(), Detection(), Chatbot(user_name),
            Summarizer(user_name), ActivityTest4(user_name), Snapshot(user_name), Settings(user_name)]

# controller modules for global events
control_mods = load_controller_modules()
# TODO: use DB
controllers_objects = {}
controllers_objects['koki'] = standard_controllers('koki')
controllers_objects['sean'] = standard_controllers('sean')

def trigger_controllers(user, event, data):
    if user is None:
        for c in control_mods:
            c.on_global_event(event, data)
    else:
        start_t = time.time()
        for c in controllers_objects[user]:
            mid_t = time.time()
            try:
                c.on_event(event, data)
            except Exception as e:
                traceback.print_exc()
            last_t = time.time()
            if event == "image" or event == "timer":
                time_taken = last_t-mid_t
                #if time_taken >= 0.1:
                    #print(str(c), "time taken:", time_taken)
        if event == "image":
            logger.info("total time taken (trigger_controllers): " + str(last_t - start_t))

def timer_loop():
    while True:
        for user in controllers_objects.keys():
            trigger_controllers(user, "timer", None)
        time.sleep(0.1)

#if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
start_new_thread(timer_loop, ())
