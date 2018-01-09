import numpy as np


class Vectorizer(object):
    def __init__(self, user):
        self.user = user

    def vectorize(self, X, y=None):
        # X = [(collection0, collection1), ()...()]
        # y = ['study', 'study'.....'bed']
        # return X(np.array), y(list)
        if y is not None:
            return np.array(), y

        return np.array()