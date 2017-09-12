from flask import Blueprint, request, jsonify
from database import mongo

bp = Blueprint("hue", __name__)

@bp.route('/data/hue')
def get_hue_data():
    return "Not implemented", 404

@bp.route('/data/hue', methods=['POST'])
def post_hue_data():
    data = request.form.to_dict()
    print("HUE>> ", data)
    data["time"] = float(data["time"])
    mongo.hue.insert_one(data)
    data.pop("_id")
    return jsonify(data), 201
