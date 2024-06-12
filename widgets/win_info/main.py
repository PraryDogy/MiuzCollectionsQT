import os
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QAction, QLabel, QWidget

from base_widgets import Btn, ContextMenuBase, LayoutH, WinStandartBase
from cfg import cnf
from styles import Names, Themes
from utils import MainUtils, get_image_size


class ImgInfoBase(dict):
    def __init__(self, img_src: str):
        try:
            name = img_src.split(os.sep)[-1]
            collection = MainUtils.get_coll_name(img_src)

            filemod = datetime.fromtimestamp(os.path.getmtime(filename=img_src))
            filemod = filemod.strftime("%d-%m-%Y, %H:%M:%S")

            try:
                w, h = get_image_size(img_src)

            except Exception as e:
                w, h = 0, 0
            resol = f"{w}x{h}"

            filesize = round(os.path.getsize(filename=img_src) / (1024*1024), 2)
            filesize = f"{filesize}{cnf.lng.mb}"

        except FileNotFoundError:
            name = cnf.lng.no_connection
            collection = cnf.lng.no_connection
            filemod = cnf.lng.no_connection
            resol = cnf.lng.no_connection
            filesize = cnf.lng.no_connection

        self.update(
            {cnf.lng.collection: collection,
             cnf.lng.file_name: name,
             cnf.lng.date_changed: filemod,
             cnf.lng.resolution: resol,
             cnf.lng.file_size: filesize,
             cnf.lng.file_path: img_src}
             )


class ImgInfo(ImgInfoBase):
    def __init__(self, img_src: str):
        super().__init__(img_src=img_src)

        lined_data = {}

        for l_text, r_text in self.items():
            max_chars = 40

            r_text = '\n'.join(
                [r_text[i:i + max_chars]
                 for i in range(0, len(r_text), max_chars)]
                 )
            l_text = l_text + "\n" * (r_text.count('\n'))
            lined_data[l_text] = r_text

        l_text = "\n".join(lined_data)
        r_text = "\n".join(lined_data.values())

        self.clear()
        self.update({l_text: r_text})


class BaseLabel(QLabel):
    def __init__(self, text, align, ww):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setAlignment(align)
        self.setText(text)
        self.adjustSize()

        self.setObjectName(Names.info_base_label)
        self.setStyleSheet(Themes.current)


class LeftLabel(BaseLabel):
    def __init__(self, text, ww):
        super().__init__(text=text, align=Qt.AlignRight, ww=ww)
        self.contextMenuEvent = lambda event: None


class CustomContextRLabel(ContextMenuBase):
    def __init__(self, parent: QLabel, event):
        super().__init__(event=event)
        self.my_parent = parent

        sel = QAction(text=cnf.lng.copy_selected, parent=self)
        sel.triggered.connect(self.my_sel)
        self.addAction(sel)

        self.addSeparator()

        sel_all = QAction(text=cnf.lng.copy_all, parent=self)
        sel_all.triggered.connect(self.my_sel_all)
        self.addAction(sel_all)

    def my_sel_all(self):
        MainUtils.copy_text(self.my_parent.text())

    def my_sel(self):
        text = self.my_parent.selectedText().replace("\u2029", "")
        MainUtils.copy_text(text)


class RightLabel(BaseLabel):
    def __init__(self, text, ww):
        super().__init__(text=text, align=Qt.AlignLeft, ww=ww)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setCursor(Qt.IBeamCursor)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        self.my_context = CustomContextRLabel(parent=self, event=ev)
        self.my_context.show_menu()
        return super().contextMenuEvent(ev)


class WinInfo(WinStandartBase):
    def __init__(self, img_src: str, parent: QWidget):
        MainUtils.close_same_win(WinInfo)

        super().__init__(close_func=self.my_close)
        self.disable_min_max()
        self.set_title(cnf.lng.info)

        self.img_src = img_src
        self.l_ww = 100
        self.init_ui()

        self.fit_size()
        self.center_win(parent)

    def init_ui(self):
        info_layout = LayoutH()
        self.content_layout.addLayout(info_layout)

        new_data = ImgInfo(img_src=self.img_src)
        
        for l_text, r_text in new_data.items():
            l_label = LeftLabel(text=l_text, ww=self.l_ww)
            l_label.setContentsMargins(0, 0, 10, 10)
            info_layout.addWidget(l_label)

            r_label = RightLabel(text=r_text, ww=self.width()-self.l_ww)
            r_label.setContentsMargins(0, 0, 0, 10)
            info_layout.addWidget(r_label)

        btn_layout = LayoutH()
        self.content_layout.addLayout(btn_layout)
        button = Btn(cnf.lng.close)
        button.mouseReleaseEvent = self.my_close
        btn_layout.addWidget(button)
  
    def my_close(self, event):
        self.deleteLater()
