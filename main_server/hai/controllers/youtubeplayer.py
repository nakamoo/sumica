from .controller import Controller


class YoutubePlayer(Controller):
    def __init__(self):
        self.re = None

    def on_event(self, event, data):
        if event == "chat":
            msg = data["message"]["text"].split()
            if msg[0] == "music":
                if msg[1] == "play":
                    self.re = list()
                    self.re.append({"platform": "play_youtube", "data": msg[2]})
                if msg[1] == "stop":
                    self.re = list()
                    self.re.append({"platform": "stop_youtube", "data": ""})

    def execute(self):
        if self.re is not None:
            re = self.re
            self.re = None
            return re
        else:
            return []
