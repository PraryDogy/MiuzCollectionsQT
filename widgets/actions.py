from PyQt5.QtWidgets import QAction, QMenu
from ._base_widgets import UMenu
from cfg import cfg
from system.lang import Lng


class OpenInView(QAction):
    def __init__(self, parent_: QMenu):
        super().__init__(parent=parent_, text=Lng.open[cfg.lng])


class ScanerRestart(QAction):
    def __init__(self, parent: QMenu):
        super().__init__(parent=parent, text=Lng.scan_folder[cfg.lng])


class WinInfoAction(QAction):
    def __init__(self, parent: QMenu):
        super().__init__(text=Lng.info[cfg.lng], parent=parent)


class CopyPath(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.copy_filepath[cfg.lng]} ({total})"
        super().__init__(parent=parent, text=text)


class CopyName(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.copy_name[cfg.lng]} ({total})"
        super().__init__(parent=parent, text=text)


class RevealInFinder(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.reveal_in_finder[cfg.lng]} ({total})"
        super().__init__(parent=parent, text=text)


class SetFav(QAction):
    def __init__(self, parent: QMenu, fav_value: int):
        if not fav_value:
            t = Lng.add_to_favorites[cfg.lng]
        else:
            t = Lng.remove_from_favorites[cfg.lng]
        super().__init__(parent=parent, text=t)


class Save(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.save_to_downloads[cfg.lng]} ({total})"
        super().__init__(parent=parent, text=text)


class SaveAs(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.save_as[cfg.lng]} ({total})"
        super().__init__(parent=parent, text=text)


class RemoveFiles(QAction):
    def __init__(self, parent: QMenu, total: int):
        text_ = f"{Lng.delete[cfg.lng]} ({total})"
        super().__init__(text_, parent)


class CutFiles(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.cut[cfg.lng]} ({total})"
        super().__init__(text=text, parent=parent)

class CopyFiles(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.copy[cfg.lng]} ({total})"
        super().__init__(text=text, parent=parent)

class PasteFiles(QAction):
    def __init__(self, parent: QMenu):
        super().__init__(text=Lng.paste[cfg.lng], parent=parent)
