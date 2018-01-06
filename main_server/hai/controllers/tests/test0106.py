import time
import sys
import os
import json
import pickle
import traceback

import pymongo
from PIL import Image
from flask import Flask
from bson.son import SON
from sklearn.externals import joblib
import numpy as np

from controllers.controller import Controller
from controllers.vectorizer.person2vec import Person2Vec
from controllers.learner.hue_feature_designer import HueFeatureDesigner
from server_actors import chatbot
from notebooks.utils.utils import epoch_to_strtime, strtime_to_epoch
from controllers.dbreader.hue_koki_dbreader import pair_images

app = Flask(__name__)
app.config.from_pyfile(filename="../../application.cfg")
mongo = pymongo.MongoClient('localhost', app.config['PORT_DB']).hai

import coloredlogs, logging
from sklearn import preprocessing

logger = logging.getLogger(__name__)
coloredlogs.install(level=app.config['LOG_LEVEL'], logger=logger)


def safe_next(imgs):
    while True:
        img = imgs.next()
        try:
            Image.open(app.config['RAW_IMG_DIR'] + img["filename"]).verify()
            break
        except Exception as e:
            continue
    return img


def get_current_images(user, cam_ids):
    images = []
    for id in cam_ids:
        imgs = mongo.images.find({'user_name': user, 'cam_id': id, 'detections': {'$exists': True},
                                  'pose':{'$exists': True}},
                                 sort=[("_id", pymongo.DESCENDING)]).limit(10)

        images.append(safe_next(imgs))

    return images

# 'classes': array(['enjoy', 'etc', 'sleep', 'work'],
# ops = {0: {'bri': 254, 'hue': 2049, 'on': True, 'sat': 0},
#        3:{'bri': 254, 'hue': 14910, 'on': True, 'sat': 144},
#        2: {'on': False}}

class Test0106(Controller):
    def __init__(self, user):
        self.user = user
        self.cam_ids = ['webcam0', 'webcam1']
        with open('newsemisup.pkl', mode='rb') as f:
            hoge = pickle.load(f)

        self.classifier = hoge['classifier']
        self.classes = hoge['classes']
        self.state = None
        self.output = []

    def on_event(self, event, data):
        if event == "image":
            d = get_current_images(self.user, self.cam_ids)
            vectorizer = Person2Vec()
            a, b = vectorizer.vectorize([d])
            pa = np.concatenate([b, a], axis=1)
            ans = self.classifier.predict_proba(pa)[0]
            print(ans)
            index = np.argmax(ans)
            print(self.classes[index])
            # if self.state != ans:
            #     self.state = ans
            #     all_state = ops[ans]
            #     hue_data = json.dumps([
            #         {"id": "1", "state": all_state},
            #         {"id": "2", "state": all_state},
            #         {"id": "3", "state": all_state}
            #     ])
            #     self.output = [{"platform": "hue", "data": hue_data}]

    def execute(self):
        re = self.output
        self.output = []
        self.log_operation(re)
        return re
