import math

import cv2
from matplotlib import pylab as plt
from PIL import Image
import matplotlib.animation as animation
import numpy as np
import pymongo
from pymongo import MongoClient
import time
from datetime import datetime
from flask import Flask

import controllers.utils as utils

app = Flask(__name__)
app.config.from_pyfile(filename="../../application.cfg")
mongo = MongoClient('localhost', app.config['PORT_DB']).hai


def visualize(col):
    im_path = app.config['RAW_IMG_DIR'] + col['filename']
    img = np.array(Image.open(im_path, 'r'))

    def draw_pts(pts, col):
        for x, y, c in pts:
            if c > 0.05:
                cv2.circle(img, (int(x), int(y)), 3, col, -1)
    if len(col['pose']['body']) == 1:
        draw_pts(col['pose']['body'][0], (0, 255, 0))
    if len(col['pose']['hand']) == 1:
        draw_pts(col['pose']['hand'][0], (0, 255, 0))
    if len(col['pose']['face']) == 1:
        draw_pts(col['pose']['face'][0], (0, 255, 0))

    # plt.imshow(img)
    # return Image.fromarray(img)
    return img


def display_latest_image():
    # only display latest image
    images = mongo.images.find(sort=[("_id", pymongo.DESCENDING)])
    im = images.next()
    display_image(im)


def display_image(im, pose=False):
    print_time(im['time'])
    if pose:
        img = visualize(im)
        plt.imshow(img)
    else:
        plt.imshow(Image.open(app.config['RAW_IMG_DIR'] + im['filename']))


def display_two_images(ims, pose=False):
    im0 = ims[0]
    im1 = ims[1]
    fig, (axL, axR) = plt.subplots(ncols=2, figsize=(10, 4))
    if pose:
        img0 = visualize(im0)
        axL.imshow(img0)
    else:
        axL.imshow(Image.open(app.config['RAW_IMG_DIR'] + im0['filename']))
    axL.text(0.0, 1.0, epoch_to_strtime(im0['time']),
             horizontalalignment='left', verticalalignment='bottom')

    if pose:
        img1 = visualize(im1)
        axR.imshow(img1)
    else:
        axR.imshow(Image.open(app.config['RAW_IMG_DIR'] + im1['filename']))
    axR.text(0.0, 1.0, epoch_to_strtime(im1['time']),
             horizontalalignment='left', verticalalignment='bottom')


def print_time(t):
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t)))


def epoch_to_strtime(t):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))


def strtime_to_epoch(strtime):
    t = datetime.strptime(strtime, '%Y-%m-%d %H:%M:%S')
    return time.mktime(t.timetuple())


class UpdateDist(object):
    def __init__(self, axL, axR, image_pairs, info=None, skip=1, pose=False):
        self.image_pairs = image_pairs
        self.axL = axL
        self.axR = axR

        self.axL.set_xticklabels([])
        self.axR.set_xticklabels([])
        self.axL.set_yticklabels([])
        self.axR.set_yticklabels([])
        self.axL.grid(False)
        self.axR.grid(False)
        self.info = info
        self.skip = skip
        self.length = math.ceil(len(image_pairs) / skip)
        self.pose = pose

    def __call__(self, i):
        self.axL.clear()
        im1 = self.image_pairs[self.skip * i][1]
        if self.pose:
            img1 = visualize(im1)
            self.axL.imshow(img1)
        else:
            im1_path = app.config['RAW_IMG_DIR'] + im1['filename']
            img1 = Image.open(im1_path, 'r')
            self.axL.imshow(img1)
        self.axL.text(0.0, 1.0, epoch_to_strtime(im1['time']),
                      horizontalalignment='left', verticalalignment='bottom')
        if self.info is not None:
            self.axL.text(300, 0, str(self.info[self.skip * i]),
                          horizontalalignment='right', verticalalignment='bottom')

        self.axR.clear()
        im0 = self.image_pairs[self.skip * i][0]
        if self.pose:
            img = visualize(im0)
            self.axR.imshow(img)
        else:
            im0_path = app.config['RAW_IMG_DIR'] + im0['filename']
            img0 = Image.open(im0_path, 'r')
            self.axR.imshow(img0)
        self.axR.text(0, 1.0, epoch_to_strtime(im0['time']),
                      horizontalalignment='left', verticalalignment='bottom')

        return self.axL, self.axR


