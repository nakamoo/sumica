from itertools import chain
import pickle

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn import linear_model
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.externals import joblib

from controllers.learner.img2vec import NNFeatures


def process_posefeature(img):
    try:
        if len(img['pose']['body']) == 1:
            return list(chain.from_iterable(img['pose']['body'][0]))
        else:
            return [0] * 54
    except:
        return [0] * 54

class LogReg():
    def __init__(self, input_data, label):
        self.nn = NNFeatures()
        self.classifier = None
        self.input_data = input_data
        self.label = label
        self.X, self.y = self.create_feature()

    def data_update(self, input_data, label):
        self.input_data = input_data
        self.label = label
        self.X, self.y = self.create_feature()
        self.classifier = None

    def create_feature(self):
        X = []
        y = []
        for d, l in zip(self.input_data, self.label):
            X.append(self.vectorize(d))
            y.append(l)
        return X, y

    def vectorize(self, d):
        feature = []
        img0, img1 = d[0], d[1]
        feature.extend(process_posefeature(img0))
        feature.extend(process_posefeature(img1))
        return feature

    def train(self):
        X = np.array(self.X)
        y = np.array(self.y)

        clf = linear_model.LogisticRegression(C=1e5)
        # clf = RandomForestClassifier(n_estimators=10, class_weight="balanced")

        pipe = Pipeline([
            ("scale", StandardScaler()),
            ("pca", PCA(n_components=50)),
            ("clf", clf)
        ])

        pipe.fit(X, y)
        joblib.dump(pipe, 'hue_learner.pkl')
        self.classifier = pipe

    def predict(self, d):
        if self.classifier is None:
            self.train()
        X = self.vectorize(d)
        result = self.classifier.predict([X])[0]
        return result


