from .controller import Controller
import numpy as np
import requests
import database as db
import json
from utils import encryption
from controllers.utils import iou
import os
import cv2
import time
from _app import app

import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level=app.config['LOG_LEVEL'], logger=logger)

def nms(dets, threshold=0.5):
    #logger.error("BEFORE: " + str(len(dets)))
    
    sorted_list = sorted(dets, key=lambda k: k['confidence']) 
    filtered_list = []
    
    for det in dets:
        skip = False
        for b in filtered_list:
            if b["label"] == det["label"] and iou(b["box"], det["box"]) > threshold:
                skip = True
                break
        
        if not skip:
            filtered_list.append(det)
    
    #logger.error("AFTER: " + str(len(filtered_list)))
    return filtered_list

class Detection(Controller):
    def __init__(self, user):
        self.user = user

    def on_event(self, event, data):
        if event == "image":
            
            if app.config['ENCRYPTION']:
                image_path = app.config['ENCRYPTED_IMG_DIR'] + data['filename']
            else:
                image_path = app.config['RAW_IMG_DIR'] + data['filename']

            #state_json = requests.post("http://" +
            #                           hai.app.config['RECOGNITION_SERVER_URL'] +
            #                           "/detect",
            #                           files={'image': image}, json={'threshold': 0.5})
            
            logger.info("sending image ({}) for detection... ".format(image_path))
            logger.info(os.path.exists(image_path))
            logger.info("image shape: {}".format(str(cv2.imread(image_path).shape)))
            
            #db.mongo.images.update_one({"filename": data['filename']}, {'$set': {"history.detection_request": time.time()}}, upsert=False)
            new_data = {}
            new_data['history.detection_request'] = time.time()
            
            state_json = requests.post("http://" + app.config['RECOGNITION_SERVER_URL'] + "/detect_path", data={'path': os.path.abspath(image_path), 'threshold': 0.5, 'get_image_features': 'true', 'get_object_features': 'true'})

            #print("detections: {}".format(r.text))
            
            logger.info(state_json.text)
            dets = json.loads(state_json.text)
            dets["detections"] = nms(dets["detections"])
            new_data.update(dets)
            new_data["history.detection_recorded"] = time.time()

            #db.mongo.detections.insert_one(det_data)
            db.mongo.images.update_one({"_id": data["_id"]}, {'$set': new_data}, upsert=False)
            logger.info("DETECTION")
    
    def execute(self):
        response = []
        return response

