import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGroupBox, QSplitter, QVBoxLayout

from cfg import Dynamic, JsonData, Static
from system.filters import Filters
from system.lang import Lng

from ._base_widgets import (UMainWidget, UPushButton, UTextEdit,
                            VListSpacerItem, VListWidget, VListWidgetItem)


class WinFilters(UMainWidget):
    reset_svg = os.path.join(Static.common_icons, "reset.svg")
    closed_ = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    ww = 320
    hh = 450
    item_h = 25

    def __init__(self):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.filters[JsonData.lng_index])
        self.setFixedSize(self.ww, self.hh)

        self.central_layout.setSpacing(10)
        self.central_layout.setContentsMargins(10, 10, 10, 13)

        # Создаем вертикальный сплиттер
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setHandleWidth(15)
        self.central_layout.addWidget(self.splitter)

        # --- Верхняя группа (Список фильтров) ---
        self.list_group = QGroupBox()
        list_group_lay = QVBoxLayout(self.list_group)
        list_group_lay.setContentsMargins(1, 10, 1, 1)
        list_group_lay.setSpacing(0)
        
        self.list_widget = VListWidget()
        self.list_widget.itemClicked.connect(self.item_cmd)
        list_group_lay.addWidget(self.list_widget)
        
        # Добавляем ПЕРВУЮ ГРУППУ в сплиттер
        self.splitter.addWidget(self.list_group)

        # Заполнение списка элементами
        favs_item = VListWidgetItem(
            parent=self.list_widget,
            text=Lng.favorites[JsonData.lng_index],
            height=self.item_h
        )
        favs_item.set_checkable()
        self.list_widget.addItem(favs_item)
        if Dynamic.filter_favs:
            favs_item.setCheckState(Qt.CheckState.Checked)

        folder_item = VListWidgetItem(
            parent=self.list_widget,
            text=Lng.only_this_folder[JsonData.lng_index],
            height=self.item_h
        )
        folder_item.set_checkable()
        self.list_widget.addItem(folder_item)
        if Dynamic.filter_only_folder:
            folder_item.setCheckState(Qt.CheckState.Checked)

        self.list_widget.addItem(
            VListSpacerItem(parent=self.list_widget)
        )

        for i in Filters.items:
            item = VListWidgetItem(
                parent=self.list_widget,
                text=i,
                height=self.item_h
            )
            item.set_checkable()
            self.list_widget.addItem(item)
            if i in Dynamic.filters_enabled:
                item.setCheckState(Qt.CheckState.Checked)

        self.list_widget.setCurrentRow(0)
        
        # --- Нижняя группа (Активные фильтры) ---
        self.active_group = QGroupBox()
        active_group_lay = QVBoxLayout(self.active_group)
        active_group_lay.setContentsMargins(1, 10, 1, 1)
        active_group_lay.setSpacing(0)

        txt = f"{Lng.active_filters[JsonData.lng_index]}: {', '.join(Dynamic.filters_enabled)}"
        self.active_filters = UTextEdit()
        self.active_filters.setReadOnly(True)
        self.active_filters.setText(txt)
        active_group_lay.addWidget(self.active_filters)
        
        # Добавляем ВТОРУЮ ГРУППУ в сплиттер
        self.splitter.addWidget(self.active_group)

        # Устанавливаем базовые пропорции и логику растяжения для групп в сплиттере
        self.splitter.setSizes([300, 100])
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)

        # Кнопка сброса
        self.reset_btn = UPushButton(Lng.reset[JsonData.lng_index])
        self.reset_btn.clicked.connect(self.reset_cmd)
        self.central_layout.addWidget(self.reset_btn, alignment=Qt.AlignmentFlag.AlignCenter)


    def item_cmd(self, item: VListWidgetItem):
        if isinstance(item, VListSpacerItem):
            return
        if item.text() == Lng.favorites[JsonData.lng_index]:
            if Dynamic.filter_favs:
                Dynamic.filter_favs = False
                item.setCheckState(Qt.CheckState.Unchecked)
            else:
                Dynamic.filter_favs = True
                item.setCheckState(Qt.CheckState.Checked)
        elif item.text() == Lng.only_this_folder[JsonData.lng_index]:
            if Dynamic.filter_only_folder:
                Dynamic.filter_only_folder = False
                item.setCheckState(Qt.CheckState.Unchecked)
            else:
                Dynamic.filter_only_folder = True
                item.setCheckState(Qt.CheckState.Checked)
        elif item.text() in Dynamic.filters_enabled:
            Dynamic.filters_enabled.remove(item.text())
            item.setCheckState(Qt.CheckState.Unchecked)
        else:
            Dynamic.filters_enabled.append(item.text())
            item.setCheckState(Qt.CheckState.Checked)

        txt = f"{Lng.active_filters[JsonData.lng_index]}: {', '.join(Dynamic.filters_enabled)}"
        self.active_filters.setText(txt)

        self.reload_thumbnails.emit()

    def reset_cmd(self):
        items = [
            self.list_widget.item(i)
            for i in range(self.list_widget.count())
        ]
        # удаляем спейсер
        items.pop(2)
        for item in items:
            item.setCheckState(Qt.CheckState.Unchecked)
        Dynamic.filter_favs = False
        Dynamic.filter_only_folder = False
        Dynamic.filters_enabled.clear()
        self.reload_thumbnails.emit()

        txt = f"{Lng.active_filters[JsonData.lng_index]}: {', '.join(Dynamic.filters_enabled)}"
        self.active_filters.setText(txt)

    def mouseReleaseEvent(self, a0):
        return super().mouseReleaseEvent(a0)

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