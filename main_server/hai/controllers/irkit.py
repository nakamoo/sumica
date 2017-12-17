import time
from .controller import Controller
from database import mongo
from server_actors import chatbot


class IRKit(Controller):
    def __init__(self, user):
        self.re = None
        self.user = user
        self.tv_on = False
        n = mongo.fb_users.find_one({"id": user})
        if n:
            self.fb_id = n["fb_id"]

    def on_event(self, event, data):
        if event == "chat":
            msg = data["message"]["text"].split()
            if msg[0] == "irkit":
                if msg[1] == "TV":
                    if msg[2] == "on":
                        if self.tv_on:
                            chatbot.send_fb_message(self.fb_id, "TVは既についています")
                        else:
                            chatbot.send_fb_message(self.fb_id, "TVをつけます")
                            self.re = [{"platform": "irkit", "data": msg[1:]}]
                            self.tv_on = True
                    elif msg[2] == "off":
                        if self.tv_on:
                            chatbot.send_fb_message(self.fb_id, "TVをけします")
                            self.re = [{"platform": "irkit", "data": msg[1:]}]
                            self.tv_on = False
                        else:
                            chatbot.send_fb_message(self.fb_id, "TVは既にきえています")

                elif msg[1] == "AirConditioning":
                    pass

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