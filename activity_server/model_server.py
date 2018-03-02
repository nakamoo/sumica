import time
import json
import sys
import base64

import numpy as np
import redis
import cv2

import settings

from i3d_model import I3DModel
#import detection_nn

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

    for det in dets:
        skip = False
        for b in filtered_list:
            if b["label"] == det["label"] and iou(b["box"], det["box"]) > iou_threshold:
                skip = True
                break

        if not skip:
            filtered_list.append(det)

    return filtered_list

def base64_decode_image(a, size):
    # if this is Python 3, we need the extra step of encoding the
    # serialized NumPy string as a byte object
    if sys.version_info.major == 3:
        a = bytes(a, encoding="utf-8")
 
    # convert the string to a NumPy array using the supplied data
    # type and target shape
    a = np.frombuffer(base64.decodestring(a), dtype=np.uint8)
    a = a.reshape((size[1], size[0], settings.IMAGE_CHANS))
 
    # return the decoded image
    return a

def classify_process():
    print("* Loading model...")
    model = I3DModel()
    print("* Model loaded")
    
    # continually poll for new images to classify
    while True:
        # attempt to grab a batch of images from the database, then
        # initialize the image IDs and batch of images themselves
        queue = db.lrange(settings.IMAGE_QUEUE, 0, settings.BATCH_SIZE - 1)
        imageIDs = []
        orig_imgs = []
        batch = None

        # loop over the queue
        for q in queue:
            # deserialize the object and obtain the input image
            q = json.loads(q.decode("utf-8"))
            image = base64_decode_image(q["image"], (q["width"], q["height"]))
            orig_imgs.append(image)
            
            image = cv2.resize(image, (224, 224))
            image = image[None, None, ...]
            image = np.repeat(image, settings.TIME_LENGTH, axis=1).transpose(0, 4, 1, 2, 3)
            #image = image/128.0-1.0

            # check to see if the batch list is None
            if batch is None:
                batch = image

            # otherwise, stack the data
            else:
                 batch = np.vstack([batch, image])

            # update the list of image IDs
            imageIDs.append(q["id"])
      
        # check to see if we need to process the batch
        if len(imageIDs) > 0:
            # classify the batch
            print("* Batch size: {}".format(batch.shape))
            top_val, top_idx = model.predict(batch/128.0-1.0)
 
            # loop over the image IDs and their corresponding set of
            # results from our model
            for i, imageID in enumerate(imageIDs):
                #img_feats, obj_dets, obj_feats = detection_nn.detect(orig_imgs[i], thres=0.5, only_img_feats=False)
                #obj_dets = nms(obj_dets, 0.5)
                
                outData = {"label": model.kinetics_classes[top_idx[i]], "confidence": float(top_val[i])}#, "detections": obj_dets}
                
                db.set(imageID, json.dumps(outData))
 
            # remove the set of images from our queue
            db.ltrim(settings.IMAGE_QUEUE, len(imageIDs), -1)
 
        # sleep for a small amount
        time.sleep(settings.SERVER_SLEEP)
        
if __name__ == "__main__":
    classify_process()