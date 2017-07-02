import sys
sys.path.insert(0, '../../tf-faster-rcnn/tools')
import _init_paths
from model.test import test_net, im_detect, nms
from model.config import cfg, cfg_from_file, cfg_from_list
from datasets.factory import get_imdb
import argparse
import pprint
import time, os, sys
import numpy as np
import cv2
import colorsys

import tensorflow as tf
from nets.resnet_v1 import resnetv1

root = '../../tf-faster-rcnn'

model_ckpt = os.path.join(root, "models/coco_2014_train+coco_2014_valminusminival/default/res101_faster_rcnn_iter_1190000.ckpt")

cfg_from_file(os.path.join(root, "experiments/cfgs/res101.yml"))
cfg_from_list(['ANCHOR_SCALES', '[4,8,16,32]', 'ANCHOR_RATIOS', '[0.5,1,2]'])

imdb = get_imdb("coco_2014_minival")
imdb.competition_mode(False)

#tfconfig = tf.ConfigProto(device_count={'GPU': 0})
#tfconfig.gpu_options.allow_growth=True

# init session
sess = tf.Session()

net = resnetv1(batch_size=1, num_layers=101)

net.create_architecture(sess, "TEST", imdb.num_classes, tag='default',
                      anchor_scales=cfg.ANCHOR_SCALES,
                      anchor_ratios=cfg.ANCHOR_RATIOS)

print(('Loading model check point from {:s}').format(model_ckpt))
saver = tf.train.Saver()
saver.restore(sess, model_ckpt)
print('Loaded.')

def detect(image, conf_thresh=0.7, nms_thresh=0.3, get_image=False):
    all_boxes = []
    frame = image
    scores, boxes = im_detect(sess, net, frame)

    CONF_THRESH = conf_thresh
    NMS_THRESH = nms_thresh
    for cls_ind, cls in enumerate(imdb._classes[1:]):
        cls_ind += 1 # because we skipped background
        cls_boxes = boxes[:, 4*cls_ind:4*(cls_ind + 1)]
        cls_scores = scores[:, cls_ind]
        dets = np.hstack((cls_boxes,
                          cls_scores[:, np.newaxis])).astype(np.float32)
        keep = nms(dets, NMS_THRESH)
        dets = dets[keep, :]

        for det in dets:
          if det[-1] > CONF_THRESH:
              all_boxes.append({"label": str(cls), "box": det[:4].astype(np.int32).tolist(), "confidence": float(det[-1])})

    if get_image:
        for result in all_boxes:
            det = result["box"]
            name = result["label"]

            i = sum([ord(x) for x in name])
            c = colorsys.hsv_to_rgb(i%100.0/100.0, 1.0, 0.9)
            c = tuple([int(x * 255.0) for x in c])
            cv2.putText(frame, name, (det[0], det[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2)
            cv2.rectangle(frame, (det[0], det[1]), (int(det[2]), int(det[3])), c, 2)

        cv2.imshow("frame", frame[..., [2,1,0]])
        cv2.waitKey(1)

        return all_boxes, frame
    
    return all_boxes

def close():
    sess.close()

if __name__ == "__main__":
    print(detect(cv2.imread("room.png")))
