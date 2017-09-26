from .controller import Controller
import numpy as np
import requests
import database as db
import json
from utils import encryption
import os

class Detection(Controller):
    def __init__(self):
        pass

    def on_event(self, event, data):
        if event == "image":
            #print("image received")
            #print(data)

            from _app import app
            if app.config['ENCRYPTION']:
                image_path = app.config['ENCRYPTED_IMG_DIR'] + data['filename']
                image = encryption.open_encrypted_img(image_path)
            else:
                image_path = app.config['RAW_IMG_DIR'] + data['filename']
                image = open(image_path, 'rb')

            #state_json = requests.post("http://" +
            #                           hai.app.config['RECOGNITION_SERVER_URL'] +
            #                           "/detect",
            #                           files={'image': image}, json={'threshold': 0.5})
            
            print("sending image for detection...")
            state_json = requests.post("http://" + app.config['RECOGNITION_SERVER_URL'] + "/detect_path", data={'path': os.path.abspath(image_path), 'threshold': 0.5, 'get_image_features': 'true', 'get_object_features': 'true'})

            #print("detections: {}".format(r.text))
            
            print(state_json.text)
            dets = json.loads(state_json.text)

            #db.mongo.detections.insert_one(det_data)
            db.mongo.images.update_one({"_id": data["_id"]}, {'$set': dets}, upsert=False)

            print("image analyzed.")
    
    def execute(self):
        response = []
        response.append({"app": "hue", "cmd": "turn on", "controller": "Detection"})
        return response

