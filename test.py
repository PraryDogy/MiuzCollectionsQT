a  = [
    "/Users/evlosh/Desktop/08.11.2024_R2018-HDR-0161.jpg",
    "/Users/evlosh/Desktop/IMAGE 2026-03-10 13:54:00.tif",
    "/Users/evlosh/Desktop/2017-09-10_14-28-38.jpg",
    "/Users/evlosh/Desktop/Без названия.txt",
]

import os

dirs = []
dirs_to_scan = list(set(
    os.path.dirname(i)
    for i in a
))


dirs.append(*dirs_to_scan)

print