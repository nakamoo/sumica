from pymongo import MongoClient
from _app import app
client = MongoClient('localhost', app.config['PORT_DB'])
mongo = client.hai
mongo.images.ensure_index('time')
mongo.hue.ensure_index('time')

import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level=app.config['LOG_LEVEL'], logger=logger)

import os
import traceback
import importlib
import threading

from controllers.detection import Detection
from controllers.chatbot import Chatbot
from controllers.hello import HelloController
from controllers.settings import Settings
from controllers.pose2 import Pose2
from controllers.snapshot import Snapshot
from controllers.summarizer import Summarizer
from controllers.tests.activity_test5 import ActivityTest5
from controllers.actionrec import ActionRecognition
from controllers.youtubeplayer import YoutubePlayer
from controllers.irkit import IRKit
from controllers.printtest import PrintTest
from controllers.imageprocessor import ImageProcessor
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
    return [YoutubePlayer(user_name), IRKit(user_name), PrintTest(user_name), Pose2(user_name), Detection(user_name), ActionRecognition(), Chatbot(user_name), Snapshot(user_name), Settings(user_name)]

# controller modules for global events
control_mods = load_controller_modules()
# TODO: use DB
controllers_objects = {}
# controllers_objects['koki'] = standard_controllers('koki')
controllers_objects['sean'] = standard_controllers('sean')

def trigger_controllers(user, event, data, parallel=False):
    if user is None:
        for c in control_mods:
            c.on_global_event(event, data)
    else:
        start_t = time.time()
        threads = []
        for c in controllers_objects[user]:
            mid_t = time.time()
            try:
                if parallel:
                    t = threading.Thread(target=c.on_event, args=(event, data,))
                    threads.append([c, t])
                    t.start()
                else:
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
            
        if parallel:
            for c, t in threads:
                t.join()
                
        #logger.error("COMPLETE " + event)

def start_timer_loops():
    
    """
    def timer_loop(c):
        while True:
            c.on_event("timer", None)
            time.sleep(0.1)
    
    for user in controllers_objects.keys():
        for c in controllers_objects[user]:
            t = threading.Thread(target=timer_loop, args=(c,))
            t.start()
    
    """
    while True:
        #logger.debug("CYCLE")
        for user in controllers_objects.keys():
            for c in controllers_objects[user]:
                #print("start " + str(c))
                try:
                    c.on_event("timer", None)
                except:
                    logger.error("error in " + str(c))
                    traceback.print_exc()
                #print("end " + str(c))
        time.sleep(0.1)
    

#if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
start_new_thread(start_timer_loops, ())
#start_timer_loops()
