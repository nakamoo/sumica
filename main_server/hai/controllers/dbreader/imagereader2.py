from pymongo import MongoClient
import controllers.dbreader.dbreader as dbreader
import configparser, os
import json

# Todo: use config parser
from flask import Flask
import pymongo
app = Flask(__name__)
app.config.from_pyfile(filename="../../application.cfg")
mongo = pymongo.MongoClient('localhost', app.config['PORT_DB']).hai


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


class ImageReader(dbreader.DBReader):
    def __init__(self):
        pass

    def read_db(self, username, start_time, end_time, cams, max_lag=5):
        query = {"user_name": username, "cam_id": {"$in": cams}, "pose":{"$exists": True}, "detections":{"$exists": True}, "time": {"$gte": start_time, "$lt": end_time}}
        cursor = mongo.images.find(query).sort([("time", 1)])
        music_ops = mongo.operation.find({'user': username, 'controller': 'YoutubePlayer',
                                          'time': {"$gte": start_time, "$lt": end_time}})
        tv_ops = mongo.operation.find({'user': username, 'controller': 'IRKit',
                                       'operation.0.data.0': 'TV', 'time': {"$gte": start_time, "$lt": end_time}})

        munual_changes = mongo.hue.find({'user_name': username,
                                         'state_changed': 'True',
                                         'program_control': 'False',
                                         'time': {'$gt': start_time, '$lt': end_time}})

        im = 'stop_youtube'
        it = 'off'
        # ih = {'bri': 254, 'hue': 2049, 'on': True, 'sat': 0}
        ih = {'bri': 254, 'hue': 14910, 'on': True, 'sat': 144}

        nm = music_ops.next()
        nt = tv_ops.next()
        nh = munual_changes.next()

        re_data = []
        y_data = []
        current_data = [None for cam in cams]

        for im_data in cursor:
            current_time = im_data["time"]
            current_data[cams.index(im_data["cam_id"])] = im_data

            skip = False
            for cam_image in current_data:
                if cam_image is None or current_time - cam_image["time"] > max_lag: #old data
                    skip = True

            if not skip:
                re_data.append(current_data.copy())
                if cam_image["time"] > nm['time']:
                    im = nm['operation'][0]['platform']
                    try:
                        nm = music_ops.next()
                    except:
                        nm['time'] = 999999999999999999999999999999999
                if cam_image["time"] > nt['time']:
                    it = nt['operation'][0]['data'][1]
                    try:
                        nt = tv_ops.next()
                    except:
                        nt['time'] = 999999999999999999999999999999999
                if cam_image["time"] > nh['time']:
                    ih = extract_color(json.loads(nh['lights']))
                    try:
                        nh = munual_changes.next()
                    except:
                        nh['time'] = 999999999999999999999999999999999
                y_data.append((ih, im, it))


        return re_data, y_data
