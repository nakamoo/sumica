import pickle
from controllers.controller import Controller
import controllers.learner.datasets as ds
from controllers.snapshot import show_image_chat
import json
import numpy as np
from server_actors import chatbot
import database as db
import time
from controllers.learner.img2vec import NNFeatures

import os

from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
import pickle
from datetime import datetime, date
import calendar
import scipy.misc
from PIL import Image

import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)

def get_dataset(username, start_time, end_time, nn):
    logger.debug("generating dataset")
    query = {"user_name": username, "time": {"$gt": start_time, "$lt": end_time}}
    print_data = list(db.mongo.print.find(query))
    logger.debug(print_data)
    ds.port = 27017 #!!!!
    query = {"user_name": username, "summary":{"$exists": True}, "time": {"$gt": start_time, "$lt": end_time}}
    cams = db.mongo.images.find(query).distinct("cam_id")
    
    image_data = ds.get_event_images(username, print_data, cams, start_offset=0, end_offset=60, stride=5, size=10,
                                 skip=True, with_summary=True)
    def img2vec(img_list, sum_list):
        pose = [ds.data2vec([], [], summ, False, False, False, True, False, False) for summ in sum_list]
        ft = nn.img2vec(img_list)
        return np.hstack([ft])
    
    x, y, classes = ds.generate_image_event_dataset(image_data, print_data, len(cams), img2vec, augs=10)
                
    return np.array(x), np.array(y), classes, cams

class ActivityTest4(Controller):
    def __init__(self, user):
        self.user = user
        self.classifier = None
        self.stream = False
        self.nn = NNFeatures()
        self.train = False
        
        n = db.mongo.fb_users.find_one({"id": user})
        if n:
            self.fb_id = n["fb_id"]
        
        self.learn_and_load()
        
        self.enabled = True
        
    def learn_and_load(self, force_update=False):
        start_time = 1509657892
        end_time = time.time()
        username = "sean"
            
        if force_update or not os.path.exists("classifier.pkl"):    
            x, y, classes, cams = get_dataset(username, start_time, end_time, self.nn)

            if len(x) <= 0:
                return

            x = np.array(x)
            y = np.array(y)

            from sklearn.ensemble import RandomForestClassifier
            from sklearn import linear_model
            clf = linear_model.LogisticRegression(C=1e5)#RandomForestClassifier(n_estimators=10, class_weight="balanced")

            pipe = Pipeline([
                ("scale", StandardScaler()),
                #("pca", PCA(n_components=10)),
                ("clf", clf)
            ])

            pipe.fit(x, y)
            logger.debug("trained model: {}".format(pipe.score(x, y)))
            pickle.dump({"classes": classes, "classifier": pipe}, open("classifier.pkl", "wb+"))

        query = {"user_name": username, "summary":{"$exists": True}, "time": {"$gt": start_time, "$lt": end_time}}
        self.cams = db.mongo.images.find(query).distinct("cam_id")
        
        logger.debug("reloading classifier")
        data = pickle.load(open("classifier.pkl", "rb"))
        self.classifier = data["classifier"]
        self.classes = data["classes"]
        #chatbot.send_fb_message(self.fb_id, "training complete.")
    
    def get_current_images(self):
        cat = []
        
        for cam in self.cams:
            n = db.mongo.images.find({"user_name": self.user, "cam_id": cam}).limit(1).sort([("time", -1)])[0]
            mat = scipy.misc.imread("./images/raw_images/" + n["filename"])
            if mat is None:
                logger.error("file not found: " + n["filename"])
            else:
                mat = scipy.misc.imresize(mat, (224, 224))
                mat = Image.fromarray(mat)
                feats = self.nn.img2vec([mat])[0]
                cat.extend(feats)
        
        return np.array(cat)

    def on_event(self, event, data):
        if event == "timer":
            if self.classifier is not None:
                feats = self.get_current_images()
                #datasets.data2vec([], [], data, False, False, False, False, False, True)

                pred = self.classifier.predict([feats])[0]
                probs = self.classifier.predict_proba([feats])[0]
                state = self.classes[pred]

                if self.stream:
                    chatbot.send_fb_message(self.fb_id, state + " " + str(probs[pred]))
                    #show_image_chat(data, self.fb_id, send_img=True, message=state + " " + str(probs[pred]))
                    #chatbot.send_fb_message(self.fb_id, "===END===")

                probs = self.classifier.predict_proba([feats])

                logger.debug(self.classes)
                logger.debug(probs)
                #logger.debug("current: {}, pred: {}".format(self.last_pred, pred))
                logger.debug(state)
                #logger.debug("time since last change: " + str(time.time() - self.last_change))

                min_state_time = 60
            
            if self.train:
                self.train = False
                self.learn_and_load(force_update=True)
                chatbot.send_fb_message(self.fb_id, "retrained")
                
        elif event == "chat" and self.fb_id:
            msg = data["message"]["text"]
            if msg == "train":
                #self.learn_and_load()
                self.train = True
            elif msg == "stream":
                self.stream = not self.stream
            
            
    def execute(self):
        re = []

        return re