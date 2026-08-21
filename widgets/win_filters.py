import os

from PyQt6.QtCore import QLocale  # Добавьте импорт QLocale в начало файла
from PyQt6.QtCore import QDate, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (QDateEdit, QGraphicsOpacityEffect, QHBoxLayout,
                             QLabel, QSpinBox, QSplitter, QToolButton,
                             QVBoxLayout, QWidget)

from cfg import Dynamic, JsonData, Static
from system.filters import Filters
from system.lang import Lng

from ._base_widgets import (HSep, QLabel, QWidget, RowArrowWidget, UGroupBox,
                            UMainWidget, UMenu, UPushButton, UTextEditDark,
                            VListSpacerItem, VListWidget, VListWidgetItem)


class ReadableDateLabel(QLabel):

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setWordWrap(True)


class DatesWidget(UGroupBox):
    reload_thumbnails = pyqtSignal()
    calendar_svg = os.path.join(Static.common_icons, "calendar.svg")
    hh = 40

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Главный вертикальный layout для UGroupBox
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(*RowArrowWidget.group_margings)
        self.main_layout.setSpacing(RowArrowWidget.group_spacing)


        title = RowArrowWidget(Lng.dates[JsonData.lng_index])
        title.set_left_icon(self.calendar_svg)
        title.hide_arrow()  # Скрываем стрелку, так как она не нужна для заголовка
        # title.left_icon.setFixedSize(50, 50)
        self.main_layout.addWidget(title)

        self.main_layout.addWidget(HSep())
        
    
        # --- СТРОКА 1: Элементы управления (Горизонтальный layout) ---
        self.top_row_layout = QHBoxLayout()
        self.top_row_layout.setContentsMargins(0, 0, 0, 0)
        self.top_row_layout.setSpacing(0)
        self.top_row_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Период
        period_label = QLabel(Lng.period[JsonData.lng_index])
        self.top_row_layout.addWidget(period_label)
        self.top_row_layout.addSpacing(10)

        # Кнопка пресетов
        self.preset_button = UPushButton("")
        self.preset_button.setFixedWidth(120)
        self.top_row_layout.addWidget(self.preset_button)

        preset_menu = UMenu(None)
        self.preset_button.setMenu(preset_menu)

        self.preset_actions = [
            QAction(Lng.preset_all_time[JsonData.lng_index], preset_menu),
            QAction(Lng.preset_today[JsonData.lng_index], preset_menu),
            QAction(Lng.preset_yesterday[JsonData.lng_index], preset_menu), 
            QAction(Lng.preset_week[JsonData.lng_index], preset_menu),      
            QAction(Lng.preset_month[JsonData.lng_index], preset_menu),     
            QAction(Lng.preset_year[JsonData.lng_index], preset_menu),      
            QAction(Lng.preset_custom[JsonData.lng_index], preset_menu),    
        ]

        self.preset_button.setText(self.preset_actions[Dynamic.date_index].text())

        for x, act in enumerate(self.preset_actions):
            act.triggered.connect(
                lambda e, ind=x, act=act: self.action_cmd(e, ind, act)
            )
            preset_menu.addAction(act)

        self.top_row_layout.addSpacing(15)

        # Выбор дат "От" и "До"
        from_label = QLabel(Lng.from_text[JsonData.lng_index] + ":")
        self.top_row_layout.addWidget(from_label)
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_from.setFixedWidth(110)
        self.top_row_layout.addWidget(self.date_from)

        self.top_row_layout.addSpacing(10) # Небольшой отступ между датами

        to_label = QLabel(Lng.to_text[JsonData.lng_index] + ":")
        self.top_row_layout.addWidget(to_label)
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setFixedWidth(110)
        self.top_row_layout.addWidget(self.date_to)

        if Dynamic.date_start and Dynamic.date_end:
            dt = Dynamic.date_start
            self.date_from.setDate(QDate(dt.year, dt.month, dt.day))
            dt_end = Dynamic.date_end
            self.date_to.setDate(QDate(dt_end.year, dt_end.month, dt_end.day))

        for widget in [self.date_from, self.date_to]:
            widget.setEnabled(True)  
            self.style_date_edit_calendar(widget)
            widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            widget.dateChanged.connect(self.on_custom_date_changed)

        # Пружина смещает кнопку сброса вправо в первой строке
        self.top_row_layout.addStretch(1)

        # Кнопка сброса
        self.reset_btn = UPushButton(Lng.reset[JsonData.lng_index])
        self.reset_btn.clicked.connect(self.clear_btn_cmd) 
        self.top_row_layout.addWidget(self.reset_btn)

        # Добавляем первую строку в главный вертикальный layout
        self.main_layout.addLayout(self.top_row_layout)

        # --- СТРОКА 2: Разделитель HSep ---
        self.main_layout.addWidget(HSep())

        # --- СТРОКА 3: Текстовое состояние ---
        self.readable_date_label = ReadableDateLabel()
        self.main_layout.addWidget(self.readable_date_label)

        # Инициализация логики
        self.handle_preset_change(Dynamic.date_index)
        self.update_readable_date_label()

    def action_cmd(self, e, index: int, action: QAction):
        self.preset_button.setText(action.text())
        self.handle_preset_change(index)
        
        if index == 0:
            self.clear_btn_cmd()
        else:
            self.apply_filter(index)
            
    def on_custom_date_changed(self, qdate):
        custom_index = len(self.preset_actions) - 1
        if Dynamic.date_index != custom_index:
            custom_action = self.preset_actions[custom_index]
            self.preset_button.setText(custom_action.text())
            
        self.apply_filter(custom_index)
        self.update_readable_date_label()
        
    def handle_preset_change(self, index):
        is_custom = (index == len(self.preset_actions) - 1)
        
        self.date_from.blockSignals(True)
        self.date_to.blockSignals(True)
        
        today = QDate.currentDate()
        if not is_custom:
            if index == 0:
                self.date_to.setDate(today)
                self.date_from.setDate(QDate(2012, 1, 1))
            elif index == 1:
                self.date_to.setDate(today)
                self.date_from.setDate(today)
            elif index == 2:
                self.date_to.setDate(today.addDays(-1))
                self.date_from.setDate(today.addDays(-1))
            elif index == 3:
                self.date_to.setDate(today)
                self.date_from.setDate(today.addDays(-7))
            elif index == 4:
                self.date_to.setDate(today)
                self.date_from.setDate(today.addMonths(-1))
            elif index == 5:
                self.date_to.setDate(today)
                self.date_from.setDate(today.addYears(-1))
                
        self.date_from.blockSignals(False)
        self.date_to.blockSignals(False)
        self.update_readable_date_label()

    def update_readable_date_label(self):
        ind = JsonData.lng_index
        if ind == 0:
            locale = QLocale(QLocale.Language.Russian)
        else:
            locale = QLocale(QLocale.Language.English)

        if self.date_from.date() == self.date_to.date():
            str_date = locale.toString(self.date_from.date(), "d MMMM yyyy")
            text = f"{Lng.selected_period[ind]}: {str_date}"
            text = f"{str_date}"
        else:
            str_from = locale.toString(self.date_from.date(), "d MMMM yyyy")
            str_to = locale.toString(self.date_to.date(), "d MMMM yyyy")
            text = f"{Lng.selected_period[ind]}: {Lng.from_text[ind]} {str_from} по {str_to}"
            text = f"{Lng.from_text[ind]} {str_from} по {str_to}"
                
        self.readable_date_label.setText(text)

    def apply_filter(self, index: int):
        Dynamic.date_start = self.date_from.date().toPyDate()
        Dynamic.date_end = self.date_to.date().toPyDate()
        Dynamic.date_index = index
        self.reload_thumbnails.emit()

    def clear_btn_cmd(self, *args):
        Dynamic.loaded_thumbs = 0
        Dynamic.date_start = None
        Dynamic.date_end = None
        Dynamic.date_index = 0
        
        all_time_action = self.preset_actions[0]
        self.preset_button.setText(all_time_action.text())
        self.handle_preset_change(0)
        self.reload_thumbnails.emit()

    def style_date_edit_calendar(self, date_edit: QDateEdit):
        date_edit.setCalendarPopup(True)
        calendar = date_edit.calendarWidget()
        if JsonData.lng_index == 0:
            calendar.setLocale(QLocale(QLocale.Language.Russian))
        else:
            calendar.setLocale(QLocale(QLocale.Language.English))

        calendar.setFixedSize(300, 300)
        calendar.setMaximumDate(QDate.currentDate())
        calendar.setMinimumDate(QDate(2012, 1, 1))
        calendar.setVerticalHeaderFormat(
            calendar.VerticalHeaderFormat.NoVerticalHeader
        )

        widgets = calendar.findChildren(QToolButton)
        for wid in widgets:
            name = wid.objectName()
            wid.setIconSize(QSize(17, 17)) # Твой icon_size
            if name == "qt_calendar_prevmonth":
                wid.setIcon(
                    QIcon(os.path.join(Static.common_icons, "previous.svg"))
                )
            elif name == "qt_calendar_nextmonth":
                wid.setIcon(
                    QIcon(os.path.join(Static.common_icons, "next.svg"))
                )

        for child in calendar.findChildren(QSpinBox):
            child.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        # Применяем ТВОЙ оригинальный CSS-стиль напрямую к календарю
        calendar.setStyleSheet("""
            #qt_calendar_monthbutton::menu-indicator {
                image: none;
                width: 0px;
            }

            #qt_calendar_prevmonth,
            #qt_calendar_nextmonth,
            #qt_calendar_monthbutton,
            #qt_calendar_yearbutton {
                height: 25px;
                background: transparent;                                 
            }

            #qt_calendar_prevmonth,
            #qt_calendar_nextmont {
                width: 25px;
            }

            #qt_calendar_prevmonth:hover,
            #qt_calendar_nextmonth:hover,
            #qt_calendar_monthbutton:hover,
            #qt_calendar_yearbutton:hover {                  
                background: transparent;  
                border: transparent;
                color: white;                                 
            }
        """)


class WinFilters(UMainWidget):
    reset_svg = os.path.join(Static.common_icons, "reset.svg")
    closed_ = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    edit_filters = pyqtSignal()
    ww = 590
    hh = 425
    item_h = 25
    right_group_hh = 280

    def __init__(self):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.filters[JsonData.lng_index])
        self.setFixedWidth(self.ww)
        self.central_layout.setSpacing(10)

        dates = DatesWidget()
        dates.reload_thumbnails.connect(self.reload_thumbnails.emit)
        self.central_layout.addWidget(dates)

        # self.central_layout.addWidget(HSep())

        # Создаем ГОРИЗОНТАЛЬНЫЙ сплиттер
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(15)
        self.central_layout.addWidget(self.splitter)

        # --- Левая группа (Список фильтров) ---
        self.list_group = UGroupBox()
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
        right_lay.setSpacing(0)

        # Групбокс для активных фильтров
        self.active_group = UGroupBox()
        active_group_lay = QVBoxLayout(self.active_group)
        active_group_lay.setContentsMargins(1, 5, 2, 1)
        active_group_lay.setSpacing(10)

        self.active_group.setFixedHeight(self.right_group_hh)

        # Шапка групбокса: статичный лейбл
        self.active_label = QLabel(f" {Lng.active_filters[JsonData.lng_index]}:")
        active_group_lay.addWidget(self.active_label)

        # Текстовое поле для вывода списка
        self.active_filters = UTextEditDark()
        self.active_filters.setReadOnly(True)
        self.active_filters.setText(self.get_filters_text())
        active_group_lay.addWidget(self.active_filters)

        right_lay.addWidget(self.active_group)

        # --- Группа для кнопок с нулевыми отступами ---
        self.reset_group = UGroupBox()
        reset_group_lay = QVBoxLayout(self.reset_group)
        reset_group_lay.setContentsMargins(*RowArrowWidget.group_margings)
        reset_group_lay.setSpacing(RowArrowWidget.group_spacing)

        # Создаем кастомную кнопку редактирования фильтров
        self.edit_filters_btn = RowArrowWidget(Lng.edit[JsonData.lng_index])
        self.edit_filters_btn.set_left_icon(self.reset_svg) # Убедитесь, что self.edit_svg определен ранее
        self.edit_filters_btn.clicked.connect(self.edit_filters.emit) # Метод-обработчик клика

        # Создаем кастомную кнопку сброса
        self.reset_btn = RowArrowWidget(Lng.reset[JsonData.lng_index])
        self.reset_btn.set_left_icon(self.reset_svg)
        self.reset_btn.clicked.connect(self.reset_cmd)

        right_lay.addSpacing(10)
        # Добавляем сначала кнопку редактирования, затем кнопку сброса в слой группы
        reset_group_lay.addWidget(self.edit_filters_btn)
        reset_group_lay.addWidget(HSep())
        reset_group_lay.addWidget(self.reset_btn)

        # Добавляем группу в основной правый контейнер
        right_lay.addWidget(self.reset_group)
        right_lay.addSpacing(10)
        right_lay.addStretch()
        
        self.splitter.addWidget(self.right_container)

        # Устанавливаем пропорции ширины
        self.splitter.setSizes([250, 350])
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)

        self.adjustSize()
        self.setFixedHeight(self.height())

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
