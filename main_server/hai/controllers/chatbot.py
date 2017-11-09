from .controller import Controller
from server_actors import chatbot
import database as db
import json

class Chatbot(Controller):
    def __init__(self, user):
        self.fb_id = None
        self.user = user
        
        n = db.mongo.fb_users.find_one({"id": user})
        if n:
            self.fb_id = n["fb_id"]

        self.lights = None
        self.tag = ""

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
            elif msg.startswith("tag"):
              self.tag = msg.split()[-1]
            elif msg == "am i here":
              n = db.mongo.detections.find({"user_name": self.user}).sort([("time",-1)]).limit(1)
              here = False
              for obj in n.next()["detections"]["objects"]:
                  if obj["label"] == "person":
                      here = True
                      break
              if here:
                  chatbot.send_fb_message(self.fb_id, "yes")
              else:
                  chatbot.send_fb_message(self.fb_id, "no")

            else:
              chatbot.send_fb_message(self.fb_id, "どうも！")
        elif event == "image":
            db.mongo.images.update_one({"_id": data["_id"]}, {'$set': {'tag': self.tag}}, upsert=False)

    def execute(self):
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

            return [{"platform": "hue", "data": data}]
        else:
            return []

def on_global_event(event, data):
    if event == "chat":
        msg = data["message"]["text"].lower()
        fb_id = data["sender"]["id"]

        if msg.startswith("私は"):
            _id = msg.split("私は")[-1]

            if _id in db.controllers_objects:
                data = {"fb_id": fb_id, "id": _id}
                db.mongo.fb_users.insert_one(data)
                db.controllers_objects[_id][2].fb_id = fb_id
                chatbot.send_fb_message(fb_id, _id + "さんこんにちは！")
            else:
                chatbot.send_fb_message(fb_id, _id + " はデータベースに入っていません")
        elif msg.startswith("私は誰？"):
            chatbot.send_fb_message(fb_id, "わからないです")
        else:
            chatbot.send_fb_message(fb_id, "誰ですか？（私は〜〜）")
