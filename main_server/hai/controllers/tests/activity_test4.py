import pickle
from controllers.controller import Controller
from controllers.learner import datasets
from controllers.snapshot import show_image_chat
import json
import numpy as np
from server_actors import chatbot
import database as db
import time

from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
import pickle
from datetime import datetime, date
import calendar

import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)

def get_dataset(username, start_time, end_time):
    query = {"user_name": username, "time": {"$gt": time.time()-7200, "$lt": time.time()}}
    print_data = list(db.mongo.print.find(query))
    datasets.port = 27017 #!!!!
    image_data = datasets.get_event_images(username, print_data, ["misc0"])
        
    print(image_data)
        
    dataX, labels = [], []

    for x, y in zip(image_data, print_data):
        print(y["text"])

        for imgs in x:
            row = []
            skip = False
            for cam in imgs:
                if cam is not None:
                    row.append(datasets.data2vec([], [], cam, False, False, False, False, False, True))
                else:
                    skip = True
                    break
            if not skip:
                dataX.append(np.concatenate(row))
                labels.append(y["text"])
                
    classes = list(set(labels))
    dataY = [classes.index(label) for label in labels]
                
    return np.array(dataX), np.array(dataY), classes

class ActivityTest4(Controller):
    def __init__(self, user):
        self.user = user
        self.classifier = None
        self.stream = True
        
        self.learn_and_load()
        
        self.enabled = True
        
        n = db.mongo.fb_users.find_one({"id": user})
        if n:
            self.fb_id = n["fb_id"]
        
    def learn_and_load(self):
        start_time = time.time()-3600
        end_time = time.time()
        username = "sean"
        x, y, classes = get_dataset(username, start_time, end_time)
        
        if len(x) <= 0:
            return

        x = np.array(x)
        y = np.array(y)
        
        from sklearn.ensemble import RandomForestClassifier
        from sklearn import linear_model
        clf = linear_model.LogisticRegression(C=1e5)#RandomForestClassifier(n_estimators=10, class_weight="balanced")
        
        pipe = Pipeline([
            ("scale", StandardScaler()),
            ("pca", PCA(n_components=10)),
            ("clf", clf)
        ])
   
        pipe.fit(x, y)
        logger.debug("trained model: {}".format(pipe.score(x, y)))
        pickle.dump({"classes": classes, "classifier": pipe}, open("classifier.pkl", "wb+"))

        data = pickle.load(open("classifier.pkl", "rb"))
        self.classifier = data["classifier"]
        self.classes = data["classes"]
    
    def on_event(self, event, data):
        if event == "summary" and self.classifier is not None:
            feats = datasets.data2vec([], [], data, False, False, False, False, False, True)

            pred = self.classifier.predict([feats])[0]
            probs = self.classifier.predict_proba([feats])[0]
            state = self.classes[pred]
            
            if self.stream:
                chatbot.send_fb_message(self.fb_id, state)
                show_image_chat(data, self.fb_id, send_img=True, message=state + " " + str(probs[pred]))
                chatbot.send_fb_message(self.fb_id, "===END===")
            
            probs = self.classifier.predict_proba([feats])

            logger.debug(self.classes)
            logger.debug(probs)
            #logger.debug("current: {}, pred: {}".format(self.last_pred, pred))
            logger.debug(state)
            #logger.debug("time since last change: " + str(time.time() - self.last_change))
                
            min_state_time = 60
                
        elif event == "chat" and self.fb_id:
            msg = data["message"]["text"]
            if msg == "train":
                self.learn_and_load()
                chatbot.send_fb_message(self.fb_id, "retrained")
            elif msg == "stream":
                self.stream = not self.stream
            
    def execute(self):
        re = []

        return re