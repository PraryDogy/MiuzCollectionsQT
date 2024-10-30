from utils import ImageUtils, ResizeImg
from database import Dbase, ThumbsMd
import sqlalchemy


src = "/Users/Loshkarev/Desktop/S29 E53 R66 N028/2024-10-14 21-43-49.tif"
img = ImageUtils.read_image(src)
img = ResizeImg.crop_to_square(img)
img = ResizeImg.resize_aspect_ratio(img, 200)


import cv2
cv2.imshow("123", img)
cv2.waitKey(0)


# sess = Dbase.get_session()
# byte_img = ImageUtils.image_array_to_bytes(img)
# q = sqlalchemy.insert(ThumbsMd).values({"img150": byte_img})
# sess.execute(q)
# sess.commit()
# sess.close()