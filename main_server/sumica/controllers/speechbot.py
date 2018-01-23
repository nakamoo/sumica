import json
import datetime
import time

from controllers.controller import Controller
from server_actors import chatbot_actor
import utils


class Speechbot(Controller):
    def __init__(self, username):
        super().__init__(username)

        self.cmds = []
        self.fb_id = utils.get_fb_id(username)

    def on_event(self, event, data):
        if event == "speech" and data["type"] == "speech":
            msg = data["text"]

            if "何時" in msg:
                now = datetime.datetime.now()
                send = "サーバの時間は" + str(now.hour) + "時" + str(now.minute) + "分です"
                self.cmds.append({"platform": "tts", "data": send})
            elif msg.startswith("リピート"):
                self.cmds.append({"platform": "tts", "data": "".join(data["text"].strip().split()[1:])})

            chatbot_actor.send_fb_message(self.fb_id, "You said: %s" % data["text"])

    def execute(self):
        yield self.cmds

        self.cmds = []
