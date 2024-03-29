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


def check_color(data):
    color_data = json.loads(data)
    if color_data == [{'id': '1', 'state': {'bri': 254, 'hue': 14957, 'on': True, 'sat': 141}},
                      {'id': '2', 'state': {'bri': 254, 'hue': 14957, 'on': True, 'sat': 141}},
                      {'id': '3', 'state': {'bri': 254, 'hue': 14957, 'on': True, 'sat': 141}}]:
        return '電球色'
    elif color_data == [{'id': '1', 'state': {'bri': 254, 'hue': 33016, 'on': True, 'sat': 53}},
                        {'id': '2', 'state': {'bri': 254, 'hue': 33016, 'on': True, 'sat': 53}},
                        {'id': '3', 'state': {'bri': 254, 'hue': 33016, 'on': True, 'sat': 53}}]:
        return '白色'
    elif color_data == [{'id': '1', 'state': {'on': False}},
                        {'id': '2', 'state': {'on': False}},
                        {'id': '3', 'state': {'on': False}}]:
        return 'オフ'

    raise Exception


def get_hue_label(start, end=10e10):
    labels = []
    classes = set()
    hue_operations = mongo.operation.find({'controller': 'Test0106', 'time': {'$gt': start, '$lt': end}})
    for hue_operation in hue_operations:
        for op in hue_operation['operation']:
            if ('confirmation' not in op) and op['platform'] == 'hue':
                classes.add(check_color(op['data']))
                labels.append([hue_operation['time'], check_color(op['data'])])

    classes_list = list(classes)
    labels2 = [[a, classes_list.index(b)] for a, b in labels]

    return {'hue': labels2}, classes_list


# hue class
def predict():
    minute = datetime.now().minute
    return minute % 3, 0.7


class Test0106(Controller):
    def __init__(self, user, learner):
        self.user = user
        self.learner = learner
        self.cam_ids = ['webcam0', 'webcam1']
        self.state = 'initial state'
        self.re = []
        self.output = []
        self.ask_time = 0
        self.duration = 122
        self.wait = False
        self.cam_ids = self.learner.cams
        _, self.classes = get_hue_label(self.learner.start_time)

    def on_event(self, event, data):
        # prediction by AI
        if event == "image":
            if not self.wait and time.time() - self.ask_time > self.duration:
                d = get_current_images(self.user, self.cam_ids)
                index, confidence = self.learner.predict('hue', [d])
                index = int(index[0])
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
