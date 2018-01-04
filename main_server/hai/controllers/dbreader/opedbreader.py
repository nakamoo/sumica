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
from controllers.dbreader.dbreader import DBReader
from controllers.dbreader.hue_koki_dbreader import pair_images
from controllers.learner.hue_feature_designer import HueFeatureDesigner
from server_actors import chatbot
from notebooks.utils.utils import epoch_to_strtime

app = Flask(__name__)
app.config.from_pyfile(filename="../../application.cfg")
mongo = pymongo.MongoClient('localhost', app.config['PORT_DB']).hai

import coloredlogs, logging

logger = logging.getLogger(__name__)
coloredlogs.install(level=app.config['LOG_LEVEL'], logger=logger)


def collect_img_tv(user, start=0, end=time.time()):
    X = []
    y = []
    ops = mongo.operation.find({'user': user, 'controller': 'IRKit', 'operation.0.data.0': 'TV', 'time': {"$gte": start, "$lt": end}})
    count = ops.count()
    if count < 2:
        return None, None

    for i in range(count + 1):
        if i == 0:
            start_time = start
            end_op = ops.next()
            end_time = end_op['time']
            operation = 'off'
        elif i == count:
            start_op = end_op
            start_time = start_op['time']
            end_time = end
            operation = start_op['operation'][0]['data'][1]
        else:
            start_op = end_op
            start_time = start_op['time']
            end_op = ops.next()
            end_time = end_op['time']
            operation = start_op['operation'][0]['data'][1]

        imgs_cam0 = mongo.images.find({'user_name': user, 'cam_id': 'webcam0',
                                       'time': {"$gte": start_time, "$lt": end_time}})
        imgs_cam1 = mongo.images.find({'user_name': user, 'cam_id': 'webcam1',
                                       'time': {"$gte": start_time, "$lt": end_time}})
        imgs_pairs = pair_images(imgs_cam0, imgs_cam1)

        X.extend(imgs_pairs)
        y.extend([operation] * len(imgs_pairs))

    return X, y


def collect_img_music(user, start=0, end=time.time()):
    X = []
    y = []
    ops = mongo.operation.find({'user': user, 'controller': 'YoutubePlayer', 'time': {"$gte": start, "$lt": end}})
    count = ops.count()
    if count < 2:
        return None, None

    for i in range(count + 1):
        if i == 0:
            start_time = start
            end_op = ops.next()
            end_time = end_op['time']
            operation = 'stop_youtube'
        elif i == count:
            start_op = end_op
            start_time = start_op['time']
            end_time = end
            operation = start_op['operation'][0]['platform']
        else:
            start_op = end_op
            start_time = start_op['time']
            end_op = ops.next()
            end_time = end_op['time']
            operation = start_op['operation'][0]['platform']

        imgs_cam0 = mongo.images.find({'user_name': user, 'cam_id': 'webcam0',
                                       'time': {"$gte": start_time, "$lt": end_time}})
        imgs_cam1 = mongo.images.find({'user_name': user, 'cam_id': 'webcam1',
                                       'time': {"$gte": start_time, "$lt": end_time}})
        imgs_pairs = pair_images(imgs_cam0, imgs_cam1)

        X.extend(imgs_pairs)
        y.extend([operation] * len(imgs_pairs))

    return X, y


class OperationDBReader(DBReader):
    def __init__(self, user):
        self.user = user
        self.labels = None

    def read_db(self, start, end, op):
        if op == 'TV':
            X, y = collect_img_tv(self.user, start=start, end=end)
        elif op == 'music':
            X, y = collect_img_music(self.user, start=start, end=end)

        return X, y
