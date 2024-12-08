import psd_tools
import logging
from PIL import Image
import cv2
import numpy as np
import os

psd_tools.psd.tagged_blocks.warn = lambda *args, **kwargs: None
psd_logger = logging.getLogger("psd_tools")
psd_logger.setLevel(logging.CRITICAL)


def read_psd(path: str):
    with open(path, 'rb') as psd_file:

        if psd_file.read(4) != b'8BPS':
            return None

        psd_file.seek(12)
        channels = int.from_bytes(psd_file.read(2), byteorder='big')
        psd_file.seek(0)

        try:
            if channels > 3:
                img = psd_tools.PSDImage.open(psd_file)
                img = img.composite()

            else:
                img = Image.open(psd_file)
        
        except Exception as e:
            print("utils > error read psd", path)
            return None

        return np.array(img)




src = "/Users/Morkowik/Desktop/Evgeny/_miuz/tiff_psd_images 2"
images = [
    os.path.join(src, i)
    for i in os.listdir(src)
    if i.endswith((".psd", ".psb"))
]

for i in images:
    read_psd(i)


# осталось добавить try except и готово