#import hai.trigger_controllers as trigger
import uuid
from flask import Blueprint, request, jsonify

from database import mongo

app = Blueprint("images", __name__)

@app.route('/data/images')
def get_image_data():
    return "Not implemented", 404

@app.route('/data/images', methods=['POST'])
def post_image_data():
    filename = str(uuid.uuid4()) + ".png"
    request.files['image'].save("../images/" + filename)
    data = request.form.to_dict()
    data['filename'] = filename
    mongo.db.images.insert_one(data)
    data.pop("_id")

    import hai
    # hai.trigger_controllers(data['user_name'], "image", data)

    return jsonify(data), 201
