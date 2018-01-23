import pickle
from controllers.controller import Controller
import controllers.learner.datasets as ds
from controllers.snapshot import show_image_chat, show_image_chat_raw
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
    query = {"user_name": username, "pose":{"$exists": True}, "detections":{"$exists": True}, "time": {"$gt": start_time, "$lt": time.time()}}
    cams = db.mongo.images.find(query).distinct("cam_id")

    image_data = ds.get_event_images2(username, print_data, cams, start_offset=0, end_offset=30, stride=3, size=5, skip_incomplete=True)
    
    def img2vec(img_list, sample_list, box_list):
        ft = nn.img2vec(img_list)
        misc = np.vstack(box_list)
        data_mat = np.hstack([ft])
        logger.debug(data_mat)
        return data_mat
    
    x, y, classes, _, _ = ds.generate_image_event_dataset(image_data, print_data, len(cams), img2vec, augs=10)
                
    return np.array(x), np.array(y), classes, cams

class ActivityTest5(Controller):
    def __init__(self, user):
        self.user = user
        self.classifier = None
        self.stream = True
        self.nn = NNFeatures(1)
        self.train = False
        self.counter = 0
        
        self.tv_on = False
        self.music_on = False
        
        self.output = []
        
        n = db.mongo.fb_users.find_one({"id": user})
        if n:
            self.fb_id = n["fb_id"]
        
        self.learn_and_load(force_update=True)
        
        self.enabled = True
        self.last_state = "init"
        self.last_images = []
        
        self.history = []
        self.last_avg = 3
        self.prob_threshold = 0.8
        
    def learn_and_load(self, force_update=False):
        start_time = 1510935186
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
            clf = linear_model.LogisticRegression(C=1e5)
            pipe = Pipeline([
                ("scale", StandardScaler()),
                ("pca", PCA(n_components=50)),
                ("clf", clf)
            ])

            pipe.fit(x, y)
            logger.debug("trained model: {}".format(pipe.score(x, y)))
            pickle.dump({"classes": classes, "classifier": pipe}, open("classifier.pkl", "wb+"))

        query = {"user_name": username, "pose":{"$exists": True}, "detections":{"$exists": True}, "time": {"$gt": start_time, "$lt": end_time}}
        self.cams = db.mongo.images.find(query).distinct("cam_id")
        
        logger.debug("reloading classifier")
        data = pickle.load(open("classifier.pkl", "rb"))
        self.classifier = data["classifier"]
        self.classes = data["classes"]
        #chatbot.send_fb_message(self.fb_id, "training complete.")
    
    def get_current_images(self):
        cat = []
        summs = []
        last_images = []
        times = []
        
        dp = []
        for cam in self.cams:
            n = db.mongo.images.find({"user_name": self.user, "cam_id": cam, "detections":{"$exists": True}, "pose":{"$exists": True}}).limit(1).sort([("time", -1)])[0]
            mat, aug_box, person = ds.crop_person(n, crop_aug=False)
            dp.append((mat, aug_box, person))
            
        for mat, aug_box, person in dp:
            if mat is None:
                logger.error("file not found: " + n["filename"])
                return None, None
            else:
                feats = self.nn.img2vec([Image.fromarray(mat)])[0]
                cat.extend(feats)
                last_images.append(mat)
                #pose = ds.data2vec2(n)
                #cat.extend(pose)
                summs.append(n)
                times.append(n["time"])
                
        #for mat, aug_box, person in dp:
        #    cat.extend(aug_box)
        
        times = np.array(times)
        max_time = np.max(times)
        times -= max_time
        if np.min(times) < -10:
            return None, None
        self.last_images = last_images
        dp = np.array(cat)
        logger.debug("dp: " + str(dp))
        return dp, summs

    def on_event(self, event, data):
        if event == "image":
            if self.classifier is not None:
                self.counter += 1
                feats, summs = self.get_current_images()
                
                if feats is None:
                    return
                #datasets.data2vec([], [], data, False, False, False, False, False, True)

                try:
                    pred = self.classifier.predict([feats])[0]
                    probs = self.classifier.predict_proba([feats])[0]
                    
                    self.history.append(probs)
                    if len(self.history) < self.last_avg*2:
                        return
                    
                    if len(self.history) > 20:
                        history = self.history[-20:]
                        
                    if self.classes[pred] == "watch":
                        state = "watch"
                        self.last_state = state
                        probs[pred] = 1.0
                    else:    
                        # moving average
                        avg_dist = np.mean(self.history[-self.last_avg:], axis=0)
                        state = self.classes[np.argmax(avg_dist)]#self.classes[pred]
                        pred = np.argmax(avg_dist)
                        probs = avg_dist
                        self.last_state = state
                    
                    if self.stream:
                        chatbot.send_fb_message(self.fb_id, state + " " + str(int(probs[pred] * 100.0)) + "%")
                        #chatbot.send_fb_message(self.fb_id, str([int(p*100.0) for p in avg_dist]))
                        #if self.counter % 20 == 0:
                        #    show_image_chat(summs[0], self.fb_id, send_img=True, message=state + " " + str(probs[pred]))
                        #chatbot.send_fb_message(self.fb_id, "===END===")
                        
                    if probs[pred] < self.prob_threshold:
                        return
                except Exception as e:
                    logger.error(str(e))
                    return

                self.output = []
                    
                if state == "bed":
                    all_state = {"on": False}
                    #chatbot.send_fb_message(self.fb_id, "turning off lights")
                else:
                    all_state = {"on": True}
                    
                    if state == "study":
                        all_state.update({"bri":254,"hue":33016,"sat":53})
                        #chatbot.send_fb_message(self.fb_id, "brightening lights")
                    else:
                        all_state.update({"bri":254,"hue":14957,"sat":141})
                        
                if state == "study":
                    if not self.music_on:
                        chatbot.send_fb_message(self.fb_id, "playing music")
                        self.output.append({"platform": "play_youtube", "data": ""})
                        self.music_on = True
                else:
                    if self.music_on:
                        chatbot.send_fb_message(self.fb_id, "stopping music")
                        self.output.append({"platform": "stop_youtube", "data":""})
                        self.music_on = False
                    
                hue_data = json.dumps([
                        {"id": "1", "state": all_state},
                        {"id": "2", "state": all_state},
                        {"id": "3", "state": all_state}
                    ])

                self.output.append({"platform": "hue", "data": hue_data})
                
                if state == "watch":
                    if not self.tv_on:
                        self.output.append({"platform": "irkit", "data": ["TV"]})
                        self.tv_on = True
                        chatbot.send_fb_message(self.fb_id, "toggling TV (to on)")
                else:
                    if self.tv_on:
                        self.output.append({"platform": "irkit", "data": ["TV"]})
                        self.tv_on = False
                        chatbot.send_fb_message(self.fb_id, "toggling TV (to off)")

                probs = self.classifier.predict_proba([feats])

                #logger.debug(self.classes)
                #logger.debug(probs)
                ##logger.debug("current: {}, pred: {}".format(self.last_pred, pred))
                #logger.debug(state)
                ##logger.debug("time since last change: " + str(time.time() - self.last_change))

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
            elif msg == "state":
                chatbot.send_fb_message(self.fb_id, self.last_state)
                chatbot.send_fb_message(self.fb_id, str(len(self.last_images)))
                for img in self.last_images:
                    show_image_chat_raw(img, self.fb_id)
            elif msg.startswith("avg"):
                prev = self.last_avg
                self.last_avg = int(msg.strip().split()[-1])
                chatbot.send_fb_message(self.fb_id, "changed averaging from %s to %s" % (prev, self.last_avg))
            elif msg.startswith("threshold"):
                prev = self.prob_threshold
                self.prob_threshold = float(msg.strip().split()[-1])
                chatbot.send_fb_message(self.fb_id, "changed threshold from %s to %s" % (prev, self.prob_threshold))
            
    def execute(self):
        re = self.output
        self.output = []

        return re