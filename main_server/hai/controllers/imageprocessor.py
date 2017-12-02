from .controller import Controller
import database as db
import cv2
import colorsys
from server_actors import chatbot
import threading
from threading import Timer
import os
import time
import controllers.utils as utils
from _thread import start_new_thread

import coloredlogs, logging

from _app import app
logger = logging.getLogger(__name__)
coloredlogs.install(level=app.config['LOG_LEVEL'], logger=logger)

class ImageProcessor(Controller):
    def __init__(self, user):
        self.user = user

    def on_event(self, event, data):
        if event == "timer":
            results = db.mongo.images.find({"user_name": self.user, "processing_start": False}).limit(5).sort([("time",-1)])
            
            if results.count() <= 0:
                return
            
            for data in results:
                def process(img_data):
                    db.mongo.images.update_one({"filename": img_data['filename']}, {'$set': {"processing_start": True, "history.image_processing_start": time.time()}}, upsert=False)

                    if data["motion_update"]:
                        db.trigger_controllers(data['user_name'], "image", img_data, parallel=True)
                        #data["history.image_processing_finish"] = time.time()
                        db.mongo.images.update_one({"filename": img_data['filename']}, {'$set': {"history.image_processing_finish": time.time()}}, upsert=False)
                    #db.mongo.images.update_one({"filename": data['filename']}, {'$set': data}, upsert=False)
                    logger.debug("processed image.")
                    
                #process(data)
                start_new_thread(process, (data,))

    def execute(self):
        return []
