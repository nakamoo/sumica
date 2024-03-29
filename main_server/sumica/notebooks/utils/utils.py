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
from sklearn.preprocessing import normalize

from controllers.learner import datasets as ds

from controllers.dbreader.utils import get_db

mongo = get_db()
app = Flask(__name__)
app.config.from_pyfile(filename="../../application.cfg") # needs cleanup with Config module

import controllers.utils as utils
from controllers.dbreader.utils import get_db
from config import Config

def visualize(col, pose=True, detect_human=True):
    im_path = app.config['RAW_IMG_DIR'] + col['filename']
    img = np.array(Image.open(im_path, 'r'))

    if detect_human:
        person, _, _, _ = ds.person_box(col)
        if person is not None:
            person_box = list(person['box'])
            cv2.putText(img, '{:.3f}'.format(person['confidence']), (person_box[0], person_box[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 1)
            cv2.rectangle(img, (person_box[0], person_box[1]), (person_box[2], person_box[3]), (255,0,0), 3)

    if pose:
        def draw_pts(pts, col):
            for x, y, c in pts:
                if c > 0.05:
                    cv2.circle(img, (int(x), int(y)), 3, col, -1)
        if 'pose' not in col:
            return img

        if len(col['pose']['body']) == 1:
            draw_pts(col['pose']['body'][0], (0, 255, 0))
        if len(col['pose']['hand']) == 1:
            draw_pts(col['pose']['hand'][0], (0, 255, 0))
        if len(col['pose']['face']) == 1:
            draw_pts(col['pose']['face'][0], (0, 255, 0))

    # plt.imshow(img)
    # return Image.fromarray(img)
    return img


def display_latest_image(cam=None):
    # only display latest image
    if cam is None:
        images = mongo.images.find(sort=[("_id", pymongo.DESCENDING)])
    else:
        images = mongo.images.find({'cam_id': cam}, sort=[("_id", pymongo.DESCENDING)])
    im = images.next()
    display_image(im)


def display_image(im, pose=False, diff=False):
    print_time(im['time'])
    if pose:
        img = visualize(im, pose=True)
        plt.imshow(img)
    elif diff:
        plt.imshow(Image.open(app.config['RAW_IMG_DIR'] + im['diff_filename']))
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
    def __init__(self, axL, axR, image_pairs, info=None, skip=1, pose=False, human=False):
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
        self.human = human

    def __call__(self, i):
        self.axL.clear()
        im1 = self.image_pairs[self.skip * i][1]
        if self.pose or self.human:
            img1 = visualize(im1, pose=self.pose, detect_human=self.human)
            self.axL.imshow(img1)
        else:
            im1_path = app.config['RAW_IMG_DIR'] + im1['filename']
            img1 = Image.open(im1_path, 'r')
            self.axL.imshow(img1)
        self.axL.text(0.0, 1.0, epoch_to_strtime(im1['time']),
                      horizontalalignment='left', verticalalignment='bottom')
        if self.info is not None:
            self.axL.text(0, 40, str(self.info[self.skip * i]),
                          horizontalalignment='left', verticalalignment='bottom')

        self.axR.clear()
        im0 = self.image_pairs[self.skip * i][0]
        if self.pose or self.human:
            img = visualize(im0, pose=self.pose, detect_human=self.human)
            self.axR.imshow(img)
        else:
            im0_path = app.config['RAW_IMG_DIR'] + im0['filename']
            img0 = Image.open(im0_path, 'r')
            self.axR.imshow(img0)
        self.axR.text(0, 1.0, epoch_to_strtime(im0['time']),
                      horizontalalignment='left', verticalalignment='bottom')

        return self.axL, self.axR


class ImageUpdater(object):
    def __init__(self, cams, axes, imdata, pose_mat, act_mat, com_mat, meta, raw_labels, labels, predictions, classes, out2class, diffs, mask, bkpts, mode_breaks, clusters, skip=1):
        self.cams = cams
        self.axes = axes
        self.imdata = imdata
        self.pose_mat = pose_mat
        self.act_mat = act_mat
        self.com_mat = com_mat
        self.meta = meta
        self.acts = [[] for _ in range(len(self.axes[0]))]
        self.act_classes = []
        self.labels = labels
        self.predictions = predictions
        self.classes = classes#.tolist()
        self.skip = skip
        self.diffs = diffs
        self.mask = mask
        self.bkpts = bkpts
        self.out2class = out2class
        self.raw_labels = raw_labels
        #self.certainty = certainty
        self.mode_breaks = mode_breaks
        self.clusters = clusters
        
        if self.diffs is None:
            self.diffs = np.sin(np.arange(0, com_mat.shape[0] / 0.1, 0.1))
        self.diffs /= np.max(self.diffs) # normalize
        
        self.colors = []
        
        #for c in self.classes:
        #    self.colors.append(np.random.uniform(0, 1, 3))
            
        self.colors = list([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [0, 1, 1], [1, 0, 1], [1, 0.5, 0], [0, 1, 0.5]])[:len(self.classes)]
        self.colors.append([0.5, 0.5, 0.5])
        self.colors = np.array(self.colors)
        
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
        
        for view_i in range(len(self.cams)):
            ax = self.axes[0][view_i]
            data = self.imdata[scene_i][view_i]
            m = self.meta[scene_i][view_i]
            
            img = imread(Config.RAW_IMG_DIR + data["filename"])
            #img = utils.visualize(img, data, draw_objects=False)
            if m is not None:
                utils.draw_object(img, m)
                
                if "pose_body_index" in m:
                    utils.draw_pose(img, data["pose"]["body"][m["pose_body_index"]])
                
            ax.clear()
            ax.imshow(img)
            text = "#" + str(self.mask[scene_i]) + ": " + epoch_to_strtime(data['time']) + " {}/{}".format(scene_i+1, len(self.imdata))
            
            if m is not None and "action" in m:
                self.acts[view_i].append(self.act_classes.index(m["action"]))
                text += "  \n " + m["action"] + ", prediction: " + self.classes[self.out2class[np.argmax(self.predictions[scene_i])]] + " " + str(int(np.max(self.predictions[scene_i])*100)) + "%"
            else:
                self.acts[view_i].append(0)
                
            ax.set_title(text)
            
        def draw_scatter(ax, mat, title, labs):
            ax.clear()
            ax.set_title(title)
            ax.set_xlim(np.min(mat[:, 0]), np.max(mat[:, 0]))
            ax.set_ylim(np.min(mat[:, 1]), np.max(mat[:, 1]))
            if self.labels is None:
                col = "blue"
                ax.scatter(mat[:scene_i, 0], mat[:scene_i, 1], c=col)
            else:
                ax.scatter(mat[:scene_i, 0], mat[:scene_i, 1], c=self.colors[-1], label="etc")
                
                for i, c in enumerate(self.classes):
                    #if c != "etc":
                    m = labs == i
                    ax.scatter(mat[m, 0], mat[m, 1], c=self.colors[i], label=self.classes[i])

                ax.legend()
                
            ax.scatter(mat[scene_i, 0], mat[scene_i, 1], c="black", marker="*", s=300)
            
        if self.pose_mat is not None:
            draw_scatter(self.axes[1][0], self.pose_mat, "pose concat vector")
            
        if self.act_mat is not None:
            draw_scatter(self.axes[2][0], self.act_mat, "action cnn concat vector")
            
        """
        self.axes[1][2].clear()
        self.axes[1][2].imshow(self.clusters[:, None].T, aspect="auto")
        i = np.searchsorted(self.bkpts, scene_i)
        self.axes[1][2].set_ylim(0, 0.5)
        self.axes[1][2].plot([i, i], [0, 0.5], '-', lw=2, c='red')
        if i < len(self.clusters):
            self.axes[1][2].set_title("cluster: {}".format(self.clusters[i]))
        """
            
        if self.com_mat is not None:
            draw_scatter(self.axes[2][1], self.com_mat, "predictions", self.out2class[np.argmax(self.predictions, axis=1)])
            draw_scatter(self.axes[2][0], self.com_mat, "labels", self.labels)
            
        drawto = len(self.com_mat)-1
        marker = scene_i
        #drawto = scene_i
        
        self.axes[2][2].clear()
        self.axes[2][2].set_ylim(-0.2, 1.2)
        self.axes[2][2].set_title("classification certainty")
        self.axes[2][2].plot(np.max(self.predictions[:drawto], axis=1))
        self.axes[2][2].plot([marker,marker], [-2, 2], '-', lw=2, c='blue')
        self.axes[2][2].set_xlim(max(0, marker-200), marker+50)
            
        self.axes[1][0].clear()
        self.axes[1][0].set_title("image difference")
        
        for start, end in zip([0] + self.bkpts[:-1], self.bkpts):
            labs = None
            
            if start > drawto:
                break
            elif drawto > end:
                p = self.axes[1][0].plot(np.arange(start, end), self.diffs[start:end])
                labs = self.labels[start:end]
                self.axes[1][0].plot([end,end], [-2, 2], '--', lw=1, c='red')
                
                
            elif drawto >= start:
                p = self.axes[1][0].plot(np.arange(start, drawto), self.diffs[start:drawto])
                labs = self.labels[start:drawto]
            
            if p is not None:
                labs_loc = np.where(labs != -1)[0]
                if len(labs_loc) > 0:
                    self.axes[1][0].scatter(labs_loc + start, np.ones_like(labs_loc), c=self.colors[labs[labs_loc]])
                    
        #for b in self.mode_breaks:
        #    self.axes[1][0].plot([b, b], [-2, 2], '--', lw=1, c='blue')
        for b in self.bkpts:
            self.axes[1][0].plot([b, b], [-2, 2], '--', lw=2, c='red')
        
                    
        self.axes[1][0].set_ylim(-0.2, 1.2)
        self.axes[1][0].set_xlim(max(0, marker-200), marker+50)
        self.axes[1][0].scatter(np.arange(drawto), np.ones(drawto) * -0.1, c=self.colors[self.out2class[np.argmax(self.predictions[:drawto], axis=1)]])
        lab_x = np.where(self.raw_labels[:drawto] != -1)
        lab_c = self.raw_labels[lab_x]
        self.axes[1][0].scatter(lab_x, np.ones_like(lab_x) * 0.8, c=self.colors[lab_c], marker="*")
        
        self.axes[1][0].plot([marker,marker], [-2, 2], '-', lw=2, c='blue')

        self.axes[1][1].clear()
        self.axes[1][1].set_title("clusters")
        self.axes[1][1].set_xlim(np.min(self.com_mat[:, 0]), np.max(self.com_mat[:, 0]))
        self.axes[1][1].set_ylim(np.min(self.com_mat[:, 1]), np.max(self.com_mat[:, 1]))
        
        for start, end in zip([0] + self.bkpts[:-1], self.bkpts):
            if start > scene_i:
                break
            elif scene_i >= start:
                self.axes[1][1].scatter(self.com_mat[start:scene_i, 0], self.com_mat[start:scene_i, 1])
            else:
                self.axes[1][1].scatter(self.com_mat[start:end, 0], self.com_mat[start:end, 1])
        
        #for i in range(len(self.axes[0])):
        #    self.axes[1][i].clear()
        #    self.axes[1][i].imshow([self.acts[i]], aspect='auto', cmap="rainbow")

        return self.axes
    
    def write_video(cams, models, misc, mode, path, skip=5, class_names=None):
        mat = misc["matrix"]
        print("total frames:", mat.shape[0])
        
        fig, axes = plt.subplots(3, max(len(cams), 3), figsize=(12,9), squeeze=False)
        
        predictions = models[mode].predict_proba(mat)
        classes = models[mode].classes_
        raw_labels = misc["train_labels"][mode]["raw"]
        train_labels = misc["train_labels"][mode]["augmented"]
        mat.shape[0]
        
        diffs = np.array(([0] + np.sum(mat[:-1] - mat[1:], axis=1)**2.0)[:, None])

        if class_names is None:
            class_names = [str(c) for c in classes]
            
        updater = ImageUpdater(cams, axes, np.array(misc["raw_data"]), None, None, mat,
                               np.array(misc["meta"]), raw_labels, train_labels, predictions, class_names, classes, diffs, range(mat.shape[0]), misc["breaks"], misc["mode_breaks"][mode], misc["clusters"], skip=skip)
        fig.tight_layout()
        ani = animation.FuncAnimation(fig, updater, frames=list(range(0, len(misc["matrix"]), skip)) + [len(misc["matrix"])-1], interval=100, repeat=False)
        ani.save(path, writer="ffmpeg")