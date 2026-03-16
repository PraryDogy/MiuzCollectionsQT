src = "/Users/Loshkarev/Documents/_Projects/MiuzCollectionsQT/images/broken_image.jpg"


from system.shared_utils import ImgUtils
import cv2

img = ImgUtils._get_broken_image()
cv2.imshow("123", img)
cv2.waitKey(0)