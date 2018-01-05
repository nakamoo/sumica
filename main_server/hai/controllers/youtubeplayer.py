import time
from .controller import Controller
from database import mongo


class YoutubePlayer(Controller):
    def __init__(self, user):
        self.re = []
        self.user = user

    def on_event(self, event, data):
        if event == "chat":
            msg = data["message"]["text"].split()
            if msg[0] == "music":
                if msg[1] == "play":
                    self.re = [{"platform": "play_youtube", "data": msg[2],
                                "confirmation": msg[2] + "を再生しますか?"}]
                if msg[1] == "stop":
                    self.re = [{"platform": "stop_youtube", "data": ""}]

                inserted_data = dict()
                inserted_data['message'] = msg
                inserted_data['user_name'] = self.user
                inserted_data['time'] = time.time()
                mongo.music.insert_one(inserted_data)

        if event == "speech" and data["type"] == "speech":
            msg = data["text"]
            if "を流" in msg:
                keyword = msg[:msg.find('を流')]
                self.re.append({"platform": "tts", "data": keyword+"を検索して再生します"})
                self.re.append({"platform": "play_youtube", "data": keyword})
            if "音楽を消し" in msg or '音楽を止めt ':
                self.re.append({"platform": "tts", "data": "音楽を消します"})
                self.re.append({"platform": "stop_youtube", "data": ''})

    def execute(self):
        if self.re:
            re = self.re
            self.re = []
            self.log_operation(re)
            return re
        else:
            return []
