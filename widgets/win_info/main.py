import os
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent
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
        super().__init__(text=text, align=Qt.AlignmentFlag.AlignRight, ww=ww)
        self.contextMenuEvent = lambda event: None


class CustomContextRLabel(ContextMenuBase):
    def __init__(self, parent: QLabel, event):
        super().__init__(event=event)
        self.my_parent = parent

        selected_text = parent.selectedText().replace("\u2029", "")
        if selected_text:
            label_text = f"{cnf.lng.copy} \"{selected_text}\""
            sel = QAction(text=label_text, parent=self)
            sel.triggered.connect(lambda: self.my_sel(text=selected_text))
        else:
            sel = QAction(text=cnf.lng.copy, parent=self)
            sel.setDisabled(True)
        self.addAction(sel)

        self.addSeparator()

        sel_all = QAction(text=cnf.lng.copy_all, parent=self)
        sel_all.triggered.connect(self.my_sel_all)
        self.addAction(sel_all)

    def my_sel_all(self):
        MainUtils.copy_text(self.my_parent.text())

    def my_sel(self, text: str):
        # text = self.my_parent.selectedText().replace("\u2029", "")
        MainUtils.copy_text(text)


class RightLabel(BaseLabel):
    def __init__(self, text, ww):
        super().__init__(text=text, align=Qt.AlignmentFlag.AlignLeft, ww=ww)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        self.my_context = CustomContextRLabel(parent=self, event=ev)
        self.my_context.show_menu()
        return
        return super().contextMenuEvent(ev)


class WinInfo(WinStandartBase):
    def __init__(self, img_src: str, parent: QWidget):
        super().__init__(close_func=self.my_close)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
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

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.my_close(a0)
        return super().keyPressEvent(a0)
  
    def my_close(self, event):
        if not cnf.image_viewer:
            try:
                cnf.selected_thumbnail.regular_style()
            except Exception as e:
                MainUtils.print_err(parent=self, error=e)
        self.close()
