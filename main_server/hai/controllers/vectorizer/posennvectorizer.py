from itertools import chain
import pickle

import cv2
import numpy as np
import scipy
from tqdm import tqdm
from imgaug import augmenters as iaa
from PIL import Image
from sklearn.ensemble import RandomForestClassifier
from sklearn import linear_model
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.externals import joblib

from controllers.learner.img2vec import NNFeatures
from controllers.learner import datasets as ds
from controllers.vectorizer.vectorizer import Vectorizer
from controllers.learner.i3dnn import I3DNN
from controllers.utils import filter_persons

import pymongo
from flask import Flask
app = Flask(__name__)
app.config.from_pyfile(filename="../../application.cfg")
mongo = pymongo.MongoClient('localhost', app.config['PORT_DB']).hai


def process_posefeature(img):
    try:
        if len(img['pose']['body']) == 1:
            return list(chain.from_iterable(img['pose']['body'][0]))
        else:
            return [0] * 54
    except:
        return [0] * 54


def search_person_index(img_col):
    if 'detections' not in img_col:
        return -1

    confs = []
    person_exists = False
    dets = img_col['detections']
    for det in dets:
        if det['label'] == 'person':
            person_exists = True
            confs.append(det['confidence'])
        else:
            confs.append(0.0)

    if not person_exists:
        return -1
    else:
        return np.argmax(confs)


class ActVectorizer(Vectorizer):
    def __init__(self, user, debug=False):
        self.user = user
        self.debug = debug
        self.nn = I3DNN()

        self.seq = iaa.Sequential([
            iaa.Sometimes(0.5,
                          iaa.GaussianBlur(sigma=(0, 0.5))
                          ),
            iaa.ContrastNormalization((0.75, 1.5)),
            iaa.AdditiveGaussianNoise(loc=0, scale=(0.0, 0.05 * 255), per_channel=0.5),
            iaa.Multiply((0.8, 1.2), per_channel=0.2),
        ], random_order=True)
        self.act_matrix = None

    def vectorize(self, X, y=None, color_augmentation_times=-1):
        if color_augmentation_times is not 1:
            raise NotImplementedError
        if self.debug:
            pbar = tqdm(total=len(X))

        features = []
        for d in X:
            features_tmp = []
            img_col0, img_col1 = d[0], d[1]
            img0 = cv2.imread("./images/raw_images/" + img_col0["filename"])
            img1 = cv2.imread("./images/raw_images/" + img_col1["filename"])
            img0 = cv2.cvtColor(img0, cv2.COLOR_BGR2RGB)
            img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
            if color_augmentation_times >= 1:
                images = self.seq.augment_images([img0, img1])
                for cam in [0, 1]:
                    index = search_person_index(d[cam])
                    if index == -1:
                        act_vec = np.zeros(1024)
                    elif 'action_crop' not in d[cam]['detections'][index]:
                        act_vec = np.zeros(1024)
                    else:
                        box = d[cam]['detections'][index]['action_crop']
                        x1, y1, x2, y2 = box
                        crop = images[cam][y1:y2, x1:x2, :]
                        crop = cv2.resize(crop, (224, 224))
                        input_img = np.array([[crop for _ in range(10)]])
                        _, _, _, act_vec = self.nn.process_image(input_img, verbose=False)

                    features_tmp.extend(act_vec)

            else:
                raise NotImplementedError

            features.append(features_tmp)
            if self.debug:
                pbar.update(1)

        self.act_matrix = np.array(features)
        return np.array(features)


class NNVectorizer(Vectorizer):
    def __init__(self, user, debug=False):
        self.user = user
        self.debug = debug
        self.nn = NNFeatures()

    def vectorize(self, X, y=None, color_augmentation_times=-1):
        features = []
        if self.debug:
            pbar = tqdm(total=len(X))

        for d in X:
            # TODO: カメラ増えても大丈夫なように
            img_col0, img_col1 = d[0], d[1]
            img0 = scipy.misc.imread("./images/raw_images/" + img_col0["filename"])
            img1 = scipy.misc.imread("./images/raw_images/" + img_col1["filename"])
            if color_augmentation_times >= 1:
                augmented_images0 = ds.augment_images([img0], color_augmentation_times,
                                                      verbose=False)
                augmented_images1 = ds.augment_images([img1], color_augmentation_times,
                                                      verbose=False)
                embed_vector0 = self.nn.img2vec([Image.fromarray(ai) for ai in augmented_images0],
                                                progress=-1)
                embed_vector1 = self.nn.img2vec([Image.fromarray(ai) for ai in augmented_images1],
                                                progress=-1)
                for v0, v1 in zip(embed_vector0, embed_vector1):
                    feature = []
                    feature.extend(v0)
                    feature.extend(v1)
                    # feature.extend(process_posefeature(img_col0))
                    # feature.extend(process_posefeature(img_col1))
                    features.append(feature)

            else:
                feature = []
                img_list = [Image.fromarray(img0), Image.fromarray(img1)]
                embed_vector = self.nn.img2vec(img_list, progress=-1)
                for v in embed_vector:
                    feature.extend(v)
                # feature.extend(process_posefeature(img0))
                # feature.extend(process_posefeature(img1))
                features.append(feature)
            if self.debug:
                pbar.update(1)

        if y is None:
            return np.array(features)
        else:
            labels = []
            for l in y:
                labels.extend([l] * color_augmentation_times)
            return np.array(features), labels

