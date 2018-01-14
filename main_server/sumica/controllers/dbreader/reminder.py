import time
from datetime import datetime


from .controller import Controller


def predict():
    minute = datetime.now().minute
    return minute % 2, 0.7

class Reminder(Controller):
    def __init__(self):
        self.classes = ['勉強', '睡眠']
        pass


    def on_event(self, event, data):
        if event == "image":



