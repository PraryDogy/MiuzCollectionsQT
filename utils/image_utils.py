import io
import os
import subprocess
from random import randint

import cv2
import numpy as np
from PyQt5.QtCore import QByteArray
from PyQt5.QtGui import QPixmap

from cfg import cnf
from database import *

from .main_utils import MainUtils


class ReadImage:
    def __init__(self, src: str, desaturate_value: float) -> io.BytesIO:
        super().__init__()

        img = cv2.imread(src, cv2.IMREAD_UNCHANGED)

        if img.shape[-1] == 4:
            img = self.read_transparent_png(img)

        if len(img.shape) == 2:
            self.rgb_image = img
            return

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hsv[:, :, 1] = hsv[:, :, 1] * desaturate_value
        self.rgb_image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    def read_transparent_png(self, image) -> np.ndarray:
        alpha_channel = image[:, :, 3]
        rgb_channels = image[:, :, :3]

        # Преобразуйте значения альфа-канала в диапазон от 0 до 1
        alpha_factor = alpha_channel[:, :, np.newaxis] / 255.0

        # Установите цвет фона (в данном случае, черный)
        background_color = np.array([0, 0, 0], dtype=np.uint8)

        # Создайте изображение фона
        background = np.full_like(rgb_channels, background_color)

        # Сложите изображение и фон
        return (
            rgb_channels * alpha_factor + background * (1 - alpha_factor)
            ).astype(np.uint8)

    def get_bgr_image(self):
        return self.rgb_image
    
    def get_rgb_image(self) -> bytearray:
        return cv2.cvtColor(self.rgb_image, cv2.COLOR_BGR2RGB)


class PixmapFromBytes(QPixmap):
    def __init__(self, byte_array: QByteArray) -> QPixmap:
        super().__init__()

        ba = QByteArray(byte_array)
        self.loadFromData(ba, "JPEG")
        self.crop_to_center()

    def crop_to_center(self):
        ax = (self.width() - cnf.THUMBSIZE) // 2
        ay = (self.height() - cnf.THUMBSIZE) // 2

        crop = self.copy(ax, ay, cnf.THUMBSIZE, cnf.THUMBSIZE)
        self.swap(crop)


class UndefBytesThumb(io.BytesIO,  MainUtils):
    def __init__(self):
        super().__init__()
        img = cv2.imread("images/thumb.jpg")
        res, buffer = cv2.imencode(".JPEG", img)
        self.write(buffer)


class HeifImage:
    def __init__(self, img_src) -> str:
        self.img_src = img_src
        self.heif_to_jpg = "applescripts/heif_to_jpg.scpt"
        is_heif = "applescripts/heif_check.scpt"

        result = subprocess.run(
            ["osascript", is_heif, img_src],
            capture_output=True,
            text=True
            )

        is_heif = None

        if result.returncode == 0:
            self.converted_img_path = self.convert_heif_to_jpeg()
        else:
            raise ZeroDivisionError("not heif")

    def convert_heif_to_jpeg(self) -> str:
        temp_img = os.path.join(
            cnf.app_support_app_dir,
            f"{randint(0, 100000)}.jpg"
            )

        result = subprocess.run(
            ["osascript", self.heif_to_jpg, self.img_src, temp_img],
            capture_output=True,
            text=True
            )

        self.heif_to_jpg = None

        if result.returncode == 0:
            return temp_img
        else:
            raise ZeroDivisionError("heif convert err")


class BaseBytesThumb(io.BytesIO):
    def __init__(self, src: str) -> io.BytesIO:
        super().__init__()

        img = ReadImage(src)
        img = img.get_bgr_image()

        resized = self.fit_thumb(img)
        res, buffer = cv2.imencode(".JPEG", resized)
        self.write(buffer)

    def fit_thumb(self, img):
        height, width = img.shape[:2]
        min_side = min(height, width)
        scale_factor = cnf.THUMBSIZE / min_side
        new_height = int(height * scale_factor)
        new_width = int(width * scale_factor)
        return cv2.resize(
            img,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA
            )


class BytesThumb(io.BytesIO):
    def __init__(self, img_src: str) -> None:
        super().__init__()

        try:
            bytes_thumb = BaseBytesThumb(img_src)
            self.write(bytes_thumb.getvalue())

        except Exception as e:
            print(f"Bytes thumb: {str(e)}, try heif convert")
        
        if not self.getvalue():
            try:
                heif = HeifImage(img_src)
                bytes_thumb = BaseBytesThumb(heif.converted_img_path)
                self.write(bytes_thumb.getvalue())
                os.remove(heif.converted_img_path)

            except Exception as e:
                print(f"Unable to convert HEIF to JPEG: {str(e)}")
            
        if not self.getvalue():
            raise ZeroDivisionError("Unable to open or convert image.")
