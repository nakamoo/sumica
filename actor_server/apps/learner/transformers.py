def person_point(x):
	dets = x["detections"]

	max_area = 0
	pt = None
	for det in dets:
		if det["label"] == "person":
			#print(det)
			area = (det["box"][2]-det["box"][0])*(det["box"][3]-det["box"][1])
			if area > max_area:
				cX = (det["box"][0] + det["box"][2]) / 2.0
				cY = (det["box"][1] + det["box"][3]) / 2.0
				max_area = area
				pt = [cX, cY]

	return pt

def person_rect(x):
	dets = x["detections"]

	max_area = 0
	pt = None
	for det in dets:
		if det["label"] == "person":
			#print(det)
			area = (det["box"][2]-det["box"][0])*(det["box"][3]-det["box"][1])
			if area > max_area:
				cX = (det["box"][0] + det["box"][2]) / 2.0
				cY = (det["box"][1] + det["box"][3]) / 2.0
				w = det["box"][2] - det["box"][0]
				h = det["box"][3] - det["box"][1]
				max_area = area
				pt = [cX, cY, w, h]

	return pt