import os

coll = "/Volumes/Shares-1/Studio/Photo/Art/Ready/22 Millenium/2 Model IMG/2022_MIUZ1709_draft.jpg"
coll_name = "22 Millenium"

old_coll = coll.split(os.sep)
old_coll = old_coll[:old_coll.index(coll_name)]
old_coll = "/".join(old_coll)

print(old_coll)