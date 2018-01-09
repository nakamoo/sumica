import numpy as np
import os
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import zipfile

from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image

os.environ["CUDA_VISIBLE_DEVICES"]="0"

det_root = "../../models"

# This is needed since the notebook is stored in the object_detection folder.
sys.path.append(det_root + "/object_detection")
sys.path.append(det_root)

from utils import label_map_util

from utils import visualization_utils as vis_util

# What model to download.
#MODEL_NAME = 'faster_rcnn_inception_resnet_v2_atrous_coco_11_06_2017'
MODEL_NAME = 'faster_rcnn_resnet101_coco_11_06_2017'
MODEL_FILE = MODEL_NAME + '.tar.gz'
DOWNLOAD_BASE = 'http://download.tensorflow.org/models/object_detection/'

# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT = det_root + '/object_detection/' + MODEL_NAME + '/frozen_inference_graph.pb'

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join(det_root, 'object_detection', 'data', 'mscoco_label_map.pbtxt')

NUM_CLASSES = 90

#opener = urllib.request.URLopener()
#opener.retrieve(DOWNLOAD_BASE + MODEL_FILE, MODEL_FILE)
#tar_file = tarfile.open(MODEL_FILE)
#for file in tar_file.getmembers():
#  file_name = os.path.basename(file.name)
#  if 'frozen_inference_graph.pb' in file_name:
#    tar_file.extract(file, os.getcwd())

detection_graph = tf.Graph()
with detection_graph.as_default():
  od_graph_def = tf.GraphDef()
  with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
    serialized_graph = fid.read()
    od_graph_def.ParseFromString(serialized_graph)
    tf.import_graph_def(od_graph_def, name='')

label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)

#with detection_graph.as_default():
sess = tf.Session(graph=detection_graph)

image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
# Each box represents a part of the image where a particular object was detected.
#for n in detection_graph.as_graph_def().node:
#  if "relu" in n.name.lower() or "pool" in n.name.lower():
#    print(n.name)
boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
# Each score represent how level of confidence for each of the objects.
# Score is shown on the result image, together with the class label.
scores = detection_graph.get_tensor_by_name('detection_scores:0')
classes = detection_graph.get_tensor_by_name('detection_classes:0')
num_detections = detection_graph.get_tensor_by_name('num_detections:0')
relu6 = detection_graph.get_tensor_by_name('Conv/Relu6:0')
avgpool = detection_graph.get_tensor_by_name('SecondStageBoxPredictor/AvgPool:0')

def detect(image, thres, only_img_feats):
  # the array based representation of the image will be used later in order to prepare the
  # result image with boxes and labels on it.
  image_np = image#load_image_into_numpy_array(image)
  height, width = image.shape[0], image.shape[1]
  # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
  image_np_expanded = np.expand_dims(image_np, axis=0)
  ##image_np_expanded = np.stack([image_np] * 8)

  if only_img_feats:
    img_feats = sess.run(
        [relu6],
        feed_dict={image_tensor: image_np_expanded})

    img_feats = np.squeeze(img_feats)
    return img_feats, None, None
  else:
    # Actual detection.
    (boxes_out, scores_out, classes_out, num_detections_out, img_feats_out, obj_feats_out) = sess.run(
        [boxes, scores, classes, num_detections,
         relu6,
         avgpool],
        feed_dict={image_tensor: image_np_expanded})

    boxes_out = np.squeeze(boxes_out)
    scores_out = np.squeeze(scores_out)
    classes_out = np.squeeze(classes_out)
    img_feats_out = np.squeeze(img_feats_out)
    obj_feats_raw = np.squeeze(obj_feats_out)

    all_boxes = []
    obj_feats = []

    for label, box, confidence, feats in zip(classes_out, boxes_out, scores_out, obj_feats_raw):
        if confidence < thres:
            continue      

        box[1] *= width
        box[0] *= height
        box[3] *= width
        box[2] *= height
        box = [box[1], box[0], box[3], box[2]]

        all_boxes.append({"label": category_index[label]["name"], "box": [int(b) for b in box], "confidence": float(confidence)})
          #"features": feats.tolist()})
        obj_feats.append(feats)

    #outputs = {"features": img_feats.tolist(), "objects": all_boxes}

    return img_feats_out, all_boxes, obj_feats

