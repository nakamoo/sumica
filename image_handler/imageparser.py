import numpy as np
import requests
from PIL import Image

def mean(path):
	img = np.array(Image.open(path))
	mean = np.mean(img, axis=(0, 1))
	return mean.tolist()

def detect(path):
	r = requests.post("http://localhost:5002/detect", files={'image': open(path, "rb")})
	
	return r.text