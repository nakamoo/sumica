import pickle
from _app import app
from .controller import Controller
from controllers.learner import datasets
import json
import numpy as np
from server_actors import chatbot
import database as db
import time

from sklearn.preprocessing import StandardScaler
import pickle
from datetime import datetime, date
import calendar

import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level=app.config['LOG_LEVEL'], logger=logger)

class ActivityTest3(Controller):
    def __init__(self, user):
        self.user = user
        
        self.learn_and_load()
        
        self.action = None
        self.enabled = True
        self.output = {}
        self.last_change = 0
        self.last_pred = -1
        self.last2_pred = -1
        
    def learn_and_load(self):
        start_time = calendar.timegm(date(2017, 10, 9).timetuple())
        end_time = calendar.timegm(date(2017, 10, 11).timetuple())
        username = "sean"
        x, y, classes, counts = datasets.get_hue_dataset2(username, start_time, end_time, incl_pose=True, incl_feats=False)

        x = np.array(x)
        y = np.array(y)
        
        scaler = StandardScaler()
        x = scaler.fit_transform(x)
        
        from sklearn.ensemble import RandomForestClassifier
        clf = RandomForestClassifier(n_estimators=10, class_weight="balanced")
        clf.fit(x, y)
        logger.debug("trained model: {}".format(clf.score(x, y)))
        pickle.dump({"classes": classes, "classifier": clf, "preprocessor": scaler}, open("classifier.pkl", "wb+"))

        data = pickle.load(open("classifier.pkl", "rb"))
        self.classifier = data["classifier"]
        self.classes = data["classes"]
        self.preprocessor = data["preprocessor"]
        #self.last_pred = -1
        #self.last2_pred = -1
        self.last_learn = time.time()
        self.goback = -1
        
    def to_dict(self, state):
        def format(hue_state):
                if hue_state["on"]:
                    return hue_state
                else:
                    return {"on": False}
                
        return {"platform": "hue", "data": json.dumps([
                    {"id": "1", "state":format({"on": bool(state[1] == 1.0), "hue": state[2], "sat": state[3], "bri": state[4]})},
                    {"id": "2", "state":format({"on": bool(state[6] == 1.0), "hue": state[7], "sat": state[8], "bri": state[9]})},
                    {"id": "3", "state":format({"on": bool(state[11] == 1.0), "hue": state[12], "sat": state[13], "bri": state[14]})}
                ])}
    
    def go_back_and_learn(self):
        if self.last2_pred >= 0:
            logger.debug("GOING back to {}".format(self.last2_pred))
            self.output = self.to_dict(self.classes[self.last2_pred])
            self.last_change = time.time()
            self.goback = time.time()

    def on_event(self, event, data):
        if event == "summary":
            feats = datasets.data2vec([], [], data, False, False, False, True, False, False)
            #feats = np.load("./image_features/" + fn)
            pred = self.classifier.predict([feats])[0]
            state = self.classes[pred]
            
            probs = self.classifier.predict_proba([feats])
            #pred = np.argsort(probs)[0, -1]
            #state = self.classes[pred]
            logger.debug(self.classes)
            logger.debug(probs)
            logger.debug("current: {}, pred: {}".format(self.last_pred, pred))
            logger.debug(state)
            logger.debug("time since last change: " + str(time.time() - self.last_change))
                
            min_state_time = 60
                
            if self.last_pred != pred and time.time() - self.last_change > min_state_time: # dont flicker
                self.last2_pred = self.last_pred
                self.last_pred = pred
                
                self.last_change = time.time()
                
                self.output = self.to_dict(state)
                
            if time.time() - self.last_learn > 60:
                self.learn_and_load()

        elif event == "chat":
            msg = data["message"]["text"]
            if msg == "act on":
                self.enabled = True
            elif msg == "act off":
                self.enabled = False
            elif msg == "no":
                self.go_back_and_learn()
        elif event == "hue":
            if int(data["last_manual"]) == 0:
                n = db.mongo.fb_users.find_one({"id": self.user})
                if n:
                    fb_id = n["fb_id"]
                chatbot.send_fb_message(fb_id, "manual control detected.")
            
    def execute(self):
        re = []
        
        if self.enabled:
            logger.debug("sending {}".format(self.output))
            re.extend([self.output, {"platform": "send_hue", "data": "False"}])
        else:
            re.append({"platform": "send_hue", "data": "True"})
                             
        #if self.goback >= 0:
        re.append({"platform": "hue_back", "data":self.goback})
        self.goback = -1
        
        return re