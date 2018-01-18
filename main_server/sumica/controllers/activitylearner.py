import time
import threading
import traceback

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

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)


class ActivityLearner(Controller):
    def __init__(self, username):
        super().__init__(username)

        # declare start_time for imagereader
        self.start_time = time.time() - 3600*10

        self.cams = ActivityLearner.get_cams(username, self.start_time, time.time())

        # update request when initializing
        self.update = True

        self.learner = Learner(self.username, self.cams)
        self.misc = None
        self.labels = []
        self.label_data = []

        # start loop separate from flask thread
        self.thread = threading.Thread(target=self.loop)
        self.thread.daemon = True
        self.thread.start()

    def loop(self):
        while True:
            try:
                if self.update:
                    self.start_time = time.time() - 3600*10
                    end_time = time.time()
                    results = db.labels.find(
                        {"username": self.username, "time": {"$gt": self.start_time, "$lt": end_time}})
                    label_types = results.distinct("label")
                    results = list(results)

                    self.label_data = results
                    self.labels = [r["label"] for r in results]
                    results = [(r["time"], label_types.index(r["label"])) for r in results]
                    labels = {"activity": results}

                    _, misc = self.learner.update_models(labels, self.start_time, end_time)

                    self.misc = misc

                    self.update = False
            except:
                traceback.print_exc()

    def on_event(self, event, data):
        if event == "image":
            # request update
            self.update = True

    def execute(self):
        return []

    def get_cams(username, start_time, end_time):
        query = {"user_name": username, "time": {"$gt": start_time, "$lt": end_time}}
        results = db.images.find(query)
        cams = results.distinct("cam_id")
        cams.sort()

        return cams