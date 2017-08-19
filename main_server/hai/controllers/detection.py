from .controller import Controller
import numpy as np
import requests

class Detection(Controller):
    def __init__(self):
        pass

    def on_event(self, event, data):
        if event == "image":
            print("image received")
            #print(data)


            from hai import app
            image_path = './images/' + data['filename']
            state_json = requests.post("http://" +
                                       app.config['RECOGNITION_SERVER_URL'] +
                                       "/detect",
                                       files={'image': open(image_path, "rb")})

            print("image analyzed.")
            #print("detections: {}".format(r.text))

    def execute(self):
        response = []
        response.append({"app": "hue", "cmd": "turn on", "controller": "Detection"})
        return response
