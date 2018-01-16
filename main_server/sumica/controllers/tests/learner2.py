from controllers.dbreader.imagereader import ImageReader
from controllers.vectorizer.person2vec import Person2Vec
import ruptures as rpt
import time
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import os
import pickle
from collections import Counter

class Learner:
    def __init__(self, username, cams):
        self.models = {}
        self.data2vec = Person2Vec()
        self.username = username
        self.cams = cams

    def learn_model(self, x_times, x, label_set, breaks):
        y_times = [t[0] for t in label_set]
        y = [t[1] for t in label_set]
        counts = Counter(y)
        assigned = {t: 0 for t in list(set(y))}
        x_indices = np.searchsorted(x_times, y_times)
        # no label = -1
        label_mat = np.ones(x.shape[0], dtype=np.int32) * -1
        intervals = [[] for _ in range(len(label_set))]

        _breaks = [0] + breaks

        #  label augmentation
        # choose which breakpoint to assign
        #clusters = np.searchsorted(_breaks, x_indices)


        alpha = 0 # threshold
        beta = alpha # new break
        new_breaks = []
        
        """
        for i, c in enumerate(clusters):
            if x_indices[i] == 0:
                c += 1
                
            past = x_indices[i] - _breaks[c-1]

            if past > alpha:
                new_breaks.append(x_indices[i]-beta)
        
        _breaks = _breaks + new_breaks
        _breaks.sort()
        """
        
        clusters = np.searchsorted(_breaks, x_indices)
        
        for i, xx in enumerate(x_indices):
            label_mat[xx - 1] = y[i]
        sparse_labels = label_mat.copy()

        for i, c in enumerate(clusters):
            # special case for 0
            if x_indices[i] == 0:
                c += 1
                
            prev_label = label_mat[_breaks[c-1]]

            if prev_label != -1 and (counts[y[i]] < counts[prev_label] or (counts[y[i]] == counts[prev_label] and assigned[y[i]] < assigned[prev_label])):
                print("warning: overwriting segment w/ label {} ({}) to {} ({})".format(prev_label, counts[prev_label], y[i], counts[y[i]]))
                assigned[prev_label] -= 1
                intervals[prev_label] = []

            label_mat[_breaks[c-1]:_breaks[c]] = y[i]
            intervals[i] = [_breaks[c-1], _breaks[c]]
            assigned[y[i]] += 1

        # take out remaining unlabeled data
        labeled_mask = label_mat != -1

        labeled_x = x[labeled_mask]
        train_labels = label_mat[labeled_mask]

        clf = RandomForestClassifier(n_estimators=20)
        clf.fit(labeled_x, train_labels)

        return clf, {"raw": sparse_labels, "augmented": label_mat, "intervals": intervals,
                     "indices": x_indices, "mapping": clusters.tolist()}, _breaks[1:]

    def get_down_times(self, times):
        down_threshold = 30

        t = np.array(times[1:]) - np.array([0] + times[:-1])
        downs = t > down_threshold

        return downs

    def create_image_matrix(self, imdata):
        pose_mat, act_mat, meta = self.data2vec.vectorize(imdata, get_meta=True)

        mat = np.concatenate([act_mat, pose_mat], axis=1)

        return mat, meta

    def calculate_intervals(self, X, times):
        downs = np.where(self.get_down_times(times))
        ups = [0] + (downs + 1)
        partitions = []
        for start, end in zip(ups, downs):
            partitions.append(X[start:end])

        intervals = []

        for i, part in enumerate(partitions):
            offset = ups[i]
            model = "l1"  # "l2", "rbf"
            algo = rpt.BottomUp(model=model, min_size=1, jump=1).fit(X)
            breaks = algo.predict(pen=np.log(X.shape[0])*X.shape[1]*2**2)
            breaks += offset
            intervals.append(zip([0] + breaks[:-1], breaks[1:]))

        return intervals

    def update_models(self, labels, start_time, end_time=None):
        imreader = ImageReader()

        if end_time is None:
            end_time = time.time()

        imdata, times = imreader.read_db(self.username, start_time, end_time, self.cams, skip_absent=False)

        if len(imdata) == 0:
            return None, None
        else:
            X, meta = self.create_image_matrix(imdata)
            intervals = self.calculate_intervals(X, times)
            train_labels = {}

            for mode, label_set in labels.items():
                if len(label_set) <= 0:
                    label_data = {"raw": np.array([]), "augmented": np.array([]), "intervals": [], "indices": []}
                    m, m_breaks = None, []
                else:
                    m, label_data, m_breaks = self.learn_model(times, X, label_set, breaks)

                self.models[mode] = m
                train_labels[mode] = label_data
                mode_breaks[mode] = m_breaks

            misc = {}
            misc["matrix"] = X
            misc["times"] = times
            misc["raw_data"] = imdata
            misc["meta"] = meta
            misc["breaks"] = breaks
            misc["train_labels"] = train_labels
            misc["mode_breaks"] = mode_breaks

            return self.models, misc

    def predict(self, mode, images):
        clf = self.models[mode]
        pose_mat, act_mat = self.data2vec.vectorize(images)
        input_mat = np.concatenate([act_mat, pose_mat], axis=1)
        probs = clf.predict_proba(input_mat)
        pred_labels = clf.classes_[np.argmax(probs, axis=1)]
        confidences = np.max(probs, axis=1)

        return pred_labels, confidences
