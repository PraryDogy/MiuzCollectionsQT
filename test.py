from system.utils import Utils
from system.shared_utils import ImgUtils
import cv2

src = '/Users/Loshkarev/Desktop/ПРОБЛЕМНЫЙ ПНГ/E2018-EMP-0067.png'
# src = '/Users/Loshkarev/Desktop/ПРОБЛЕМНЫЙ ПНГ/E2018-EMP-0067 — копия.png'
dst = '/Users/Loshkarev/Desktop/ПРОБЛЕМНЫЙ ПНГ/test.png'

# img = ImgUtils.read_img(src)
img = ImgUtils._read_png(src)
# cv2.imshow("1", img)
# cv2.waitKey(0)