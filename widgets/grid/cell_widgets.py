import os

from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QMouseEvent, QPixmap
from PyQt5.QtWidgets import QFrame, QLabel, QSizePolicy

from base_widgets import LayoutVer
from cfg import Dynamic, Static, ThumbData
from signals import SignalsApp
from utils.utils import Utils

from ._db_images import DbImage


class CellWid:
    def __init__(self):
        super().__init__()
        self.row = 0
        self.col = 0


class Title(QLabel, CellWid):
    r_click = pyqtSignal()
    style_ = f"""
        font-size: 18pt;
        font-weight: bold;
        border: {Static.border_transparent};
    """

    def __init__(self, title: str):
        CellWid.__init__(self)
        QLabel.__init__(self, text=title)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Preferred
            )

        self.setStyleSheet(self.style_)

    def set_frame(self):
        return

    def set_no_frame(self):
        return
    
    def contextMenuEvent(self, ev):
        return super().contextMenuEvent(ev)


class TextWid(QLabel):
    def __init__(self, parent, name: str, coll: str):
        super().__init__(parent)
        self.name = name
        self.coll = coll

    def set_text(self) -> list[str]:
        name: str | list = self.name
        ind = Dynamic.thumb_size_ind
        max_row = ThumbData.MAX_ROW[ind]
        lines: list[str] = []

        if len(name) > max_row:

            first_line = name[:max_row]
            second_line = name[max_row:]

            if len(second_line) > max_row:

                second_line = self.short_text(
                    text=second_line,
                    max_row=max_row
                )

            for i in (first_line, second_line):
                lines.append(i)

        else:
            name = lines.append(name)

        self.setText("\n".join(lines))

    def short_text(self, text: str, max_row: int):
        return f"{text[:max_row - 10]}...{text[-7:]}"

    def mouseReleaseEvent(self, ev):
        return super().mouseReleaseEvent(ev)
    
    def contextMenuEvent(self, ev):
        return super().contextMenuEvent(ev)
    
    def mouseDoubleClickEvent(self, a0):
        return super().mouseDoubleClickEvent(a0)
    
    
class ImgWid(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def test(self):
        ev = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            self.cursor().pos(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        super().mouseReleaseEvent(ev)

    def mouseReleaseEvent(self, ev):
        return super().mouseReleaseEvent(ev)
    
    def contextMenuEvent(self, ev):
        return super().contextMenuEvent(ev)
    
    def mouseDoubleClickEvent(self, a0):
        return super().mouseDoubleClickEvent(a0)


class Thumbnail(QFrame, CellWid):
    select = pyqtSignal(str)
    path_to_wid: dict[str, "Thumbnail"] = {}

    img_frame_size = 0
    pixmap_size = 0
    thumb_w = 0
    thumb_h = 0

    style_ = f"""
        border-radius: 7px;
        color: rgb(255, 255, 255);
        background: {Static.gray_color};
        border: {Static.border_transparent};
        padding-left: 2px;
        padding-right: 2px;
    """

    def __init__(self, pixmap: QPixmap, rel_img_path: str, coll_name: str, fav: int):
        CellWid.__init__(self)
        QFrame.__init__(self)
        self.setStyleSheet(Static.border_transparent_style)

        self.img = pixmap
        self.rel_img_path = rel_img_path
        self.collection = coll_name
        self.fav_value = fav

        if fav == 0 or fav is None:
            self.name = os.path.basename(rel_img_path)
        elif fav == 1:
            self.name = Static.STAR_SYM + os.path.basename(rel_img_path)

        self.v_layout = LayoutVer()
        self.v_layout.setSpacing(ThumbData.SPACING)
        self.v_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.v_layout)

        self.img_wid = ImgWid()
        self.v_layout.addWidget(self.img_wid, alignment=Qt.AlignmentFlag.AlignCenter)
        self.text_wid = TextWid(self, self.name, coll_name)
        self.text_wid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.v_layout.addWidget(
            self.text_wid,
            alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.setup()
        # self.setStyleSheet("background: BLACK;")

    @classmethod
    def calculate_size(cls):
        ind = Dynamic.thumb_size_ind
        cls.pixmap_size = ThumbData.PIXMAP_SIZE[ind]
        cls.img_frame_size = Thumbnail.pixmap_size + ThumbData.OFFSET
        cls.thumb_w = ThumbData.THUMB_W[ind]
        cls.thumb_h = ThumbData.THUMB_H[ind]

    def setup(self):
        # инициация текста
        self.text_wid.set_text()

        self.setFixedSize(Thumbnail.thumb_w, Thumbnail.thumb_h)

        # рамка вокруг pixmap при выделении Thumb
        self.img_wid.setFixedSize(Thumbnail.pixmap_size + ThumbData.OFFSET, Thumbnail.pixmap_size + ThumbData.OFFSET)
        self.img_wid.setPixmap(Utils.pixmap_scale(self.img, self.pixmap_size))

    def set_frame(self):
        self.img_wid.setStyleSheet(self.style_)
        text_style = Static.blue_bg_style + "font-size: 11px;"
        self.text_wid.setStyleSheet(text_style)

    def set_no_frame(self):
        self.img_wid.setStyleSheet(Static.border_transparent_style)
        text_style = Static.border_transparent_style + "font-size: 11px;"
        self.text_wid.setStyleSheet(text_style)

    def change_fav(self, value: int):
        if value == 0:
            self.fav_value = value
            self.name = os.path.basename(self.rel_img_path)
        elif value == 1:
            self.fav_value = value
            self.name = Static.STAR_SYM + os.path.basename(self.rel_img_path)

        self.text_wid.name = self.name
        self.text_wid.set_text()

        # удаляем из избранного и если это избранные то обновляем сетку
        if value == 0 and Dynamic.curr_coll_name == Static.NAME_FAVS:
            SignalsApp.instance.grid_thumbnails_cmd.emit("reload")
