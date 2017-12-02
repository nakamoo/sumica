from .controller import Controller
import subprocess
from shutil import copyfile
from subprocess import check_output
import glob
import time
import os
import threading
import json
import database as db
import time
from _app import app
import PyOpenPose as OP
import cv2
from concurrent.futures import ThreadPoolExecutor, wait

import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level=app.config['LOG_LEVEL'], logger=logger)

def init_pose():
    OPENPOSE_ROOT = os.environ["OPENPOSE_ROOT"]
    op = OP.OpenPose((656, 368), (368, 368), (1280, 720), "COCO", "/home/sean/openpose/models/", 0, False,
                OP.OpenPose.ScaleMode.ZeroToOne, True, True)
    return op

pose_executor = ThreadPoolExecutor(1)
future = pose_executor.submit(init_pose)
wait([future])
op = future.result()

def extract_keypoints(img):
    op.detectPose(img)
    op.detectFace(img)
    op.detectHands(img)
    body = op.getKeypoints(op.KeypointType.POSE)[0]
    hand = op.getKeypoints(op.KeypointType.HAND)[0]
    face = op.getKeypoints(op.KeypointType.FACE)[0]
    return body, hand, face

class Pose2(Controller):
    def __init__(self, user):
        self.user = user

    def on_event(self, event, data):
        if event == "image":
            if app.config['ENCRYPTION']:
                image_path = app.config['ENCRYPTED_IMG_DIR'] + data['filename']
            else:
                image_path = app.config['RAW_IMG_DIR'] + data['filename']

            new_data = {}
            new_data['history.pose_request'] = time.time()
            
            img = cv2.imread(image_path)
            future = pose_executor.submit(extract_keypoints, (img))
            wait([future])
            body, hand, face = future.result()
            new_data['history.pose_recorded'] = time.time()
            
            if body is not None:
                new_data['pose.body'] = body.tolist()
            else:
                new_data['pose.body'] = []
                
            if hand is not None:
                new_data['pose.hand'] = hand.tolist()
            else:
                new_data['pose.hand'] = []
                
            if face is not None:
                new_data['pose.face'] = face.tolist()
            else:
                new_data['pose.face'] = []
            
            db.mongo.images.update_one({"_id": data["_id"]}, {'$set': new_data}, upsert=False)

    def execute(self):
        return []
