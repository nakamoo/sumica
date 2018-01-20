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

        self.cams = ActivityLearner.get_cams(username, self.start_time, time.time())

        # update request when initializing
        self.update = True

        self.learner = Learner(self.username, self.cams)
        self.misc = None
        self.labels = []
        self.label_data = []
        self.predictions, self.classes, self.confidences = None, None, None
        self.current_images, self.current_predictions = None, None

        if start_thread:
            # start loop separate from flask thread
            self.thread = threading.Thread(target=self.loop)
            self.thread.daemon = True
            self.thread.start()

    def update_learner(self):
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

        if models["activity"] is not None:
            raw_pred = models["activity"].predict_proba(misc["matrix"])
            self.confidences = np.max(raw_pred, axis=1).tolist()
            self.predictions = np.argmax(raw_pred, axis=1).tolist()
            self.classes = classes

        self.misc = misc

    def loop(self):
        while True:
            try:
                if self.update:
                    self.update_learner()

                    self.update = False
            except:
                traceback.print_exc()

    def on_event(self, event, data):
        if event == "image":
            # request update
            self.update = True

            self.current_images = get_newest_images(self.username, self.cams)

            # if model is ready
            if "activity" in self.learner.models:
                pred, pred_probs = self.learner.predict("activity", [self.current_images])
                self.current_predictions = pred_probs[0].tolist()

    def execute(self):
        return []

    def get_cams(username, start_time, end_time):
        query = {"user_name": username, "time": {"$gt": start_time, "$lt": end_time}}
        results = db.images.find(query)
        cams = results.distinct("cam_id")
        cams.sort()

        return cams