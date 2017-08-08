from flask import render_template, request
from hai import app, mongo


@app.route('/')
def home_page():
    return render_template('index.html')


@app.route('/data/image')
def get_image_data():
    return render_template('index.html')


@app.route('/data/image', methods=['POST'])
def post_image_data():
    mongo.save_file("./images/unique_name.png", request.files['image'])
    ## rename image and save at ./images/
    return render_template('index.html')


@app.route('/data/hue')
def get_hue_data():
    return render_template('index.html')


@app.route('/data/hue', methods=['POST'])
def post_hue_data():
    return render_template('index.html')


@app.route('/data/youtube')
def get_youtube_data():
    return render_template('index.html')


@app.route('/data/youtube', methods=['POST'])
def post_youtube_data():
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

