#import sys
#sys.path.insert(0, '../../tf-faster-rcnn/tools')
#sys.path.insert(0, '../../tf-faster-rcnn/lib')
#sys.path.insert(0, '../../tf-faster-rcnn/data/coco/PythonAPI')
import json
import cv2
import numpy as np
import datetime
from sklearn import neighbors
from subprocess import call
from subprocess import Popen
from .. import actor
import time
from .bagger_model import BaggerModel
import cv2

object_names = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus','train',
	'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter','bench', 'bird', 'cat',
	'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack','umbrella', 'handbag',
	'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite','baseball bat', 'baseball glove',
	'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
	'banana', 'apple', 'sandwich', 'orange', 'broccoli','carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
	'potted plant', 'bed', 'dining table','toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
	'microwave', 'oven','toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier','toothbrush']
classes = 80

class Dataset:
	def __init__(self):
		self.update()

	def transform(self, x):
		dets = json.loads(x["detections"])
		X = []

		for det in dets:
			class_i = object_names.index(det["label"])
			class_vec = np.zeros([classes])
			class_vec[class_i] = 1
			box_vec = np.array(det["box"])
			fin_vec = np.concatenate([class_vec, box_vec], axis=0)

			X.append(fin_vec)

		return np.array(X, dtype=np.float32)

	def update(self):
		self.X = []
		self.Y = []
		tmpX = []
		tmpY = []
		y_names = []

		actions = actor.hai_db.actions
		images = actor.hai_db.images

		for action in actions.find():
			isoDate = action["time"]
			before = isoDate - datetime.timedelta(seconds=10)#minutes=1)
			results = images.find({"time":{"$gte": before, "$lt": isoDate}})

			for r in results:
				tmpX.append(r)
				tmpY.append((action["app"], action["action"]))

		for img_data, y in zip(tmpX, tmpY):
			x = self.transform(img_data)

			self.X.append(x)

			y_names.append(y)

		self.class_names = list(set(y_names))

		for y in tmpY:
			self.Y.append(self.class_names.index(y))

		print(self.class_names)

class NNActor(actor.Actor):
	def __init__(self):
		self.execute = -1
		self.action_history = []
		self.model = None
		self.rebuild()

	def rebuild(self):
		print("rebuilding")
		self.dataset = Dataset()

		if len(self.dataset.class_names) <= 0:
			return

		print("rebuilt")
		print("training actor")

		if self.model is not None:
			return

		self.model = BaggerModel(self.dataset)
		print("training complete.")

	def observe_state(self, state):
		pass

	def observe_action(self, action):
		self.rebuild()

	def act(self, state):
		if len(self.dataset.class_names) <= 0:
			return

		state = self.dataset.transform(state)

		pred_y, probs = self.model.predict([state])#[0]
		self.action_history.append(pred_y)
		probs = probs[0]

		print(["{}:{}".format(str(self.dataset.class_names[i]), probs[i]) for i in range(len(probs))])
		print(self.dataset.class_names[pred_y])

		canvas = np.zeros([300, 300, 3])
		cv2.putText(canvas, str(self.dataset.class_names[self.execute]), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, 255)
		cv2.imshow("m", canvas)
		cv2.waitKey(1)

		repeated = True

		for a, b in zip(self.action_history[-5:-1], self.action_history[-4:]):
			if a != b:
				repeated = False
				break

		msg = None

		if repeated and self.execute != self.action_history[-1]:
			self.execute = self.action_history[-1]
			msg = self.dataset.class_names[self.execute]

		if len(self.action_history) > 100:
			self.action_history = self.action_history[-50:]

		return msg

if __name__ == "__main__":
	dataset = Dataset()

	canvas = cv2.zeros([600, 800, 3])

	for x, y in zip(dataset.X, dataset.Y):
		print(x)
		print(y)