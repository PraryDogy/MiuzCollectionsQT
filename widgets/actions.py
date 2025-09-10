import os

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QAction, QFileDialog, QMainWindow, QMenu

from cfg import Cfg, Dynamic, Static
from system.lang import Lng
from system.main_folder import MainFolder
from system.tasks import FavTask
from system.utils import MainUtils, UThreadPool

from .win_warn import WinSmb


class SmbWin:
    """
    Класс-обёртка для отображения окна WinSmb как модального дочернего окна.
    
    Методы:
        show(parent_: QMainWindow): Создаёт экземпляр WinSmb, центрирует относительно родителя и отображает.
    """

    @classmethod
    def show(cls, parent_: QMainWindow):
        # --- Создаём окно ---
        cls.win_warn = WinSmb()
        cls.win_warn.adjustSize()

        # --- Центрируем относительно родителя ---
        cls.win_warn.center_to_parent(parent_)

        # --- Отображаем окно ---
        cls.win_warn.show()


class OpenInView(QAction):
    def __init__(self, parent_: QMenu):
        super().__init__(parent=parent_, text=Lng.open[Cfg.lng])


class ScanerRestart(QAction):
    def __init__(self, parent: QMenu):
        super().__init__(parent=parent, text=Lng.reload_gui[Cfg.lng])


class WinInfoAction(QAction):
    def __init__(self, parent: QMenu):
        super().__init__(text=Lng.info[Cfg.lng], parent=parent)


class CopyPath(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.copy_filepath[Cfg.lng]} ({total})"
        super().__init__(parent=parent, text=text)


class CopyName(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.copy_name[Cfg.lng]} ({total})"
        super().__init__(parent=parent, text=text)


class RevealInFinder(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.reveal_in_finder[Cfg.lng]} ({total})"
        super().__init__(parent=parent, text=text)


class SetFav(QAction):
    def __init__(self, parent: QMenu, fav_value: int):
        if not fav_value:
            t = Lng.add_to_favorites[Cfg.lng]
        else:
            t = Lng.remove_from_favorites[Cfg.lng]
        super().__init__(parent=parent, text=t)


class Save(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.save_to_downloads[Cfg.lng]} ({total})"
        super().__init__(parent=parent, text=text)


class SaveAs(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.save_as[Cfg.lng]} ({total})"
        super().__init__(parent=parent, text=text)


class RemoveFiles(QAction):
    def __init__(self, parent: QMenu, total: int):
        text_ = f"{Lng.delete[Cfg.lng]} ({total})"
        super().__init__(text_, parent)


class MoveFiles(QAction):
    def __init__(self, parent: QMenu, rel_img_path_list: list[str]):
        text = f"{Lng.move[Cfg.lng]} ({len(rel_img_path_list)})"
        super().__init__(text=text, parent=parent)


class OpenDefault(QAction):
    def __init__(self, parent: QMenu, rel_img_path_list: list[str]):
        text = f"{Lng.open_default[Cfg.lng]} ({len(rel_img_path_list)})"
        super().__init__(text=text, parent=parent)
