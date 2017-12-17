from controllers.trainer.trainer import Trainer


class HueTrainer(Trainer):
    def __init__(self):
        pass

    def train(self, X, y):
        # X = [(collection0, collection1), ()...()]
        # y = ['study', 'study'.....'bed']
        # return X(np.array), y(list)
        pass

    def predict(self, X):
        # X is vector
        # return 'study'
        pass
