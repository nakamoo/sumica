import numpy as np
from PIL import Image

def mean(path):
	img = np.array(Image.open(path))
	return np.mean(img, axis=(0, 1))