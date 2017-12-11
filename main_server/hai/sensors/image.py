#import hai.trigger_controllers as trigger
import uuid
from flask import Blueprint, request, jsonify

from database import mongo
import database as db
import time

from utils.encryption import cryptographic_key
from _app import app
from concurrent.futures import ThreadPoolExecutor, wait

import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)

bp = Blueprint("images", __name__)

image_processor = ThreadPoolExecutor(8)

@bp.route('/data/images')
def get_image_data():
    return "Not implemented", 404

@bp.route('/data/images', methods=['POST'])
def post_image_data():
    data = request.form.to_dict()
    #logger.debug(data)
    data['history'] = {'image_arrived': time.time()}
    data["time"] = float(data["time"])
    data["motion_update"] = bool(data["motion_update"])
    
    if data["motion_update"]:
        if app.config['ENCRYPTION']:
            byte_data = request.files['image'].read()
            token = cryptographic_key.encrypt(byte_data)
            filename = str(uuid.uuid4()) + ".dat"
            with open(app.config['ENCRYPTED_IMG_DIR'] + filename, 'wb') as f:
                f.write(token)
            data['encryption'] = True
        else:
            filename = str(uuid.uuid4()) + ".jpg"
            request.files['image'].save(app.config['RAW_IMG_DIR'] + filename)
            m_filename = str(uuid.uuid4()) + ".jpg"
            request.files['diff'].save(app.config['RAW_IMG_DIR'] + m_filename)
            data['encryption'] = False

    logger.info(filename + " latency: " + str(time.time()-data["time"]))
    data['filename'] = filename
    data['diff_filename'] = m_filename
    data['version'] = '0.2'
    data['history']['image_recorded'] = time.time()
    result = mongo.images.insert_one(data)
    
    def process(img_data):
        if data["motion_update"]:
            db.mongo.images.update_one({"filename": img_data['filename']}, {'$set': {"history.image_processing_start": time.time()}}, upsert=False)
            db.trigger_controllers(data['user_name'], "image", img_data, parallel=False)
            db.mongo.images.update_one({"filename": img_data['filename']}, {'$set': {"history.image_processing_finish": time.time()}}, upsert=False)
            
    future = image_processor.submit(process, data.copy())
    wait([future])

    #db.mongo.images.update_one({"_id": data["_id"]}, {'$set': {'history.arrival': arrival_time, 'history.first_loop_done': return_time}}, upsert=False)

    data.pop("_id")
    logger.debug("unprocessed image stored.")
    return jsonify(data), 201
