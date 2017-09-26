from .controller import Controller
from database import mongo
import cv2
import colorsys
from server_actors import chatbot
from threading import Timer
import os
import time
import json
import pymongo
from sklearn.externals import joblib


class LogisticRegressionHueOperator(Controller):
    def __init__(self, user):
        self.user = user
        self.re = []
        self.clf = joblib.load('models/logreg_nakamura.pkl')
        self.history = [-1, -1, -1]

    def control_hue(self, cmd_hue):
        # ベッドに横たわる
        print(cmd_hue)
        if cmd_hue == 0:
            bri = 52
            hue = 10780
            sat = 251
        # ベッドの上でくつろぐ
        elif cmd_hue == 1:
            bri = 144
            hue = 13524
            sat = 200
        # 机の前で作業
        elif cmd_hue == 2:
            bri = 254
            hue = 34076
            sat = 251
        # 不在
        elif cmd_hue == 3:
            bri = 52
            hue = 10780
            sat = 251
        else:
            return

        self.re = [{"platform": "hue", "data": json.dumps({"on": True, "hue": hue, "brightness": bri, "sat": sat})}]

    def on_event(self, event, data):
        if event == "image":
            im_doc = mongo.images.find_one({"user_name": self.user,
                                            "keypoints": {"$exists": True}},
                                           sort=[("_id", pymongo.DESCENDING)])

            if len(im_doc['keypoints']['people']) == 1:
                logistic_predict = self.clf.predict([im_doc['keypoints']['people'][0]['pose_keypoints']])[0]
                mongo.images.update_one({"_id": im_doc["_id"]},
                                        {'$set': {'logistic_predict': str(logistic_predict)}},
                                        upsert=False)
                self.history.pop(0)
                self.history.append(logistic_predict)
            elif len(im_doc['keypoints']['people']) == 0:
                mongo.images.update_one({"_id": im_doc["_id"]},
                                        {'$set': {'logistic_predict': "absence"}},
                                        upsert=False)
                self.history.pop(0)
                self.history.append(3)
            else:
                mongo.images.update_one({"_id": im_doc["_id"]},
                                        {'$set': {'logistic_predict': "error"}},
                                        upsert=False)

            if len(list(set(self.history))) == 1:
                cmd_hue = list(set(self.history))[0]
                self.control_hue(cmd_hue)

    def execute(self):
        re = self.re
        self.re = []
        return re

