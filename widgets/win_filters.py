import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGroupBox, QSplitter, QVBoxLayout

from cfg import Dynamic, JsonData, Static
from system.filters import Filters
from system.lang import Lng

from ._base_widgets import (QLabel, QWidget, RowArrowWidget, UMainWidget,
                            UPushButton, UTextEdit, VListSpacerItem,
                            VListWidget, VListWidgetItem)


class WinFilters(UMainWidget):
    reset_svg = os.path.join(Static.common_icons, "reset.svg")
    closed_ = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    ww = 600
    hh = 390
    item_h = 25
    right_group_hh = 280

    def __init__(self):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.filters[JsonData.lng_index])
        self.setFixedSize(self.ww, self.hh)

        # Создаем ГОРИЗОНТАЛЬНЫЙ сплиттер
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(15)
        self.central_layout.addWidget(self.splitter)

        # --- Левая группа (Список фильтров) ---
        self.list_group = QGroupBox()
        list_group_lay = QVBoxLayout(self.list_group)
        list_group_lay.setContentsMargins(1, 10, 1, 1)
        list_group_lay.setSpacing(0)
        
        self.list_widget = VListWidget()
        self.list_widget.itemClicked.connect(self.item_cmd)
        list_group_lay.addWidget(self.list_widget)
        
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
            text=Lng.without_subfolders[JsonData.lng_index],
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
        
        # --- Правая часть (Контейнер) ---
        self.right_container = QWidget()
        right_lay = QVBoxLayout(self.right_container)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(10)

        # Групбокс для активных фильтров
        self.active_group = QGroupBox()
        active_group_lay = QVBoxLayout(self.active_group)
        active_group_lay.setContentsMargins(1, 5, 2, 1)
        active_group_lay.setSpacing(10)

        self.active_group.setFixedHeight(self.right_group_hh)

        # Шапка групбокса: статичный лейбл
        self.active_label = QLabel(f" {Lng.active_filters[JsonData.lng_index]}:")
        active_group_lay.addWidget(self.active_label)

        # Текстовое поле для вывода списка
        self.active_filters = UTextEdit()
        self.active_filters.setReadOnly(True)
        self.active_filters.setText(self.get_filters_text())
        active_group_lay.addWidget(self.active_filters)

        right_lay.addWidget(self.active_group)

        # --- Группа для кнопки сброса с нулевыми отступами ---
        self.reset_group = QGroupBox()
        reset_group_lay = QVBoxLayout(self.reset_group)
        reset_group_lay.setContentsMargins(5, 0, 5, 0)
        reset_group_lay.setSpacing(0)

        # Создаем кастомную кнопку сброса
        self.reset_btn = RowArrowWidget(Lng.reset[JsonData.lng_index])
        self.reset_btn.setFixedHeight(25)
        self.reset_btn.set_left_icon(self.reset_svg)
        self.reset_btn.hide_sep()
        self.reset_btn.clicked.connect(self.reset_cmd)
        
        # Добавляем кнопку в слой группы, а группу — в основной правый контейнер
        reset_group_lay.addWidget(self.reset_btn)
        right_lay.addWidget(self.reset_group)

        right_lay.addStretch()

        
        self.splitter.addWidget(self.right_container)

        # Устанавливаем пропорции ширины
        self.splitter.setSizes([250, 350])
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)

    def get_filters_text(self):
        active_list = []

        if Dynamic.filter_favs:
            active_list.append(Lng.favorites[JsonData.lng_index])

        if Dynamic.filter_only_folder:
            active_list.append(Lng.without_subfolders[JsonData.lng_index])

        if Dynamic.filters_enabled:
            active_list.extend(Dynamic.filters_enabled)

        if not active_list:
            return Lng.no[JsonData.lng_index]
        
        return ', '.join(active_list)

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
        elif item.text() == Lng.without_subfolders[JsonData.lng_index]:
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

        self.active_filters.setText(self.get_filters_text())
        self.reload_thumbnails.emit()

    def reset_cmd(self):
        items = [
            self.list_widget.item(i)
            for i in range(self.list_widget.count())
        ]
        items.pop(2)  # удаляем спейсер из списка обработки
        for item in items:
            item.setCheckState(Qt.CheckState.Unchecked)
        Dynamic.filter_favs = False
        Dynamic.filter_only_folder = False
        Dynamic.filters_enabled.clear()
        self.reload_thumbnails.emit()
        self.active_filters.setText(self.get_filters_text())

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
