import cv2
from matplotlib import pylab as plt
from PIL import Image
import matplotlib.animation as animation
import numpy as np
import pymongo
import time
from datetime import datetime

import controllers.utils as utils
from _app import app
from database import mongo


def visualize(col):
    im_path = app.config['RAW_IMG_DIR'] + col['filename']
    img = np.array(Image.open(im_path, 'r'))

    if len(col['keypoints']['people']) == 1:
        def draw_pts(pts, col):
            for x, y, c in utils.chunker(pts, 3):
                if c > 0.05:
                    cv2.circle(img, (int(x), int(y)), 3, col, -1)

        draw_pts(col["keypoints"]['people'][0]["pose_keypoints"], (0, 255, 0))
        draw_pts(col["keypoints"]['people'][0]["hand_left_keypoints"], (255, 0, 0))
        draw_pts(col["keypoints"]['people'][0]["hand_right_keypoints"], (255, 0, 0))

    plt.imshow(img)


def display_latest_image():
    # only display latest image
    images = mongo.images.find({"cam_id": "webcam0"}, sort=[("_id", pymongo.DESCENDING)])
    im = images.next()
    display_image(im)


def display_image(im):
    print_time(im['time'])
    plt.imshow(Image.open(app.config['RAW_IMG_DIR'] + im['filename']))


def print_time(t):
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t)))


def epoch_to_strtime(t):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))


def strtime_to_epoch(strtime):
    t = datetime.strptime(strtime, '%Y-%m-%d %H:%M:%S')
    return time.mktime(t.timetuple())