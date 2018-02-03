import time
import os
import pickle

from flask import current_app
import ruptures as rpt
import numpy as np
import coloredlogs
import logging

from controllers.dbreader.imagereader import ImageReader
from controllers.vectorizer.person2vec import Person2Vec
from utils import db
from controllers.tests.trainer import Trainer

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)


def check_recorded_segments(times, username, start_time, end_time, min_fit_size):
    results = db.segments.find({'username': username, "end_time": {"$gte": start_time, "$lt": end_time}}).sort(
        [("end_time", 1)])
    results = list(results)

    latest_start_fit_index = max(0, len(times) - min_fit_size)

    if len(results) > 0:
        #logger.debug("last recorded segment: {}".format(results[-1]))
        last_fixed_index = times.index(results[-1]["end_time"])  # np.searchsorted(times, results[-1]["time"])
    else:
        last_fixed_index = 0

    start_fit_index = min(latest_start_fit_index, last_fixed_index)
    segments = np.array([[r["start_time"], r["end_time"]] for r in results])
    segments = np.searchsorted(times, segments.flatten()).reshape([-1, 2]).tolist()

    return segments, last_fixed_index, start_fit_index


def record_segments(username, segments, segment_times, start_record, end_record):
    data = []
    #misc = []
    accum = 0

    for i, (start, end) in enumerate(segment_times[::-1]):
        seg_len = end - start

        if start >= start_record and (end < end_record or accum+seg_len > 2000):
            d = {'username': username, 'start_time': start, 'end_time': end}
            data.append(d)
            #misc.append(segments[i])
            accum += seg_len

    data = data[::-1]
    #misc = misc[::-1]

    if len(data) > 0:
        db.segments.insert_many(data)


class Learner:
    def __init__(self, username, cams):
        self.models = {}
        self.data2vec = Person2Vec()
        self.username = username
        self.cams = cams
        self.trainers = {}

    def get_down_times(self, times):
        down_threshold = 30

        t = np.array(times[1:]) - np.array(times[:-1])
        downs = t > down_threshold

        return downs

    def create_image_matrix(self, imdata):
        pose_mat, act_mat, meta = self.data2vec.vectorize(imdata, get_meta=True, average=True)

        mat = np.concatenate([act_mat, pose_mat], axis=1)

        return mat, meta

    def calculate_segments(self, X, times, start_time, end_time):
        min_fit_size = 1000
        recorded_segments, last_fixed_index, start_fit_index = \
            check_recorded_segments(times, self.username, start_time, end_time, min_fit_size)

        # TODO inefficient repetition
        downs = (np.where(self.get_down_times(times))[0] + 1).tolist()
        starts = [0] + downs
        ends = downs + [len(times)]
        cam_segments = [list(a) for a in zip(starts, ends)]
        downs = (np.where(self.get_down_times(times[start_fit_index:]))[0] + 1 + start_fit_index).tolist()
        starts = [start_fit_index] + downs
        ends = downs + [len(times)]

        segments = []

        #logger.debug(str(recorded_segments[-1]))
        #logger.debug("calculating breakpoints, {}".format(list(zip(starts, ends))))

        for start, end in zip(starts, ends):
            #logger.debug("{} -> {}".format(start, end))

            if end - start > 1:
                part = X[start:end]
                model = "l1"  # "l2", "rbf"
                algo = rpt.BottomUp(model=model, min_size=1, jump=1).fit(part)
                breaks = algo.predict(pen=np.log(part.shape[0]) * part.shape[1] * 2 ** 2)
                breaks = (np.array(breaks) + start).tolist()
                breaks[-1] -= 1  # avoid index out of range
                part_intervals = [list(a) for a in zip([start] + breaks[:-1], breaks)]
                segments.extend(part_intervals)
            else:
                # avoid index out of range
                end -= 1
                segments.append((start, end))

        segments = [(max(s, last_fixed_index), e) for s, e in segments if e > last_fixed_index]
        segment_times = [(times[s], times[e]) for s, e in segments]

        fix_threshold = len(times) - min_fit_size // 2
        #logger.debug("new segments: {}".format(segments))
        record_segments(self.username, segments, segment_times, times[last_fixed_index], times[fix_threshold])

        segments = recorded_segments + segments
        segment_times = [(times[s], times[e]) for s, e in segments]

        return segments, segment_times, cam_segments, times[last_fixed_index]

    def update_models(self, labels, start_time, end_time=None):
        imreader = ImageReader()

        if end_time is None:
            end_time = time.time()

        imdata, times = imreader.read_db(self.username, start_time, end_time, self.cams, skip_absent=False)

        if len(imdata) == 0:
            return None, None
        else:
            X, meta = self.create_image_matrix(imdata)
            segments, segment_times, cam_segments, fixed_time = self.calculate_segments(X, times, start_time, end_time)
            train_labels = {}

            for mode, label_set in labels.items():
                if mode not in self.trainers:
                    self.trainers[mode] = Trainer()

                if len(label_set) <= 0:
                    label_data = {"raw": np.array([]), "augmented": np.array([]),
                                  "intervals": [], "indices": [], 'seg_mapping': []}
                    m, m_breaks = None, []
                else:
                    m, label_data, update_model = self.trainers[mode].learn_model(times, X, label_set, segments, segment_times)

                    if update_model:
                        logger.debug("model <{}> updated.".format(mode))

                self.models[mode] = m
                train_labels[mode] = label_data

            misc = {}
            misc["matrix"] = X
            misc["times"] = times
            misc["raw_data"] = imdata
            misc["meta"] = meta
            misc["segments"] = segments
            misc["segment_times"] = segment_times
            misc["segments_last_fixed"] = fixed_time
            misc["cam_segments"] = cam_segments
            misc["train_labels"] = train_labels
            misc["time_range"] = {"min": start_time, "max": end_time}

            return self.models, misc

    def predict(self, mode, images):
        clf = self.models[mode]
        pose_mat, act_mat = self.data2vec.vectorize(images, average=True)
        input_mat = np.concatenate([act_mat, pose_mat], axis=1)
        probs = clf.predict_proba(input_mat)
        pred_labels = clf.classes_[np.argmax(probs, axis=1)]

        return pred_labels, probs
