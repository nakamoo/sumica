from pymongo import MongoClient
client = MongoClient()
mongo = client.hai

import os
import importlib

from controllers.detection import Detection
from controllers.chatbot import Chatbot
from controllers.hello import HelloController
from controllers.settings import Settings

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

# controller modules for global events
control_mods = load_controller_modules()

def standard_controllers(user_name):
    return [Detection(), Chatbot(user_name), HelloController(user_name), Settings(user_name)]

# TODO: use DB
controllers_objects = {}
controllers_objects['koki'] = standard_controllers('koki')
controllers_objects['sean'] = standard_controllers('sean')

def trigger_controllers(user, event, data):
    if user is None:
        for c in control_mods:
            c.on_global_event(event, data)
    else:
        for c in controllers_objects[user]:
            c.on_event(event, data)
