from .controller import Controller
import numpy as np
import requests
import database as db
import json

class Detection(Controller):
    def __init__(self):
        pass

    def on_event(self, event, data):
        if event == "image":
            #print("image received")
            #print(data)


            from hai import app
            image_path = './images/' + data['filename']
            state_json = requests.post("http://" +
                                       app.config['RECOGNITION_SERVER_URL'] +
                                       "/detect",
                                       files={'image': open(image_path, "rb")})

            print("image analyzed.")
            #print("detections: {}".format(r.text))
            dets = json.loads(state_json.text)
            det_data = {"detections": dets}
            det_data.update(data)
            #print(det_data)
            db.mongo.detections.insert_one(det_data)

    def execute(self):
        response = []
        response.append({"app": "hue", "cmd": "turn on", "controller": "Detection"})
        return response
