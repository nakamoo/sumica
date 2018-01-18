from controllers.dbreader.imagereader import ImageReader
from controllers.vectorizer.person2vec import Person2Vec
import ruptures as rpt
import time
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import os
import pickle
from collections import Counter

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

    def calculate_segments(self, X, times):
        downs = (np.where(self.get_down_times(times))[0]+1).tolist()
        starts = [0] + downs
        ends = downs + [len(times)]

        segments = []

        for start, end in zip(starts, ends):
            if end - start > 1:
                part = X[start:end]
                model = "l1"  # "l2", "rbf"
                algo = rpt.BottomUp(model=model, min_size=1, jump=1).fit(part)
                breaks = algo.predict(pen=np.log(part.shape[0])*part.shape[1]*2**2)
                breaks = (np.array(breaks) + start).tolist()
                breaks[-1] -= 1
                part_intervals = list(zip([start] + breaks[:-1], breaks))
                segments.extend(part_intervals)
            else:
                segments.append((start, end-1))

        # remove last segment because index out of range
        #if len(segments) > 0:
        #segments = segments[:-1]
        #    segments[-1] = (segments[-1][0], segments[-1][1]-1)
        segment_times = [(times[s], times[e]) for s, e in segments]
        return segments, segment_times

    def update_models(self, labels, start_time, end_time=None):
        imreader = ImageReader()

        if end_time is None:
            end_time = time.time()

        imdata, times = imreader.read_db(self.username, start_time, end_time, self.cams, skip_absent=False)

        if len(imdata) == 0:
            return None, None
        else:
            X, meta = self.create_image_matrix(imdata)
            segments, segment_times = self.calculate_segments(X, times)
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
