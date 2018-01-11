import uuid
import time
from concurrent.futures import ThreadPoolExecutor, wait

from flask import Blueprint, request, jsonify, current_app
import coloredlogs
import logging

from encryption import cryptographic_key
from utils import db
import controllermanager as cm

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)

bp = Blueprint("images", __name__)

image_processor = ThreadPoolExecutor(8)


@bp.route('/data/images', methods=['POST'])
def post_image_data():
    data = request.form.to_dict()

    data['history'] = {'image_arrived': time.time()}
    data["time"] = float(data["time"])
    data["motion_update"] = bool(data["motion_update"])

    if data["motion_update"]:
        if current_app.config['ENCRYPTION']:
            byte_data = request.files['image'].read()
            token = cryptographic_key.encrypt(byte_data)
            filename = str(uuid.uuid4()) + ".dat"
            with open(Config.ENCRYPTED_IMG_DIR + filename, 'wb') as f:
                f.write(token)
            data['encryption'] = True
        else:
            filename = str(uuid.uuid4()) + ".jpg"
            request.files['image'].save(current_app.config['RAW_IMG_DIR'] + filename)
            m_filename = str(uuid.uuid4()) + ".jpg"
            request.files['diff'].save(current_app.config['RAW_IMG_DIR'] + m_filename)
            data['encryption'] = False

    data['filename'] = filename
    data['diff_filename'] = m_filename
    data['version'] = '0.2'
    data['history']['image_recorded'] = time.time()
    db.images.insert_one(data)

    def process(img_data):
        if data["motion_update"]:
            db.images.update_one({"filename": img_data['filename']},
                                       {'$set': {"history.image_processing_start": time.time()}}, upsert=False)
            cm.trigger_controllers(data['user_name'], "image", img_data, parallel=False)
            db.images.update_one({"filename": img_data['filename']},
                                       {'$set': {"history.image_processing_finish": time.time()}}, upsert=False)

    future = image_processor.submit(process, data.copy())
    wait([future])

    data.pop("_id")

    return jsonify(data), 201
