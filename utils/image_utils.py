import io
import logging
import os
import subprocess
import traceback
from random import randint

import cv2
import numpy as np
import psd_tools
from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtGui import QImage, QPixmap
from tifffile import tifffile

from cfg import cnf
from database import *

from .main_utils import MainUtils

psd_tools.psd.tagged_blocks.warn = lambda *args, **kwargs: None
psd_logger = logging.getLogger("psd_tools")
psd_logger.setLevel(logging.CRITICAL)

class ImageUtils:
    @classmethod
    def read_tiff(cls, path: str) -> np.ndarray | None:
        try:
            img = tifffile.imread(files=path)[:,:,:3]
            if str(object=img.dtype) != "uint8":
                img = (img/256).astype(dtype="uint8")
            # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            return img
        except (tifffile.tifffile.TiffFileError, RuntimeError) as e:
            cls.print_error(cls, e)
            return None

    @classmethod
    def read_psd(cls, path: str) -> np.ndarray | None:
        try:
            img = psd_tools.PSDImage.open(fp=path)
            img = img.composite()

            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            img = np.array(img)
            return img

        except Exception as e:
            cls.print_error(cls, e)
            return None
            
    @classmethod
    def read_jpg(cls, path: str) -> np.ndarray | None:
        try:
            image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            return image
        except (Exception, cv2.error) as e:
            cls.print_error(cls, e)
            return None
        
    @classmethod
    def read_png(cls, path: str) -> np.ndarray | None:
        try:
            image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if image.shape[2] == 4:
                alpha_channel = image[:, :, 3] / 255.0
                rgb_channels = image[:, :, :3]
                background_color = np.array([255, 255, 255], dtype=np.uint8)
                background = np.full(rgb_channels.shape, background_color, dtype=np.uint8)
                converted = (rgb_channels * alpha_channel[:, :, np.newaxis] + background * (1 - alpha_channel[:, :, np.newaxis])).astype(np.uint8)
            else:
                converted = image
            converted = cv2.cvtColor(converted, cv2.COLOR_BGR2RGB)
            return converted
        
        except Exception as e:
            cls.print_error(cls, e)
            return None

    @classmethod
    def read_image(cls, src: str) -> np.ndarray | None:

        src_lower: str = src.lower()

        if src_lower.endswith((".psd", ".psb")):
            img = cls.read_psd(src)

        elif src_lower.endswith((".tiff", ".tif")):
            img = cls.read_tiff(src)

        elif src_lower.endswith((".jpg", ".jpeg", "jfif")):
            img = cls.read_jpg(src)

        elif src_lower.endswith((".png")):
            img = cls.read_png(src)

        else:
            img = None

        return img
    
    @classmethod
    def pixmap_from_bytes(cls, image: bytes) -> QPixmap | None:
        if isinstance(image, bytes):
            ba = QByteArray(image)
            pixmap = QPixmap()
            pixmap.loadFromData(ba, "JPEG")
            return pixmap
        return None
    
    @classmethod
    def pixmap_from_array(cls, image: np.ndarray) -> QPixmap | None:
        if isinstance(image, np.ndarray):
            height, width, channel = image.shape
            bytes_per_line = channel * width
            qimage = QImage(image.tobytes(), width, height, bytes_per_line, QImage.Format.Format_RGB888)
            return QPixmap.fromImage(qimage)
        else:
            return None

    @classmethod
    def image_array_to_bytes(cls, image: np.ndarray, quality: int = 80) -> bytes | None:
        if isinstance(image, np.ndarray):
            img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            res, buffer = cv2.imencode(".jpeg", img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            image_io = io.BytesIO()
            image_io.write(buffer)
            img = image_io.getvalue()
            return img
        else:
            return None

    @classmethod
    def pixmap_scale(cls, pixmap: QPixmap, size: int) -> QPixmap:
        return pixmap.scaled(
            size,
            size,
            aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
            transformMode=Qt.TransformationMode.SmoothTransformation
            )

    @classmethod
    def print_error(cls, parent: object, error: Exception):
        tb = traceback.extract_tb(error.__traceback__)

        # Попробуем найти первую строчку стека, которая относится к вашему коду.
        for trace in tb:
            filepath = trace.filename
            filename = os.path.basename(filepath)
            
            # Если файл - не стандартный модуль, считаем его основным
            if not filepath.startswith("<") and filename != "site-packages":
                line_number = trace.lineno
                break
        else:
            # Если не нашли, то берем последний вызов
            trace = tb[-1]
            filepath = trace.filename
            filename = os.path.basename(filepath)
            line_number = trace.lineno

        class_name = parent.__class__.__name__
        error_message = str(error)

        print()
        print("#" * 100)
        print(f"{filepath}:{line_number}")
        print()
        print("ERROR:", error_message)
        print("#" * 100)
        print()






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

        img = ReadImage(src=src, desaturate_value=0.85)
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
            MainUtils.print_err(parent=self, error=e)
        
        if not self.getvalue():
            try:
                heif = HeifImage(img_src)
                bytes_thumb = BaseBytesThumb(heif.converted_img_path)
                self.write(bytes_thumb.getvalue())
                os.remove(heif.converted_img_path)

            except Exception as e:
                MainUtils.print_err(parent=self, error=e)
            
        if not self.getvalue():
            raise ZeroDivisionError("Unable to open or convert image.")
