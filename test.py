import os
from utils import MainUtils


# coll = "/Volumes/Shares-1/Collections/22 Millenium/2 Model IMG/2022_MIUZ1709_draft.jpg"
coll = "/Volumes/Shares-1/Collections/2022_MIUZ1709_draft.jpg"
coll_name = MainUtils.get_coll_name(coll)

old_coll, tail = os.path.split(coll)
old_coll = coll.split(os.sep)
old_coll = old_coll[:old_coll.index(coll_name)]
# old_coll = "/".join(old_coll)


print(old_coll)