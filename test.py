import io
import numpy as np
import tifffile
from PIL import Image, ImageCms
from system.shared_utils import ImgUtils
import cv2

jpg_path = "/Users/Loshkarev/Desktop/N01-MLN2782H_2.jpg"  # ваш jpg
tif_path = "/Users/Loshkarev/Desktop/N01-MLN2782H_2.tif"  # ваш tif

img_arr = ImgUtils.read_img(jpg_path)
img_arr = cv2.cvtColor(img_arr, cv2.COLOR_BGR2RGB)

cv2.imshow("1", img_arr)
cv2.waitKey(0)