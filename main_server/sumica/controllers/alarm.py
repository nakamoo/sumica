from flask import current_app
import time
from datetime import datetime

import coloredlogs
import logging

from .controller import Controller
from server_actors import tts_actor

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)


def get_current_activity():
    minute = datetime.now().minute
    classes = ['勉強', '睡眠']
    return classes[minute % 2]


class Alarm(Controller):
    def __init__(self, username):
        self.username = username
        self.time_to_wake_up = -1
        self.response = []
        self.operation_time = 0
        self.operation_interval = 10
        self.monitor_time = 3 * 60 * 60

    def check(self, activity):
        if time.time() - self.operation_time > self.operation_interval:
            if self.time_to_wake_up <= time.time() <= self.time_to_wake_up + self.monitor_time:
                return activity == 'resting'
        return False

    def on_event(self, event, data):
        if event == "activity":
            if self.check(data):
                self.operation_time = time.time()
                self.response = [tts_actor.speech("起きる時間です")]

    def execute(self):
        yield self.response
        self.response = []



