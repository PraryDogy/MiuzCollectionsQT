# from database import Dbase, ThumbsMd
# from utils.image_utils import ImageUtils
# import sqlalchemy
# from cfg import cnf

# Dbase.create_engine()
# conn = Dbase.engine.connect()
# q = sqlalchemy.select(ThumbsMd.id, ThumbsMd.img150)
# res = conn.execute(q).fetchall()

# for id, bytes_img in res:
#     img = ImageUtils.bytes_to_image_array(bytes_img)
#     img = ImageUtils.resize_max_aspect_ratio(img, cnf.IMG_SIZE)
#     img = ImageUtils.image_array_to_bytes(img, quality=100)

#     q = sqlalchemy.update(ThumbsMd).values({"img150": img}).where(ThumbsMd.id==id)
#     conn.execute(q)

# conn.commit()
# conn.close()
# Dbase.vacuum()