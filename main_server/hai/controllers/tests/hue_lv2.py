import time
import sys
import os
import json

import pymongo
from PIL import Image
from flask import Flask
from bson.son import SON
from sklearn.externals import joblib

from controllers.controller import Controller
from controllers.learner.hue_feature_designer import HueFeatureDesigner
from server_actors import chatbot
from notebooks.utils.utils import epoch_to_strtime

app = Flask(__name__)
app.config.from_pyfile(filename="../../application.cfg")
mongo = pymongo.MongoClient('localhost', app.config['PORT_DB']).hai

import coloredlogs, logging

logger = logging.getLogger(__name__)
coloredlogs.install(level=app.config['LOG_LEVEL'], logger=logger)


def safe_next(imgs):
    while True:
        img = imgs.next()
        try:
            Image.open(app.config['RAW_IMG_DIR'] + img["filename"]).verify()
            break
        except:
            continue
    return img


def pair_images(ims_cam0, ims_cam1):
    # Images should be sorted in ascending order.
    im_pairs = []
    try:
        target = safe_next(ims_cam0)
        earlier_img = safe_next(ims_cam1)
        while target['time'] < earlier_img['time']:
            target = safe_next(ims_cam0)
        latter_img = safe_next(ims_cam1)

        while True:
            while target['time'] > latter_img['time']:
                earlier_img = latter_img
                latter_img = safe_next(ims_cam1)
            if latter_img['time'] - target['time'] > target['time'] - earlier_img['time']:
                im_pairs.append((target, earlier_img))
            else:
                im_pairs.append((target, latter_img))
            target = safe_next(ims_cam0)

    except StopIteration:
        return im_pairs


def extract_color(light_states):
    if (not light_states[0]['state']['on']) and (not light_states[1]['state']['on']) and (
            not light_states[2]['state']['on']):
        return {'on': False}

    else:
        c = (light_states[0]['state']['bri'],
             light_states[0]['state']['hue'],
             light_states[0]['state']['sat'])
        return {'on': True, 'bri': c[0], 'hue': c[1], 'sat': c[2]}


def group_colors(n=3, start=0, end=999999999999):
    pipeline = [
        {'$match': {'time': {'$gt': start, '$lt': end}}},
        {'$sort': {'_id': -1}},
        {'$limit': 5000},
        {"$group": {"_id": "$lights", "count": {"$sum": 1}}},
        {"$sort": SON([("count", -1), ("_id", -1)])}
    ]
    light_colors = mongo.hue.aggregate(pipeline)
    colors = []

    for c in light_colors:
        light_states = json.loads(c['_id'])
        color = extract_color(light_states)
        if color not in colors:
            colors.append(color)

        if len(colors) >= n:
            break

    return colors


def collect_img_hue(operating_instructions, user, duration=1800, start=0, end=999999999999, nums=400):
    X = []
    y = []
    for i, op in enumerate(operating_instructions):
        X_tmp = []
        y_tmp = []
        if len(op) <= 1:
            munual_changes = mongo.hue.find({'user_name': user,
                                             'light_states.0.state.on': False,
                                             'state_changed': 'True',
                                             'program_control': 'False',
                                             'time': {'$gt': start, '$lt': end}},
                                            sort=[("_id", pymongo.DESCENDING)])
        else:
            munual_changes = mongo.hue.find({'user_name': user,
                                             'light_states.0.state.on': True,
                                             'light_states.0.state.bri': op['bri'],
                                             'light_states.0.state.hue': op['hue'],
                                             'light_states.0.state.sat': op['sat'],
                                             'state_changed': 'True',
                                             'program_control': 'False',
                                             'time': {'$gt': start, '$lt': end}},
                                            sort=[("_id", pymongo.DESCENDING)])

        num_remains = nums
        for mc in munual_changes:
            start_time = mc['time']
            next_change = mongo.hue.find_one({'user_name': user, 'state_changed': 'True', 'time': {'$gt': start_time}})

            if next_change is None:
                next_change_time = time.time()
            else:
                next_change_time = next_change['time']

            if next_change_time > start_time + duration:
                end_time = start_time + duration
            else:
                end_time = next_change_time

            imgs_cam0 = mongo.images.find({'user_name': user, 'cam_id': 'webcam0',
                                           'time': {"$gte": start_time, "$lt": end_time}},
                                          sort=[("_id", pymongo.ASCENDING)]).limit(num_remains+5)
            imgs_cam1 = mongo.images.find({'user_name': user, 'cam_id': 'webcam1',
                                           'time': {"$gte": start_time, "$lt": end_time}},
                                          sort=[("_id", pymongo.ASCENDING)]).limit(num_remains+5)
            img_pairs = pair_images(imgs_cam0, imgs_cam1)
            if len(img_pairs) > num_remains:
                img_pairs = img_pairs[:num_remains]
            X_tmp.extend(img_pairs)
            y_tmp.extend([i] * len(img_pairs))
            num_remains -= len(img_pairs)
            if num_remains <= 0:
                break

        X.extend(X_tmp)
        y.extend(y_tmp)

    return X, y


def get_current_images(user, cam_ids):
    images = []
    for id in cam_ids:
        imgs = mongo.images.find({'user_name': user, 'cam_id': id},
                                 sort=[("_id", pymongo.DESCENDING)]).limit(10)

        images.append(safe_next(imgs))

    return images


class HueLv2(Controller):
    def __init__(self, user, debug=False, xy=None):
        self.user = user
        self.output = []
        n = mongo.fb_users.find_one({"id": user})
        if n:
            self.fb_id = n["fb_id"]

        self.start = 0
        self.end = 999999999999

        self.cam_ids = ['webcam0', 'webcam1']
        self.operating_instructions = group_colors(start=self.start, end=self.end)
        # TODO: 消す
        # print(self.operating_instructions)
        self.X, self.y = collect_img_hue(self.operating_instructions, self.user,
                                         start=self.start, end=self.end)
        self.learner = HueFeatureDesigner(self.X, self.y, debug=debug)
        self.control = False

    def on_event(self, event, data):
        if event == "chat" and self.fb_id:
            msg = data["message"]["text"]
            if msg == "train":
                chatbot.send_fb_message(self.fb_id, "start training")
                self.X, self.y = collect_img_hue(self.operating_instructions, self.user,
                                                 start=self.start, end=self.end)
                self.learner.data_update(self.X, self.y)
                self.learner.train()
                chatbot.send_fb_message(self.fb_id, "finish training")
                joblib.dump(self.learner.classifier, 'huelv2.pkl')

            if msg == "control true":
                self.control = True
            if msg == "control false":
                self.control = False

        if event == "timer":
            if self.learner.classifier is not None and self.control:
                d = get_current_images(self.user, self.cam_ids)
                all_state = self.operating_instructions[self.learner.predict(d)]
                hue_data = json.dumps([
                    {"id": "1", "state": all_state},
                    {"id": "2", "state": all_state},
                    {"id": "3", "state": all_state}
                ])
                self.output = [{"platform": "hue", "data": hue_data}]

    def execute(self):
        re = self.output
        self.output = []
        self.log_operation(re)
        return re
