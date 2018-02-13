import time
from datetime import datetime

from .controller import Controller
from server_actors import tts_actor


class Reminder(Controller):
    def __init__(self, username):
        super(Reminder).__init__(username)

        self.username = username
        self.get_schedules()
        self.response = []
        self.operation_time = 0
        self.operation_interval = 60 * 5

    # TODO: get from DB
    def get_schedules(self):
        self.schedules = [{'start': time.time(), 'end': time.time() + 10e9, 'activity': '研究'},
                          {'start': time.time()+10e9, 'end': time.time() + 10e10, 'activity': '睡眠'}]

    def get_current_schedule(self):
        for sc in self.schedules:
            if sc['start'] <= time.time() <= sc['end']:
                return sc['activity']
        return None

    # TODO: change function name
    def check(self):
        if time.time() - self.operation_time > self.operation_interval:
            current_schedule = self.get_current_schedule()
            if current_schedule and current_schedule != get_current_activity():
                return True
        return False

    def on_event(self, event, data):
        if event == "image":
            if self.check():
                self.operation_time = time.time()
                current_schedule = self.get_current_schedule()
                self.response.append(tts_actor.speech(
                    "今は" + current_schedule + "をする時間ではないですか？"))

    def execute(self):
        response = self.response
        self.response = []
        return response




