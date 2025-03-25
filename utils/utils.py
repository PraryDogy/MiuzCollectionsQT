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
from brands import Brand

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
    def read_tiff(cls, path: str) -> np.ndarray | None:

        errors = (
            tifffile.TiffFileError,
            RuntimeError,
            DelayedImportError,
            Exception
        )

        try:
            # Оставляем только три канала (RGB)
            img = tifffile.imread(files=path)
            img = img[..., :3]

            # Проверяем, соответствует ли тип данных изображения uint8.
            # `uint8` — это 8-битный целочисленный формат данных, где значения
            # пикселей лежат в диапазоне [0, 255].
            # Большинство изображений в RGB используют именно этот формат
            # для хранения данных.
            # Если тип данных не `uint8`, требуется преобразование.
            if str(object=img.dtype) != "uint8":

                # Если тип данных отличается, то предполагаем, что значения
                # пикселей выходят за пределы диапазона [0, 255].
                # Например, они могут быть в формате uint16 (диапазон [0, 65535]).
                # Для преобразования выполняем нормализацию значений.
                # Делим на 256, чтобы перевести диапазон [0, 65535] в [0, 255]:
                # 65535 / 256 ≈ 255 (максимальное значение в uint8).
                # Приводим типданных массива к uint8.
                img = (img / 256).astype(dtype="uint8")

            return img

        except errors as e:

            print("error read tiff", path, e)

            try:
                img = Image.open(path)
                img = img.convert("RGB")
                return np.array(img)

            except Exception:
                return None


    @classmethod
    def read_psd(cls, path: str) -> np.ndarray | None:

        with open(path, "rb") as psd_file:

            # Проверяем, что файл имеет правильную подпись PSD/PSB:
            # В начале файла (первые 4 байта) должна быть строка '8BPS', 
            # которая является стандартной подписью для форматов PSD и PSB.
            # Если подпись не совпадает, файл не является корректным PSD/PSB.
            if psd_file.read(4) != b"8BPS":
                return None

            # Переходим к байту 12, где согласно спецификации PSD/PSB
            # содержится число каналов изображения. Число каналов (2 байта)
            # определяет, сколько цветовых и дополнительных каналов содержится в файле.
            psd_file.seek(12)

            # Считываем число каналов (2 байта, big-endian формат,
            # так как PSD/PSB используют этот порядок байтов).
            channels = int.from_bytes(psd_file.read(2), byteorder="big")

            # Возвращаем указатель в начало файла (offset = 0),
            # чтобы psd-tools или Pillow могли корректно прочитать файл с самого начала.
            # Это важно, так как мы изменяли положение указателя для проверки структуры файла.
            psd_file.seek(0)

            try:

                # if channels > 3:
                #     img = psd_tools.PSDImage.open(psd_file)
                #     img = img.composite()
                #     print("psd tools")
                # else:
                #     print("PIL")
                #     img = Image.open(psd_file)

                img = psd_tools.PSDImage.open(psd_file)
                img = img.composite()
                img = img.convert("RGB")
                print("here")
                return np.array(img)

            except Exception as e:

                print("utils > error read psd", "src:", path)
                print(e)
                return None
        
    @classmethod
    def read_psb(cls, path: str):

        try:
            img = psd_tools.PSDImage.open(path)
            img = img.composite()
            img = img.convert("RGB")
            return np.array(img)

        except Exception as e:
            print("utils > error read psd", "src:", path)
            print(e)
            return None

    @classmethod
    def read_png(cls, path: str) -> np.ndarray | None:
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
    def read_jpg(cls, path: str) -> np.ndarray | None:

        try:
            img = Image.open(path)
            img = img.convert("RGB")
            img = np.array(img)
            return img

        except Exception as e:
            return None

    @classmethod
    def read_raw(cls, path: str) -> np.ndarray | None:
        try:
            with rawpy.imread(path) as raw:
                thumb = raw.extract_thumb()

            if thumb.format == rawpy.ThumbFormat.JPEG:
                img = Image.open(io.BytesIO(thumb.data))
                img = img.convert("RGB")

            elif thumb.format == rawpy.ThumbFormat.BITMAP:
                img = Image.fromarray(thumb.data)

            assert isinstance(img, Image.Image)

            exif = img._getexif()

            if exif:
                for tag, value in exif.items():
                    if ExifTags.TAGS.get(tag) == "Orientation":
                        if value == 3:
                            img = img.rotate(180, expand=True)
                        elif value == 6:
                            img = img.rotate(270, expand=True)
                        elif value == 8:
                            img = img.rotate(90, expand=True)
                        break

            return np.array(img)

        except (Exception, rawpy._rawpy.LibRawDataError) as e:
            return None

    @classmethod
    def read_image(cls, full_src: str) -> np.ndarray | None:
        _, ext = os.path.splitext(full_src)
        ext = ext.lower()

        data = {
            ".psb": cls.read_psb,
            # ".psd": cls.read_psd,
            ".psd": cls.read_psb,

            ".tif": cls.read_tiff,
            ".tiff": cls.read_tiff,

            ".nef": cls.read_raw,
            ".cr2": cls.read_raw,
            ".cr3": cls.read_raw,
            ".arw": cls.read_raw,
            ".raf": cls.read_raw,

            ".jpg": cls.read_jpg,
            ".jpeg": cls.read_jpg,
            "jfif": cls.read_jpg,

            ".png": cls.read_png,
        }

        read_img_func = data.get(ext)

        if read_img_func:
            img = read_img_func(full_src)

        else:
            img = None

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
    def brand_coll_folder(cls, brand_ind: int) -> str | None:
        for coll_folder in JsonData.collfolders[brand_ind]:
            if os.path.exists(coll_folder):
                return coll_folder
        return None

    @classmethod
    def get_brand_coll_folder(cls, brand: Brand):
        for coll_folder in brand.coll_folders:
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
