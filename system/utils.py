import hashlib
import os
import subprocess
import sys
import traceback

import cv2
import numpy as np
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QImage, QPixmap
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
    def create_abs_thumb_path(cls, rel_img_path: str, mf_alias: str) -> str | None:
        filename = hashlib.md5(rel_img_path.encode('utf-8')).hexdigest() + ".jpg"
        new_folder = os.path.join(
            Static.external_hashdir,
            f"{mf_alias}-{filename[:2]}"
        )
        os.makedirs(new_folder, exist_ok=True)
        return os.path.join(new_folder, filename)

    @classmethod
    def get_rel_thumb_path(cls, thumb_path: str) -> str | None:
        try:
            return thumb_path.replace(Static.external_files_dir, "")
        except Exception as e:
            print(f"get_rel_hash: {e}")
            return None

    @classmethod
    def get_abs_thumb_path(cls, rel_thumb_path: str) -> str | None:
        try:
            return Static.external_files_dir + rel_thumb_path
        except Exception as e:
            print(f"get_abs_hash: {e}")
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
    def get_abs_any_path(cls, mf_path: str, rel_path: str) -> str:
        if mf_path in rel_path:
            return rel_path
        else:
            return mf_path + rel_path
    
    @classmethod
    def get_rel_any_path(cls, mf_path: str, abs_img_path: str) -> str:
        return abs_img_path.replace(mf_path, "")

    @classmethod
    def desaturate_image(cls, image: np.ndarray, factor=0.2):
        try:
            # если 4 канала (RGBA), убираем альфу для операции
            has_alpha = image.shape[2] == 4
            img = image[:, :, :3] if has_alpha else image

            # преобразуем в серый
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

            # объединяем с оригиналом
            desat = cv2.addWeighted(img, 1 - factor, gray_bgr, factor, 0)

            # если был альфа-канал, добавляем обратно
            if has_alpha:
                desat = np.dstack([desat, image[:, :, 3]])

            return desat
        except Exception:
            cls.print_error()
            return image

    @classmethod
    def qiconed_resize(cls, pixmap: QPixmap, max_side: int) -> QPixmap:
        if pixmap.isNull():
            return QPixmap()
        w, h = pixmap.width(), pixmap.height()
        if w > h:
            new_w = max_side
            new_h = int(h * max_side / w)
        else:
            new_h = max_side
            new_w = int(w * max_side / h)
        icon = QIcon(pixmap)
        return icon.pixmap(QSize(new_w, new_h))

    @classmethod
    def print_error(cls):
        print()
        print("Исключение обработано")
        print(traceback.format_exc())
        print()
