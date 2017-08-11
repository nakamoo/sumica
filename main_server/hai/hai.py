from flask import Flask, render_template, request, jsonify
from flask_pymongo import PyMongo

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


@app.route('/')
def home_page():
    return render_template('index.html')


@app.route('/data/image')
def get_image_data():
    return "Not implemented", 404

def trigger_controllers(user, event, data):
    for c in controllers_objects[user]:
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
