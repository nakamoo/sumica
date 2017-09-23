from flask import Blueprint

bp = Blueprint("youtube", __name__)

@bp.route('/data/youtube')
def get_youtube_data():
    return "Not implemented", 404


@bp.route('/data/youtube', methods=['POST'])
def post_youtube_data():
    data = request.form.to_dict()
    mongo.db.youtube.insert_one(data)
    data.pop("_id")
    return jsonify(data), 201