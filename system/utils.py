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

SCRIPTS = "scripts"
REVEAL_SCPT = os.path.join(SCRIPTS, "reveal_files.scpt")



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
    def get_abs_thumb_path(cls, rel_thumb_path: str):
        return Static.APP_SUPPORT_DIR + rel_thumb_path

    @classmethod
    def write_thumb(cls, thumb_path: str, thumb: np.ndarray) -> bool:
        try:
            if thumb is None or thumb.size == 0:
                print("Utils - write_thumb - пустой thumb")
                return False

            if len(thumb.shape) == 2:  # grayscale
                img = thumb
            elif thumb.shape[2] == 3:  # BGR
                img = cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)
            elif thumb.shape[2] == 4:  # BGRA
                img = cv2.cvtColor(thumb, cv2.COLOR_BGRA2RGB)
            else:
                print(f"Utils - write_thumb - неподдерживаемое число каналов: {thumb.shape}")
                return False

            return cv2.imwrite(thumb_path, img)
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
            if h == 0 or w == 0:
                print("fit_to_thumb error: пустое изображение")
                return None

            scale = size / max(h, w)
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))

            return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        except Exception as e:
            print("fit_to_thumb error:", e)
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
    def reveal_files(cls, img_paths: list[str]):
        command = ["osascript", REVEAL_SCPT] + img_paths
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    @classmethod
    def start_new_app(cls):
        os.execl(sys.executable, sys.executable, *sys.argv)
        
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
