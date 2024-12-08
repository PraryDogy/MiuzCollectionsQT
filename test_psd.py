import psd_tools
import logging
from PIL import Image
import cv2
import numpy as np
import os

psd_tools.psd.tagged_blocks.warn = lambda *args, **kwargs: None
psd_logger = logging.getLogger("psd_tools")
psd_logger.setLevel(logging.CRITICAL)


def psd_tools_channels(path: str):
    with open(path, 'rb') as psd_file:
        psd_file.seek(12)
        channels = int.from_bytes(psd_file.read(2), byteorder='big')
        psd_file.seek(0)

        if channels > 3:
            img = psd_tools.PSDImage.open(psd_file)
            img = img.composite()
        else:
            img = Image.open(psd_file)

        img = np.array(img)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        cv2.imshow(os.path.basename(path), img)
        cv2.waitKey(0)




src = "/Users/Morkowik/Desktop/Evgeny/_miuz/tiff_psd_images 2"
images = [
    os.path.join(src, i)
    for i in os.listdir(src)
    if i.endswith((".psd", ".psb"))
]

for i in images:
    psd_tools_channels(i)