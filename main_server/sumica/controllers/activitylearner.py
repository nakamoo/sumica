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

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)


class ActivityLearner(Controller):
    def __init__(self, username):
        super().__init__(username)

        self.imreader = ImageReader()
        self.data2vec = Person2Vec()
        self.start_time = time.time() - 3600

        max_lag = 3600
        start_time = time.time() - max_lag
        end_time = time.time()
        query = {"user_name": "sean", "time": {"$gt": start_time, "$lt": end_time}}
        results = db.images.find(query)
        self.cams = results.distinct("cam_id")
        self.cams.sort()

        self.update = True
        self.breaks = []

        self.thread = threading.Thread(target=self.loop)
        self.thread.start()

    def loop(self):
        while True:
            try:
                if self.update:
                    imdata, times = self.imreader.read_db(self.username, self.start_time, time.time(), self.cams, skip_absent=False,
                                                     filtered=False)

                    if len(imdata) > 0:
                        X, _ = self.create_image_matrix(imdata)
                        print(X)
                        self.breaks = self.calculate_breakpoints(X)
                        print(self.breaks)

                    self.update = False
            except:
                traceback.print_exc()

    def create_image_matrix(self, imdata):
        pose_mat, act_mat, meta = self.data2vec.vectorize(imdata, get_meta=True)
        mat = np.concatenate([act_mat, pose_mat], axis=1)

        return mat, meta

    def calculate_breakpoints(self, X):
        if X.shape[0] < 2:
            return []

        model = "l1"  # "l2", "rbf"
        algo = rpt.BottomUp(model=model, min_size=1, jump=1).fit(X)
        breaks = algo.predict(pen=np.log(X.shape[0]) * X.shape[1] * 2 ** 2)

        return breaks

    def on_event(self, event, data):
        if event == "image":
            self.update = True

    def execute(self):
        return []

