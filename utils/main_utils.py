import os
import platform
import subprocess

from PyQt5.QtWidgets import QVBoxLayout

from cfg import cnf
from signals import gui_signals_app

class MainUtils:
    @staticmethod
    def smb_check() -> bool:
        if not os.path.exists(cnf.coll_folder):

            old_coll = os.sep + cnf.coll_folder.strip(os.sep)

            if "Volumes" + os.sep in old_coll:

                try:
                    old_coll = old_coll.strip(os.sep).split(os.sep)[2:]
                except Exception as e:
                    print(e)
                    return False

                old_coll = os.path.join(os.sep, *old_coll)


            volumes = [
                os.path.join(os.sep, "Volumes", i)
                for i in os.listdir(os.sep + "Volumes")
                ]

            for i in volumes:
                new_coll = os.path.join(os.sep, i.strip(os.sep), old_coll.strip(os.sep))

                if os.path.exists(new_coll):
                    cnf.coll_folder = new_coll
                    gui_signals_app.reload_menu.emit()
                    gui_signals_app.reload_thumbnails.emit()
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
    def close_same_win(object):
        widgets = MainUtils.get_app().topLevelWidgets()
        for widget in widgets:
            if isinstance(widget, object):
                # win with delete_win signal in base_widgets > win > StandartWin
                widget.deleteLater()

    @staticmethod
    def get_app():
        from app import app
        return app
    
    @staticmethod
    def get_central_widget():
        return MainUtils.get_app().main_win