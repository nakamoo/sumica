from flask import Blueprint, request, jsonify
import database as db
import coloredlogs, logging

bp = Blueprint("hue", __name__)
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)

@bp.route('/data/hue')
def get_hue_data():
    return "Not implemented", 404

@bp.route('/data/hue', methods=['POST'])
def post_hue_data():
    data = request.form.to_dict()
    #logger.info(data)
    data["time"] = float(data["time"])
    data["last_manual"] = float(data["last_manual"])
    db.mongo.hue.insert_one(data)
    
    db.trigger_controllers(data['user_name'], "hue", data)
    
    data.pop("_id")
    return jsonify(data), 201
