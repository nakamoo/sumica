import pickle
from controllers.controller import Controller
from controllers.learner import datasets
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
    query = {"user_name": username}
    hue_data = list(db.mongo.print.find(query))
    print(len(hue_data))
    
    import scipy.misc

    image_data = []
    for data in hue_data:
        data2 = []
        start_time = int(data["time"])
        end_time = int(data["time"]+30)
        interval = 5

        for s in range(start_time, end_time, interval):
            interval_data = []
            skip = False

            for cam in ["misc0"]:
                query = {"user_name": username, "summary":{"$exists": True}, "cam_id": cam, "time": {"$gte": s, "$lt": s+interval}}
                n = db.mongo.images.find(query)

                if n.count() > 0:
                    interval_data.append(n[0])
                else:
                    interval_data.append(None)
                    #skip = True

            if not skip:
                data2.append(interval_data)
        image_data.append(data2)
        
    print(image_data)
        
    dataX, labels = [], []

    for x, y in zip(image_data, hue_data):
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
        
        self.learn_and_load()
        
        self.action = None
        self.enabled = True
        self.output = {}
        self.last_change = 0
        self.last_pred = -1
        self.last2_pred = -1
        
        n = db.mongo.fb_users.find_one({"id": user})
        if n:
            self.fb_id = n["fb_id"]
        
    def learn_and_load(self):
        start_time = time.time()-3600*24
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
        #self.last_pred = -1
        #self.last2_pred = -1
        self.last_learn = time.time()
        self.goback = -1
    
    def on_event(self, event, data):
        if event == "summary" and self.classifier is not None:
            feats = datasets.data2vec([], [], data, False, False, False, False, False, True)
            #feats = np.load("./image_features/" + fn)
            pred = self.classifier.predict([feats])[0]
            state = self.classes[pred]
            chatbot.send_fb_message(self.fb_id, state)
            
            probs = self.classifier.predict_proba([feats])
            #pred = np.argsort(probs)[0, -1]
            #state = self.classes[pred]
            logger.debug(self.classes)
            logger.debug(probs)
            logger.debug("current: {}, pred: {}".format(self.last_pred, pred))
            logger.debug(state)
            logger.debug("time since last change: " + str(time.time() - self.last_change))
                
            min_state_time = 60
                
            if self.last_pred != pred: # dont flicker
                self.last2_pred = self.last_pred
                self.last_pred = pred
                
                self.last_change = time.time()
                
                self.output = state
                
                
            logger.debug(state)
                
            if time.time() - self.last_learn > 60:
                self.learn_and_load()
            
    def execute(self):
        re = []

        return re