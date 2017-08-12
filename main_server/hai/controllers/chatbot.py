from .controller import Controller

class Chatbot(Controller):
    def __init__(self):
        self.fb_id = None

    def on_event(self, event, data):
        if event == "chat" and fb_id:
            chatbot.send_fb_message(self.fb_id, "hi!")

    def execute(self):
        return {}

def on_global_event(event, data):
    import hai

    if event == "unknown chat":
        msg = event["message"]["text"].lower()
        fb_id = event["sender"]["id"]

        #has_id = len(hai.mongo.fb_users.find({"fb_id": fb_id, "id": {'$exists': True}})) > 0

        print("received msg", msg, "from", event["sender"]["id"])

        if msg.startswith("i am"):
            _id = msg.split()[-1]

            if _id in hai.controllers_objects:
                data = {"fb_id": fb_id, "id": _id}
                hai.mongo.fb_users.insert_one(data)
                chatbot.send_fb_message(fb_id, "hi " + _id)
            else:
                chatbot.send_fb_message(fb_id, _id + " is not in the database")
        elif msg.startswith("who am i"):
            chatbot.send_fb_message(fb_id, "i dont know")
        else:
            chatbot.send_fb_message(fb_id, "who are you?")