
class Thing:
	def __init__(self, det):
		self.box = det["box"]
		self.label = det["label"]
		self.history = []

	def iou(self, boxA, boxB):
		xA = max(boxA[0], boxB[0])
		yA = max(boxA[1], boxB[1])
		xB = min(boxA[2], boxB[2])
		yB = min(boxA[3], boxB[3])
	 
		# compute the area of intersection rectangle
		interArea = (xB - xA + 1) * (yB - yA + 1)
	 
		# compute the area of both the prediction and ground-truth
		# rectangles
		boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
		boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
	 
		# compute the intersection over union by taking the intersection
		# area and dividing it by the sum of prediction + ground-truth
		# areas - the interesection area
		iou = interArea / float(boxAArea + boxBArea - interArea)
	 
		# return the intersection over union value
		return iou

	def match(self, det):
		if self.label == det["label"] and self.iou(self.box, det["box"]) > 0.5:
			return True

		return False

class Tracker:
	def __init__(self):
		self.past_n = 10
		self.things = []

	def update(self, d):
		dets = list(d)

		for i, thing in enumerate(self.things):
			match = None

			for det in dets:
				if thing.match(det):
					match = det
					del det
					break

			if match:
				# update
				thing.history.append(1)
				thing.box = match["box"]
				thing.label = match["label"]
			else:
				thing.history.append(0)

		for det in dets:
			thing = Thing(det)
			thing.history.append(0)
			self.things.append(thing)

		clean_dets = []

		for thing in self.things:
			if len(thing.history) >= self.past_n:
				avg_conf = sum(thing.history[-self.past_n:]) / self.past_n

				if avg_conf <= 0.5:
					del thing
				elif avg_conf >= 0.7:
					clean_dets.append({"label": thing.label, "box": thing.box, "confidence": -1})

		return clean_dets
			