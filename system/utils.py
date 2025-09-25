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
        try:
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
                print(f"qimage_from_array: channels trouble {image.shape}")
                return None
            return qimage
        except Exception as e:
            print(f"qimage_from_array: {e}")
            return None

    @classmethod
    def pixmap_from_array(cls, image: np.ndarray) -> QPixmap | None:
        try:
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
        except Exception as e:
            print(f"pixmap_from_array: {e}")
            return None

    @classmethod
    def pixmap_scale(cls, pixmap: QPixmap, w: int, h: int) -> QPixmap | None:
        try:
            aspect = Qt.AspectRatioMode.KeepAspectRatio
            transf = Qt.TransformationMode.SmoothTransformation
            return pixmap.scaled(w, h, aspect, transf)
        except Exception as e:
            print(f"pixmap_scale: {e}")
            return None

    @classmethod
    def create_abs_hash(cls, path: str) -> str | None:
        try:
            new_name = hashlib.md5(path.encode('utf-8')).hexdigest() + ".jpg"
            new_folder = os.path.join(Static.app_support_hashdir, new_name[:2])
            os.makedirs(new_folder, exist_ok=True)
            return os.path.join(new_folder, new_name)
        except Exception as e:
            print(f"create_abs_hash: {e}")
            return None

    @classmethod
    def get_rel_hash(cls, thumb_path: str) -> str | None:
        try:
            return thumb_path.replace(Static.app_support, "")
        except Exception as e:
            print(f"get_rel_hash: {e}")
            return None

    @classmethod
    def get_abs_hash(cls, rel_thumb_path: str) -> str | None:
        try:
            return Static.app_support + rel_thumb_path
        except Exception as e:
            print(f"get_abs_hash: {e}")
            return None

    @classmethod
    def write_thumb(cls, thumb_path: str, thumb: np.ndarray) -> bool:
        try:
            if len(thumb.shape) == 2:  # grayscale
                img = thumb
            elif thumb.shape[2] == 3:  # BGR
                img = cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)
            elif thumb.shape[2] == 4:  # BGRA
                img = cv2.cvtColor(thumb, cv2.COLOR_BGRA2RGB)
            else:
                print(f"write_thumb: неподдерживаемое число каналов {thumb.shape}")
                return None
            return cv2.imwrite(thumb_path, img)
        except Exception as e:
            print(f"write_thumb: ошибка записи thumb на диск: {e}")
            return None

    @classmethod
    def read_thumb(cls, thumb_path: str) -> np.ndarray | None:
        try:
            if os.path.exists(thumb_path):
                img = cv2.imread(thumb_path, cv2.IMREAD_UNCHANGED)
                return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            else:
                print(f"read_thumb: файл не существует {thumb_path}")
                return None
        except Exception as e:
            print(f"read_thumb: ошибка чтения thumb: {e}")
            return None

    @classmethod
    def fit_to_thumb(cls, image: np.ndarray, size: int) -> np.ndarray | None:
        try:
            h, w = image.shape[:2]
            if h == 0 or w == 0:
                print("fit_to_thumb: пустое изображение")
                return None

            scale = size / max(h, w)
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))

            return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        except Exception as e:
            print(f"fit_to_thumb: ошибка масштабирования: {e}")
            return None

    @classmethod
    def copy_text(cls, text: str):
        QApplication.clipboard().setText(text)
        return True

    @classmethod
    def paste_text(cls) -> str:
        return QApplication.clipboard().text()
        
    @classmethod
    def reveal_files(cls, paths: list[str]):
        subprocess.Popen(["osascript", REVEAL_SCPT] + paths)

    @classmethod
    def start_new_app(cls):
        os.execl(sys.executable, sys.executable, *sys.argv)
        
    @classmethod
    def get_abs_path(cls, mf_path: str, rel_path: str) -> str:
        if mf_path in rel_path:
            return rel_path
        else:
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
