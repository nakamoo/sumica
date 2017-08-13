import requests
import json
import pymongo

from controllers.controller import Controller
from server_actors import actor


def has_object(obj_class, state):
    for obj in state["objects"]:
        if obj["label"] == obj_class:
            return True

    return False


class HelloController(Controller):
    def __init__(self, user_name):
        self.on = False
        self.user_name = user_name

    def execute(self, image_path=None):
        if image_path is None:
            from database import mongo
            data = mongo.db.images.find_one({"user_name": self.user_name},
                                     sort=[("_id", pymongo.DESCENDING)])
            image_path = './images/' + data['filename']

        from hai import app
        state_json = requests.post("http://" +
                                   app.config['RECOGNITION_SERVER_URL'] +
                                   "/detect",
                                   files={'image': open(image_path, "rb")})
        state = json.loads(state_json.text)

        response = []
        if has_object("person", state):
            if not self.on:
                response.append({"app":"print", "cmd":"hi", "controller": "HelloController"})
                #re.append({"app":"sound", "cmd":"button83.mp3"})
                #re.append({"app":"hue", "cmd":'{"bri":255}'})
                actor.sample("there is person")
                self.on = True
        else:
            if self.on:
                response.append({"app":"print", "cmd":"bye", "controller": "HelloController"})
                #re.append({"app":"hue", "cmd":'{"bri":64}'})
                actor.sample("there is not person")
                self.on = False

        return response

