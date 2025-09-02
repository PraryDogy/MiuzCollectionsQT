import hashlib
import io
import json
import logging
import os
import subprocess
import sys
import traceback
from datetime import datetime, timedelta

import cv2
import jsonschema
import numpy as np
import psd_tools
import rawpy
from imagecodecs.imagecodecs import DelayedImportError
from PIL import Image, ImageOps
from PyQt5.QtCore import QRunnable, Qt, QThreadPool
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication
from tifffile import tifffile

from cfg import Static

psd_tools.psd.tagged_blocks.warn = lambda *args, **kwargs: None
psd_logger = logging.getLogger("psd_tools")
psd_logger.setLevel(logging.CRITICAL)
Image.MAX_IMAGE_PIXELS = None

SCRIPTS = "scripts"
REVEAL_SCPT = os.path.join(SCRIPTS, "reveal_files.scpt")


class ImgUtils:

    @classmethod
    def read_tiff(cls, img_path: str) -> np.ndarray | None:
        try:
            img = tifffile.imread(img_path)
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
            MainUtils.print_error()
            try:
                img = Image.open(img_path)
                img = img.convert("RGB")
                array_img = np.array(img)
                img.close()
                return array_img
            except Exception as e:
                MainUtils.print_error()
                return None
                    
    @classmethod
    def read_psb(cls, img_path: str):
        try:
            img = psd_tools.PSDImage.open(img_path)
            img = img.composite()
            img = img.convert("RGB")
            array_img = np.array(img)
            return array_img
        except Exception as e:
            # MainUtils.print_error()
            print("Utils - read psb - ошибка чтения psb", e)
            return None

    @classmethod
    def read_png(cls, img_path: str) -> np.ndarray | None:
        try:
            img = Image.open(img_path)
            if img.mode == "RGBA":
                white_background = Image.new("RGBA", img.size, (255, 255, 255))
                img = Image.alpha_composite(white_background, img)
            img = img.convert("RGB")
            array_img = np.array(img)
            img.close()
            return array_img
        except Exception as e:
            MainUtils.print_error()
            return None

    @classmethod
    def read_jpg(cls, img_path: str) -> np.ndarray | None:
        try:
            img = Image.open(img_path)
            img = ImageOps.exif_transpose(img) 
            img = img.convert("RGB")
            array_img = np.array(img)
            img.close()

            return array_img
        except Exception as e:
            MainUtils.print_error()
            return None

    @classmethod
    def read_raw(cls, img_path: str) -> np.ndarray | None:
        try:
            # https://github.com/letmaik/rawpy
            # Извлечение встроенного эскиза/превью из RAW-файла и преобразование в изображение:
            # Открываем RAW-файл с помощью rawpy
            with rawpy.imread(img_path) as raw:
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
                MainUtils.print_error()
            array_img = np.array(img)
            img.close()
            return array_img
        except (Exception, rawpy._rawpy.LibRawDataError) as e:
            MainUtils.print_error()
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
            MainUtils.print_error()
            return None

    @classmethod
    def read_any(cls, img_path: str) -> np.ndarray | None:
        ...

    @classmethod
    def read_image(cls, img_path: str) -> np.ndarray | None:
        _, ext = os.path.splitext(img_path)
        ext = ext.lower()

        read_any_dict: dict[str, callable] = {}

        for i in Static.ext_psd:
            read_any_dict[i] = cls.read_psb
        for i in Static.ext_tiff:
            read_any_dict[i] = cls.read_tiff
        for i in Static.ext_raw:
            read_any_dict[i] = cls.read_raw
        for i in Static.ext_jpeg:
            read_any_dict[i] = cls.read_jpg
        for i in Static.ext_png:
            read_any_dict[i] = cls.read_png
        for i in Static.ext_video:
            read_any_dict[i] = cls.read_movie

        for i in Static.ext_all:
            if i not in read_any_dict:
                raise Exception (f"utils > ReadImage > init_read_dict: не инициирован {i}")

        fn = read_any_dict.get(ext)

        if fn:
            cls.read_any = fn
            return cls.read_any(img_path)

        else:
            return None

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


class ThumbUtils:
    @classmethod
    def create_thumb_path(cls, img_path: str) -> str:
        new_name = hashlib.md5(img_path.encode('utf-8')).hexdigest() + ".jpg"
        new_folder = os.path.join(Static.APP_SUPPORT_HASHDIR, new_name[:2])
        os.makedirs(new_folder, exist_ok=True)
        return os.path.join(new_folder, new_name)

    @classmethod
    def get_rel_thumb_path(cls, thumb_path: str):
        return thumb_path.replace(Static.APP_SUPPORT_DIR, "")
    
    @classmethod
    def get_thumb_path(cls, rel_thumb_path: str):
        return Static.APP_SUPPORT_DIR + rel_thumb_path

    @classmethod
    def write_thumb(cls, thumb_path: str, thumb: np.ndarray) -> bool:
        try:
            img = cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)
            cv2.imwrite(thumb_path, img)
            return True
        except Exception as e:
            print("Utils - write_thumb - ошибка записи thumb на диск", e)
            return False

    @classmethod
    def read_thumb(cls, thumb_path: str) -> np.ndarray | None:
        try:
            if os.path.exists(thumb_path):
                img = cv2.imread(thumb_path, cv2.IMREAD_UNCHANGED)
                return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            else:
                # print("system > read_thumb > изображения не существует")
                return None
        except Exception as e:
            MainUtils.print_error()
            return None

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


class PixmapUtils:

    @classmethod
    def qimage_from_array(cls, image: np.ndarray) -> QImage | None:
        if not (isinstance(image, np.ndarray) and QApplication.instance()):
            return None
        if image.ndim == 2:  # grayscale
            height, width = image.shape
            bytes_per_line = width
            qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
        elif image.ndim == 3 and image.shape[2] in (3, 4):
            height, width, channels = image.shape
            bytes_per_line = channels * width
            fmt = QImage.Format_RGB888 if channels == 3 else QImage.Format_RGBA8888
            qimage = QImage(image.data, width, height, bytes_per_line, fmt)
        else:
            print("pixmap from array channels trouble", image.shape)
            return None
        return qimage

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


class MainUtils:

    @classmethod
    def get_coll_name(cls, main_folder_path: str, img_path: str) -> str:
        coll = cls.get_rel_path(main_folder_path, img_path)
        coll = coll.strip(os.sep)
        coll = coll.split(os.sep)

        if len(coll) > 1:
            return coll[0]
        else:
            return os.path.basename(main_folder_path.strip(os.sep))

    @classmethod
    def copy_text(cls, text: str):
        QApplication.clipboard().setText(text)
        return True

    @classmethod
    def paste_text(cls) -> str:
        return QApplication.clipboard().text()
        
    @classmethod
    def reveal_files(cls, img_path_list: list[str]):
        command = ["osascript", REVEAL_SCPT] + img_path_list
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    @classmethod
    def start_new_app(cls):
        os.execl(sys.executable, sys.executable, *sys.argv)

    @classmethod
    def open_in_app(cls, abs_path: str, app_path: str = None):
        if app_path:
            subprocess.Popen(["open", "-a", app_path, abs_path])
        else:
            subprocess.Popen(["open", abs_path])

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
    def get_f_date(cls, timestamp_: int, date_only: bool = False) -> str:
        date = datetime.fromtimestamp(timestamp_).replace(microsecond=0)
        now = datetime.now()
        today = now.date()
        yesterday = today - timedelta(days=1)

        if date.date() == today:
            return f"сегодня {date.strftime('%H:%M')}"
        elif date.date() == yesterday:
            return f"вчера {date.strftime('%H:%M')}"
        else:
            return date.strftime("%d.%m.%y %H:%M")
        
    @classmethod
    def get_abs_path(cls, main_folder_path: str, rel_path: str) -> str:
        return main_folder_path + rel_path
    
    @classmethod
    def get_rel_path(cls, main_folder_path: str, abs_path: str) -> str:
        return abs_path.replace(main_folder_path, "")

    @classmethod
    def rm_rf(cls, folder_path: str):
        try:
            subprocess.run(["rm", "-rf", folder_path], check=True)
            print(f"Папка '{folder_path}' успешно удалена.")
        except subprocess.CalledProcessError as e:
            print(f"Ошибка удаления: {e}")
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")

    @classmethod
    def image_apps(cls, apps: list[str]):
        app_dirs = [
            "/Applications",
            os.path.expanduser("~/Applications"),
            "/System/Applications"
        ]
        found_apps = []

        def search_dir(directory):
            try:
                for entry in os.listdir(directory):
                    path = os.path.join(directory, entry)
                    if entry.endswith(".app"):
                        name_lower = entry.lower()
                        if any(k in name_lower for k in apps):
                            found_apps.append(path)
                    elif os.path.isdir(path):
                        search_dir(path)
            except PermissionError:
                pass

        for app_dir in app_dirs:
            if os.path.exists(app_dir):
                search_dir(app_dir)

        return found_apps


    @classmethod
    def print_error(cls):
        print()
        print("Исключение обработано")
        print(traceback.format_exc())
        print()


class JsonUtils:

    @classmethod
    def validate_data(cls, data: dict, schema: dict):
        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as ve:
            path = ".".join(str(p) for p in ve.path)
            print()
            print(f"JsonUtils.validate_data error: '{path}': {ve.message}")
            print(data)
            print()
            return None
        return True
        
    @classmethod
    def write_json_data(cls, json_file: str, data: list[dict]) -> bool | None:
        try:
            with open(json_file, "w", encoding='utf-8') as f:
                f.write(json.dumps(obj=data, indent=4, ensure_ascii=False))
            return True
        except Exception:
            MainUtils.print_error()
            return None

    @classmethod
    def read_json_data(cls, json_file: str) -> list[dict] | None:
        try:
            with open(json_file, "r", encoding='utf-8') as f:
                return json.loads(f.read())
        except Exception:
            MainUtils.print_error()
            return None


class TaskState:
    __slots__ = ["_should_run", "_finished"]

    def __init__(self, value=True, finished=False):
        self._should_run = value
        self._finished = finished

    def should_run(self):
        return self._should_run
    
    def set_should_run(self, value: bool):
        self._should_run = value

    def set_finished(self, value: bool):
        self._finished = value

    def finished(self):
        return self._finished


class URunnable(QRunnable):
    def __init__(self):
        """
        Внимание:   
        Не переопределяйте метод self.run() как в QRunnable, переопределите
        метод self.task()

        self.task_state:
        - для управления QRunnable.
        - Можно остановить задачу self.task_state.set_should_run(False)
        - По завершению задачи self.task_state.finished() вернет True
        """
        super().__init__()
        self.task_state = TaskState()
    
    def run(self):
        try:
            self.task()
        finally:
            self.task_state.set_finished(True)
            # if self in UThreadPool.tasks:
                # QTimer.singleShot(5000, lambda: UThreadPool.tasks.remove(self))

    def task(self):
        raise NotImplementedError("Переопредели метод task() в подклассе.")
    

class UThreadPool:
    pool: QThreadPool = None
    tasks: list[URunnable] = []

    @classmethod
    def init(cls):
        cls.pool = QThreadPool.globalInstance()

    @classmethod
    def start(cls, runnable: URunnable):
        """
        Запускает URunnable, добавляет в список UThreadPool.tasks
        """
        # cls.tasks.append(runnable)
        cls.pool.start(runnable)
