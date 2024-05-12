from functools import partial

from PyQt5.QtWidgets import QAction, QLabel, QMainWindow

from base_widgets import ContextMenuBase, ContextSubMenuBase
from cfg import cnf
from styles import Names, Themes

from ..gui_thread_reveal_files import GuiThreadRevealFiles
from ..gui_thread_save_files import GuiThreadSaveFiles
from ..win_info import WinInfo


class Manager:
    win_info = None
    win_image_view = None


class ImageContext(ContextMenuBase):
    def __init__(
            self,
            parent: QLabel | QMainWindow,
            img_src: str,
            event
            ):

        super().__init__(event)
        self.my_parent = parent
        
        if not isinstance(parent, QMainWindow):
            open_action = QAction(cnf.lng.view, self)
            open_action.triggered.connect(partial(self.show_image_viewer, img_src))
            self.addAction(open_action)

        info_action = QAction(cnf.lng.info, self)
        info_action.triggered.connect(partial(self.show_info_win, img_src))
        self.addAction(info_action)

        self.addSeparator()

        reveal_menu = ContextSubMenuBase(self, cnf.lng.reveal_in_finder)
        self.addMenu(reveal_menu)

        reveal_jpg = QAction("JPG")
        reveal_jpg.triggered.connect(lambda: self.reveal_jpg(img_src))
        reveal_menu.addAction(reveal_jpg)

        reveal_menu.addSeparator()

        reveal_layers = QAction(cnf.lng.layers)
        reveal_layers.triggered.connect(lambda: self.reveal_tiffs(img_src))
        reveal_menu.addAction(reveal_layers)

        self.addSeparator()

        save_as_menu = ContextSubMenuBase(self, cnf.lng.save_image_in)
        self.addMenu(save_as_menu)

        save_as_jpg = QAction("JPG")
        save_as_jpg.triggered.connect(lambda: self.save_as_jpg(img_src))
        save_as_menu.addAction(save_as_jpg)

        save_as_menu.addSeparator()

        save_as_layers = QAction(cnf.lng.layers)
        save_as_layers.triggered.connect(lambda: self.save_as_tiffs(img_src))
        save_as_menu.addAction(save_as_layers)

        save_menu = ContextSubMenuBase(self, cnf.lng.save_image_downloads)
        self.addMenu(save_menu)

        save_jpg = QAction("JPG")
        save_jpg.triggered.connect(lambda: self.save_jpg(img_src))
        save_menu.addAction(save_jpg)

        save_menu.addSeparator()

        save_layers = QAction(cnf.lng.layers)
        save_layers.triggered.connect(lambda: self.save_tiffs(img_src))
        save_menu.addAction(save_layers)

        self.reveal_files = None
        self.tiff_thread = None
        self.save_files = None

        if parent.objectName() == Names.thumbnail_normal:
            try:
                parent.setObjectName(Names.thumbnail_selected)
                parent.setStyleSheet(Themes.current)
                self.show_menu()
                parent.setObjectName(Names.thumbnail_normal)
                parent.setStyleSheet(Themes.current)
            except Exception as e:
                print(e)
        else:
            try:
                self.show_menu()
            except Exception as e:
                print(e)

    def show_info_win(self, img_src):
        if isinstance(self.my_parent, QMainWindow):
            Manager.win_info = WinInfo(img_src, self.my_parent)
        else:
            Manager.win_info = WinInfo(img_src)
        Manager.win_info.show()
        
    def show_image_viewer(self, img_src):
        from ..win_image_view import WinImageView
        Manager.win_image_view = WinImageView(img_src)
        Manager.win_image_view.show()

    def reveal_jpg(self, img_src):
        self.reveal_files = GuiThreadRevealFiles(
            parent=self.my_parent,
            files=[img_src],
            is_tiff=False
            )

    def reveal_tiffs(self, img_src):
        self.reveal_files = GuiThreadRevealFiles(
            parent=self.my_parent,
            files=[img_src],
            is_tiff=True
            )

    def save_as_jpg(self, img_src):
        self.save_files = GuiThreadSaveFiles(
            parent=self.my_parent,
            files=[img_src],
            is_fiff=False,
            is_downloads=False
            )

    def save_as_tiffs(self, img_src):
        self.save_files = GuiThreadSaveFiles(
            parent=self.my_parent, 
            files=[img_src],
            is_fiff=True,
            is_downloads=False
            )

    def save_jpg(self, img_src):
        self.save_files = GuiThreadSaveFiles(
            parent=self.my_parent,
            files=[img_src],
            is_fiff=False,
            is_downloads=True
            )

    def save_tiffs(self, img_src):
        self.save_files = GuiThreadSaveFiles(
            parent=self.my_parent,
            files=[img_src],
            is_fiff=True,
            is_downloads=True
            )
        