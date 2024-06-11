from PyQt5.QtWidgets import QAction, QLabel, QWidget

from base_widgets import ContextMenuBase, ContextSubMenuBase
from cfg import cnf
from styles import Names, Themes

from ..gui_thread_save_files import GuiThreadSaveFiles


class CustomContext(ContextMenuBase):
    def __init__(
            self,
            parent: QLabel | QWidget, 
            files_list: list,
            event
            ):

        super().__init__(event=event)
        self.my_parent = parent

        save_as_menu = ContextSubMenuBase(self, cnf.lng.save_group_in)
        self.addMenu(save_as_menu)

        save_as_jpg = QAction("JPG")
        save_as_jpg.triggered.connect(lambda: self.save_as_jpg(files_list))
        save_as_menu.addAction(save_as_jpg)

        save_as_menu.addSeparator()

        save_as_layers = QAction(cnf.lng.layers)
        save_as_layers.triggered.connect(lambda: self.save_as_tiffs(files_list))
        save_as_menu.addAction(save_as_layers)

        self.addSeparator()

        save_menu = ContextSubMenuBase(self, cnf.lng.save_group_downloads)
        self.addMenu(save_menu)

        save_jpg = QAction("JPG")
        save_jpg.triggered.connect(lambda: self.save_jpg(files_list))
        save_menu.addAction(save_jpg)

        save_menu.addSeparator()

        save_layers = QAction(cnf.lng.layers)
        save_layers.triggered.connect(lambda: self.save_tiffs(files_list))
        save_menu.addAction(save_layers)
        self.save_as_win = None

        self.show_menu()

    def save_as_jpg(self, files_list):
        self.save_as_win = GuiThreadSaveFiles(
            parent=self.my_parent,
            files=files_list,
            is_downloads=False,
            is_fiff=False
            )

    def save_as_tiffs(self, files_list):
        self.save_as_win = GuiThreadSaveFiles(
            parent=self.my_parent,
            files=files_list,
            is_downloads=False,
            is_fiff=True
            )

    def save_jpg(self, files_list):
        self.save_as_win = GuiThreadSaveFiles(
            parent=self.my_parent,
            files=files_list,
            is_downloads=True,
            is_fiff=False
            )

    def save_tiffs(self, files_list):
        self.save_as_win = GuiThreadSaveFiles(
            parent=self.my_parent,
            files=files_list,
            is_downloads=True,
            is_fiff=True
            )


class Title(QLabel):
    def __init__(
            self,
            title: str,
            images: list,
            width: int
            ):

        super().__init__(f"{title}. {cnf.lng.total}: {len(images)}")
        self.setFixedWidth(width - 20)
        self.setWordWrap(True)
        self.setContentsMargins(0, 0, 0, 5)
        self.setObjectName(Names.th_title)
        self.setStyleSheet(Themes.current)

        self.images = images
        self.my_context = None

    def contextMenuEvent(self, event):
        self.my_context = CustomContext(
            parent=self,
            files_list=self.images,
            event=event
            )