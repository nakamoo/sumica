import time
from .controller import Controller
from database import mongo


class IRKit(Controller):
    def __init__(self, user_name):
        self.re = None
        self.user_name = user_name

    def on_event(self, event, data):
        if event == "chat":
            msg = data["message"]["text"].split()
            if msg[0] == "irkit":
                if msg[1] == "TV" or msg[1] == "AirConditioning":
                    self.re = [{"platform": "irkit", "data": msg[1:]}]

                inserted_data = dict()
                inserted_data['message'] = msg
                inserted_data['device'] = msg[1]
                inserted_data['user_name'] = self.user_name
                inserted_data['time'] = time.time()
                mongo.irkit.insert_one(inserted_data)

    def execute(self):
        if self.re is not None:
            re = self.re
            self.re = None
            return re
        else:
            return []