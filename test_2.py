import cv2
import numpy as np


def is_grayscale(img: np.ndarray, saturation_threshold=3):
    if len(img.shape) < 3 or img.shape[2] == 1:
        return True
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    _, s, _ = cv2.split(hsv)
    mean_saturation = np.mean(s)
    return mean_saturation < saturation_threshold

src = "/Users/evlosh/Desktop/R1-01777-0006 А4 3.jpg"
img = cv2.imread(src)
result = is_grayscale_hsv(img)

print(result)