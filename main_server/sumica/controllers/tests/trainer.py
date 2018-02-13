from collections import Counter
import time

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import SGDClassifier
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.neighbors import KNeighborsClassifier
import numpy as np


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

def clf_instance():
    #clf = SGDClassifier(loss='log', max_iter=100)
    #logreg = LogisticRegression(class_weight="balanced")
    # logreg = KNeighborsClassifier()
    logreg = RandomForestClassifier(n_estimators=5, class_weight="balanced")
    # pca = PCA(50)
    return Pipeline([('clf', logreg)])

class Trainer:
    def __init__(self):
        self.train_x = None
        self.train_y = None
        self.clf = None
        self.train_info = None
        self.label_set = None
        self.last_update = 0

    def learn_model(self, x_times, x, label_set, segments, segment_times):
        t = time.time()
        update_model = True

        # TODO better update necessity check
        # e.g. if all labels are the same as last time and are on the same fixed segments, update_model=False

        self.label_set = label_set
        y_times = np.array([t[0] for t in label_set])
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
            # if x_indices[i] == 0:
            #    c += 1

            prev_label = label_mat[y_indices[i]]

            if prev_label != -1 and (counts[y[i]] < counts[prev_label] or (
                    counts[y[i]] == counts[prev_label] and assigned[y[i]] < assigned[prev_label])):
                print(
                "warning: overwriting segment w/ label {} ({}) to {} ({})".format(prev_label, counts[prev_label], y[i],
                                                                                  counts[y[i]]))
                assigned[prev_label] -= 1

            label_mat[segments[segment_i][0]:segments[segment_i][1]] = y[i]
            assigned[y[i]] += 1

        self.train_info = {"raw": sparse_labels, "augmented": label_mat, "indices": y_indices, "seg_mapping": seg_indices.tolist()}

        print("data prepared", time.time()-t)
        t = time.time()

        # take out remaining unlabeled data
        labeled_mask = label_mat != -1

        labeled_x = x[labeled_mask]
        labeled_y = label_mat[labeled_mask]

        if np.array_equal(labeled_x, self.train_x) and np.array_equal(labeled_y, self.train_y):
            update_model = False
        else:
            self.train_x = labeled_x
            self.train_y = labeled_y

            if len(labeled_x) > 0:
                #logreg = LogisticRegression(class_weight="balanced")
                #logreg = KNeighborsClassifier()
                #logreg = RandomForestClassifier(n_estimators=10, class_weight="balanced")
                #pca = PCA(50)
                # self.clf = RandomForestClassifier(n_estimators=10, class_weight="balanced")

                self.clf = clf_instance()

                self.clf.fit(labeled_x, labeled_y)

                print("first fitted", time.time() - t)
                print(self.clf.score(labeled_x, labeled_y))
                t = time.time()

                semisup = True
                if semisup:
                    pseudo = self.clf.predict(x)
                    print("labeled size:", labeled_x.shape)
                    self.clf = self.pseudolabel(x, pseudo, segments)
                    print("pseudo fitted", time.time() - t)

        return self.clf, self.train_info, update_model

    def pseudolabel(self, x, pseudo, segments):
        from scipy import stats
        print("DATA SIZE", x.shape)
        #mask = np.random.choice(np.arange(x.shape[0]), 10000)

        new_labels = np.zeros_like(pseudo)

        for start, end in segments:
            if end - start > 0:
                #print(start, end, new_labels.shape, new_labels[start:end].shape)
                new_labels[start:end] = stats.mode(pseudo[start:end])[0][0]

        clf = clf_instance()
        clf.fit(x[-10000:], new_labels[-10000:])

        return clf