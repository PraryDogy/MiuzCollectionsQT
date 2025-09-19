import hashlib
import os
import subprocess
import sys
import traceback

import cv2
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication

from cfg import Static

SCRIPTS = "scripts"
REVEAL_SCPT = os.path.join(SCRIPTS, "reveal_files.scpt")


class Utils:

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

    @classmethod
    def create_abs_hash(cls, path: str) -> str:
        new_name = hashlib.md5(path.encode('utf-8')).hexdigest() + ".jpg"
        new_folder = os.path.join(Static.APP_SUPPORT_HASHDIR, new_name[:2])
        os.makedirs(new_folder, exist_ok=True)
        return os.path.join(new_folder, new_name)

    @classmethod
    def get_rel_hash(cls, thumb_path: str):
        return thumb_path.replace(Static.APP_SUPPORT_DIR, "")
    
    @classmethod
    def get_abs_hash(cls, rel_thumb_path: str):
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
            print("utils, read thumb error")
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

    @classmethod
    def get_coll_name(cls, mf_path: str, path: str) -> str:
        coll = cls.get_rel_path(mf_path, path)
        coll = coll.strip(os.sep)
        coll = coll.split(os.sep)

        if len(coll) > 1:
            return coll[0]
        else:
            return os.path.basename(mf_path.strip(os.sep))

    @classmethod
    def copy_text(cls, text: str):
        QApplication.clipboard().setText(text)
        return True

    @classmethod
    def paste_text(cls) -> str:
        return QApplication.clipboard().text()
        
    @classmethod
    def reveal_files(cls, paths: list[str]):
        command = ["osascript", REVEAL_SCPT] + paths
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    @classmethod
    def start_new_app(cls):
        os.execl(sys.executable, sys.executable, *sys.argv)
        
    @classmethod
    def get_abs_path(cls, mf_path: str, rel_path: str) -> str:
        return mf_path + rel_path
    
    @classmethod
    def get_rel_path(cls, mf_path: str, abs_path: str) -> str:
        return abs_path.replace(mf_path, "")

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
