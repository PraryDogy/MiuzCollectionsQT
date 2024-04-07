import os

src = "/Volumes/Untitled/_Collections/big_images/2022-04-20 13-32-22.jpg"
coll = "big_images"

old_coll = src.split(os.sep + coll + os.sep)[0]
# old_coll = src.split(os.sep)
# old_coll = old_coll[:old_coll.index(coll)]
# old_coll = "/".join(old_coll)


print(old_coll)