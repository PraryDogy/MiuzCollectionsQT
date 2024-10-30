from utils import ImageUtils
from database import Dbase, ThumbsMd
import sqlalchemy
import cv2


src = "/Volumes/Shares-1/Collections/0 Other/1 IMG/2020-02-12 20-44-30 (B,Radius4,Smoothing1).jpg"
img = ImageUtils.read_image(src)
# img = ImageUtils.crop_to_square(img)
# img = ImageUtils.resize_min_aspect_ratio(img, 200)

test = ImageUtils.image_array_to_bytes(img)


# cv2.imshow("123", img)
# cv2.waitKey(0)


# sess = Dbase.get_session()
# byte_img = ImageUtils.image_array_to_bytes(img)
# q = sqlalchemy.insert(ThumbsMd).values({"img150": byte_img})
# sess.execute(q)
# sess.commit()
# sess.close()