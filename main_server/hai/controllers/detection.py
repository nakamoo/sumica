from .controller import Controller
import numpy as np
import requests
import database as db
import json
from utils import encryption

class Detection(Controller):
    def __init__(self):
        pass

    def on_event(self, event, data):
        if event == "image":
            #print("image received")
            #print(data)

            import hai
            if hai.app.config['ENCRYPTION']:
                image_path = hai.app.config['ENCRYPTED_IMG_DIR'] + data['filename']
                image = encryption.open_encrypted_img(image_path)
            else:
                image_path = hai.app.config['RAW_IMG_DIR'] + data['filename']
                image = open(image_path, 'rb')

            state_json = requests.post("http://" +
                                       hai.app.config['RECOGNITION_SERVER_URL'] +
                                       "/detect",
                                       files={'image': image}, json={'threshold': 0.5})

            #print("detections: {}".format(r.text))
            dets = json.loads(state_json.text)
            det_data = {"detections": dets}
            det_data.update(data)
            #print(det_data)

            db.mongo.detections.insert_one(det_data)
            db.mongo.images.update_one({"_id": data["_id"]}, {'$set': {'detections': dets}}, upsert=False)

            print("image analyzed.")
            print("detections: {}".format(state_json.text))

    def execute(self):
        response = []
        response.append({"app": "hue", "cmd": "turn on", "controller": "Detection"})
        return response

