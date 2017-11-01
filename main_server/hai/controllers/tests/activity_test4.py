import pickle
from controllers.controller import Controller
from controllers.learner import datasets
from controllers.snapshot import show_image_chat
import json
import numpy as np
from server_actors import chatbot
import database as db
import time
from controllers.learner.img2vec import NNFeatures

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
    query = {"user_name": username, "time": {"$gt": start_time, "$lt": end_time}, "$or": [{"text": "stand"}, {"text": "lie"}, {"text": "bed"}, {"text": "sit"}]}
    print_data = list(db.mongo.print.find(query))
    logger.debug(print_data)
    datasets.port = 27017 #!!!!
    image_data = datasets.get_event_images(username, print_data, ["misc0"])
        
    img_files, labels = [], []

    for x, y in zip(image_data, print_data):
        for imgs in x:
            row_files = []
            skip = False
            for cam in imgs:
                #  discard incomplete data
                if cam is not None:
                    row_files.append(cam["filename"])
                else:
                    skip = True
                    break
            if not skip:
                #dataX.append(np.concatenate(row))
                img_files.append(row_files)
                labels.append(y["text"])
                
    img_batch = []

    for t in img_files:
        for img in t:
            mat = scipy.misc.imread("./images/raw_images/" +  img)
            mat = scipy.misc.imresize(mat, (224, 224))
            img_batch.append(mat)
            
    times = 100
    logger.debug("augmenting image dataset of {} to {}".format(len(img_batch), len(img_batch)*times))
    aug_imgs = datasets.augment_images(img_batch, times)
    aug_imgs_pil = [Image.fromarray(img) for img in aug_imgs]
    
    logger.debug("converting {} images to vectors".format(len(aug_imgs_pil)))
    dataX = nn.img2vec(aug_imgs_pil)
    labels = labels * times
    logger.debug(labels)
                
    classes = list(set(labels))
    dataY = [classes.index(label) for label in labels]
                
    return np.array(dataX), np.array(dataY), classes

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
        
    def learn_and_load(self):
        start_time = time.time()-3600
        end_time = time.time()
        username = "sean"
        x, y, classes = get_dataset(username, start_time, end_time, self.nn)
        
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

        data = pickle.load(open("classifier.pkl", "rb"))
        self.classifier = data["classifier"]
        self.classes = data["classes"]
        #chatbot.send_fb_message(self.fb_id, "training complete.")
    
    def on_event(self, event, data):
        if event == "image" and self.classifier is not None:
            mat = scipy.misc.imread("./images/raw_images/" +  data["filename"])
            mat = scipy.misc.imresize(mat, (224, 224))
            mat = Image.fromarray(mat)
            feats = self.nn.img2vec([mat])[0]
            #datasets.data2vec([], [], data, False, False, False, False, False, True)

            pred = self.classifier.predict([feats])[0]
            probs = self.classifier.predict_proba([feats])[0]
            state = self.classes[pred]
            
            if self.stream:
                chatbot.send_fb_message(self.fb_id, state)
                #show_image_chat(data, self.fb_id, send_img=True, message=state + " " + str(probs[pred]))
                #chatbot.send_fb_message(self.fb_id, "===END===")
            
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
                #self.learn_and_load()
                self.train = True
            elif msg == "stream":
                self.stream = not self.stream
        elif event == "timer" and self.train:
            self.train = False
            self.learn_and_load()
            chatbot.send_fb_message(self.fb_id, "retrained")
            
    def execute(self):
        re = []

        return re