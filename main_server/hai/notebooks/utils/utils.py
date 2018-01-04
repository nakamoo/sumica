import math

import cv2
from matplotlib import pylab as plt
from matplotlib.pyplot import imread
from PIL import Image
import matplotlib.animation as animation
import numpy as np
import pymongo
from pymongo import MongoClient
import time
from datetime import datetime
from flask import Flask
import configparser
import matplotlib.cm as cm

import controllers.utils as utils

config = configparser.ConfigParser()
config.read('application.cfg')
mongo = MongoClient('localhost', int(config["flask"]["PORT_DB"])).hai


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


class ImageUpdater(object):
    def __init__(self, axes, imdata, pose_mat, act_mat, com_mat, meta, labels):
        self.axes = axes
        self.imdata = imdata
        self.pose_mat = pose_mat
        self.act_mat = act_mat
        self.com_mat = com_mat
        self.meta = meta
        self.acts = [[] for _ in range(len(self.axes[0]))]
        self.act_classes = []
        self.labels = labels
        
        for ax in self.axes[0]:
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.grid(False)
            
        for scene in meta:
            for view in scene:
                if view is not None and "action" in view:
                    self.act_classes.append(view["action"])
                    
        self.act_classes = list(set(self.act_classes))

    def __call__(self, scene_i):
        print(scene_i)
        
        for view_i, ax in enumerate(self.axes[0]):
            ax.clear()
            data = self.imdata[scene_i][view_i]
            m = self.meta[scene_i][view_i]
            
            img = imread("images/raw_images/" + data["filename"])
            #img = utils.visualize(img, data, draw_objects=False)
            if m is not None:
                utils.draw_object(img, m)
                
                if "pose_body_index" in m:
                    utils.draw_pose(img, data["pose"]["body"][m["pose_body_index"]])
                
            ax.imshow(img)
            text = epoch_to_strtime(data['time']) + " {}/{}".format(scene_i+1, len(self.imdata))
            
            if m is not None and "action" in m:
                self.acts[view_i].append(self.act_classes.index(m["action"])+1)
                text += " " + m["action"]
            else:
                self.acts[view_i].append(0)
                
            ax.set_title(text)
            
        def draw_scatter(ax, mat, title):
            ax.clear()
            ax.set_title(title)
            ax.set_xlim(np.min(mat[:, 0]), np.max(mat[:, 0]))
            ax.set_ylim(np.min(mat[:, 1]), np.max(mat[:, 1]))
            if self.labels is None:
                col = "blue"
            else:
                col = self.labels[:scene_i]
                
            ax.scatter(mat[:scene_i, 0], mat[:scene_i, 1], c=col, cmap="rainbow")
            ax.scatter(mat[scene_i, 0], mat[scene_i, 1], c="black", marker="*", s=300)
            
        if self.pose_mat is not None:
            draw_scatter(self.axes[1][0], self.pose_mat, "pose concat vector")
            
        if self.act_mat is not None:
            draw_scatter(self.axes[2][0], self.act_mat, "action cnn concat vector")
            
        draw_scatter(self.axes[3][0], self.com_mat, "combined vector")
        
        #for i in range(len(self.axes[0])):
        #    self.axes[1][i].clear()
        #    self.axes[1][i].imshow([self.acts[i]], aspect='auto', cmap="rainbow")

        return self.axes