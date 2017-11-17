import time
from .controller import Controller
from database import mongo


class YoutubePlayer(Controller):
    def __init__(self, user_name):
        self.re = None
        self.user_name = user_name

    def on_event(self, event, data):
        if event == "chat":
            msg = data["message"]["text"].split()
            if msg[0] == "music":
                if msg[1] == "play":
                    self.re = [{"platform": "play_youtube", "data": msg[2]}]
                if msg[1] == "stop":
                    self.re = [{"platform": "stop_youtube", "data": ""}]

                inserted_data = dict()
                inserted_data['message'] = msg
                inserted_data['user_name'] = self.user_name
                inserted_data['time'] = time.time()
                mongo.music.insert_one(inserted_data)

    def execute(self):
        if self.re is not None:
            re = self.re
            self.re = None
            self.log_operation(re)
            return re
        else:
            return []
