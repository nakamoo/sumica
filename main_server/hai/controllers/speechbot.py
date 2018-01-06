from .controller import Controller
from server_actors import chatbot
import database as db
import json
import datetime
import time

class Speechbot(Controller):
    def __init__(self, user):
        self.lights = None
        self.cmds = []
        self.tag = ""
        self.user = user
        
        n = db.mongo.fb_users.find_one({"id": user})
        if n:
            self.fb_id = n["fb_id"]

    def on_event(self, event, data):
        if event == "speech" and data["type"] == "speech":
            msg = data["text"]

            if "電気" in msg and "つけて" in msg:
                self.cmds.append({"platform": "tts", "data": "電気をつけます"})
                self.lights = True
            elif "電気" in msg and "消して" in msg:
                self.cmds.append({"platform": "tts", "data": "電気を消します"})
                self.lights = False
            elif "何時" in msg:
                now = datetime.datetime.now()
                send = "サーバの時間は" + str(now.hour) + "時" + str(now.minute) + "分です"
                self.cmds.append({"platform": "tts", "data": send})
            elif msg.startswith("記録"):
                if "記録　" in msg or "記録 " in msg:
                    label = msg[3:]
                else:
                    label = msg[2:]
                self.cmds.append({"platform": "tts", "data": label + "を記録しました"})
                log_data = {"time": time.time(), "user": self.user, "type": "label", "label": label}
                db.mongo.events.insert_one(log_data)
            elif msg.startswith("リピート"):
                self.cmds.append({"platform": "tts", "data": "".join(data["text"].strip().split()[1:])})

            chatbot.send_fb_message(self.fb_id, "You said: %s" % data["text"])

    def execute(self):
        re = []

        re.extend(self.cmds)
        if self.lights is not None:
            l = self.lights
            self.lights = None

            def format(hue_state):
                if hue_state["on"]:
                    return hue_state
                else:
                    return {"on": False}

            data = json.dumps([
                    {"id": "1", "state":format({"on": l})},
                    {"id": "2", "state":format({"on": l})},
                    {"id": "3", "state":format({"on": l})}
                ])

            re.append({"platform": "hue", "data": data})
        
        self.cmds = []
        if re:
            self.log_operation(re)
        return re
