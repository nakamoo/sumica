from flask import Blueprint

app = Blueprint("hue", __name__)

@app.route('/data/hue')
def get_hue_data():
    return "Not implemented", 404

@app.route('/data/hue', methods=['POST'])
def post_hue_data():
    data = request.form.to_dict()
    mongo.db.hue.insert_one(data)
    data.pop("_id")
    return jsonify(data), 201