#import hai.trigger_controllers as trigger
import uuid
from flask import Blueprint, request, jsonify

from database import mongo
import database as db
import time

from utils.encryption import cryptographic_key
from _app import app

bp = Blueprint("images", __name__)

@bp.route('/data/images')
def get_image_data():
    return "Not implemented", 404

@bp.route('/data/images', methods=['POST'])
def post_image_data():
    data = request.form.to_dict()
    print(data)
    data["time"] = float(data["time"])

    if app.config['ENCRYPTION']:
        byte_data = request.files['image'].read()
        token = cryptographic_key.encrypt(byte_data)
        filename = str(uuid.uuid4()) + ".dat"
        with open(app.config['ENCRYPTED_IMG_DIR'] + filename, 'wb') as f:
            f.write(token)
        data['encryption'] = True
    else:
        filename = str(uuid.uuid4()) + ".png"
        request.files['image'].save(app.config['RAW_IMG_DIR'] + filename)
        m_filename = str(uuid.uuid4()) + ".png"
        request.files['diff'].save(app.config['RAW_IMG_DIR'] + m_filename)
        data['encryption'] = False

    print(filename, "latency:", time.time()-data["time"])
    arrival_time = time.time()
    data['filename'] = filename
    data['diff_filename'] = m_filename
    data['version'] = '0.2'
    mongo.images.insert_one(data)
    
    #if request.args.get('execute') == 'True': # what is this?
    db.trigger_controllers(data['user_name'], "image", data)
    
    return_time = time.time()
    db.mongo.images.update_one({"_id": data["_id"]}, {'$set': {'history.arrival': arrival_time, 'history.first_loop_done': return_time}}, upsert=False)

    data["detections"] = db.mongo.images.find_one({"_id": data["_id"]})["detections"]
    data["return_time"] = return_time

    data.pop("_id")
    return jsonify(data), 201
