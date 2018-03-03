import time
import os
import random
import traceback
import importlib
import threading
from _thread import start_new_thread
from collections import OrderedDict
import types

from flask import Flask, current_app, copy_current_request_context

import coloredlogs
import logging

from controllers.features import FeatureExtractor
from controllers.chatbot import Chatbot
from controllers.speechbot import Speechbot
from controllers.activitylearner import ActivityLearner
from controllers.nodemanager import NodeManager

from controllers.reminder import Reminder
from controllers.alarm import Alarm
from controllers.timetracker import TimeTracker

from statetracker import StateTracker
from server_actors import hue_actor
from utils import log_command

import sys
sys.path.insert(0, '../../activity_server')

import redis
from PIL import Image
import settings
import json
import io
import base64
import numpy as np
import uuid
from utils import db
from controllers.utils import sort_persons


logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)

rdb = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)

def global_event(event, data):
    Chatbot.on_global_event(event, data)


def standard_controllers(username):
    return OrderedDict([
        #("featureextractor", FeatureExtractor(username)),
        ("chatbot", Chatbot(username)),
        ("speechbot", Speechbot(username)),
        ("activitylearner", ActivityLearner(username)),
        ("nodemanager", NodeManager(username))
    ])


def trigger_controllers(user, event, data):
    if user is None:
        global_event(event, data)
    else:
        for c in cons[user].values():
            c.on_event(event, data)

# to be set by launcher
cons = dict()
states = dict()
# for stateless test commands (probably from browser)
test_commands = dict()
test_commands[current_app.config['USER']] = []

def initialize():
    global cons

    # TODO: use DB
    for user in [current_app.config['USER']]:
        cons[user] = standard_controllers(user)
        states[user] = StateTracker()
        test_commands[user].append({'platform': 'tts', 'data': 'サーバを起動しました．行動認識モジュールの準備をお待ちください．'})

    thread_stream = threading.Thread(target=image_loop)
    thread_stream.daemon = True
    thread_stream.start()

def base64_decode_image(a, size):
    if sys.version_info.major == 3:
        a = bytes(a, encoding="utf-8")

    a = np.frombuffer(base64.decodestring(a), dtype=np.uint8)
    a = a.reshape((size[1], size[0], settings.IMAGE_CHANS))

    return a

def image_loop():
    #with current.test_request_context():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    with app.app_context():
        while True:
            queue = rdb.lrange('master', 0, 0)

            if len(queue) > 0:
                d = json.loads(queue[0])
                a = bytes(d["image"], encoding="utf-8")
                image = Image.open(io.BytesIO(base64.decodestring(a)))
                #image = np.array(image)

                #print('IMAGE', image.shape)

                data = {}
                data['user_name'] = 'sean'
                data['cam_id'] = 'cam1'
                data['history'] = {'image_arrived': time.time()}
                data["time"] = time.time()#float(data["time"])
                data["motion_update"] = True#bool(data["motion_update"])

                if data["motion_update"]:
                    if current_app.config['ENCRYPTION']:
                        byte_data = request.files['image'].read()
                        token = cryptographic_key.encrypt(byte_data)
                        filename = str(uuid.uuid4()) + ".dat"
                        with open(Config.ENCRYPTED_IMG_DIR + filename, 'wb') as f:
                            f.write(token)
                        data['encryption'] = True
                    else:
                        filename = str(uuid.uuid4()) + ".jpg"
                        image.save(current_app.config['RAW_IMG_DIR'] + filename)
                        #logger.debug('saved: ' + current_app.config['RAW_IMG_DIR'] + filename)
                        #m_filename = str(uuid.uuid4()) + ".jpg"
                        #request.files['diff'].save(current_app.config['RAW_IMG_DIR'] + m_filename)
                        data['encryption'] = False

                data['filename'] = filename
                #data['diff_filename'] = m_filename
                data['version'] = '0.2'
                data['history']['image_recorded'] = time.time()
                data['detections'] = d['predictions']['object']
                data['pose'] = d['predictions']['pose']
                db.images.insert_one(data)

                def process(img_data):
                    try:
                        with current_app.test_request_context('/'):
                            if data["motion_update"]:
                                persons = sort_persons(img_data)
                                img_data.update({"persons": persons})

                                db.images.update_one({"filename": img_data['filename']},
                                                     {'$set': {"history.image_processing_start": time.time(),
                                                               'persons': persons}},
                                                     upsert=False)

                                trigger_controllers(data['user_name'], "image", img_data)
                                db.images.update_one({"filename": img_data['filename']},
                                                     {'$set': {"history.image_processing_finish": time.time()}},
                                                     upsert=False)
                    except:
                        traceback.print_exc()

                rdb.ltrim('master', 1, -1)
                process(data.copy())

def get_node_types():
    nodes = []

    for name, node in NodeManager.node_types.items():
        data = {
            "name": name,
            "param_file": node.param_file,
            "testable": node.testable,
            "input_types": node.input_types,
            "output_types": node.output_types,
            "icon": node.icon,
            "askable": node.askable
        }

        if node.display_name is None:
            data["display_name"] = name
        else:
            data["display_name"] = node.display_name

        nodes.append(data)

    return nodes

def test_execute(args):
    node_type = args["platform"]
    test_commands[args['username']].extend(NodeManager.node_types[node_type].test_execute(args))

def server_execute(username, command):
    platform = command["platform"]
    data = command["data"]

    # TODO e.g. tts not in platforms
    if platform in platforms:
        send_to_client = platforms[platform].execute(data)
        logger.debug("server execute: {}, {}".format(platform, send_to_client))

        return send_to_client

    return True

def client_execute(username):
    commands = []

    for con_name, controller in cons[username].items():
        con_commands = controller.execute()

        if isinstance(con_commands, types.GeneratorType):
            con_commands = next(con_commands)

        #logger.debug("{}: {}".format(con_name, con_commands))

        for command in con_commands:
            commands.append(command)

            if command:
                log_command(command, controller)

    # prioritize test actions over controllers
    for test in test_commands[username]:
        p = test['platform']

        # remove conflicting actions
        commands = [c for c in commands if p != c['platform']]

        commands.append(test)

    test_commands[username].clear()

    if len(commands) > 0:
        logger.debug("commands: {}".format(commands))

    states[username].track(commands)

    # ???
    #commands = [[c] for c in commands]

    return commands