import sys
from pathlib import Path

from PyQt6.QtCore import QAbstractListModel, QModelIndex, QRect, QSize, Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QImageReader, QPen, QPixmap
from PyQt6.QtWidgets import (QAbstractItemView, QApplication, QListView,
                             QStyle, QStyledItemDelegate)

FOLDER = Path("/Users/evlosh/Desktop/2005 - 2025 семейное")
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}

THUMB = 160      # размер миниатюры по большей стороне
CAPTION_H = 24   # высота области под подпись
PAD = 8          # отступ вокруг карточки


class PhotoModel(QAbstractListModel):
    """Хранит пути к файлам и отдаёт миниатюры по требованию."""

    def __init__(self, paths: list[Path], parent=None):
        super().__init__(parent)
        self.paths = paths
        self._cache: dict[Path, QPixmap] = {}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.paths)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        path = self.paths[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            return path.name
        if role == Qt.ItemDataRole.ToolTipRole:
            return str(path)
        if role == Qt.ItemDataRole.DecorationRole:
            return self._thumbnail(path)
        return None

    def _thumbnail(self, path: Path) -> QPixmap:
        pm = self._cache.get(path)
        if pm is not None:
            return pm

        reader = QImageReader(str(path))
        reader.setAutoTransform(True)  # учитывать EXIF-поворот
        size = reader.size()
        if size.isValid():
            # декодируем сразу в нужном размере, это намного быстрее полной загрузки
            reader.setScaledSize(size.scaled(THUMB, THUMB, Qt.AspectRatioMode.KeepAspectRatio))
        img = reader.read()

        pm = QPixmap.fromImage(img) if not img.isNull() else QPixmap()
        self._cache[path] = pm
        return pm


class PhotoDelegate(QStyledItemDelegate):
    """Рисует карточку: миниатюра по центру, подпись снизу, рамка при выделении."""

    def sizeHint(self, option, index):
        return QSize(THUMB + PAD * 2, THUMB + CAPTION_H + PAD * 2)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(painter.RenderHint.SmoothPixmapTransform)

        card = option.rect.adjusted(PAD // 2, PAD // 2, -PAD // 2, -PAD // 2)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)

        if selected:
            painter.setPen(QPen(option.palette.highlight().color(), 3))
            painter.drawRect(card.adjusted(1, 1, -1, -1))

        # миниатюра
        pm = index.data(Qt.ItemDataRole.DecorationRole)
        img_area = QRect(card.left(), card.top(), card.width(), THUMB)
        if pm is not None and not pm.isNull():
            w, h = pm.deviceIndependentSize().width(), pm.deviceIndependentSize().height()
            x = img_area.x() + (img_area.width() - w) / 2
            y = img_area.y() + (img_area.height() - h) / 2
            painter.drawPixmap(int(x), int(y), pm)

        # подпись
        caption = index.data(Qt.ItemDataRole.DisplayRole) or ""
        cap_rect = QRect(card.left(), img_area.bottom() + 2, card.width(), CAPTION_H)
        text = painter.fontMetrics().elidedText(
            caption, Qt.TextElideMode.ElideMiddle, cap_rect.width() - 6
        )
        color = option.palette.highlightedText().color() if selected else option.palette.text().color()
        painter.setPen(color)
        painter.drawText(cap_rect, Qt.AlignmentFlag.AlignCenter, text)

        painter.restore()


class PhotoView(QListView):
    def __init__(self, paths: list[Path]):
        super().__init__()
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setMovement(QListView.Movement.Static)
        self.setSpacing(4)
        self.setUniformItemSizes(True)  # важно для скорости: все карточки одинаковые
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setItemDelegate(PhotoDelegate(self))
        self.setModel(PhotoModel(paths, self))
        self.doubleClicked.connect(self._open)

    def _open(self, index):
        path = self.model().paths[index.row()]
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


def find_images(folder: Path) -> list[Path]:
    files = [p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in EXTS]
    return sorted(files, key=lambda p: p.stat().st_mtime)


def main():
    if not FOLDER.is_dir():
        sys.exit(f"Папка не найдена: {FOLDER}")

    paths = find_images(FOLDER)
    print(f"Найдено изображений: {len(paths)}")

    app = QApplication(sys.argv)
    view = PhotoView(paths)
    view.setWindowTitle(FOLDER.name)
    view.resize(1100, 750)
    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()