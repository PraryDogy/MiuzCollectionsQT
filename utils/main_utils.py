import os
import platform
import subprocess
import traceback

import sqlalchemy
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout

from cfg import cnf
from database import Dbase, ThumbsMd


class MainUtils:
    @staticmethod
    def print_err(write=False):
        print(traceback.format_exc())

        if write:
            log = os.path.join(
                cnf.app_support_app_dir,
                "log.txt"
                )

            with open(log, "a") as f:
                f.write(traceback.format_exc())

    @staticmethod
    def smb_check() -> bool:
        return bool(os.path.exists(path=cnf.coll_folder))

    @staticmethod
    def get_coll_name(src_path: str) -> str:
        coll = src_path.replace(cnf.coll_folder, "").strip(os.sep).split(os.sep)

        if len(coll) > 1:
            return coll[0]
        else:
            return cnf.coll_folder.strip(os.sep).split(os.sep)[-1]
    
    @staticmethod
    def clear_layout(layout: QVBoxLayout):
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                else:
                    MainUtils.clear_layout(item.layout())

    @staticmethod
    def get_mac_ver():
        ver = platform.mac_ver()[0].split(".")
        if len(ver) >= 2:
            return float(f'{ver[0]}.{ver[1]}')
        else:
            return None

    @staticmethod
    def copy_text(text):
        text_bytes = text.encode('utf-8')
        subprocess.run(['pbcopy'], input=text_bytes, check=True)
        return True

    @staticmethod
    def paste_text():
        paste_result = subprocess.run(
            ['pbpaste'],
            capture_output=True,
            text=True,
            check=True
            )
        return paste_result.stdout.strip()
    
    @staticmethod
    def close_all_win():
        for child_window in MainUtils.get_app().topLevelWidgets():
            if isinstance(child_window, QMainWindow):
                if child_window.windowTitle() != cnf.app_name:
                    child_window.deleteLater()

    @staticmethod
    def close_same_win(object):
        widgets = MainUtils.get_app().topLevelWidgets()
        for widget in widgets:
            if isinstance(widget, object):
                # win with delete_win signal in base_widgets > win > StandartWin
                widget.delete_win.emit()
                widget.deleteLater()

    @staticmethod
    def get_app():
        from app import app
        return app
    
    @staticmethod
    def get_central_widget():
        return MainUtils.get_app().main_win