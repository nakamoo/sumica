from flask import Flask, render_template, request, jsonify
from flask_pymongo import PyMongo

import uuid

app = Flask(__name__)
mongo = PyMongo(app)

@app.route('/')
def home_page():
    return render_template('index.html')


@app.route('/data/images')
def get_image_data():
    return "Not implemented", 404


@app.route('/data/images', methods=['POST'])
def post_image_data():
    filename = str(uuid.uuid4()) + ".png"
    request.files['image'].save("./images/" + filename)
    data = request.form.to_dict()
    data['filename'] = filename
    mongo.db.images.insert_one(data)

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
    return "Not implemented", 404

if __name__ == '__main__':
    app.run()
