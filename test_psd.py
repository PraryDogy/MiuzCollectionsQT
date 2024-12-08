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
    img = Image.open(path)
    img = np.array(img)
    name = os.path.basename(path)
    cv2.imshow(name, img)
    cv2.waitKey(0)

src = "/Users/Morkowik/Desktop/Evgeny/_miuz/tiff_psd_images 2"
images = [
    os.path.join(src, i)
    for i in os.listdir(src)
    if i.endswith((".psd", ".psb"))
]

for i in images:
    psd_tools_channels(i)