# Author: Deepak Pathak (c) 2016

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
# from __future__ import unicode_literals
import sys

sys.path.append("../../pyflow")

import numpy as np
from PIL import Image
import time
import argparse
import pyflow
from scipy.misc import imresize
import cv2
import matplotlib.pyplot as plt

# Flow Options:
alpha = 0.012
ratio = 0.75
minWidth = 20
nOuterFPIterations = 7
nInnerFPIterations = 1
nSORIterations = 30
colType = 0  # 0 or default:RGB, 1:GRAY (but pass gray image with shape (h,w,1))
#cv2.namedWindow("frame", cv2.WINDOW_NORMAL)

def flow(im1, im2):
    s = time.time()
    u, v, im2W = pyflow.coarse2fine_flow(
        im1, im2, alpha, ratio, minWidth, nOuterFPIterations, nInnerFPIterations,
        nSORIterations, colType)
    e = time.time()
    #print('Time Taken: %.2f seconds for image of size (%d, %d, %d)' % (
    #    e - s, im1.shape[0], im1.shape[1], im1.shape[2]))
    flow = np.concatenate((u[..., None], v[..., None]), axis=2)

    hsv = np.zeros(im1.shape, dtype=np.uint8)
    hsv[:, :, 0] = 255
    hsv[:, :, 1] = 255
    mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    hsv[..., 0] = ang * 180 / np.pi / 2
    hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    #gray = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)
    gray = np.dot(rgb[...,:3], [0.3, 0.3, 0.3]) / 255.0

    gray = cv2.resize(gray, (640, 480))
    cv2.imshow("frame", gray)
    cv2.waitKey(1)
    #print(rgb)
    
    #print(np.max(rgb))
