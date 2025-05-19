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
from PIL import ExifTags, Image
from PyQt5.QtCore import QRunnable, Qt, QThreadPool
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication
from tifffile import tifffile
import io
from cfg import JsonData, Static
from main_folders import MainFolder

psd_tools.psd.tagged_blocks.warn = lambda *args, **kwargs: None
psd_logger = logging.getLogger("psd_tools")
psd_logger.setLevel(logging.CRITICAL)

SCRIPTS = "scripts"
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
    def print_error(cls, error: Exception):
        LIMIT_ = 200
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

        msg = str(error)
        if msg.startswith("[Errno"):
            msg = msg.split("]", 1)[-1].strip()

        print(f"\n{type(error).__name__}: {msg}\n{filepath}:{line_number}\n")
        return msg


class ReadImage:
    read_any_dict = {}

    @classmethod
    def init_read_dict(cls, cfg: Static):
        """
        В Static должны содержаться данные о расширениях
        """
        for ext in cfg.ext_psd:
            cls.read_any_dict[ext] = cls.read_psb
        for ext in cfg.ext_tiff:
            cls.read_any_dict[ext] = cls.read_tiff
        for ext in cfg.ext_raw:
            cls.read_any_dict[ext] = cls.read_raw
        for ext in cfg.ext_jpeg:
            cls.read_any_dict[ext] = cls.read_jpg
        for ext in cfg.ext_png:
            cls.read_any_dict[ext] = cls.read_png
        for ext in cfg.ext_video:
            cls.read_any_dict[ext] = cls.read_movie

        for i in cfg.ext_all:
            if i not in ReadImage.read_any_dict:
                raise Exception (f"utils > ReadImage > init_read_dict: не инициирован {i}")

    @classmethod
    def read_tiff(cls, path: str) -> np.ndarray | None:
        try:
            img = tifffile.imread(path)
            # Проверяем, что изображение трёхмерное
            if img.ndim == 3:
                channels = min(img.shape)
                channels_index = img.shape.index(channels)
                # Транспонируем, если каналы на первом месте
                if channels_index == 0:
                    img = img.transpose(1, 2, 0)
                # Ограничиваем количество каналов до 3
                if channels > 3:
                    img = img[:, :, :3]
                # Преобразуем в uint8, если тип другой
                if str(img.dtype) != "uint8":
                    img = (img / 256).astype(dtype="uint8")
            # Если изображение уже 2D, просто показываем его
            elif img.ndim == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            return img
        except (tifffile.TiffFileError, RuntimeError, DelayedImportError, Exception) as e: 
            Err.print_error(e)
            try:
                img = Image.open(path)
                img = img.convert("RGB")
                array_img = np.array(img)
                img.close()
                return array_img
            except Exception as e:
                Err.print_error(e)
                return None
                    
    @classmethod
    def read_psb(cls, path: str):
        try:
            img = psd_tools.PSDImage.open(path)
            img = img.composite()
            img = img.convert("RGB")
            array_img = np.array(img)
            return array_img
        except Exception as e:
            Err.print_error(e)
            return None

    @classmethod
    def read_png(cls, path: str) -> np.ndarray | None:
        try:
            img = Image.open(path)
            if img.mode == "RGBA":
                white_background = Image.new("RGBA", img.size, (255, 255, 255))
                img = Image.alpha_composite(white_background, img)
            img = img.convert("RGB")
            array_img = np.array(img)
            img.close()
            return array_img
        except Exception as e:
            Err.print_error(e)
            return None

    @classmethod
    def read_jpg(cls, path: str) -> np.ndarray | None:
        try:
            img = Image.open(path)
            img = img.convert("RGB")
            array_img = np.array(img)
            img.close()
            return array_img
        except Exception as e:
            Err.print_error(e)
            return None

    @classmethod
    def read_raw(cls, path: str) -> np.ndarray | None:
        try:
            # https://github.com/letmaik/rawpy
            # Извлечение встроенного эскиза/превью из RAW-файла и преобразование в изображение:
            # Открываем RAW-файл с помощью rawpy
            with rawpy.imread(path) as raw:
                # Извлекаем встроенный эскиз (thumbnail)
                thumb = raw.extract_thumb()
            # Проверяем формат извлечённого эскиза
            if thumb.format == rawpy.ThumbFormat.JPEG:
                # Если это JPEG — открываем как изображение через BytesIO
                img = Image.open(io.BytesIO(thumb.data))
                # Конвертируем в RGB (на случай, если изображение не в RGB)
                img = img.convert("RGB")
            elif thumb.format == rawpy.ThumbFormat.BITMAP:
                # Если формат BITMAP — создаём изображение из массива
                img: Image.Image = Image.fromarray(thumb.data)
            try:
                exif = img.getexif()
                orientation_tag = 274  # Код тега Orientation
                if orientation_tag in exif:
                    orientation = exif[orientation_tag]
                    # Коррекция поворота на основе EXIF-ориентации
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
            except Exception as e:
                Err.print_error(e)
            array_img = np.array(img)
            img.close()
            return array_img
        except (Exception, rawpy._rawpy.LibRawDataError) as e:
            Err.print_error(e)
            return None

    @classmethod
    def read_movie(cls, path: str, time_sec=1) -> np.ndarray | None:
        try:
            cap = cv2.VideoCapture(path)
            cap.set(cv2.CAP_PROP_POS_MSEC, time_sec * 1000)
            success, frame = cap.read()
            cap.release()
            if success:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return frame
            else:
                return None
        except Exception as e:
            Err.print_error(e)
            return None

    @classmethod
    def read_any(cls, path: str) -> np.ndarray | None:
        ...

    @classmethod
    def read_image(cls, path: str) -> np.ndarray | None:
        _, ext = os.path.splitext(path)
        ext = ext.lower()

        fn = ReadImage.read_any_dict.get(ext)

        if fn:
            cls.read_any = fn
            return cls.read_any(path)

        else:
            return None


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
            # print("read img hash error:", src)
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
        

class Utils(Hash, Pixmap, ReadImage):

    @classmethod
    def desaturate_image(cls, image: np.ndarray, factor=0.2):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.addWeighted(
            image,
            1 - factor,
            cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR),
            factor,
            0
        )

    @classmethod
    def get_main_folder_path(cls, main_folder: MainFolder):
        for coll_folder in main_folder.paths:
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
    def get_full_src(cls, coll_folder: str, short_src: str) -> str:
        return coll_folder + short_src
    
    @classmethod
    def get_short_src(cls, coll_folder: str, full_src: str) -> str:
        return full_src.replace(coll_folder, "")

    @classmethod
    def rm_rf(cls, folder_path: str):
        try:
            subprocess.run(["rm", "-rf", folder_path], check=True)
            print(f"Папка '{folder_path}' успешно удалена.")
        except subprocess.CalledProcessError as e:
            print(f"Ошибка удаления: {e}")
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
