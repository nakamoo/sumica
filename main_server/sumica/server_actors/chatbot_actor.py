import requests

from config import Config

fb_token = Config.FB_TOKEN


def send_fb_message(fb_id, text):
    data = {"access_token": fb_token}
    data2 = {"recipient": {"id": fb_id}, "message": {"text": text}}
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=data, json=data2)
    print(r.text)


def send_fb_image(fb_id, imurl):
    data = {"access_token": fb_token}
    data2 = {"recipient": {"id": fb_id}, "message": {"attachment": {"type": "image",
                                                                    "payload": {"url": imurl}}}}
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=data, json=data2)
    print(r.text)
