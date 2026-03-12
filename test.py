from system.shared_utils import ImgUtils
import cv2

src = "/Users/Loshkarev/Desktop/2022_MIUZ_3005_7195.psb"
img = ImgUtils.read_img(
    src
)

cv2.imshow("1", img)
cv2.waitKey(0)