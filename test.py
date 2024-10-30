from PIL import Image
import io
from database import ThumbsMd, Dbase
import sqlalchemy
from utils import ImageUtils

ses = Dbase.get_session()
q = sqlalchemy.select(ThumbsMd.id, ThumbsMd.img150)
res = ses.execute(q).mappings().fetchall()

ids = []


for row in res:
    image = Image.open(io.BytesIO(row.get("img150")))
    width, height = image.size
    if width > 200 or height > 200:
        ids.append(row.get("id"))
        print(row.get("id"))


for id in ids:
    q = sqlalchemy.delete(ThumbsMd).where(ThumbsMd.id==id)
    ses.execute(q)

ses.commit()
ses.close()