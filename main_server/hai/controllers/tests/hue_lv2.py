import time
import sys
import os
import json

import pymongo
from PIL import Image
from flask import Flask
from bson.son import SON

from controllers.controller import Controller
from controllers.learner.logreg import LogReg
from server_actors import chatbot

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
    if light_states[0]['state']['on'] == 'False' and \
                    light_states[1]['state']['on'] == 'False' and \
                    light_states[2]['state']['on'] == 'False':
        return 0
    else:
        color = (light_states[0]['state']['bri'],
                 light_states[0]['state']['hue'],
                 light_states[0]['state']['sat'])
        return color


def group_colors(n=4, start=0, end=999999999999):
    pipeline = [
        {'$match': {'time': {'$gt': start, '$lt': end}}},
        {'$sort': {'_id': -1}},
        {'$limit': 5000},
        {"$group": {"_id": "$lights", "count": {"$sum": 1}}},
        {"$sort": SON([("count", -1), ("_id", -1)])}
    ]
    light_colors = mongo.hue.aggregate(pipeline)
    collections = []
    colors = []

    for c in light_colors:
        light_states = json.loads(c['_id'])
        color = extract_color(light_states)
        if color not in colors:
            collections.append(c['_id'])
            colors.append(color)

        if len(collections) >= n:
            break

    return collections


def collect_img_hue(light_states, user, duration=1800, start=0, end=999999999999):
    X = []
    y = []
    X_tmp = []
    y_tmp = []
    for i, ls in enumerate(light_states):
        munual_changes = mongo.hue.find({'user_name': user,
                                         'lights': ls,
                                         'state_changed': 'True',
                                         'program_control': 'False',
                                         'time': {'$gt': start, '$lt': end}},
                                        sort=[("_id", pymongo.DESCENDING)])
        for mc in munual_changes:
            start_time = mc['time']
            next_change = mongo.hue.find_one({'user_name': user, 'state_changed': 'True',
                                              'program_control': 'False', 'time': {'$gt': start_time}})

            if next_change is None:
                next_change_time = time.time()
            else:
                next_change_time = next_change['time']

            if next_change_time > start_time + duration:
                end_time = start_time + duration
            else:
                end_time = next_change_time

            imgs_cam0 = mongo.images.find({'user_name': user, 'cam_id': 'webcam0', 'time': {"$gte": start_time, "$lt": end_time}})
            imgs_cam1 = mongo.images.find({'user_name': user, 'cam_id': 'webcam1', 'time': {"$gte": start_time, "$lt": end_time}})
            img_pairs = pair_images(imgs_cam0, imgs_cam1)
            X_tmp.extend(img_pairs)
            y_tmp.extend([i] * len(img_pairs))
            # TODO: Here is parameter.
            if len(X_tmp) >= 500:
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


def get_instructions(light_states):
    instractions = []
    colors = [extract_color(json.loads(s)) for s in light_states]
    for c in colors:
        if c == 0:
            instractions.append({'on': False})
        else:
            instractions.append({'on': True, 'bri':c[0], 'hue':c[1], 'sat':c[2]})
    return instractions


class HueLv2(Controller):
    def __init__(self, user):
        self.user = user
        self.output = []
        n = mongo.fb_users.find_one({"id": user})
        if n:
            self.fb_id = n["fb_id"]

        self.start = 0
        self.end = 999999999999

        self.cam_ids = ['webcam0, webcam1']
        self.light_states = group_colors()
        self.operating_instructions = get_instructions(self.light_states)
        self.X, self.y = collect_img_hue(self.light_states, self.user)
        self.learner = LogReg(self.X, self.y)

    def on_event(self, event, data):
        if event == "chat" and self.fb_id:
            msg = data["message"]["text"]
            if msg == "train":
                chatbot.send_fb_message(self.fb_id, "start training")
                self.X, self.y = collect_img_hue(self.light_states, self.user)
                self.learner.data_update(self.X, self.y)
                self.learner.train()

        if event == "timer":
            if self.learner.classifier is not None:
                d = get_current_images()
                self.output.append(self.operating_instructions(self.learner.predict(d)))

    def execute(self):
        re = self.output
        self.output = []
        self.log_operation(re)
        return re


