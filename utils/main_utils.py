import os
import platform
import subprocess
import traceback

from PyQt5.QtWidgets import QMainWindow, QVBoxLayout

from cfg import cnf
from signals import signals_app


class MainUtils:

    @classmethod
    def smb_check(cls) -> bool:
        if not os.path.exists(cnf.coll_folder):
            for coll_folder in cnf.coll_folder_list:
                if os.path.exists(coll_folder):
                    cnf.coll_folder = coll_folder
                    signals_app.scaner_stop.emit()
                    signals_app.scaner_start.emit()
                    return True
            return False
        return True

    @classmethod
    def get_coll_name(cls, src_path: str) -> str:
        coll = src_path.replace(cnf.coll_folder, "").strip(os.sep).split(os.sep)

        if len(coll) > 1:
            return coll[0]
        else:
            return cnf.coll_folder.strip(os.sep).split(os.sep)[-1]
    
    @classmethod
    def clear_layout(cls, layout: QVBoxLayout):
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                else:
                    cls.clear_layout(item.layout())

    @classmethod
    def get_mac_ver(cls):
        ver = platform.mac_ver()[0].split(".")
        if len(ver) >= 2:
            return float(f'{ver[0]}.{ver[1]}')
        else:
            return None

    @classmethod
    def copy_text(cls, text: str):
        text_bytes = text.encode('utf-8')
        subprocess.run(['pbcopy'], input=text_bytes, check=True)
        return True

    @classmethod
    def paste_text(cls) -> str:
        paste_result = subprocess.run(
            ['pbpaste'],
            capture_output=True,
            text=True,
            check=True
            )
        return paste_result.stdout.strip()
    
    @classmethod
    def get_app(cls):
        from app import app
        return app
    
    @classmethod
    def get_main_win(cls) -> QMainWindow:
        return cls.get_app().main_win
    
    @classmethod
    def reveal_files(cls, files_list: list):
        reveal_script = "applescripts/reveal_files.scpt"
        command = ["osascript", reveal_script] + files_list
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def send_notification(cls, text: str):
        if cnf.image_viewer:
            signals_app.noti_img_view.emit(text)
        else:
            signals_app.noti_main.emit(text)

    @classmethod
    def print_err(cls, parent: object, error: Exception):
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