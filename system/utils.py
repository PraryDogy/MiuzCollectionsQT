import hashlib
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QVBoxLayout

from cfg import Static


class Utils:

    @classmethod
    def qimage_from_array(cls, image: np.ndarray) -> QImage | None:
        try:
            image = np.ascontiguousarray(image)
            if image.ndim == 2:  # grayscale
                height, width = image.shape
                bytes_per_line = width
                qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
            elif image.ndim == 3 and image.shape[2] in (3, 4):
                height, width, channels = image.shape
                bytes_per_line = channels * width
                fmt = QImage.Format.Format_RGB888 if channels == 3 else QImage.Format.Format_RGBA8888
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
    def scaled_high_dpi(cls, qimage: QImage, size: int, dpr: int = 2):
        scaled = qimage.scaled(
            int(size * dpr),
            int(size * dpr),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        scaled.setDevicePixelRatio(dpr)
        return scaled

    @classmethod
    def qiconed_resize(cls, pixmap: QPixmap, max_side: int) -> QPixmap:
        return QIcon(pixmap).pixmap(QSize(max_side, max_side))

    @classmethod
    def create_abs_thumb_path(cls, rel_img_path: str, mf_alias: str) -> str | None:
        filename = hashlib.md5(rel_img_path.encode('utf-8')).hexdigest() + ".jpg"
        new_folder = os.path.join(
            Static.hashdir,
            f"{mf_alias}-{filename[:2]}"
        )
        os.makedirs(new_folder, exist_ok=True)
        return os.path.join(new_folder, filename)

    @classmethod
    def get_rel_thumb_path(cls, abs_thumb_path: str, app_data_dir = Static.APP_DATA_DIR):
        p_base = Path(app_data_dir.strip(os.sep))
        p_abs = Path(abs_thumb_path.strip(os.sep))
        if p_abs.is_relative_to(p_base):
            return os.sep + str(p_abs.relative_to(p_base))

    @classmethod
    def get_abs_thumb_path(cls, rel_thumb_path: str, app_data_dir = Static.APP_DATA_DIR):
        app_data_dir = Path(app_data_dir)
        rel_thumb_path = Path(rel_thumb_path.strip(os.sep))
        return app_data_dir / rel_thumb_path

    @classmethod
    def copy_text_pyqt(cls, text: str):
        QApplication.clipboard().setText(text)
        return True

    @classmethod
    def paste_text_pyqt(cls) -> str:
        return QApplication.clipboard().text()
        
    @classmethod
    def reveal_files_macos(cls, paths: list[str], scpt = "reveal_files.scpt"):
        script_path = os.path.join(Static.scripts, scpt)
        subprocess.Popen(["osascript", script_path] + paths)

    @classmethod
    def add_mf_path(cls, mf_path: str, rel_path: str) -> str:
        p_mf = Path(mf_path.strip(os.sep))
        p_abs = Path(rel_path.strip(os.sep))
        if p_abs.is_relative_to(p_mf):
            return os.sep + str(p_abs)
        combined_path = p_mf / p_abs
        return os.sep + str(combined_path)
    
    @classmethod
    def remove_mf_path(cls, mf_path: str, abs_path: str) -> str:
        p_mf = Path(mf_path.strip(os.sep))
        p_abs = Path(abs_path.strip(os.sep))
        if p_abs == p_mf:
            return os.sep
        if p_abs.is_relative_to(p_mf):
            return os.sep + str(p_abs.relative_to(p_mf))
        return abs_path

    @classmethod
    def clear_layout(cls, layout: QVBoxLayout | QHBoxLayout | QGridLayout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    @classmethod
    def print_error(cls):
        print()
        print("Исключение обработано")
        print(traceback.format_exc())
        print()
