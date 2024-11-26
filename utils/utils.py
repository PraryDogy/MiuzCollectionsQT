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


class Utils:

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

    @classmethod
    def get_coll_folder(cls, brand_ind: int) -> str | None:
        for coll_folder in JsonData.coll_folders[brand_ind]:
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
    def create_full_hash_path(cls, full_src: str) -> str:
        new_name = hashlib.md5(full_src.encode('utf-8')).hexdigest() + ".jpg"
        
        new_folder = os.path.join(Static.HASH_DIR, new_name[:2])
        os.makedirs(new_folder, exist_ok=True)

        return os.path.join(new_folder, new_name)

    @classmethod
    def get_short_hash_path(cls, full_hash_path: str):
        return full_hash_path.replace(Static.APP_SUPPORT_DIR, "")
    
    @classmethod
    def get_full_hash_path(cls, short_hash_path: str):
        return Static.APP_SUPPORT_DIR + short_hash_path

    @classmethod
    def write_image_hash(cls, full_hash_path: str, array_img: np.ndarray) -> bool:
        try:
            cv2.imwrite(full_hash_path, array_img)
            return True
        except Exception as e:
            cls.print_err(error=e)
            return False
        
    @classmethod
    def read_image_hash(cls, full_hash_path: str) -> np.ndarray | None:
        try:
            array_img = cv2.imread(full_hash_path, cv2.IMREAD_UNCHANGED)
            return cls.array_color(array_img, "BGR")
        except Exception as e:
            cls.print_err(error=e)
            return None

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
    def read_tiff(cls, full_src: str) -> np.ndarray | None:
        try:
            img = tifffile.imread(files=full_src)[:,:,:3]
            if str(object=img.dtype) != "uint8":
                img = (img/256).astype(dtype="uint8")
            return img

        except (
            Exception,
            tifffile.TiffFileError,
            RuntimeError,
            DelayedImportError
            ) as e:

            # Utils.print_err(error=e)
            print("read_tiff error")
            print("try open tif with PIL")
            return cls.read_tiff_pil(full_src)
    
    @classmethod
    def read_tiff_pil(cls, full_src: str) -> np.ndarray | None:
        try:
            print("PIL: try open tif")
            img: Image = Image.open(full_src)
            return np.array(img)
        except Exception as e:
            # Utils.print_err(error=e)
            print("read_tiff_pil error")
            return None

    @classmethod
    def read_psd(cls, full_src: str) -> np.ndarray | None:
        try:
            img = psd_tools.PSDImage.open(fp=full_src)
            img = img.composite()

            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            img = np.array(img)
            return img

        except Exception as e:
            print("read_psd error")
            # Utils.print_err(error=e)
            return None
            
    @classmethod
    def read_jpg(cls, full_src: str) -> np.ndarray | None:
        try:
            image = cv2.imread(full_src, cv2.IMREAD_UNCHANGED)
            return image
        except (Exception, cv2.error) as e:
            # Utils.print_err(error=e)
            print("read jpg error")
            return None
        
    @classmethod
    def read_png(cls, full_src: str) -> np.ndarray | None:
        try:
            image = cv2.imread(full_src, cv2.IMREAD_UNCHANGED)
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
            print("read png error")
            # Utils.print_err(error=e)
            return None

    @classmethod
    def read_image(cls, full_src: str) -> np.ndarray | None:

        src_lower: str = full_src.lower()

        if src_lower.endswith((".psd", ".psb")):
            img = cls.read_psd(full_src)

        elif src_lower.endswith((".tiff", ".tif")):
            img = cls.read_tiff(full_src)

        elif src_lower.endswith((".jpg", ".jpeg", "jfif")):
            img = cls.read_jpg(full_src)

        elif src_lower.endswith((".png")):
            img = cls.read_png(full_src)

        else:
            print("image utils > read img > none", full_src)
            img = None

        return img
    
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
            print("array_color")
            # cls.print_err(error=e)

    @classmethod
    def pixmap_from_array(cls, image: np.ndarray) -> QPixmap | None:
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

    @classmethod
    def pixmap_scale(cls, pixmap: QPixmap, size: int) -> QPixmap:
        return pixmap.scaled(
            size,
            size,
            aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
            transformMode=Qt.TransformationMode.SmoothTransformation
            )
        
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
