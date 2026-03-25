from system.shared_utils import ImgUtils
from PIL import Image
from pathlib import Path
import cv2

img = ImgUtils._get_broken_image()
cv2.imshow("1", img)
cv2.waitKey(0)