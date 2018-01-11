import requests
import json
import os
import time

from flask import current_app
import numpy as np
import cv2
import coloredlogs
import logging

from controllers.controller import Controller

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)


class FeatureExtractor(Controller):
    def __init__(self, username):
        super().__init__(username)

    def on_event(self, event, data):
        if event == "image":
            if app.config['ENCRYPTION']:
                image_path = app.config['ENCRYPTED_IMG_DIR'] + data['filename']
            else:
                image_path = app.config['RAW_IMG_DIR'] + data['filename']

            new_data = {}
            new_data['history.features_request'] = time.time()

            state_json = requests.post("http://" + app.config['FEATURES_SERVER_URL'] + "/extract_features", data={'path': os.path.abspath(image_path), 'detection_threshold': 0.5, 'nms_threshold': 0.5})

            features = json.loads(state_json.text)
            new_data.update(features)
            new_data["history.features_recorded"] = time.time()

            db.mongo.images.update_one({"_id": data["_id"]}, {'$set': new_data}, upsert=False)

    def execute(self):
        return []

