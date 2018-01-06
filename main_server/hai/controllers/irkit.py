import time
from .controller import Controller
from database import mongo
from server_actors import chatbot
from datetime import datetime

# hue class
def predict():
    minute = datetime.now().minute
    return minute % 2, 0.7


class IRKit(Controller):
    def __init__(self, user):
        self.re = []
        self.user = user
        self.tv_on = False
        self.ask_time = 0
        self.duration = 600
        self.wait = False
        n = mongo.fb_users.find_one({"id": user})
        if n:
            self.fb_id = n["fb_id"]
        self.classes = [True, False]

    def on_event(self, event, data):
        if event == "image":
            if not self.wait and time.time() - self.ask_time > self.duration:
                index, confidence = predict()
                predicted_on = self.classes[index]
                if self.tv_on and (not predicted_on):
                    self.wait = True
                    self.ask_time = time.time()
                    self.re.append({"platform": "irkit", "data": ['TV', 'off'],
                                    "confirmation": "テレビをけしますか?"})
                elif (not self.tv_on) and predicted_on:
                    self.wait = True
                    self.ask_time = time.time()
                    self.re.append({"platform": "irkit", "data": ['TV', 'on'],
                                    "confirmation": "テレビをつけますか?"})

            if time.time() - self.ask_time > self.duration:
                self.wait = False

        if event == 'confirmation':
            if data['platform'] == 'irkit':
                self.wait = False
                if 'answer' in data:
                    if data['confirmation'] == 'テレビをつけますか?' and data['answer']:
                        self.tv_on = True
                    if data['confirmation'] == 'テレビをけしますか?' and data['answer']:
                        self.tv_on = False

        if event == "chat":
            msg = data["message"]["text"].split()
            if msg[0] == "irkit":
                if msg[1] == "TV":
                    if msg[2] == "on":
                        if self.tv_on:
                            chatbot.send_fb_message(self.fb_id, "TVは既についています")
                        else:
                            self.re.append({"platform": "irkit", "data": msg[1:],
                                            "confirmation": "テレビをつけますか?"})
                    elif msg[2] == "off":
                        if self.tv_on:
                            self.re.append({"platform": "irkit", "data": msg[1:],
                                            "confirmation": "テレビをけしますか?"})
                        else:
                            chatbot.send_fb_message(self.fb_id, "TVはすでにきえています")

                elif msg[1] == "AirConditioning":
                    pass

        if event == "speech" and data["type"] == "speech":
            msg = data["text"]
            if "テレビ" in msg and "つけて" in msg:
                if self.tv_on:
                    self.re.append({"platform": "tts", "data": "TVはすでについています"})
                else:
                    self.re.append({"platform": "tts", "data": "TVをつけます"})
                    self.re.append({"platform": "irkit", "data": ['TV', 'on']})
                    self.tv_on = True
            if "テレビ" in msg and "消して" in msg:
                if self.tv_on:
                    self.re.append({"platform": "tts", "data": "TVを消します"})
                    self.re.append({"platform": "irkit", "data": ['TV', 'off']})
                    self.tv_on = False
                else:
                    self.re.append({"platform": "tts", "data": "TVは既に消えています"})

    def execute(self):
        if self.re:
            re = self.re
            self.re = []
            self.log_operation(re)
            return re
        else:
            return []
