import time
import json
import sys

import numpy as np
import redis
import cv2

import settings
from myutils import base64_decode_image

db = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)


def iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    # compute the area of intersection rectangle
    interArea = (xB - xA + 1) * (yB - yA + 1)

    # compute the area of both the prediction and ground-truth
    # rectangles
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)

    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = interArea / float(boxAArea + boxBArea - interArea)

    # return the intersection over union value
    return iou

def nms(dets, iou_threshold=0.5):
    sorted_list = sorted(dets, key=lambda k: k['confidence'])
    filtered_list = []

    for det in sorted_list:
        skip = False
        for b in filtered_list:
            if b["label"] == det["label"] and iou(b["box"], det["box"]) > iou_threshold:
                skip = True
                break

        if not skip:
            filtered_list.append(det)

    return filtered_list

def start_process():
    print("* Loading object model...")
    import detection_nn
    print("* Object model loaded")

    # continually poll for new images to classify
    while True:
        # attempt to grab a batch of images from the database, then
        # initialize the image IDs and batch of images themselves
        queue = db.lrange(settings.OBJECT_QUEUE, 0, settings.BATCH_SIZE - 1)
        imageIDs = []
        orig_imgs = []
        jsons = []
        batch = None

        # loop over the queue
        for q in queue:
            q = json.loads(q)
            image = base64_decode_image(q["image"], (q["width"], q["height"]))

            orig_imgs.append(image)
            jsons.append(q)

            # update the list of image IDs
            imageIDs.append(q["id"])

        # check to see if we need to process the batch
        if len(imageIDs) > 0:
            print("* Object batch size: {}".format(len(imageIDs)))

            # loop over the image IDs and their corresponding set of
            # results from our model
            for i, imageID in enumerate(imageIDs):
                img_feats, obj_dets, obj_feats = detection_nn.detect(orig_imgs[i], thres=0.5, only_img_feats=False)
                obj_dets = nms(obj_dets, 0.5)

                db.set(imageID + "-object", json.dumps(obj_dets))

                jsons[i]['object'] = obj_dets

                db.rpush(settings.ACTION_QUEUE, json.dumps(jsons[i]))

            # remove the set of images from our queue
            db.ltrim(settings.OBJECT_QUEUE, len(imageIDs), -1)

        # sleep for a small amount
        #time.sleep(settings.SERVER_SLEEP)


if __name__ == "__main__":
    start_process()