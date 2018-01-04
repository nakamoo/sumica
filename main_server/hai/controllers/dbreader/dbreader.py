import numpy as np

class DBReader(object):
    def __init__(self, user):
        self.user = user

    def read_db(self, start=0, end=9999999999999):
        # X = [(collection0, collection1), ()...()]
        # y = ['study', 'study'.....'bed']
        # return X, y
        return [], []