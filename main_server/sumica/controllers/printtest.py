from .controller import Controller
from server_actors import chatbot
import database as db
import json
import time

class PrintTest(Controller):
    def __init__(self, user):
        self.fb_id = None
        self.user = user
        
        n = db.mongo.fb_users.find_one({"id": user})
        if n:
            self.fb_id = n["fb_id"]

    def on_event(self, event, data):
        if event == "chat":
            msg = data["message"]["text"]

            if msg.startswith("print"):
                data = {"user_name": self.user, "text": msg[6:], "time": time.time()}
                db.mongo.print.insert_one(data)
                chatbot.send_fb_message(self.fb_id, "stored text")

    def execute(self):
        return []

