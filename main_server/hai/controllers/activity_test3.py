import pickle
from .controller import Controller
from controllers.learner import datasets
import json
import numpy as np
from server_actors import chatbot
import database as db

class ActivityTest3(Controller):
    def __init__(self, user):
        self.user = user
        data = pickle.load(open("classifier.pkl", "rb"))
        self.classifier = data["classifier"]
        self.classes = data["classes"]
        self.preprocessor = data["preprocessor"]
        self.action = None
        self.enabled = True
        self.output = {}

    def on_event(self, event, data):
        if event == "summary":
            feats = datasets.data2vec([], [], data, False, False, False, False, False, True)
            #feats = np.load("./image_features/" + fn)
            pred = self.classifier.predict([feats])
            state = self.classes[pred[0]]
            
            probs = self.classifier.predict_proba([feats])
            pred = np.argsort(probs)[0, -2]
            state = self.classes[pred]
            print(probs)
            print(pred)
            print(state)
            
            def format(hue_state):
                if hue_state["on"]:
                    return hue_state
                else:
                    return {"on": False}
            
            self.output = {"platform": "hue", "data": json.dumps([
                {"id": "1", "state":format({"on": bool(state[1] == 1.0), "hue": state[2], "sat": state[3], "bri": state[4]})},
                {"id": "2", "state":format({"on": bool(state[6] == 1.0), "hue": state[7], "sat": state[8], "bri": state[9]})},
                {"id": "3", "state":format({"on": bool(state[11] == 1.0), "hue": state[12], "sat": state[13], "bri": state[14]})}
            ])}
            print(self.output)
        elif event == "chat":
            msg = data["message"]["text"]
            if msg == "act on":
                self.enabled = True
            elif msg == "act off":
                self.enabled = False
        elif event == "hue":
            if float(data["last_manual"]) == 0:
                n = db.mongo.fb_users.find_one({"id": self.user})
                if n:
                    fb_id = n["fb_id"]
                chatbot.send_fb_message(fb_id, "hue manual control detected.")
            
    def execute(self):
        if self.enabled:
            return [self.output, {"platform": "send_hue", "data": "False"}]
        else:
            return [{"platform": "send_hue", "data": "True"}]