import time
from .controller import Controller
from database import mongo


class IRKit(Controller):
    def __init__(self, user):
        self.re = None
        self.user = user

    def on_event(self, event, data):
        if event == "chat":
            msg = data["message"]["text"].split()
            if msg[0] == "irkit":
                if msg[1] == "TV" or msg[1] == "AirConditioning":
                    self.re = [{"platform": "irkit", "data": msg[1:]}]

                inserted_data = dict()
                inserted_data['message'] = msg
                inserted_data['device'] = msg[1]
                inserted_data['user'] = self.user
                inserted_data['time'] = time.time()
                mongo.irkit.insert_one(inserted_data)

    def execute(self):
        if self.re is not None:
            re = self.re
            self.re = None
            self.log_operation(re)
            return re
        else:
            return []