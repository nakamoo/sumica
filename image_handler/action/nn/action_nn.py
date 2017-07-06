import json
import cv2
import numpy as np
import datetime
from sklearn import neighbors
from subprocess import call
from subprocess import Popen
import actor
import time

imdb = get_imdb("coco_2014_minival")

class Dataset:
	def __init__(self):
		self.update()

	def transform(self, x):
		dets = json.loads(x["detections"])
		X = []

		for det in dets:
			class_i = imdb.class_names.index(det["label"])
			class_vec = np.zeros([imdb.classes])
			class_vec[class_i] = 1
			box_vec = np.array(det["box"])
			fin_vec = np.concat([class_vec, box_vec], axis=0)

			X.append(fin_vec)

		return np.array(X)

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
				tmpY.append(action)

		for img_data, y in zip(tmpX, tmpY):
			x = self.transform(img_data)

			self.X.append(x)
			y_names.append(y["action"])

		self.class_names = list(set(y_names))

		for y in tmpY:
			self.Y.append(self.class_names.index(y))

class NNActor(actor.Actor):
	def __init__(self):
		self.rebuild()
		self.execute = -1
		self.action_history = []

	def rebuild(self):
		print("rebuilding")
		self.dataset = Dataset()

		if len(self.dataset.class_names) <= 0:
			return

		# update NN

	def observe_state(self, state):
		pass

	def observe_action(self, action):
		self.rebuild()

	def act(self, state):
		if len(self.dataset.class_names) <= 0:
			return

		state = self.dataset.transform(state)

		if state:
			#pred_y = self.clf.predict([state])[0]
			self.action_history.append(pred_y)

			repeated = True

			for a, b in zip(self.action_history[-5:-1], self.action_history[-4:]):
				if a != b:
					repeated = False
					break

			if repeated and self.execute != self.action_history[-1]:
				self.execute = self.action_history[-1]
				msg = self.dataset.class_names[self.execute]
				print(msg)

				#Popen(msg, shell=True)
				#acts.execute(msg)

			if len(self.action_history) > 100:
				self.action_history = self.action_history[-50:]
