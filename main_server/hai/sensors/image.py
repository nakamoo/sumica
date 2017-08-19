#import hai.trigger_controllers as trigger
import uuid
from flask import Blueprint, request, jsonify

from database import mongo
import database as db

from utils.encryption import cryptographic_key

app = Blueprint("images", __name__)

@app.route('/data/images')
def get_image_data():
    return "Not implemented", 404

@app.route('/data/images', methods=['POST'])
def post_image_data():
    data = request.form.to_dict()

    byte_data = request.files['image'].read()
    token = cryptographic_key.encrypt(byte_data)
    filename = str(uuid.uuid4()) + ".dat"
    with open("./images/encrypted_image/" + filename, 'wb') as f:
        f.write(token)
    data['encryption'] = True

    # filename = str(uuid.uuid4()) + ".png"
    # request.files['image'].save("./images/" + filename)

    data['filename'] = filename
    mongo.db.images.insert_one(data)
    data.pop("_id")

    if request.args.get('execute') == 'True':
        db.trigger_controllers(data['user_name'], "image", data)

    return jsonify(data), 201
