from utils.utils import Utils


src = "/Users/Loshkarev/Desktop/R2018-MLN-0258.psd"
a = Utils.read_image(full_src=src)

import cv2
cv2.imshow("123", a)
cv2.waitKey(0)