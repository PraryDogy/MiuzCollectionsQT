import hashlib
import logging
import os
import subprocess
import sys
import traceback
from datetime import datetime

import cv2
import numpy as np
import psd_tools
import rawpy
from imagecodecs.imagecodecs import DelayedImportError
from PIL import Image
from PyQt5.QtCore import QRunnable, Qt, QThreadPool
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication
from tifffile import tifffile

from cfg import JsonData, Static

psd_tools.psd.tagged_blocks.warn = lambda *args, **kwargs: None
psd_logger = logging.getLogger("psd_tools")
psd_logger.setLevel(logging.CRITICAL)

SCRIPTS = "applescripts"
REVEAL_SCPT = os.path.join(SCRIPTS, "reveal_files.scpt")


class UThreadPool:
    pool: QThreadPool = None

    @classmethod
    def init(cls):
        cls.pool = QThreadPool().globalInstance()


class URunnable(QRunnable):
    def __init__(self):
        super().__init__()
        self.should_run: bool = True
        self.is_running: bool = False
    
    @staticmethod
    def set_running_state(method: callable):

        def wrapper(self, *args, **kwargs):
            self.is_running = True
            method(self, *args, **kwargs)
            self.is_running = False

        return wrapper

class Err:

    @classmethod
    def print_err(cls, error: Exception):
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

        print(f"{filepath}:{line_number}")
        print(error)


class ReadImage(Err):

    @classmethod
    def read_tiff_tifffile(cls, path: str) -> np.ndarray | None:

        errs = (
            Exception,
            tifffile.TiffFileError,
            RuntimeError,
            DelayedImportError
        )

        try:
            img = tifffile.imread(files=path)
            img = img[..., :3]

            if str(object=img.dtype) != "uint8":
                img = (img/256).astype(dtype="uint8")
            return img

        except errs as e:
            return None
    
    @classmethod
    def read_tiff_pil(cls, path: str) -> np.ndarray | None:

        try:
            img = Image.open(path)
            img = img.convert("RGB")
            img = np.array(img)
            return img

        except Exception as e:
            return None

    @classmethod
    def read_psd_pil(cls, path: str) -> np.ndarray | None:

        try:
            img = Image.open(path)
            img = img.convert("RGB")
            img = np.array(img)
            return img

        except Exception as e:
            return None

    @classmethod
    def read_psd_tools(cls, path: str) -> np.ndarray | None:

        try:
            img = psd_tools.PSDImage.open(fp=path)
            img = img.composite()
            img = np.array(img)
            img = img[..., :3]
            return img

        except Exception as e:
            return None

    @classmethod
    def read_png_pil(cls, path: str) -> np.ndarray | None:
        try:
            img = Image.open(path)

            if img.mode == "RGBA":
                white_background = Image.new("RGBA", img.size, (255, 255, 255))
                img = Image.alpha_composite(white_background, img)

            img = img.convert("RGB")
            img = np.array(img)
            return img

        except Exception as e:
            print("error read png pil", str)
            return None

    @classmethod
    def read_png_cv2(cls, path: str) -> np.ndarray | None:
        try:
            image = cv2.imread(path, cv2.IMREAD_UNCHANGED)  # Чтение с альфа-каналом

            if image.shape[2] == 4:
                alpha_channel = image[:, :, 3] / 255.0
                rgb_channels = image[:, :, :3]
                background_color = np.array([255, 255, 255], dtype=np.uint8)
                background = np.full(
                    rgb_channels.shape, background_color, dtype=np.uint8
                )
                converted = (
                    rgb_channels * alpha_channel[:, :, np.newaxis] +
                    background * (1 - alpha_channel[:, :, np.newaxis])
                ).astype(np.uint8)

            else:
                converted = image

            return converted

        except Exception as e:
            print("error read png cv2", path)
            return None

    @classmethod
    def read_jpg_pil(cls, path: str) -> np.ndarray | None:

        try:
            img = Image.open(path)
            img = np.array(img)
            return img

        except Exception as e:
            return None

    @classmethod
    def read_jpg_cv2(cls, path: str) -> np.ndarray | None:

        try:
            return cv2.imread(path, cv2.IMREAD_UNCHANGED)

        except (Exception, cv2.error) as e:
            return None

    @classmethod
    def read_raw(cls, path: str) -> np.ndarray | None:
        try:
            return rawpy.imread(path).postprocess()

        except rawpy._rawpy.LibRawDataError as e:
            return None

    @classmethod
    def read_image(cls, full_src: str) -> np.ndarray | None:
        _, ext = os.path.splitext(full_src)
        ext = ext.lower()

        data = {
            ".psb": cls.read_psd_tools,
            ".psd": cls.read_psd_tools,

            ".tif": cls.read_tiff_tifffile,
            ".tiff": cls.read_tiff_tifffile,

            ".nef": cls.read_raw,
            ".cr2": cls.read_raw,
            ".cr3": cls.read_raw,
            ".arw": cls.read_raw,
            ".raf": cls.read_raw,

            ".jpg": cls.read_jpg_pil,
            ".jpeg": cls.read_jpg_pil,
            "jfif": cls.read_jpg_pil,

            ".png": cls.read_png_pil,
        }

        data_none = {
            ".tif": cls.read_tiff_pil,
            ".tiff": cls.read_tiff_pil,
            ".psd": cls.read_psd_tools,
            ".jpg": cls.read_jpg_cv2,
            ".jpeg": cls.read_jpg_cv2,
            "jfif": cls.read_jpg_cv2,
            ".png": cls.read_png_cv2,
        }

        img = None

        # если есть подходящее расширение то читаем файл
        if data.get(ext):
            img = data.get(ext)(full_src)

        else:
            return None

        # если прочитать не удалось, то пытаемся прочесть запасными функциями
        if img is None:
            img = data_none.get(ext)

        # либо None либо ndarray изображение
        return img


class Hash:

    @classmethod
    def create_full_hash(cls, full_src: str) -> str:
        new_name = hashlib.md5(full_src.encode('utf-8')).hexdigest() + ".jpg"
        
        new_folder = os.path.join(Static.HASH_DIR, new_name[:2])
        os.makedirs(new_folder, exist_ok=True)

        return os.path.join(new_folder, new_name)

    @classmethod
    def get_short_hash(cls, full_hash: str):
        return full_hash.replace(Static.APP_SUPPORT_DIR, "")
    
    @classmethod
    def get_full_hash(cls, short_hash: str):
        return Static.APP_SUPPORT_DIR + short_hash

    @classmethod
    def write_image_hash(cls, output_path: str, array_img: np.ndarray) -> bool:
        try:
            img = cv2.cvtColor(array_img, cv2.COLOR_BGR2RGB)
            cv2.imwrite(output_path, img)
            return True
        except Exception as e:
            print("error write image hash")
            return False

    @classmethod
    def read_image_hash(cls, src: str) -> np.ndarray | None:
        try:
            img = cv2.imread(src, cv2.IMREAD_UNCHANGED)
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except Exception as e:
            print("read img hash error:", src)
            return None


class Pixmap:

    @classmethod
    def pixmap_from_array(cls, image: np.ndarray) -> QPixmap | None:

        if isinstance(image, np.ndarray) and QApplication.instance():
            height, width, channel = image.shape
            bytes_per_line = channel * width
            qimage = QImage(
                image.tobytes(),
                width,
                height,
                bytes_per_line,
                QImage.Format.Format_RGB888
            )
            return QPixmap.fromImage(qimage)

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

class Utils(Hash, Pixmap, ReadImage):

    @classmethod
    def get_coll_folder(cls, brand_ind: int) -> str | None:
        for coll_folder in JsonData.collfolders[brand_ind]:
            if os.path.exists(coll_folder):
                return coll_folder
        return None

    @classmethod
    def get_coll_name(cls, coll_folder: str, full_src: str) -> str:
        coll = cls.get_short_src(coll_folder, full_src)
        coll = coll.strip(os.sep)
        coll = coll.split(os.sep)

        if len(coll) > 1:
            return coll[0]
        else:
            return os.path.basename(coll_folder.strip(os.sep))

    @classmethod
    def copy_text(cls, text: str):
        QApplication.clipboard().setText(text)
        return True

    @classmethod
    def paste_text(cls) -> str:
        return QApplication.clipboard().text()
        
    @classmethod
    def reveal_files(cls, files_list: list[str]):
        """list of FULL SRC"""
        command = ["osascript", REVEAL_SCPT] + files_list
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    @classmethod
    def start_new_app(cls):
        os.execl(sys.executable, sys.executable, *sys.argv)

    @classmethod
    def get_f_size(cls, bytes_size: int) -> str:
        if bytes_size < 1024:
            return f"{bytes_size} байт"
        elif bytes_size < pow(1024,2):
            return f"{round(bytes_size/1024, 2)} КБ"
        elif bytes_size < pow(1024,3):
            return f"{round(bytes_size/(pow(1024,2)), 2)} МБ"
        elif bytes_size < pow(1024,4):
            return f"{round(bytes_size/(pow(1024,3)), 2)} ГБ"
        elif bytes_size < pow(1024,5):
            return f"{round(bytes_size/(pow(1024,4)), 2)} ТБ"

    @classmethod
    def get_f_date(cls, timestamp_: int) -> str:
        date = datetime.fromtimestamp(timestamp_).replace(microsecond=0)
        return date.strftime("%d.%m.%Y %H:%M")
    
    @classmethod
    def array_color(cls, img: np.ndarray, flag: str) -> np.ndarray:

        if flag == "RGB":
            colors = cv2.COLOR_RGB2BGR
        elif flag == "BGR":
            colors = cv2.COLOR_BGR2RGB
        else:
            raise Exception("utils image utils array color wrong flag", flag)
        try:
            return cv2.cvtColor(img, colors)
        except Exception as e:
            print("error array_color")
        
    @classmethod
    def fit_to_thumb(cls, image: np.ndarray, size: int) -> np.ndarray | None:
        try:
            h, w = image.shape[:2]
            scale = size / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

        except Exception as e:
            print("resize_max_aspect_ratio error:", e)
            return None
        
    @classmethod
    def get_full_src(cls, coll_folder: str, short_src: str) -> str:
        return coll_folder + short_src
    
    @classmethod
    def get_short_src(cls, coll_folder: str, full_src: str) -> str:
        return full_src.replace(coll_folder, "")
