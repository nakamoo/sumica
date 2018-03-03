import time
import json
import sys
import base64

import numpy as np
import redis
import cv2

import settings
from myutils import base64_decode_image

from i3d_model import I3DModel

db = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)


def get_crops(image, objs):
    crops = []

    for i in range(len(objs)):
        if objs[i]["label"] == "person":
            box = objs[i]["box"]
            im_w, im_h = image.shape[1], image.shape[0]
            box_w, box_h = (box[2] - box[0]), (box[3] - box[1])
            # expand
            cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
            longer_side = max(box_w, box_h) * 2.0
            constrained_side = min(min(im_w, im_h), longer_side)
            a = constrained_side / 2.0

            x1, y1, x2, y2 = cx - a, cy - a, cx + a, cy + a

            if x1 < 0:
                x2 -= x1
                x1 = 0
            if y1 < 0:
                y2 -= y1
                y1 = 0
            if x2 >= im_w:
                x1 -= x2 - im_w
                x2 = im_w
            if y2 >= im_h:
                y1 -= y2 - im_h
                y2 = im_h

            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

            crop = image[y1:y2, x1:x2, :]
            crop = cv2.resize(crop, (224, 224))
            crop = crop[None, ...]
            crop = np.repeat(crop, settings.TIME_LENGTH, axis=0).transpose(3, 0, 1, 2)
            crops.append({'image': crop, 'crop': [x1, y1, x2, y2]})

    return crops

def start_process():
    print("* Loading action model...")
    model = I3DModel()
    print("* Action model loaded")

    batch = []
    sizes = []
    jsons = []
    results = []
    batch_size = 4
    end = False

    # continually poll for new images to classify
    while True:
        # attempt to grab a batch of images from the database, then
        # initialize the image IDs and batch of images themselves
        queue = db.lrange(settings.ACTION_QUEUE, 0, 0)

        if len(queue) == 0:
            end = True
        else:
            while len(batch) < settings.BATCH_SIZE:
                queue = db.lrange(settings.ACTION_QUEUE, 0, 0)

                if len(queue) == 0:
                    break

                # deserialize the object and obtain the input image
                q = json.loads(queue[0])
                jsons.append(q)

                image = base64_decode_image(q["image"], (q["width"], q["height"]))
                objs = q["object"]

                crops = get_crops(image, objs)

                if len(crops) > 0:
                    crops = np.stack(crops)

                    # check to see if the batch list is None
                    #if len(batch) == 0:
                    #    batch = crops

                    # otherwise, stack the data
                    #else:
                    #    batch = np.vstack([batch, crops])
                    batch.extend(crops)

                # update the list of image IDs
                #imageIDs.append(q["id"])
                sizes.append(len(crops))

                db.ltrim(settings.ACTION_QUEUE, 1, -1)

        if len(batch) == 0:
            time.sleep(settings.SERVER_SLEEP)
            continue
      
        # check to see if we need to process the batch
        while len(batch) >= settings.BATCH_SIZE or end:
            #print('yo1', len(batch), len(jsons), sizes, len(results))

            # classify the batch
            current_batch = batch[:batch_size]
            imgmat = np.array([b['image'] for b in current_batch])
            print("* Action batch size: {}".format(imgmat.shape))
            top_val, top_idx, feats = model.predict(imgmat/128.0-1.0)
            #print(top_val, top_idx, feats.shape)
            #sizes[0] -= len(current_b)

            # loop over the image IDs and their corresponding set of
            # results from our model
            for i in range(len(top_idx)):
                outData = {"action_label": model.kinetics_classes[top_idx[i]], "action_confidence": float(top_val[i])}
                outData['action_crop'] = current_batch[i]['crop']
                outData['action_vector'] = feats[i].tolist()
                results.append(outData)

                #db.set(imageID + "-action", json.dumps(outData))

            batch = batch[batch_size:]
            #print('yo2', len(batch), len(jsons), sizes, len(results))

            while len(sizes) > 0 and len(results) >= sizes[0]:
                objs = jsons[0]['object']
                i = 0
                r = results[:sizes[0]]

                for obj in objs:
                    if obj['label'] == 'person':
                        obj.update(r[i])

                        i += 1

                db.set(jsons[0]['id'] + "-action", json.dumps(jsons[0]['object']))

                del jsons[0]
                del results[:sizes[0]]
                del sizes[0]

            if len(batch) == 0:
                break

        if end:
            # sleep for a small amount
            time.sleep(settings.SERVER_SLEEP)
        
if __name__ == "__main__":
    start_process()