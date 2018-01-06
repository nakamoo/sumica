# -*- coding: utf-8 -*-
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
from datetime import datetime

from controllers.controller import Controller
from controllers.vectorizer.person2vec import Person2Vec
from controllers.learner.hue_feature_designer import HueFeatureDesigner
from server_actors import chatbot
from notebooks.utils.utils import epoch_to_strtime, strtime_to_epoch
from controllers.dbreader.hue_koki_dbreader import pair_images
from server_actors import hue
import json

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
            traceback.print_exc()
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


# hue class
def predict():
    minute = datetime.now().minute
    return minute % 3, 0.7


class Test0106(Controller):
    def __init__(self, user):
        self.user = user
        self.cam_ids = ['webcam0', 'webcam1']
        with open('newsemisup.pkl', mode='rb') as f:
            hoge = pickle.load(f)

        self.classifier = hoge['classifier']
        self.classes = hoge['classes']
        self.state = 'initial state'
        self.re = []
        self.output = []
        self.ask_time = 0
        self.duration = 600
        self.wait = False
        self.classes = ['電球色', '白色', 'オフ']

    def get_label(self, start, end):
        pass

    def on_event(self, event, data):
        # prediction by AI
        if event == "image":
            if not self.wait and time.time() - self.ask_time > self.duration:
                d = get_current_images(self.user, self.cam_ids)
                # vectorizer = Person2Vec()
                # a, b = vectorizer.vectorize([d])
                # pa = np.concatenate([b, a], axis=1)
                # ans = self.classifier.predict_proba(pa)[0]
                index, confidence = predict()
                state_updated = hue.get_updated_state(self.classes[index])
                # opelation by AI
                if self.state != state_updated:
                    self.wait = True
                    self.ask_time = time.time()
                    self.output = hue.change_color(self.classes[index], confirm=True)
                else:
                    print('prediction is same as current state')

            if time.time() - self.ask_time > self.duration:
                self.wait = False

        if event == 'confirmation':
            if data['platform'] == 'hue':
                self.wait = False
                if ('answer' in data) and (data['answer'] == 'True'):
                    self.state = json.loads(data['data'])

        if event == "speech" and data["type"] == "speech":
            if not self.wait:
                msg = data["text"]
                if "白色" in msg:
                    self.check_state_and_change('白色')
                elif "電球色" in msg:
                    self.check_state_and_change('電球色')
                elif ("電気" in msg) and ("オフ" in msg):
                    self.check_state_and_change('オフ')

    def check_state_and_change(self, color):
        state_updated = hue.get_updated_state(color)
        if self.state != state_updated:
            self.state = state_updated
            self.output = hue.change_color(color)
        else:
            self.output = [{"platform": "tts", "data": "電気は既に" + color + "です"}]

    def execute(self):
        re = self.output
        self.output = []
        if re:
            self.log_operation(re)
        return re
