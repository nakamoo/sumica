from flask import Flask, render_template, request
from flask_pymongo import PyMongo

import uuid

app = Flask(__name__)
mongo = PyMongo(app)

@app.route('/')
def home_page():
    return render_template('index.html')


@app.route('/data/image')
def get_image_data():
    return render_template('index.html')


@app.route('/data/images', methods=['POST'])
def post_image_data():
    filename = str(uuid.uuid4()) + ".png"
    request.files['image'].save("./images/" + filename)
    data = request.form.to_dict()
    data['filename'] = filename
    mongo.db.images.insert_one(data)

    return render_template('index.html')


@app.route('/data/hue')
def get_hue_data():
    return render_template('index.html')


@app.route('/data/hue', methods=['POST'])
def post_hue_data():
    data = request.form.to_dict()
    mongo.db.hue.insert_one(data)
    return render_template('index.html')


@app.route('/data/youtube')
def get_youtube_data():
    return render_template('index.html')


@app.route('/data/youtube', methods=['POST'])
def post_youtube_data():
    data = request.form.to_dict()
    mongo.db.youtube.insert_one(data)
    return render_template('index.html')


@app.route('/controllers')
def get_controllers():
    return render_template('index.html')


@app.route('/controllers/update', methods=['POST'])
def update_controllers():
    return render_template('index.html')


@app.route('/controllers/execute', methods=['POST'])
def execute_controllers():
    return render_template('index.html')

if __name__ == '__main__':
    app.run()
