from .controller import Controller
from server_actors import chatbot
import random

class Chatbot(Controller):
    def __init__(self, user):
        self.fb_id = None
        import hai
        with hai.app.app_context():
          n = hai.db.fb_users.find_one({"id": user})
          if n:
            self.fb_id = n["fb_id"]

        self.lights = None
        self.id = random.random()
        print(self.id)

    def on_event(self, event, data):
        print(self.lights)
        print(self.id)
        if event == "chat" and self.fb_id:
            msg = data["message"]["text"]

            if msg == "sudo reset fb":
              import hai
              hai.db.fb_users.delete_one({"fb_id": self.fb_id})
              chatbot.send_fb_message(self.fb_id, "データベースから削除しました")
            elif msg == "help":
              chatbot.send_fb_message(self.fb_id, "どうも！ボットです！よろしくお願いします！")
            elif msg == "hue on":
              chatbot.send_fb_message(self.fb_id, "では電気をつけます")
              self.lights = True
              print(self.lights)
            elif msg == "hue off":
              chatbot.send_fb_message(self.fb_id, "では電気を消します")
              self.lights = False
            else:
              chatbot.send_fb_message(self.fb_id, "どうも！")

    def execute(self):
        print(self.id)
        print(self.lights)
        if self.lights is not None:
            l = self.lights
            self.lights = None
            return [{"platform": "hue", "data": {"on": l}}]
        else:
            return []

def on_global_event(event, data):
    import hai

    if event == "chat":
        msg = data["message"]["text"].lower()
        fb_id = data["sender"]["id"]

        #has_id = hai.mongo.fb_users.find({"fb_id": fb_id, "id": {'$exists': True}}).count() > 0

        #print("received msg", msg, "from", event["sender"]["id"])

        if msg.startswith("私は"):
            _id = msg.split("私は")[-1]

            if _id in hai.controllers_objects:
                data = {"fb_id": fb_id, "id": _id}
                hai.db.fb_users.insert_one(data)
                hai.controllers_objects[_id]["chatbot"].fb_id = fb_id
                chatbot.send_fb_message(fb_id, _id + "さんこんにちは！")
            else:
                chatbot.send_fb_message(fb_id, _id + " はデータベースに入っていません")
        elif msg.startswith("私は誰？"):
            chatbot.send_fb_message(fb_id, "わからないです")
        else:
            chatbot.send_fb_message(fb_id, "誰ですか？（私は〜〜）")
