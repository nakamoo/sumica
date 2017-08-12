from .controller import Controller
from server_actors import chatbot

class Chatbot(Controller):
    def __init__(self, user):
        self.fb_id = None
        import hai
        with hai.app.app_context():
          n = hai.db.fb_users.find_one({"id": user})
          if n:
            self.fb_id = n["fb_id"]

    def on_event(self, event, data):
        if event == "chat" and self.fb_id:
            msg = data["message"]["text"]

            if msg == "sudo reset fb":
              import hai
              hai.db.fb_users.delete_one({"fb_id": self.fb_id})
              chatbot.send_fb_message(self.fb_id, "resetting fb db")
            else:
              chatbot.send_fb_message(self.fb_id, "hi!")

    def execute(self):
        pass

def on_global_event(event, data):
    import hai

    if event == "chat":
        msg = data["message"]["text"].lower()
        fb_id = data["sender"]["id"]

        #has_id = hai.mongo.fb_users.find({"fb_id": fb_id, "id": {'$exists': True}}).count() > 0

        #print("received msg", msg, "from", event["sender"]["id"])

        if msg.startswith("i am"):
            _id = msg.split()[-1]

            if _id in hai.controllers_objects:
                data = {"fb_id": fb_id, "id": _id}
                hai.db.fb_users.insert_one(data)
                hai.controllers_objects[_id]["chatbot"].fb_id = fb_id
                chatbot.send_fb_message(fb_id, "hi " + _id)
            else:
                chatbot.send_fb_message(fb_id, _id + " is not in the database")
        elif msg.startswith("who am i"):
            chatbot.send_fb_message(fb_id, "i dont know")
        else:
            chatbot.send_fb_message(fb_id, "who are you?")
