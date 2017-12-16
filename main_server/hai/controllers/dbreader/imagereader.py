from pymongo import MongoClient
import controllers.dbreader.dbreader as dbreader
import configparser, os

config = configparser.ConfigParser()
config.read('application.cfg')
client = MongoClient('localhost', int(config["flask"]["PORT_DB"]))
mongo = client.hai

class ImageReader(dbreader.DBReader):
    def __init__(self):
        pass
    
    def read_db(self, username, start_time, end_time, cams):    
        query = {"user_name": username, "cam_id": {"$in": cams}, "pose":{"$exists": True}, "detections":{"$exists": True}, "time": {"$gte": start_time, "$lt": end_time}}
        cursor = mongo.images.find(query).sort([("time", -1)])
        
        re_data = []
        current_data = [None for cam in cams]
        
        for im_data in cursor:
            current_time = im_data["time"]
            current_data[cams.index(im_data["cam_id"])] = im_data
            
            skip = False
            for cam_image in current_data:
                if cam_image is None or current_time - cam_image["time"] > 5: #old data
                    skip = True
            
            if not skip:
                re_data.append(current_data.copy())
                
        return re_data