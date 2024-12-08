import psd_tools
import logging
from PIL import Image
import cv2
import numpy as np
import os

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




src = "/Users/Morkowik/Desktop/Evgeny/_miuz/tiff_psd_images 2"
images = [
    os.path.join(src, i)
    for i in os.listdir(src)
    if i.endswith((".psd", ".psb"))
]

for i in images:
    read_psd(i)


# осталось добавить try except и готово