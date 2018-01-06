from controllers.dbreader.imagereader import ImageReader
from controllers.vectorizer.person2vec import Person2Vec
import ruptures as rpt
import time
import numpy as np
from sklearn.ensemble import RandomForestClassifier

class Learner:
    def __init__(self, username, cams, start_time):
        self.username = username
        self.cams = cams
        self.start_time = start_time
        self.models = {}
        self.data2vec = Person2Vec()
    
    def learn_model(self, x_times, x, label_set, breaks):
        y_times = [t[0] for t in label_set]
        y = [t[1] for t in label_set]
        x_indices = np.searchsorted(x_times, y_times)
        # no label = -1
        labels = np.ones(x.shape[0]) * -1
 
        #  label augmentation
        clusters = np.searchsorted(breaks, x_indices)
        for i, c in enumerate(clusters):
            labels[breaks[c-1]:breaks[c]] = y[i]

        # take out remaining unlabeled data
        labeled_mask = labels != -1
        
        labeled_x = x[labeled_mask]
        labels = labels[labeled_mask]
        
        clf = RandomForestClassifier(n_estimators=20)
        clf.fit(labeled_x, labels)
        
        return clf
    
    def create_image_matrix(self):
        imreader = ImageReader()
        end_time = time.time()
        imdata, times = imreader.read_db(self.username, self.start_time, end_time, self.cams, skip_absent=True, filtered=False)
        
        pose_mat, act_mat = self.data2vec.vectorize(imdata, get_meta=False)
        
        mat = np.concatenate([act_mat, pose_mat], axis=1)
        
        return mat, times
    
    def calculate_breakpoints(self, X):
        model = "l1"  # "l2", "rbf"
        algo = rpt.BottomUp(model=model, min_size=1, jump=1).fit(X)
        breaks = algo.predict(pen=np.log(X.shape[0])*X.shape[1]*2**2)
        
        return breaks

    def update_models(self, labels):
        X, times = self.create_image_matrix()
        breaks = self.calculate_breakpoints(X)
        
        for mode, label_set in labels.items():
            m = self.learn_model(times, X, label_set, breaks)
            self.models[mode] = m
            
        return X, times, self.models
            
    def predict(self, mode, images):
        clf = self.models[mode]
        pose_mat, act_mat = self.data2vec.vectorize(images)
        input_mat = np.concatenate([act_mat, pose_mat], axis=1)
        probs = clf.predict_proba(input_mat)
        pred_labels = clf.classes_[np.argmax(probs, axis=1)]
        confidences = np.max(probs, axis=1)
        
        return pred_labels, confidences