file = "/Users/Loshkarev/Downloads/broken_file.svg"

from system.shared_utils import ImgUtils
import cv2

a = ImgUtils._read_svg(file)

cv2.imshow("1", a)
cv2.waitKey(0)