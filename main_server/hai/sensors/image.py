#import hai.trigger_controllers as trigger
import uuid
from flask import Blueprint, request, jsonify

from database import mongo
import database as db
import time

from utils.encryption import cryptographic_key

app = Blueprint("images", __name__)

@app.route('/data/images')
def get_image_data():
    return "Not implemented", 404

@app.route('/data/images', methods=['POST'])
def post_image_data():
    data = request.form.to_dict()
    print(data)
    data["time"] = float(data["time"])

    import hai
    if hai.app.config['ENCRYPTION']:
        byte_data = request.files['image'].read()
        token = cryptographic_key.encrypt(byte_data)
        filename = str(uuid.uuid4()) + ".dat"
        with open(hai.app.config['ENCRYPTED_IMG_DIR'] + filename, 'wb') as f:
            f.write(token)
        data['encryption'] = True
    else:
        filename = str(uuid.uuid4()) + ".png"
        request.files['image'].save(hai.app.config['RAW_IMG_DIR'] + filename)
        m_filename = str(uuid.uuid4()) + ".png"
        request.files['diff'].save(hai.app.config['RAW_IMG_DIR'] + m_filename)
        data['encryption'] = False

    print(filename, "latency:", time.time()-data["time"])
    data['filename'] = filename
    data['diff_filename'] = m_filename
    mongo.images.insert_one(data)
    
    #if request.args.get('execute') == 'True': # what is this?
    db.trigger_controllers(data['user_name'], "image", data)
    
    return_time = time.time()
    db.mongo.images.update_one({"_id": data["_id"]}, {'$set': {'history.first_loop_done': return_time}}, upsert=False)

    data["detections"] = db.mongo.images.find_one({"_id": data["_id"]})["detections"]
    data["return_time"] = return_time

    data.pop("_id")
    return jsonify(data), 201
