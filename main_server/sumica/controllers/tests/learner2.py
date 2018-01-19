import time
import os
import pickle
from collections import Counter

from flask import current_app
import ruptures as rpt
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import coloredlogs
import logging

from controllers.dbreader.imagereader import ImageReader
from controllers.vectorizer.person2vec import Person2Vec
from utils import db

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)

def get_segment_indices(y_times, segments):
    segment_indices = []

    for y in y_times:
        found = False
        for i, (s, e) in enumerate(segments):
            if y >= s and y < e:
                found = True
                segment_indices.append(i)
                break

        if not found:
            segment_indices.append(-1)

    return np.array(segment_indices)

def check_recorded_segments(times, username, start_time, end_time, min_fit_size):
    results = db.segments.find({'username': username, "end_time": {"$gte": start_time, "$lt": end_time}}).sort([("end_time", 1)])
    results = list(results)

    latest_start_fit_index = max(0, len(times) - min_fit_size)

    if len(results) > 0:
        logger.debug("last recorded segment: {}".format(results[-1]))
        last_fixed_index = times.index(results[-1]["end_time"])#np.searchsorted(times, results[-1]["time"])
    else:
        last_fixed_index = 0

    start_fit_index = min(latest_start_fit_index, last_fixed_index)
    segments = np.array([[r["start_time"], r["end_time"]] for r in results])
    segments = np.searchsorted(times, segments.flatten()).reshape([-1, 2]).tolist()

    return segments, last_fixed_index, start_fit_index

def record_segments(username, segments, segment_times, start_record, end_record):
    data = []
    misc = []

    for i, (start, end) in enumerate(segment_times):
        if start >= start_record and end < end_record:
            d = {'username': username, 'start_time': start, 'end_time': end}
            data.append(d)
            misc.append(segments[i])

    #logger.debug("newly recorded segments: {}".format(misc))
    logger.debug("stored {} new segments".format(len(data)))

    if len(data) > 0:
        db.segments.insert_many(data)
        logger.debug("last segment: {}".format(data[-1]))


class Learner:
    def __init__(self, username, cams):
        self.models = {}
        self.data2vec = Person2Vec()
        self.username = username
        self.cams = cams

    def learn_model(self, x_times, x, label_set, segments, segment_times):
        y_times = np.array([t[0] for t in label_set])
        y_indices = np.searchsorted(x_times, y_times)
        seg_indices = get_segment_indices(y_times, segment_times)
        y = np.array([t[1] for t in label_set])

        # only use labels that have corresponding segment
        y = y[seg_indices >= 0]
        y_times = y_times[seg_indices >= 0]
        seg_indices = seg_indices[seg_indices >= 0]

        # label prioritization in case of conflict
        counts = Counter(y)
        assigned = {t: 0 for t in list(set(y))}

        # find where to insert labels
        y_indices = np.searchsorted(x_times, y_times)
        # no label = -1
        label_mat = np.ones(x.shape[0], dtype=np.int32) * -1
        
        label_mat[y_indices] = y
        sparse_labels = label_mat.copy()

        for i, segment_i in enumerate(seg_indices):
            # special case for 0
            #if x_indices[i] == 0:
            #    c += 1
                
            prev_label = label_mat[y_indices[i]]

            if prev_label != -1 and (counts[y[i]] < counts[prev_label] or (counts[y[i]] == counts[prev_label] and assigned[y[i]] < assigned[prev_label])):
                print("warning: overwriting segment w/ label {} ({}) to {} ({})".format(prev_label, counts[prev_label], y[i], counts[y[i]]))
                assigned[prev_label] -= 1

            label_mat[segments[segment_i][0]:segments[segment_i][1]] = y[i]
            assigned[y[i]] += 1

        # take out remaining unlabeled data
        labeled_mask = label_mat != -1

        labeled_x = x[labeled_mask]
        train_labels = label_mat[labeled_mask]

        if len(labeled_x) > 0:
            clf = RandomForestClassifier(n_estimators=20)
            clf.fit(labeled_x, train_labels)
        else:
            clf = None

        return clf, {"raw": sparse_labels, "augmented": label_mat,
                     "indices": y_indices, "mapping": seg_indices.tolist()}, None

    def get_down_times(self, times):
        down_threshold = 30

        t = np.array(times[1:]) - np.array(times[:-1])
        downs = t > down_threshold

        return downs

    def create_image_matrix(self, imdata):
        pose_mat, act_mat, meta = self.data2vec.vectorize(imdata, get_meta=True)

        mat = np.concatenate([act_mat, pose_mat], axis=1)

        return mat, meta

    def calculate_segments(self, X, times, start_time, end_time):
        min_fit_size = 1000
        recorded_segments, last_fixed_index, start_fit_index = \
            check_recorded_segments(times, self.username, start_time, end_time, min_fit_size)

        #logger.debug("already recorded: {}".format(str(recorded_segments)))
        logger.debug("last fixed: {}, start fit: {}".format(last_fixed_index, start_fit_index))

        # TODO inefficient repetition
        downs = (np.where(self.get_down_times(times))[0]+1).tolist()
        starts = [0] + downs
        ends = downs + [len(times)]
        cam_segments = [list(a) for a in zip(starts, ends)]
        downs = (np.where(self.get_down_times(times[start_fit_index:]))[0] + 1).tolist()
        starts = [0] + downs
        ends = downs + [len(times)]

        segments = []

        for start, end in zip(starts, ends):
            start += start_fit_index
            end += start_fit_index

            if end - start > 1:
                part = X[start:end]
                model = "l1"  # "l2", "rbf"
                algo = rpt.BottomUp(model=model, min_size=1, jump=1).fit(part)
                breaks = algo.predict(pen=np.log(part.shape[0])*part.shape[1]*2**2)
                breaks = (np.array(breaks) + start).tolist()
                breaks[-1] -= 1 # avoid index out of range
                part_intervals = [list(a) for a in zip([start] + breaks[:-1], breaks)]
                segments.extend(part_intervals)
            else:
                # avoid index out of range
                end -= 1
                segments.append((start, end))

        segments = [(max(s, last_fixed_index), e) for s, e in segments if e > last_fixed_index]
        segment_times = [(times[s], times[e]) for s, e in segments]

        fix_threshold = len(times) - min_fit_size // 2
        logger.debug("new segments: {}".format(segments))
        record_segments(self.username, segments, segment_times, times[last_fixed_index], times[fix_threshold])

        segments = recorded_segments + segments
        segment_times = [(times[s], times[e]) for s, e in segments]

        return segments, segment_times, cam_segments, times[last_fixed_index]

    def update_models(self, labels, start_time, end_time=None):
        imreader = ImageReader()

        if end_time is None:
            end_time = time.time()

        imdata, times = imreader.read_db(self.username, start_time, end_time, self.cams, skip_absent=False)

        logger.debug("dataset size: {}".format(len(imdata)))

        if len(imdata) == 0:
            return None, None
        else:
            X, meta = self.create_image_matrix(imdata)
            segments, segment_times, cam_segments, fixed_time = self.calculate_segments(X, times, start_time, end_time)
            train_labels = {}

            for mode, label_set in labels.items():
                if len(label_set) <= 0:
                    label_data = {"raw": np.array([]), "augmented": np.array([]), "intervals": [], "indices": []}
                    m, m_breaks = None, []
                else:
                    m, label_data, m_breaks = self.learn_model(times, X, label_set, segments, segment_times)

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
        pose_mat, act_mat = self.data2vec.vectorize(images)
        input_mat = np.concatenate([act_mat, pose_mat], axis=1)
        probs = clf.predict_proba(input_mat)
        pred_labels = clf.classes_[np.argmax(probs, axis=1)]
        confidences = np.max(probs, axis=1)

        return pred_labels, confidences
