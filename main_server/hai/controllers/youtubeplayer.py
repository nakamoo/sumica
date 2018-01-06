import time
from .controller import Controller
from database import mongo
from datetime import datetime


def predict():
    minute = datetime.now().minute
    return minute % 2, 0.7


def predict():
    minute = datetime.now().minute
    return minute % 2, 0.7

class YoutubePlayer(Controller):
    def __init__(self, user):
        self.re = []
        self.user = user
        self.classes = ['ホワイトノイズ', False]
        self.state = False
        self.ask_time = 0
        self.duration = 600
        self.wait = False

    def on_event(self, event, data):
        if event == "image":
            if not self.wait and time.time() - self.ask_time > self.duration:
                index, confidence = predict()
                if self.state != self.classes[index]:
                    self.wait = True
                    self.ask_time = time.time()
                    if self.classes[index]:
                        self.re = [{"platform": "play_youtube", "data": self.classes[index],
                                    "confirmation": self.classes[index] + "を再生しますか?"}]
                    else:
                        self.re = [{"platform": "stop_youtube", "data": '',
                                    "confirmation": "音楽をけしますか?"}]

            if time.time() - self.ask_time > self.duration:
                self.wait = False

        if event == 'confirmation':
            if data['platform'] == 'play_youtube':
                self.wait = False
                if 'answer' in data:
                    if data['answer']:
                        self.state = data['data']
            if data['platform'] == 'stop_youtube':
                self.wait = False
                if 'answer' in data:
                    if data['answer']:
                        self.state = False

        if event == "speech" and data["type"] == "speech":
            msg = data["text"]
            if 'ホワイトノイズ' in msg:
                keyword = 'ホワイトノイズ'
                self.re.append({"platform": "tts", "data": keyword+"を検索して再生します"})
                self.re.append({"platform": "play_youtube", "data": keyword})
                self.state = keyword
            # if "を流" in msg:
            #     keyword = msg[:msg.find('を流')]
            #     self.re.append({"platform": "tts", "data": keyword+"を検索して再生します"})
            #     self.re.append({"platform": "play_youtube", "data": keyword})
            if ("消して" in msg) or ('止めて' in msg):
                self.re.append({"platform": "tts", "data": "音楽を消します"})
                self.re.append({"platform": "stop_youtube", "data": ''})
                self.state = False

        if event == "chat":
            msg = data["message"]["text"].split()
            if msg[0] == "music":
                if msg[1] == "play":
                    self.re = [{"platform": "play_youtube", "data": msg[2],
                                "confirmation": msg[2] + "を再生しますか?"}]
                if msg[1] == "stop":
                    self.re = [{"platform": "stop_youtube", "data": '',
                                "confirmation": "音楽をけしますか?"}]

                inserted_data = dict()
                inserted_data['message'] = msg
                inserted_data['user_name'] = self.user
                inserted_data['time'] = time.time()
                mongo.music.insert_one(inserted_data)

    def execute(self):
        if self.re:
            re = self.re
            self.re = []
            self.log_operation(re)
            return re
        else:
            return []
