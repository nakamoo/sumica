import time
from datetime import datetime

from .controller import Controller
from server_actors import tts_actor


def get_current_activity():
    minute = datetime.now().minute
    classes = ['勉強', '睡眠']
    return classes[minute % 2]


class Alarm(Controller):
    def __init__(self, username):
        self.username = username
        self.get_time_to_wake_up()
        self.response = []
        self.operation_time = 0
        self.operation_interval = 10
        self.monitor_time = 3 * 60 * 60

    # TODO: get from DB
    def get_time_to_wake_up(self):
        self.time_to_wake_up = time.time()

    # TODO: change function name
    def check(self):
        if time.time() - self.operation_time > self.operation_interval:
            if self.time_to_wake_up <= time.time() <= self.time_to_wake_up + self.monitor_time:
                if get_current_activity() != '睡眠':
                    return True
        return False

    def on_event(self, event, data):
        if event == "image":
            if self.check():
                self.operation_time = time.time()
                self.response.append(tts_actor.speech("起きてーーーーーーーー"))

    def execute(self):
        response = self.response
        self.response = []
        return response



