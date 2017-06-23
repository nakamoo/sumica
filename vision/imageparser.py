import numpy as np
from PIL import Image

def mean(path):
	img = np.array(Image.open(path))
	mean = np.mean(img, axis=(0, 1))
	return mean.tolist()