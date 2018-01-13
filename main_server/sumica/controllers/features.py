import requests
import json
import os
import time

from flask import current_app
import numpy as np
import cv2
import coloredlogs
import logging

from utils import db
from controllers.controller import Controller

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)


class FeatureExtractor(Controller):
    def __init__(self, username):
        super().__init__(username)

    def on_event(self, event, data):
        if event == "image":
            if current_app.config['ENCRYPTION']:
                image_path = current_app.config['ENCRYPTED_IMG_DIR'] + data['filename']
            else:
                image_path = current_app.config['RAW_IMG_DIR'] + data['filename']

            new_data = {}
            new_data['history.features_request'] = time.time()

            r = requests.post("http://" + current_app.config['FEATURES_SERVER_URL'] + "/extract_features", data={'path': os.path.abspath(image_path), 'detection_threshold': 0.5, 'nms_threshold': 0.5})

            if r.status_code != 200:
                logger.debug(r.status_code, r.text)
                return

            features = json.loads(r.text)
            new_data.update(features)
            new_data["history.features_recorded"] = time.time()

            db.images.update_one({"_id": data["_id"]}, {'$set': new_data}, upsert=False)

    def execute(self):
        return []

