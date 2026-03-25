from PyQt5.QtWidgets import QAction, QMenu

from cfg import Cfg
from system.lang import Lng


class OpenInView(QAction):
    def __init__(self, parent_: QMenu):
        super().__init__(parent=parent_, text=Lng.open[Cfg.lng_index])


class ScanerRestart(QAction):
    def __init__(self, parent: QMenu):
        super().__init__(parent=parent, text=Lng.scan_folder[Cfg.lng_index])


class WinInfoAction(QAction):
    def __init__(self, parent: QMenu):
        super().__init__(text=Lng.info[Cfg.lng_index], parent=parent)


class CopyPath(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.copy_filepath[Cfg.lng_index]} ({total})"
        super().__init__(parent=parent, text=text)


class CopyName(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.copy_name[Cfg.lng_index]} ({total})"
        super().__init__(parent=parent, text=text)


class RevealInFinder(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.reveal_in_finder[Cfg.lng_index]} ({total})"
        super().__init__(parent=parent, text=text)


class SetFav(QAction):
    def __init__(self, parent: QMenu, fav_value: int):
        if not fav_value:
            t = Lng.add_to_favorites[Cfg.lng_index]
        else:
            t = Lng.remove_from_favorites[Cfg.lng_index]
        super().__init__(parent=parent, text=t)


class Save(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.save_to_downloads[Cfg.lng_index]} ({total})"
        super().__init__(parent=parent, text=text)


class SaveAs(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.save_as[Cfg.lng_index]} ({total})"
        super().__init__(parent=parent, text=text)


class RemoveFiles(QAction):
    def __init__(self, parent: QMenu, total: int):
        text_ = f"{Lng.delete[Cfg.lng_index]} ({total})"
        super().__init__(text_, parent)


class CutFiles(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.cut[Cfg.lng_index]} ({total})"
        super().__init__(text=text, parent=parent)

class CopyFiles(QAction):
    def __init__(self, parent: QMenu, total: int):
        text = f"{Lng.copy[Cfg.lng_index]} ({total})"
        super().__init__(text=text, parent=parent)

class PasteFiles(QAction):
    def __init__(self, parent: QMenu):
        super().__init__(text=Lng.paste[Cfg.lng_index], parent=parent)


class UpdateThumbAction(QAction):
    def __init__(self, parent: QMenu):
        super().__init__(text=Lng.update_thumb[Cfg.lng_index], parent=parent)