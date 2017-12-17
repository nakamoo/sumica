from itertools import chain
import pickle

import numpy as np
import scipy
from tqdm import tqdm
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


def process_posefeature(img):
    try:
        if len(img['pose']['body']) == 1:
            return list(chain.from_iterable(img['pose']['body'][0]))
        else:
            return [0] * 54
    except:
        return [0] * 54


class PoseNNVectorizer(Vectorizer):
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
                    feature.extend(process_posefeature(img_col0))
                    feature.extend(process_posefeature(img_col1))
                    features.append(feature)

            else:
                feature = []
                img_list = [Image.fromarray(img0), Image.fromarray(img1)]
                embed_vector = self.nn.img2vec(img_list, progress=-1)
                for v in embed_vector:
                    feature.extend(v)
                feature.extend(process_posefeature(img0))
                feature.extend(process_posefeature(img1))
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

