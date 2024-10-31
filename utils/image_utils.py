import io
import logging
import os
import traceback

import cv2
import numpy as np
import psd_tools
from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtGui import QImage, QPixmap
from tifffile import tifffile

from cfg import cnf
from database import *

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
            return img
        except (tifffile.TiffFileError, RuntimeError) as e:
            print(path)
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
            print("image utils > read img > none", src)
            img = None

        return img
    
    @classmethod
    def array_bgr_to_rgb(cls, img: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    @classmethod
    def pixmap_from_bytes(cls, image: bytes) -> QPixmap | None:
        ba = QByteArray(image)
        pixmap = QPixmap()
        pixmap.loadFromData(ba, "JPEG")
        return pixmap
    
    @classmethod
    def pixmap_from_array(cls, image: np.ndarray) -> QPixmap | None:
        height, width, channel = image.shape
        bytes_per_line = channel * width
        qimage = QImage(image.tobytes(), width, height, bytes_per_line, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qimage)

    @classmethod
    def image_array_to_bytes(cls, image: np.ndarray, quality: int = 80) -> bytes | None:
        img = image
        res, buffer = cv2.imencode(".jpeg", img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        image_io = io.BytesIO()
        image_io.write(buffer)
        img = image_io.getvalue()
        return img

    @classmethod
    def pixmap_scale(cls, pixmap: QPixmap, size: int) -> QPixmap:
        return pixmap.scaled(
            size,
            size,
            aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
            transformMode=Qt.TransformationMode.SmoothTransformation
            )

    @classmethod
    def resize_min_aspect_ratio(cls, image: np.ndarray, size: int) -> np.ndarray | None:
        try:
            h, w = image.shape[:2]
            scale = size / min(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        except Exception as e:
            print("resize_min_aspect_ratio error:", e)
            return None

    @classmethod
    def crop_to_square(cls, image: np.ndarray | QPixmap) -> np.ndarray | None:

        if isinstance(image, np.ndarray):
            height, width = image.shape[:2]
            min_dim = min(height, width)
            start_x = (width - min_dim) // 2
            start_y = (height - min_dim) // 2
            return image[start_y:start_y + min_dim, start_x:start_x + min_dim]

        elif isinstance(image, QPixmap):
            w = image.width()
            h = image.height()

            side = min(w, h)
            x_offset = (w - side) // 2
            y_offset = (h - side) // 2
            
            return image.copy(x_offset, y_offset, side, side)

        else:
            return None

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
