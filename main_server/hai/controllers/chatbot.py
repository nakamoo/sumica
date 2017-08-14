from .controller import Controller
from server_actors import chatbot
import database as db

class Chatbot(Controller):
    def __init__(self, user):
        self.fb_id = None
        
        n = db.mongo.fb_users.find_one({"id": user})
        if n:
            self.fb_id = n["fb_id"]

        self.lights = None

    def on_event(self, event, data):
        if event == "chat" and self.fb_id:
            msg = data["message"]["text"]

            if msg == "delete id":
              db.mongo.fb_users.delete_one({"fb_id": self.fb_id})
              chatbot.send_fb_message(self.fb_id, "データベースから削除しました")
            elif msg == "help":
              chatbot.send_fb_message(self.fb_id, "どうも！ボットです！よろしくお願いします！")
            elif msg == "hue on":
              chatbot.send_fb_message(self.fb_id, "では電気をつけます")
              self.lights = True
            elif msg == "hue off":
              chatbot.send_fb_message(self.fb_id, "では電気を消します")
              self.lights = False
            else:
              chatbot.send_fb_message(self.fb_id, "どうも！")

    def execute(self):
        if self.lights is not None:
            l = self.lights
            self.lights = None

            return [{"platform": "hue", "data": '{"on": {}}'.format(str(l).lower())}]
        else:
            return []

def on_global_event(event, data):
    if event == "chat":
        msg = data["message"]["text"].lower()
        fb_id = data["sender"]["id"]

        if msg.startswith("私は"):
            _id = msg.split("私は")[-1]

            if _id in hai.controllers_objects:
                data = {"fb_id": fb_id, "id": _id}
                db.mongo.fb_users.insert_one(data)
                db.controllers_objects[_id]["chatbot"].fb_id = fb_id
                chatbot.send_fb_message(fb_id, _id + "さんこんにちは！")
            else:
                chatbot.send_fb_message(fb_id, _id + " はデータベースに入っていません")
        elif msg.startswith("私は誰？"):
            chatbot.send_fb_message(fb_id, "わからないです")
        else:
            chatbot.send_fb_message(fb_id, "誰ですか？（私は〜〜）")
