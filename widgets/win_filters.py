import os

from PyQt6.QtCore import QLocale  # Добавьте импорт QLocale в начало файла
from PyQt6.QtCore import QDate, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QSpinBox, QSplitter,
                             QToolButton, QVBoxLayout, QWidget)

from cfg import Dynamic, JsonData, Static
from system.filters import Filters
from system.lang import Lng

from ._base_widgets import (HSep, QLabel, QWidget, RowArrowWidget, UDateEdit,
                            UGroupBox, UMainWidget, UMenu, UPushButton,
                            UTextEditDark, UListSpacerItem, UListWidget,
                            UListWidgetItem)
from .caledar_widget import Calendar, CalendarBigDate


class WinDatesDateLabel(QLabel):

    def __init__(self):
        super().__init__()


class DatesWidget(UGroupBox):
    reload_thumbnails = pyqtSignal()
    calendar_svg = Static.COMMON_ICONS / "calendar.svg"
    hh = 40

    def __init__(self, parent=None):
        super().__init__(parent)

        if Dynamic.date_start:
            dt = Dynamic.date_start
            self.q_date_start = QDate(dt.year, dt.month, dt.day)
        else:
            self.q_date_start = QDate(Calendar.min_year, 1, 1)

        if Dynamic.date_end:
            dt = Dynamic.date_end
            self.q_date_end = QDate(dt.year, dt.month, dt.day)
        else:
            dt = QDate.currentDate()
            self.q_date_end = QDate(dt)
        
        # Главный вертикальный layout для UGroupBox
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(*RowArrowWidget.group_margings)
        self.main_layout.setSpacing(RowArrowWidget.group_spacing)

        self.title_widget = RowArrowWidget("")
        self.title_widget.set_left_icon(self.calendar_svg)
        self.title_widget.hide_arrow()  
        self.main_layout.addWidget(self.title_widget)

        self.main_layout.addWidget(HSep())
        self.main_layout.addSpacing(5)
        
        # --- СТРОКА 1: Виджет панели управления (Вместо вложенного layout) ---
        self.top_row_widget = QWidget()
        self.top_row_layout = QHBoxLayout(self.top_row_widget)
        self.top_row_layout.setContentsMargins(0, 0, 0, 0)
        self.top_row_layout.setSpacing(0)
        self.top_row_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Период
        period_label = QLabel(Lng.period[JsonData.lng_index])
        self.top_row_layout.addWidget(period_label)
        self.top_row_layout.addSpacing(10)

        # Кнопка пресетов
        self.preset_button = UPushButton("")
        self.preset_button.setFixedWidth(100)
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
        self.top_row_layout.addSpacing(5)
        self.date_start_btn = UPushButton(self.date_digits(self.q_date_start))
        self.date_start_btn.clicked.connect(lambda: self.show_calendar_win("start"))
        self.top_row_layout.addWidget(self.date_start_btn)

        self.top_row_layout.addSpacing(10) 

        to_label = QLabel(Lng.to_text[JsonData.lng_index] + ":")
        self.top_row_layout.addWidget(to_label)
        self.top_row_layout.addSpacing(5)
        self.date_end_btn = UPushButton(self.date_digits(self.q_date_end))
        self.date_end_btn.clicked.connect(lambda: self.show_calendar_win("end"))
        self.top_row_layout.addWidget(self.date_end_btn)

        # Пружина смещает кнопку сброса вправо
        self.top_row_layout.addStretch(1)

        # Кнопка сброса
        self.reset_btn = UPushButton(Lng.reset[JsonData.lng_index])
        self.reset_btn.clicked.connect(self.clear_btn_cmd) 
        self.top_row_layout.addWidget(self.reset_btn)

        # Добавляем созданную строку-виджет в главный вертикальный layout
        self.main_layout.addWidget(self.top_row_widget)

        self.main_layout.addSpacing(5)

        self.update_readable_date_label(index=0)

    def date_digits(self, q_date: QDate):
        return q_date.toString("dd.MM.yyyy")

    def show_calendar_win(self, flag: str):

        def set_date_end(date: QDate):
            self.date_end_btn.setText(self.date_digits(date))
            self.q_date_end = date
            index = len(self.preset_actions) - 1
            self.handle_preset_change(index)
            self.apply_filter(index)
            self.preset_button.setText(Lng.period[JsonData.lng_index])

        def set_date_start(date: QDate):
            self.date_start_btn.setText(self.date_digits(date))
            self.q_date_start = date
            index = len(self.preset_actions) - 1
            self.handle_preset_change(index)
            self.apply_filter(index)
            self.preset_button.setText(Lng.period[JsonData.lng_index])

        if flag == "start":
            qdate = self.q_date_start
            callback = lambda qdate: set_date_start(qdate)
        elif flag == "end":
            qdate = self.q_date_end
            callback = lambda qdate: set_date_end(qdate)

        self.calendar_win = Calendar(qdate)
        self.calendar_win.center_to_parent(self.window())
        self.calendar_win.date_selected.connect(callback)
        self.calendar_win.show()

    def action_cmd(self, e, index: int, action: QAction):
        self.preset_button.setText(action.text())
        self.handle_preset_change(index)
        self.apply_filter(index)

    def handle_preset_change(self, index):
        is_custom = (index == len(self.preset_actions) - 1)
        
        self.date_start_btn.blockSignals(True)
        self.date_end_btn.blockSignals(True)
        
        today = QDate.currentDate()
        if not is_custom:
            if index == 0:  # Все время
                self.q_date_start = QDate(Calendar.min_year, 1, 1)
                self.q_date_end = today
            elif index == 1:  # Сегодня
                self.q_date_start = today
                self.q_date_end = today
            elif index == 2:  # Вчера
                self.q_date_start = today.addDays(-1)
                self.q_date_end = today.addDays(-1)
            elif index == 3:  # Последняя неделя
                self.q_date_start = today.addDays(-7)
                self.q_date_end = today
            elif index == 4:  # Последний месяц
                self.q_date_start = today.addMonths(-1)
                self.q_date_end = today
            elif index == 5:  # Последний год
                self.q_date_start = today.addYears(-1)
                self.q_date_end = today
                
        self.date_start_btn.setText(self.date_digits(self.q_date_start))
        self.date_end_btn.setText(self.date_digits(self.q_date_end))
        self.update_readable_date_label(index)
        
        # Не забудьте разблокировать сигналы кнопок
        self.date_start_btn.blockSignals(False)
        self.date_end_btn.blockSignals(False)

    def update_readable_date_label(self, index: int):
        ind = JsonData.lng_index
        if ind == 0:
            locale = QLocale(QLocale.Language.Russian)
        else:
            locale = QLocale(QLocale.Language.English)

        text = self.preset_actions[index].text()
        if index == len(self.preset_actions) - 1:
            if self.q_date_start == self.q_date_end:
                str_date = locale.toString(self.q_date_start, "d MMMM yyyy")
                text = f"{str_date}"
            else:
                str_from = locale.toString(self.q_date_start, "d MMMM yyyy")
                str_to = locale.toString(self.q_date_end, "d MMMM yyyy")
                text = f"{Lng.from_text[ind]} {str_from} по {str_to}"

        self.title_widget.text_widget.setText(text)

    def apply_filter(self, index: int):
        Dynamic.date_start = self.q_date_start.toPyDate()
        Dynamic.date_end = self.q_date_end.toPyDate()
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


class WinFilters(UMainWidget):
    reset_svg = Static.COMMON_ICONS / "reset.svg"
    edit_svg = Static.COMMON_ICONS / "edit.svg"
    closed_ = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    edit_filters = pyqtSignal()
    ww = 590
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
        
        self.list_widget = UListWidget()
        self.list_widget.itemClicked.connect(self.item_cmd)
        self.splitter.addWidget(self.list_widget)
        
        self.splitter.addWidget(self.list_widget)

        # Заполнение списка элементами
        favs_item = UListWidgetItem(
            parent=self.list_widget,
            text=Lng.favorites[JsonData.lng_index]
        )
        favs_item.set_checkable()
        self.list_widget.addItem(favs_item)
        if Dynamic.filter_favs:
            favs_item.setCheckState(Qt.CheckState.Checked)

        folder_item = UListWidgetItem(
            parent=self.list_widget,
            text=Lng.without_subfolders[JsonData.lng_index]
        )
        folder_item.set_checkable()
        self.list_widget.addItem(folder_item)
        if Dynamic.filter_only_folder:
            folder_item.setCheckState(Qt.CheckState.Checked)

        self.list_widget.addItem(
            UListSpacerItem(parent=self.list_widget)
        )

        for i in Filters.items:
            item = UListWidgetItem(
                parent=self.list_widget,
                text=i
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

        # Шапка групбокса: статичный лейбл
        self.active_label = QLabel(f" {Lng.active_filters[JsonData.lng_index]}:")
        right_lay.addWidget(self.active_label)

        right_lay.addSpacing(5)

        # Текстовое поле для вывода списка
        self.active_filters = UTextEditDark()
        self.active_filters.setReadOnly(True)
        self.active_filters.setText(self.get_filters_text())
        self.active_filters.setFixedHeight(self.right_group_hh)
        right_lay.addWidget(self.active_filters)

        # --- Группа для кнопок с нулевыми отступами ---
        self.reset_group = UGroupBox()
        reset_group_lay = QVBoxLayout(self.reset_group)
        reset_group_lay.setContentsMargins(*RowArrowWidget.group_margings)
        reset_group_lay.setSpacing(RowArrowWidget.group_spacing)

        # Создаем кастомную кнопку редактирования фильтров
        self.edit_filters_btn = RowArrowWidget(Lng.edit[JsonData.lng_index])
        self.edit_filters_btn.set_left_icon(self.edit_svg) # Убедитесь, что self.edit_svg определен ранее
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

    def item_cmd(self, item: UListWidgetItem):
        if isinstance(item, UListSpacerItem):
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
