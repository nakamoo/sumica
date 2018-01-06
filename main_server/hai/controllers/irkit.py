import time
from .controller import Controller
from server_actors import chatbot
from datetime import datetime
import pymongo
from pymongo import MongoClient
from flask import Flask
app = Flask(__name__)
app.config.from_pyfile(filename="../application.cfg")
mongo = MongoClient('localhost', app.config['PORT_DB']).hai
from controllers.tests.test0106 import get_current_images

# hue class
def predict():
    minute = datetime.now().minute
    return minute % 2, 0.7


def get_tv_label(start, end=10e10):
    labels = []
    classes = ['on', 'off']
    irkit_operations = mongo.operation.find({'controller': 'IRKit', 'time': {'$gt': start, '$lt': end}})
    for irkit_operation in irkit_operations:
        for op in irkit_operation['operation']:
            if ('confirmation' not in op) and op['platform'] == 'irkit':
                labels.append([irkit_operation['time'], classes.index(op['data'][1])])

    irkit_confirmations = mongo.confirmation.find(
        {'platform': 'irkit', 'answer': 'True', 'time': {'$gt': start, '$lt': end}})
    for irkit_confirmation in irkit_confirmations:
        if irkit_confirmation['confirmation'] == 'テレビをつけますか?':
            labels.append([irkit_confirmation['time'], classes.index('on')])
        elif irkit_confirmation['confirmation'] == 'テレビをけしますか?':
            labels.append([irkit_confirmation['time'], classes.index('off')])

    return {'TV': labels}, classes


class IRKit(Controller):
    def __init__(self, user, learner):
        self.re = []
        self.learner = learner
        _, self.classes = get_tv_label(self.learner.start_time)
        self.cam_ids = self.learner.cams
        self.user = user
        self.tv_on = False
        self.ask_time = 0
        self.duration = 600
        self.wait = False
        n = mongo.fb_users.find_one({"id": user})
        if n:
            self.fb_id = n["fb_id"]
        self.classes = [True, False]

    def on_event(self, event, data):
        if event == "image":
            if not self.wait and time.time() - self.ask_time > self.duration:
                d = get_current_images(self.user, self.cam_ids)
                index, confidence = self.learner.predict('youtube', [d])
                index = int(index[0])
                predicted_on = self.classes[index]
                if self.tv_on and (not predicted_on):
                    self.wait = True
                    self.ask_time = time.time()
                    self.re.append({"platform": "irkit", "data": ['TV', 'off'],
                                    "confirmation": "テレビをけしますか?"})
                elif (not self.tv_on) and predicted_on:
                    self.wait = True
                    self.ask_time = time.time()
                    self.re.append({"platform": "irkit", "data": ['TV', 'on'],
                                    "confirmation": "テレビをつけますか?"})

            if time.time() - self.ask_time > self.duration:
                self.wait = False

        if event == 'confirmation':
            if data['platform'] == 'irkit':
                self.wait = False
                if 'answer' in data:
                    if data['confirmation'] == 'テレビをつけますか?' and data['answer']:
                        self.tv_on = True
                    if data['confirmation'] == 'テレビをけしますか?' and data['answer']:
                        self.tv_on = False

        if event == "chat":
            msg = data["message"]["text"].split()
            if msg[0] == "irkit":
                if msg[1] == "TV":
                    if msg[2] == "on":
                        if self.tv_on:
                            chatbot.send_fb_message(self.fb_id, "TVは既についています")
                        else:
                            self.re.append({"platform": "irkit", "data": msg[1:],
                                            "confirmation": "テレビをつけますか?"})
                    elif msg[2] == "off":
                        if self.tv_on:
                            self.re.append({"platform": "irkit", "data": msg[1:],
                                            "confirmation": "テレビをけしますか?"})
                        else:
                            chatbot.send_fb_message(self.fb_id, "TVはすでにきえています")

                elif msg[1] == "AirConditioning":
                    pass

        if event == "speech" and data["type"] == "speech":
            msg = data["text"]
            if "テレビ" in msg and "つけて" in msg:
                if self.tv_on:
                    self.re.append({"platform": "tts", "data": "TVはすでについています"})
                else:
                    self.re.append({"platform": "tts", "data": "TVをつけます"})
                    self.re.append({"platform": "irkit", "data": ['TV', 'on']})
                    self.tv_on = True
            if "テレビ" in msg and "消して" in msg:
                if self.tv_on:
                    self.re.append({"platform": "tts", "data": "TVを消します"})
                    self.re.append({"platform": "irkit", "data": ['TV', 'off']})
                    self.tv_on = False
                else:
                    self.re.append({"platform": "tts", "data": "TVは既に消えています"})

    def execute(self):
        if self.re:
            re = self.re
            self.re = []
            self.log_operation(re)
            return re
        else:
            return []
