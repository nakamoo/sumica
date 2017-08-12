from .controller import Controller

class Chatbot(Controller):
    def __init__(self):
        pass

    def on_event(self, event, data):
        if event == "user chat":
            msg = event["message"]["text"].lower()

            print("received msg", msg, "from", event["sender"]["id"])

            # temporary (test)
            if msg.startswith("reset"):
                global fb2user
                fb2user = {}
            elif msg.startswith("i am"):
                fb2user[fb_id] = msg.split()[-1]
                chatbot.send_fb_message(fb_id, "hi " + msg.split()[-1])
            elif msg.startswith("who am i"):
                if fb_id in fb2user:
                    chatbot.send_fb_message(fb_id, "you are " + fb2user[fb_id])
                else:
                    chatbot.send_fb_message(fb_id, "i dont know")
            elif fb_id not in fb2user:
                chatbot.send_fb_message(fb_id, "who are you?")
            else:
                chatbot.send_fb_message(event["sender"]["id"], "what")

    def execute(self):
        pass
