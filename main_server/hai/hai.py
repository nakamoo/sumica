from flask import Flask, render_template, request, jsonify
from flask_pymongo import PyMongo
import json
import requests
import uuid

from controllers.controller import Sample
from controllers.detection import Detection

app = Flask(__name__)
mongo = PyMongo(app)

def standard_controllers():
    return {"SampleController": Sample(),
            "detection": Detection()}

# TODO: use DB
controllers_objects = {}
controllers_objects['koki'] = standard_controllers()
controllers_objects['sean'] = standard_controllers()

# temporary
fb2user = {}

fb_token = "EAAF0dXCeCJwBANZB6PIdJYHmpsvoRDMj8bZCMZAjZB3eZCosq69BS1yR2cSsFCrkxrsWtvzjgeJZCMaVt73sYz5CP98nBQlrxVxm7QSHMxyUpjCTkn69EZA4xymrEpBmGIVTl7RZAJDJwvoo49CZCvzdMQ0A8hF0vomiQqL3yH9o34t569ZA51nHUn"

@app.route('/')
def home_page():
    return render_template('index.html')


@app.route('/data/image')
def get_image_data():
    return "Not implemented", 404

def trigger_controllers(user, event, data):
    for c in controllers_objects[user].values():
        c.on_event(event, data)

@app.route('/data/image', methods=['POST'])
def post_image_data():
    filename = str(uuid.uuid4()) + ".png"
    request.files['image'].save("./images/" + filename)
    data = request.form.to_dict()
    data['filename'] = filename
    mongo.db.images.insert_one(data)

    trigger_controllers(data['user_id'], "image", data)

    data.pop("_id")
    return jsonify(data), 201

def send_fb_message(id, text):
    data = {"access_token": fb_token}
    data2 = {"recipient": {"id": id}, "message": {"text": text}}
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=data, json=data2)
    print(r.text)

# messenger
@app.route('/data/fb', methods=['POST'])
def post_fb_data():
    data = request.form.to_dict()
    event = json.loads(data["event"])
    bot_id = "318910425200757"
    fb_id = event["sender"]["id"]
    msg = event["message"]["text"].lower()

    if fb_id != bot_id:
        print("received msg", msg, "from", event["sender"]["id"])

        # temporary (test)
        if msg.startswith("reset"):
            global fb2user
            fb2user = {}
        elif msg.startswith("i am"):
            fb2user[fb_id] = msg.split()[-1]
            send_fb_message(fb_id, "hi " + msg.split()[-1])
        elif msg.startswith("who am i"):
            if fb_id in fb2user:
                send_fb_message(fb_id, "you are " + fb2user[fb_id])
            else:
                send_fb_message(fb_id, "i dont know")
        elif fb_id not in fb2user:
            send_fb_message(fb_id, "who are you?")
        else:
            send_fb_message(event["sender"]["id"], "what")

    return "Not implemented", 404

@app.route('/data/hue')
def get_hue_data():
    return "Not implemented", 404


@app.route('/data/hue', methods=['POST'])
def post_hue_data():
    data = request.form.to_dict()
    mongo.db.hue.insert_one(data)
    data.pop("_id")
    return jsonify(data), 201


@app.route('/data/youtube')
def get_youtube_data():
    return "Not implemented", 404


@app.route('/data/youtube', methods=['POST'])
def post_youtube_data():
    data = request.form.to_dict()
    mongo.db.youtube.insert_one(data)
    data.pop("_id")
    return jsonify(data), 201


@app.route('/controllers')
def get_controllers():
    return "Not implemented", 404


@app.route('/controllers/update', methods=['POST'])
def update_controllers():
    return "Not implemented", 404


@app.route('/controllers/execute', methods=['POST'])
def execute_controllers():
    user_id = request.form['user_id']
    commands = {}
    for c, i in controllers_objects[user_id].items():
        cmd = i.execute()
        if cmd is not None:
            commands[c] = cmd

    return jsonify(commands), 201


@app.route('/controllers/<controller_name>/execute', methods=['POST'])
def execute_specific_controller():
    return "Not implemented", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
