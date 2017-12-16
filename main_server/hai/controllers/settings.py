from .controller import Controller
import database as db
import os
import time
from _app import app

import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level=app.config['LOG_LEVEL'], logger=logger)

class Settings(Controller):
    def __init__(self, user):
        self.user = user
        n = db.mongo.settings.find_one({"user_name": user})

        if not n:
            db.mongo.settings.insert_one({"user_name": user, "save_images": True})

        self.load_settings(user)

    def load_settings(self, user):
        n = db.mongo.settings.find_one({"user_name": user})
        self.save_images = n["save_images"]

    def on_event(self, event, data):
        if event == "chat":
            if data["message"]["text"] == "save images on":
                self.save_images = True
            elif data["message"]["text"] == "save images off":
                self.save_images = False

            print("changed settings: save images", self.save_images)
            db.mongo.settings.update_one({"user_name": self.user}, {"$set": {"save_images": self.save_images}})
        elif event == "image":
            
            if not self.save_images:
                for n in db.mongo.images.find({"user_name": self.user, "time": {"$lt": time.time() - 30000}}):
                    #if os.path.isfile("./images/" + n["filename"]):
                    try:
                        print("removing {}".format(n["filename"]))
                        os.remove(app.config["RAW_IMG_DIR"] + n["filename"])
                    except:
                        print("could not delete")
            else:
                logger.info("preserving image " + self.user)

    def execute(self):
        return []
