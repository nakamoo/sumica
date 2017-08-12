import ..hai as hai
from flask import Blueprint

app = Blueprint("image", __name__)

@app.route('/data/image')
def get_image_data():
    return "Not implemented", 404

@app.route('/data/image', methods=['POST'])
def post_image_data():
    filename = str(uuid.uuid4()) + ".png"
    request.files['image'].save("./images/" + filename)
    data = request.form.to_dict()
    data['filename'] = filename
    mongo.db.images.insert_one(data)

    hai.trigger_controllers(data['user_id'], "image", data)

    data.pop("_id")
    return jsonify(data), 201