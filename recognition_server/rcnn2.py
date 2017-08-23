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

# This is needed to display the images.
#%matplotlib inline

# This is needed since the notebook is stored in the object_detection folder.
sys.path.append("../../models/object_detection")
sys.path.append("../../models")

from utils import label_map_util

from utils import visualization_utils as vis_util

# What model to download.
MODEL_NAME = 'faster_rcnn_inception_resnet_v2_atrous_coco_11_06_2017'
#MODEL_NAME = 'faster_rcnn_resnet101_coco_11_06_2017'
MODEL_FILE = MODEL_NAME + '.tar.gz'
DOWNLOAD_BASE = 'http://download.tensorflow.org/models/object_detection/'

# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT = '../../models/object_detection/' + MODEL_NAME + '/frozen_inference_graph.pb'

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join('../../models/object_detection', 'data', 'mscoco_label_map.pbtxt')

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

# For the sake of simplicity we will use only 2 images:
# image1.jpg
# image2.jpg
# If you want to test the code with your images, just add path to the images to the TEST_IMAGE_PATHS.
#PATH_TO_TEST_IMAGES_DIR = 'test_images'
#TEST_IMAGE_PATHS = [ os.path.join(PATH_TO_TEST_IMAGES_DIR, 'image{}.jpg'.format(i)) for i in range(1, 3) ]

# Size, in inches, of the output images.
IMAGE_SIZE = (12, 8)


#with detection_graph.as_default():
sess = tf.Session(graph=detection_graph)

def detect(image, thres, only_img_feats):
  # the array based representation of the image will be used later in order to prepare the
  # result image with boxes and labels on it.
  image_np = image#load_image_into_numpy_array(image)
  height, width = image.shape[0], image.shape[1]
  # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
  image_np_expanded = np.expand_dims(image_np, axis=0)
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

  if only_img_feats:
    img_feats = sess.run(
        [detection_graph.get_tensor_by_name('Conv/Relu6:0')],
        feed_dict={image_tensor: image_np_expanded})

    img_feats = np.squeeze(img_feats)
    return img_feats
  else:
    # Actual detection.
    (boxes, scores, classes, num_detections, img_feats, obj_feats) = sess.run(
        [boxes, scores, classes, num_detections,
         detection_graph.get_tensor_by_name('Conv/Relu6:0'),
         detection_graph.get_tensor_by_name('SecondStageBoxPredictor/AvgPool:0')],
        feed_dict={image_tensor: image_np_expanded})

    boxes = np.squeeze(boxes)
    scores = np.squeeze(scores)
    classes = np.squeeze(classes)
    img_feats = np.squeeze(img_feats)
    obj_feats_raw = np.squeeze(obj_feats)

    all_boxes = []
    obj_feats = []

    for label, box, confidence, feats in zip(classes, boxes, scores, obj_feats_raw):
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

    return img_feats, all_boxes, obj_feats
