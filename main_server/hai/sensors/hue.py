from flask import Blueprint, request, jsonify
import database as db

bp = Blueprint("hue", __name__)

@bp.route('/data/hue')
def get_hue_data():
    return "Not implemented", 404

@bp.route('/data/hue', methods=['POST'])
def post_hue_data():
    data = request.form.to_dict()
    print("HUE>> ", data)
    data["time"] = float(data["time"])
    db.mongo.hue.insert_one(data)
    
    db.trigger_controllers(data['user_name'], "hue", data)
    
    data.pop("_id")
    return jsonify(data), 201
