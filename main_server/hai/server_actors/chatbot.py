import requests

fb_token = "EAAF0dXCeCJwBANZB6PIdJYHmpsvoRDMj8bZCMZAjZB3eZCosq69BS1yR2cSsFCrkxrsWtvzjgeJZCMaVt73sYz5CP98nBQlrxVxm7QSHMxyUpjCTkn69EZA4xymrEpBmGIVTl7RZAJDJwvoo49CZCvzdMQ0A8hF0vomiQqL3yH9o34t569ZA51nHUn"

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
