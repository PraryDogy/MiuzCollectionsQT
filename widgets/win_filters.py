from PyQt5.QtCore import Qt, pyqtSignal

from cfg import cfg, Dynamic
from system.filters import Filters
from system.lang import Lng

from ._base_widgets import (SingleActionWindow, UListSpacerItem,
                            UListWidgetItem, VListWidget)



class WinFilters(SingleActionWindow):
    closed_ = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    ww = 400
    hh = 400

    def __init__(self):
        super().__init__()
        self.setWindowTitle(Lng.filters[cfg.lng])
        self.setFixedSize(self.ww, self.hh)

        self.list_widget = VListWidget()
        self.list_widget.itemClicked.connect(
            self.item_cmd
        )
        self.central_layout.addWidget(self.list_widget)

        favs_item = UListWidgetItem(
            parent=self.list_widget,
            text=Lng.favorites[cfg.lng]
        )
        favs_item.setFlags(
            favs_item.flags() | Qt.ItemFlag.ItemIsUserCheckable
        )
        favs_item.setCheckState(Qt.CheckState.Unchecked)
        self.list_widget.addItem(favs_item)

        folder_item = UListWidgetItem(
            parent=self.list_widget,
            text=Lng.only_this_folder[cfg.lng]
        )
        folder_item.setFlags(
            folder_item.flags() | Qt.ItemFlag.ItemIsUserCheckable
        )
        folder_item.setCheckState(Qt.CheckState.Unchecked)
        self.list_widget.addItem(folder_item)

        self.list_widget.addItem(UListSpacerItem(parent=self.list_widget))

        for i in Filters.filters:
            item = UListWidgetItem(
                parent=self.list_widget,
                text=i
            )
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)
            if i in Dynamic.filters_enabled:
                item.setCheckState(Qt.CheckState.Checked)

        self.list_widget.setCurrentRow(0)

    def item_cmd(self, item: UListWidgetItem):
        if item.text() in Dynamic.filters_enabled:
            Dynamic.filters_enabled.remove(item.text())
            item.setCheckState(Qt.CheckState.Unchecked)
        else:
            Dynamic.filters_enabled.append(item.text())
            item.setCheckState(Qt.CheckState.Checked)
        self.reload_thumbnails.emit()

    def closeEvent(self, a0):
        self.closed_.emit()
        return super().closeEvent(a0)
    
    def deleteLater(self):
        self.closed_.emit()
        return super().deleteLater()
    
    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)