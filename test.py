from cfg import Static

dynamic = []


if len(dynamic) == 1:
    exts_ = dynamic[0]
else:
    exts_ = Static.IMG_EXT

print(exts_, type(exts_))