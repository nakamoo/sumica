import numpy as np


class Trainer(object):
    def __init__(self, user):
        self.user = user
        self.classes = None

    def train(self, X, y):
        # X = [(collection0, collection1), ()...()]
        # y = ['study', 'study'.....'bed']
        # return X(np.array), y(list)
        pass

    def predict(self, X):
        # X is vector
        # return 'study'
        pass

