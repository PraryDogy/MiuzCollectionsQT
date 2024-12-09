import logging
import os
from time import time

import cv2
import numpy as np
import psd_tools
from PIL import Image

from utils.utils import Utils

psd_tools.psd.tagged_blocks.warn = lambda *args, **kwargs: None
psd_logger = logging.getLogger("psd_tools")
psd_logger.setLevel(logging.CRITICAL)


def read_psd(path: str) -> np.ndarray | None:

    with open(path, 'rb') as psd_file:

        # Проверяем, что файл имеет правильную подпись PSD/PSB:
        # В начале файла (первые 4 байта) должна быть строка '8BPS', 
        # которая является стандартной подписью для форматов PSD и PSB.
        # Если подпись не совпадает, файл не является корректным PSD/PSB.
        if psd_file.read(4) != b'8BPS':
            return None

        # Переходим к байту 12, где согласно спецификации PSD/PSB
        # содержится число каналов изображения. Число каналов (2 байта)
        # определяет, сколько цветовых и дополнительных каналов содержится в файле.
        psd_file.seek(12)

        # Считываем число каналов (2 байта, big-endian формат,
        # так как PSD/PSB используют этот порядок байтов).
        channels = int.from_bytes(psd_file.read(2), byteorder='big')

        # Возвращаем указатель в начало файла (offset = 0),
        # чтобы psd-tools или Pillow могли корректно прочитать файл с самого начала.
        # Это важно, так как мы изменяли положение указателя для проверки структуры файла.
        psd_file.seek(0)

        # print(channels, os.path.basename(path))

        try:
            if channels > 3:
                img = psd_tools.PSDImage.open(psd_file)
                img = img.composite()
            else:
                img = Image.open(psd_file)
        except Exception as e:
            print("utils > error read psd", "src:", path, "channels: ", channels)
            return None

        return np.array(img)




src = "/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready/4 Royal/1 IMG"

images = [
    os.path.join(src, i)
    for i in os.listdir(src)
    if i.lower().endswith((".psd", ".psb"))
]

images = images[:30]




start = time()

for i in images:
    img = read_psd(i)

end = round(
    time() - start, 2
)
print("combine", end)




start = time()

for i in images:
    img = Utils.read_psd_pil(i)

end = round(
    time() - start, 2
)
print("pil", end)





start = time()

for i in images:
    img = Utils.read_psd_tools(i)

end = round(
    time() - start, 2
)
print("psd tools", end)