import os
import platform
import subprocess
import traceback

from PyQt5.QtWidgets import QVBoxLayout, QMainWindow

from cfg import cnf
from signals import utils_signals_app


class MainUtils:
    @staticmethod
    def smb_check() -> bool:
        if not os.path.exists(cnf.coll_folder):

            old_coll = os.sep + cnf.coll_folder.strip(os.sep)

            if "Volumes" + os.sep in old_coll:

                try:
                    old_coll = old_coll.strip(os.sep).split(os.sep)[2:]
                except Exception as e:
                    print("MainUtils > smb_check",e)
                    return False

                old_coll = os.path.join(os.sep, *old_coll)

            volumes = [
                os.path.join(os.sep, "Volumes", i)
                for i in os.listdir(os.sep + "Volumes")
                ]

            for i in volumes:
                new_coll = os.path.join(os.sep, i.strip(os.sep), old_coll.strip(os.sep))

                if os.path.exists(new_coll):
                    cnf.old_coll_folder = cnf.coll_folder
                    cnf.coll_folder = new_coll
                    utils_signals_app.scaner_stop.emit()
                    utils_signals_app.scaner_start.emit()
                    return True

            return False

        return True

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
    def copy_text(text: str):
        text_bytes = text.encode('utf-8')
        subprocess.run(['pbcopy'], input=text_bytes, check=True)
        return True

    @staticmethod
    def paste_text() -> str:
        paste_result = subprocess.run(
            ['pbpaste'],
            capture_output=True,
            text=True,
            check=True
            )
        return paste_result.stdout.strip()
    
    @staticmethod
    def get_app():
        from app import app
        return app
    
    @staticmethod
    def get_main_win() -> QMainWindow:
        return MainUtils.get_app().main_win

    @staticmethod
    def print_err(parent: object, error: Exception):
        tb = traceback.extract_tb(error.__traceback__)
        last_call = tb[-1]
        filepath = last_call.filename
        filename = os.path.basename(filepath)
        class_name = parent.__class__.__name__
        line_number = last_call.lineno
        error_message = str(error)
        
        print()
        print(f"{filename} > {class_name} > row {line_number}: {error_message}")
        print(f"{filepath}:{line_number}")
        print()