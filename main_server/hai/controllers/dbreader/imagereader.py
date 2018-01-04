import controllers.dbreader.dbreader as dbreader
from controllers.dbreader.utils import get_db
import os

mongo = get_db()

class ImageReader(dbreader.DBReader):
    def __init__(self):
        pass

    def read_db(self, username, start_time, end_time, cams, max_lag=5):
        query = {"user_name": username, "cam_id": {"$in": cams}, "pose":{"$exists": True}, "detections":{"$exists": True}, "time": {"$gte": start_time, "$lt": end_time}}
        cursor = mongo.images.find(query).sort([("time", 1)])

        re_data = []
        times = []

        current_data = [None for cam in cams]

        for im_data in cursor:
            current_time = im_data["time"]
            current_data[cams.index(im_data["cam_id"])] = im_data

            skip = False
            for cam_image in current_data:
                if cam_image is None or current_time - cam_image["time"] > max_lag: #old data
                    skip = True

            if not skip:
                re_data.append(current_data.copy())
                times.append(current_time)

        return re_data, times
