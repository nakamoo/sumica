import json
import utils
import time

from controllers.controller import Controller
from server_actors import chatbot_actor
import controllermanager as cm
from utils import db


class Chatbot(Controller):
    def __init__(self, username):
        super().__init__(username)

        self.fb_id = utils.get_fb_id(username)

        self.lights = None
        self.cmds = []

    def on_event(self, event, data):
        if event == "chat" and self.fb_id:
            msg = data["message"]["text"]

            if msg == "delete id":
                db.fb_users.delete_one({"fb_id": self.fb_id})
                chatbot_actor.send_fb_message(self.fb_id, "データベースから削除しました")
            elif msg == "help":
                chatbot_actor.send_fb_message(self.fb_id, "どうも！ボットです！よろしくお願いします！")
            elif msg == "hue on":
                chatbot_actor.send_fb_message(self.fb_id, "電気をつけます")
                self.lights = True
            elif msg == "hue off":
                chatbot_actor.send_fb_message(self.fb_id, "電気を消します")
                self.lights = False
            elif msg.split()[0] == "say":
                self.cmds.append({"platform": "tts", "data": "".join(msg.strip().split()[1:])})
            elif msg.split()[0] == "label":
                db.labels.insert_one({"username": self.username, "time": time.time(), "label": msg.split()[1]})
                chatbot_actor.send_fb_message(self.fb_id, "「{}」を記録しました".format(msg.split()[1]))
            else:
                chatbot_actor.send_fb_message(self.fb_id, "どうも！")

    def execute(self):
        if self.lights is not None:
            def hue_format(hue_state):
                if hue_state["on"]:
                    return hue_state
                else:
                    return {"on": False}

            data = json.dumps([
                {"id": "1", "state": hue_format({"on": self.lights})},
                {"id": "2", "state": hue_format({"on": self.lights})},
                {"id": "3", "state": hue_format({"on": self.lights})}
            ])

            self.cmds.append({"platform": "hue", "data": data})

            # TODO
            #self.log_operation(re)

        yield self.cmds

        self.cmds = []
        self.lights = None


    def on_global_event(event, data):
        if event == "chat":
            msg = data["message"]["text"].lower()
            fb_id = data["sender"]["id"]

            if msg.startswith("私は"):
                username = msg.split("私は")[-1]

                if username in db.cons.keys():
                    data = {"fb_id": fb_id, "username": username}
                    db.fb_users.insert_one(data)
                    chatbot_actor.send_fb_message(fb_id, username + "さんこんにちは！")
                else:
                    chatbot_actor.send_fb_message(fb_id, _id + " はデータベースに入っていません")
            elif msg.startswith("私は誰？"):
                chatbot_actor.send_fb_message(fb_id, "わからないです")
            else:
                chatbot_actor.send_fb_message(fb_id, "誰ですか？（私は〜〜）")
