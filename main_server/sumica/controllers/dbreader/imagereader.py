import os

import controllers.dbreader.dbreader as dbreader
from utils import db

class ImageReader(dbreader.DBReader):
    def __init__(self):
        pass

    def read_db(self, username, start_time, end_time, cams, max_lag=5, skip_absent=False):
        query = {"user_name": username, "cam_id": {"$in": cams}, "pose":{"$exists": True}, "detections":{"$exists": True}, "time": {"$gte": start_time, "$lt": end_time}}
        cursor = db.images.find(query).sort([("time", 1)])

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
                    break
                    
            if not skip and skip_absent:
                contains_person = False
            
                for cam_image in current_data:
                    if len(cam_image["persons"]) > 0 \
                            and cam_image["detections"][cam_image["persons"][0]["det_index"]]["confidence"] > 0.8:
                        contains_person = True
                        break
                       
                if not contains_person:
                    skip = True

            if not skip:
                re_data.append(current_data.copy())
                times.append(current_time)

        return re_data, times
