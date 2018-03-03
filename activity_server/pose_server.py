import time
import json
import sys
import base64

import numpy as np
import redis
import cv2

import settings
from myutils import base64_decode_image

import PyOpenPose as OP

db = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)


def pose_estimation(op, img):
    op.detectPose(img)
    op.detectFace(img)
    op.detectHands(img)
    body = op.getKeypoints(op.KeypointType.POSE)[0]
    hand = op.getKeypoints(op.KeypointType.HAND)[0]
    face = op.getKeypoints(op.KeypointType.FACE)[0]
    new_data = {'body': [], 'hand': [], 'face': []}

    if body is not None:
        new_data['body'] = body.tolist()

    if hand is not None:
        new_data['hand'] = hand.tolist()

    if face is not None:
        new_data['face'] = face.tolist()

    return new_data

def start_process():
    print("* Loading pose model...")
    op = OP.OpenPose((656, 368), (368, 368), (1280, 720), "COCO", "/home/sean/openpose/models/", 0, False,
                     OP.OpenPose.ScaleMode.ZeroToOne, True, True)
    print("* Pose model loaded")

    # continually poll for new images to classify
    while True:
        # attempt to grab a batch of images from the database, then
        # initialize the image IDs and batch of images themselves
        queue = db.lrange(settings.POSE_QUEUE, 0, settings.BATCH_SIZE - 1)
        imageIDs = []
        orig_imgs = []
        batch = None

        # loop over the queue
        for q in queue:
            q = json.loads(q)
            image = base64_decode_image(q["image"], (q["width"], q["height"]))
            orig_imgs.append(image)

            # update the list of image IDs
            imageIDs.append(q["id"])

        # check to see if we need to process the batch
        if len(imageIDs) > 0:
            # classify the batch
            print("* Pose batch size: {}".format(len(imageIDs)))

            # loop over the image IDs and their corresponding set of
            # results from our model
            for i, imageID in enumerate(imageIDs):
                pose_data = pose_estimation(op, orig_imgs[i])

                db.set(imageID + "-pose", json.dumps(pose_data))

            # remove the set of images from our queue
            db.ltrim(settings.POSE_QUEUE, len(imageIDs), -1)

        # sleep for a small amount
        #time.sleep(settings.SERVER_SLEEP)


if __name__ == "__main__":
    start_process()