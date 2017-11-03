from .controller import Controller
import database as db
import cv2
import colorsys
from server_actors import chatbot
from threading import Timer
import os
import time
import controllers.utils as utils

import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)

class ImageProcessor(Controller):
    def __init__(self, user):
        self.user = user

    def on_event(self, event, data):
        if event == "timer":
            results = db.mongo.images.find({"user_name": self.user, "processed": False}).limit(5).sort([("time",-1)])
            
            if results.count() <= 0:
                return
            
            for data in results:
                db.mongo.images.update_one({"filename": data['filename']}, {'$set': {"processed": True, "history.image_processing_start": time.time()}}, upsert=False)
                
                if data["motion_update"]:
                    db.trigger_controllers(data['user_name'], "image", data, parallel=True)
                    
                db.mongo.images.update_one({"filename": data['filename']}, {'$set': {"history.image_processing_finish": time.time()}}, upsert=False)

    def execute(self):
        return []
