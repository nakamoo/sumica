from pymongo import MongoClient
client = MongoClient()
mongo = client.hai

import os
import importlib

from controllers.detection import Detection
from controllers.chatbot import Chatbot
from controllers.hello import HelloController
from controllers.settings import Settings
from controllers.pose import Pose
from controllers.snapshot import Snapshot
from controllers.summarizer import Summarizer
from controllers.activity_test import ActivityTest
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
    return [Pose(), Detection(), Chatbot(user_name), Summarizer(user_name), Snapshot(user_name), ActivityTest(user_name), Settings(user_name)]

#!!!!!!!

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
                print("error;", e, str(c))
            last_t = time.time()
            #if event == "image":
            #    print(str(c), "time taken:", last_t-mid_t)
        #if event == "image":
        #    print("total time taken:", last_t - start_t)

def timer_loop():
    while True:
        for user in controllers_objects.keys():
            trigger_controllers(user, "timer", None)
        #time.sleep(0.1)

#!!!!!!!
start_new_thread(timer_loop, ())
