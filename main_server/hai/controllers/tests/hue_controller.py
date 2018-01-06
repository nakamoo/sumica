import time
import sys
import os
import json

import pymongo
from PIL import Image
from flask import Flask
from bson.son import SON
from sklearn.externals import joblib
import numpy as np

from controllers.controller import Controller
from server_actors import chatbot
from notebooks.utils.utils import epoch_to_strtime
from controllers.dbreader.hue_koki_dbreader import HueDBReader
from controllers.vectorizer.posennvectorizer import PoseNNVectorizer

app = Flask(__name__)
app.config.from_pyfile(filename="../../application.cfg")
mongo = pymongo.MongoClient('localhost', app.config['PORT_DB']).hai


class HueLv2(Controller):
    def __init__(self, user, debug=False, xy=None):
        self.user = user
        self.debug = debug

        self.output = []
        n = mongo.fb_users.find_one({"id": user})
        if n:
            self.fb_id = n["fb_id"]

        self.start = 0
        self.end = 999999999999
        self.cam_ids = ['webcam0', 'webcam1']

        self.dbreader = HueDBReader(self.user)
        self.vectorizer = PoseNNVectorizer(self.user, debug=self.debug)

        if xy is None:
            # self.X_cols, self.labels = self.dbreader.read_db(self.start, self.end)
            self.X_cols, self.labels = None, None
        else:
            self.X_cols, self.labels = xy

        self.X, self.y = None, None

    def vectorize(self):
        self.X, self.y = self.vectorizer.vectorize(self.X_cols, y=self.labels, color_augmentation_times=1)

    def on_event(self, event, data):
        if event == "chat" and self.fb_id:
            msg = data["message"]["text"]
            if msg == "train":
                chatbot.send_fb_message(self.fb_id, "start training")
                self.X_cols, self.labels = HueDBReader.read_db(self.start, self.end)
                self.learner.data_update(self.X, self.y)
                self.learner.train()
                chatbot.send_fb_message(self.fb_id, "finish training")
                joblib.dump(self.learner.classifier, 'huelv2.pkl')

            if msg == "control true":
                self.control = True
            if msg == "control false":
                self.control = False

        # if event == "timer":
        #     if self.learner.classifier is not None and self.control:
        #         d = get_current_images(self.user, self.cam_ids)
        #         all_state = self.operating_instructions[self.learner.predict(d)]
        #         hue_data = json.dumps([
        #             {"id": "1", "state": all_state},
        #             {"id": "2", "state": all_state},
        #             {"id": "3", "state": all_state}
        #         ])
        #         self.output = [{"platform": "hue", "data": hue_data}]

    def execute(self):
        re = self.output
        self.output = []
        self.log_operation(re)
        return re