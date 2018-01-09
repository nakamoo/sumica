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
# from _app import app

from controllers.dbreader.utils import get_db
db = get_db()

import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level=app.config['LOG_LEVEL'], logger=logger)


def nms(dets, iou_threshold=0.5):
    sorted_list = sorted(dets, key=lambda k: k['confidence'])
    filtered_list = []

    for det in dets:
        skip = False
        for b in filtered_list:
            if b["label"] == det["label"] and iou(b["box"], det["box"]) > iou_threshold:
                skip = True
                break

        if not skip:
            filtered_list.append(det)

    return filtered_list

class FeatureExtractor(Controller):
    def __init__(self, user):
        self.user = user

    def on_event(self, event, data):
        if event == "image":
            if app.config['ENCRYPTION']:
                image_path = app.config['ENCRYPTED_IMG_DIR'] + data['filename']
            else:
                image_path = app.config['RAW_IMG_DIR'] + data['filename']

            new_data = {}
            new_data['history.features_request'] = time.time()

            state_json = requests.post("http://" + app.config['FEATURES_SERVER_URL'] + "/extract_features", data={'path': os.path.abspath(image_path), 'detection_threshold': 0.5, 'nms_iou_threshold': 0.5})

            features = json.loads(state_json.text)
            new_data.update(features)
            new_data["history.features_recorded"] = time.time()

            db.mongo.images.update_one({"_id": data["_id"]}, {'$set': new_data}, upsert=False)

    def execute(self):
        return []

