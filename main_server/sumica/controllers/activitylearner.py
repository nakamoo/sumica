import time
import threading
import traceback
import datetime

from flask import current_app
import coloredlogs
import logging
import ruptures as rpt
import numpy as np

from utils import db
import controllermanager as cm
from controllers.controller import Controller
from controllers.vectorizer.person2vec import Person2Vec
from controllers.dbreader.imagereader import ImageReader
from controllers.tests.learner2 import Learner
from controllers.utils import get_newest_images

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)


class ActivityLearner(Controller):
    def __init__(self, username, start_thread=True):
        super().__init__(username)

        # declare start_time for imagereader
        self.start_time = time.mktime(datetime.datetime(2018, 1, 20, 20).timetuple())

        self.cams = ["cam1", "cam2"]#["ipcam0", "ipcam1"]#ActivityLearner.get_cams(username, self.start_time, time.time())

        # update request when initializing
        self.update = True

        self.learner = Learner(self.username, self.cams)
        self.misc = None
        self.labels = []
        self.label_data = []
        self.predictions, self.classes, self.confidences = None, None, None
        self.current_images, self.current_predictions = None, None
        self.current_activity = None
        self.firstupdate = True

        self.last_asked = time.time()
        self.re = []

        if start_thread:
            # start loop separate from flask thread
            self.thread = threading.Thread(target=self.loop)
            #self.thread.daemon = True
            self.thread.start()

    def update_learner(self):
        logger.debug("updating learner...")

        end_time = time.time()
        results = db.labels.find(
            {"username": self.username, "time": {"$gt": self.start_time, "$lt": end_time}})
        classes = results.distinct("label")
        results = list(results)

        self.label_data = results
        self.labels = [r["label"] for r in results]
        results = [(r["time"], classes.index(r["label"])) for r in results]
        labels = {"activity": results}

        models, misc = self.learner.update_models(labels, self.start_time, end_time)

        if self.classes is None and self.firstupdate:
            self.re.append({"platform": "tts", "data": "行動認識モジュールの準備ができました"})
        self.firstupdate = False

        if models is not None and models["activity"] is not None:
            raw_pred = models["activity"].predict_proba(misc["matrix"])
            self.confidences = np.max(raw_pred, axis=1).tolist()
            self.predictions = np.argmax(raw_pred, axis=1).tolist()
            self.classes = classes

        self.misc = misc

        logger.debug("model update time taken: {}".format(time.time() - end_time))

    def loop(self):
        while True:
            try:
                if self.update:
                    self.update = False
                    self.update_learner()
            except:
                traceback.print_exc()

    def confirm_label(self, msg):
        match = None

        if "という行動" in msg:
            if "今は" in msg:
                match = msg[2:msg.index("という行動")]
            elif "今" in msg:
                match = msg[1:msg.index("という行動")]
            else:
                match = msg[:msg.index("という行動")]


        # find match
        for c in self.classes:
            if c in msg:
                match = c

        if match is None:
            self.re.append({"platform": "tts", "data": "すみません，全くわからなかったです．"})
        else:
            prefix = ""
            if match in self.classes:
                prefix = "既存の行動ラベルである"
            else:
                prefix = "新しい行動ラベルとして"

            # if match in self.classes:
            self.re.append({"platform": "", "data": "", "confirmation": {
                "question": prefix + match + "という認識でよろしいでしょうか？",
                "response": {
                    "yes": "わかりました．勉強します．",
                    "no": "そうですか．すみません．",
                    "none": "わかりませんでした．"
                },
                "data": {"label": match, "phase": 0}
            }})

    def on_event(self, event, data):
        if event == "image":
            # request update
            self.update = True

            self.current_images = get_newest_images(self.username, self.cams)

            # if model is ready
            if "activity" in self.learner.models and self.classes is not None:
                pred, pred_probs = self.learner.predict("activity", [self.current_images])
                self.current_predictions = pred_probs[0].tolist()
                self.current_activity = self.classes[np.argmax(self.current_predictions)]
                cm.trigger_controllers(self.username, "activity", self.current_activity)

                conf_mean = np.mean(self.confidences[-1000:])
                conf_std = np.std(self.confidences[-1000:])
                sigma = 1.0
                current_conf = np.max(pred_probs[0])
                patience = 60*60 # actually 1 hour or more is probably good

                if current_conf < conf_mean - conf_std * sigma:
                    logger.debug("current confidence: {}; mean: {}, std: {}".format(current_conf, conf_mean, conf_std))

                    if time.time() - self.last_asked > patience:
                        ask = {"platform": "", "data": "", "confirmation": {
                            "question": "今は何をしてるんですか？",
                            "open": "",
                            "data": "activity"
                        }}

                        if ask not in self.re:
                            self.re.append(ask)

                        self.last_asked = time.time()

        elif event == "speech" and data["type"] == "speech":
            msg = "".join(data["text"].split())

            if ("という行動" in msg or ("今" in msg and "してる" in msg)) and self.classes is not None:
                self.confirm_label(msg)

        elif event == "confirmation":
            if "data" in data and "label" in data["data"]:
                phase = data["data"]["phase"]
                ans = data["answer"]

                if ans and self.classes is not None:
                    label = data["data"]["label"]

                    db.labels.insert_one({"username": self.username, "time": data['response_time'], "label": label})

                    #if label in self.classes:
                    #    self.re.append({"platform": "tts", "data": label + "をデータベースに追加しました．"})
                    #else:
                    #    self.re.append({"platform": "tts", "data": label + "をデータベースに新しいクラスとして追加しました．"})
            if "data" in data and data["data"] == "activity":
                msg = data["answer"]
                self.confirm_label(msg)


    def execute(self):
        re = self.re
        self.re = []

        return re

    def get_cams(username, start_time, end_time):
        query = {"user_name": username, "time": {"$gt": start_time, "$lt": end_time}}
        results = db.images.find(query)
        cams = results.distinct("cam_id")
        cams.sort()

        return cams
