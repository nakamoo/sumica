import requests
from flask import Flask

app = Flask(__name__)
app.config.from_pyfile(filename="../application.cfg")

# fb_token = "EAACPbD64AjUBAMhcfZCXbQoYuEmjZCQavHnaoG0MpcZCqo9waS5nXVuzuZBDLS5W9iEgcP3DvMuS92uJG3hlmSWoAyXzVt8wIYtbCdYj0LzAXiZAFv98QxMmoHojU8lrevGZAEBChHHMiq1IgYcpUOzOwpZAAjZCxF3IKO3XUnbiVMOYTdMqvgXJ"
fb_token = app.config['FB_TOKEN']

def send_fb_message(id, text):
    data = {"access_token": fb_token}
    data2 = {"recipient": {"id": id}, "message": {"text": text}}
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=data, json=data2)
    print(r.text)

def send_fb_image(id, imurl):
    data = {"access_token": fb_token}
    data2 = {"recipient": {"id": id}, "message": {"attachment": {"type":"image",
     "payload": {"url": imurl}}}}
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=data, json=data2)
    print(r.text)
