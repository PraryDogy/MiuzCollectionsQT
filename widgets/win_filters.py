import os

from PyQt6.QtCore import QDate, QLocale, QPoint, Qt, pyqtSignal, QSize
from PyQt6.QtGui import QAction
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QHBoxLayout, QSplitter, QVBoxLayout

from cfg import Dynamic, JsonData, Static
from system.filters import Filters
from system.lang import Lng

from ._base_widgets import (RowArrowWidget, TransparentLabel,
                            TransparentWidget, UGroupBox, USep,
                            FlowLayout, UListWidget, UListWidgetItem,
                            UMainWidget, UMenu, UPushButton, TransparentFrame)
from .caledar_widget import Calendar


UGroupBox_margins = (5, 5, 5, 5)
UGroupBox_spacing = 10



class WinFiltersTitle(TransparentLabel):
    def __init__(self, text: str):
        super().__init__(text)


class DatesWidget(UGroupBox):
    reload_thumbnails = pyqtSignal()
    calendar_svg = Static.COMMON_ICONS / "calendar.svg"
    svg_calendar_size = (15, 15)

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
        # self.main_layout.setContentsMargins(*RowArrowWidget.group_margings)
        self.main_layout.setContentsMargins(*UGroupBox_margins)
        # self.main_layout.setSpacing(RowArrowWidget.group_spacing)
        self.main_layout.setSpacing(UGroupBox_spacing)

        self.title_widget = WinFiltersTitle(Lng.dates_management[JsonData.lng_index])
        self.main_layout.addWidget(self.title_widget)

        self.main_layout.addWidget(USep())

        # --- 1. Блок большой даты ---
        dynamic_container = TransparentWidget()
        self.main_layout.addWidget(dynamic_container) # Добавляем сразу
        
        dynamic_container_lay = QHBoxLayout(dynamic_container)
        dynamic_container_lay.setContentsMargins(0, 0, 0, 0)
        dynamic_container_lay.setSpacing(10)

        calendar_icon = QSvgWidget()
        calendar_icon.load(str(self.calendar_svg))
        calendar_icon.setFixedSize(*self.svg_calendar_size)
        dynamic_container_lay.addWidget(calendar_icon)

        self.dynamic_label = TransparentLabel()
        self.dynamic_label.setFixedWidth(self.width())
        dynamic_container_lay.addWidget(self.dynamic_label)
        dynamic_container_lay.addStretch()

        # self.main_layout.addWidget(USep())
        
        # --- СТРОКА 1: Виджет панели управления (Вместо вложенного layout) ---
        self.top_row_widget = TransparentWidget()
        self.top_row_layout = QHBoxLayout(self.top_row_widget)
        self.top_row_layout.setContentsMargins(0, 0, 0, 0)
        self.top_row_layout.setSpacing(0)

        # Период
        period_label = TransparentLabel(Lng.period[JsonData.lng_index])
        self.top_row_layout.addWidget(period_label)
        self.top_row_layout.addSpacing(10)

        # Кнопка пресетов
        self.preset_button = UPushButton("")
        self.preset_button.setFixedWidth(100)
        self.top_row_layout.addWidget(self.preset_button)

        preset_menu = UMenu(parent=self)
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
        from_label = TransparentLabel(Lng.from_text[JsonData.lng_index] + ":")
        self.top_row_layout.addWidget(from_label)
        self.top_row_layout.addSpacing(5)
        self.date_start_btn = UPushButton(self.date_digits(self.q_date_start))
        self.date_start_btn.clicked.connect(lambda: self.show_calendar_win("start"))
        self.top_row_layout.addWidget(self.date_start_btn)

        self.top_row_layout.addSpacing(10) 

        to_label = TransparentLabel(Lng.to_text[JsonData.lng_index] + ":")
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
            target_btn = self.date_start_btn
        elif flag == "end":
            qdate = self.q_date_end
            callback = lambda qdate: set_date_end(qdate)
            target_btn = self.date_end_btn

        self.calendar_win = Calendar(qdate)
        global_pos = target_btn.mapToGlobal(QPoint(0, target_btn.height()))
        offset = QPoint(0, 0)  # (по X, по Y)
        self.calendar_win.move(global_pos + offset)
        # self.calendar_win.center_to_parent(self.window())
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

        str_from = locale.toString(self.q_date_start, "d MMMM yyyy")
        str_to = locale.toString(self.q_date_end, "d MMMM yyyy")
        text = f"{Lng.from_text[ind]} {str_from} по {str_to}"

        self.dynamic_label.setText(text)

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


class WinFiltersTagWidget(TransparentFrame):
    icon_path = Static.COMMON_ICONS / "trash.svg"
    clicked_trash = pyqtSignal()
    toggled = pyqtSignal(bool) 

    # Добавляем параметр show_trash=True по умолчанию
    def __init__(self, text: str, active: bool = False, show_trash: bool = True):
        super().__init__()
        self.setFixedHeight(23)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._active = active
        self.setProperty("active", str(active))

        self.h_lay = QHBoxLayout(self)
        self.h_lay.setContentsMargins(7, 2, 7, 2)
        self.h_lay.setSpacing(6)

        self.title = TransparentLabel(text)
        self.h_lay.addWidget(self.title)

        # Создаем контейнер и иконку только если передан флаг True
        if show_trash:
            self.close_btn_wrapper = TransparentWidget()
            close_lay = QVBoxLayout(self.close_btn_wrapper)
            close_lay.setContentsMargins(0, 1, 0, 0)
            close_lay.setSpacing(0)

            self.trash_btn = QSvgWidget()
            self.trash_btn.mouseReleaseEvent = self.on_trash_clicked
            self.trash_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.trash_btn.load(str(self.icon_path))
            self.trash_btn.setFixedSize(12, 12)

            close_lay.addWidget(self.trash_btn)
            self.h_lay.addWidget(self.close_btn_wrapper)

        if active:
            self.set_active(True)

    @property
    def is_active(self) -> bool:
        return self._active

    def set_active(self, active: bool):
        if self._active != active:
            self._active = active
            self.setProperty("active", str(active))
            self.style().unpolish(self)
            self.style().polish(self)
            self.update()

    def on_trash_clicked(self, event):
        event.accept()
        self.clicked_trash.emit()

    def clicked_trash_cmd(self):
        self.clicked_trash.emit()

    def hide_trash_btn(self):
        # Метод можно оставить для обратной совместимости, если где-то вызывается, 
        # но теперь он больше не нужен для наследников.
        if hasattr(self, 'close_btn_wrapper'):
            self.close_btn_wrapper.deleteLater()

    def mouseReleaseEvent(self, a0):
        new_state = not self._active
        self.set_active(new_state)
        self.toggled.emit(new_state)
        super().mouseReleaseEvent(a0)


class WinFiltersFavTag(WinFiltersTagWidget):
    def __init__(self, text):
        if Dynamic.favs_tag_enabled:
            active = True
        else:
            active = False
        super().__init__(text, show_trash=False, active=active)

    def clicked_trash_cmd(self):
        pass


class WinFiltersOnlyFolderTag(WinFiltersTagWidget):
    def __init__(self, text):
        if Dynamic.no_subfolders_tag_enabled:
            active = True
        else:
            active = False
        super().__init__(text, show_trash=False, active=active)

    def clicked_trash_cmd(self):
        pass


class WinFiltersWordTag(WinFiltersTagWidget):
    def __init__(self, text):
        if text in Dynamic.word_tags_list:
            active = True
        else:
            active = False
        super().__init__(text, show_trash=True, active=active)

    def clicked_trash_cmd(self):
        pass


class TagsContolWidget(TransparentWidget):
    load_st_grid = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.flow_layout = FlowLayout(self, spacing=7)
        self.flow_layout.setContentsMargins(0, 0, 0, 0)
        self._create_tags()

    def _create_tags(self):
        tag = WinFiltersFavTag(Lng.favorites[JsonData.lng_index])
        tag.clicked_trash.connect(self.load_st_grid.emit)
        self.flow_layout.addWidget(tag)

        tag = WinFiltersOnlyFolderTag(Lng.without_subfolders[JsonData.lng_index])
        tag.clicked_trash.connect(self.load_st_grid.emit)
        self.flow_layout.addWidget(tag)

        for word in Filters.items:
            tag = WinFiltersWordTag(word)
            tag.clicked_trash.connect(self.load_st_grid.emit)
            self.flow_layout.addWidget(tag)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.flow_layout.heightForWidth(width)

    def sizeHint(self):
        width = self.parentWidget().width() if self.parentWidget() else 500
        return QSize(width, self.heightForWidth(width))


class TagsWidget(UGroupBox):
    def __init__(self):
        super().__init__()
        self.v_lay = QVBoxLayout(self)
        self.v_lay.setContentsMargins(*UGroupBox_margins)
        self.v_lay.setSpacing(UGroupBox_spacing)

        self.title_widget = WinFiltersTitle(Lng.tag_management[JsonData.lng_index])
        self.v_lay.addWidget(self.title_widget)

        self.v_lay.addWidget(USep())

        self.tags_control_widget = TagsContolWidget()
        self.v_lay.addWidget(self.tags_control_widget)
    

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

        self.dates_widget = DatesWidget()
        self.dates_widget.reload_thumbnails.connect(self.reload_thumbnails.emit)
        self.central_layout.addWidget(self.dates_widget)

        self.tags_widget = TagsWidget()
        self.central_layout.addWidget(self.tags_widget)

        # self.central_layout.addWidget(HSep())

        # Создаем ГОРИЗОНТАЛЬНЫЙ сплиттер
        # self.splitter = QSplitter(Qt.Orientation.Horizontal)
        # self.splitter.setHandleWidth(15)
        # self.central_layout.addWidget(self.splitter)
        
        # self.list_widget = UListWidget()
        # self.list_widget.itemClicked.connect(self.item_cmd)
        # self.splitter.addWidget(self.list_widget)
        
        # self.splitter.addWidget(self.list_widget)

        # # Заполнение списка элементами
        # favs_item = UListWidgetItem(
        #     parent=self.list_widget,
        #     text=Lng.favorites[JsonData.lng_index]
        # )
        # favs_item.set_checkable()
        # self.list_widget.addItem(favs_item)
        # if Dynamic.favs_tag_enabled:
        #     favs_item.setCheckState(Qt.CheckState.Checked)

        # folder_item = UListWidgetItem(
        #     parent=self.list_widget,
        #     text=Lng.without_subfolders[JsonData.lng_index]
        # )
        # folder_item.set_checkable()
        # self.list_widget.addItem(folder_item)
        # if Dynamic.no_subfolders_tag_enabled:
        #     folder_item.setCheckState(Qt.CheckState.Checked)

        # self.list_widget.addItem(
        #     UListSpacerItem(parent=self.list_widget)
        # )

        # for i in Filters.items:
        #     item = UListWidgetItem(
        #         parent=self.list_widget,
        #         text=i
        #     )
        #     item.set_checkable()
        #     self.list_widget.addItem(item)
        #     if i in Dynamic.word_tags_list:
        #         item.setCheckState(Qt.CheckState.Checked)

        # self.list_widget.setCurrentRow(0)
        
        # # --- Правая часть (Контейнер) ---
        # self.right_container = TransparentWidget()
        # right_lay = QVBoxLayout(self.right_container)
        # right_lay.setContentsMargins(0, 0, 0, 0)
        # right_lay.setSpacing(0)

        # # Шапка групбокса: статичный лейбл
        # self.active_label = TransparentLabel(f" {Lng.active_filters[JsonData.lng_index]}:")
        # right_lay.addWidget(self.active_label)

        # right_lay.addSpacing(5)

        # # Текстовое поле для вывода списка
        # self.active_filters = UTextEdit()
        # self.active_filters.setReadOnly(True)
        # self.active_filters.setText(self.get_filters_text())
        # self.active_filters.setFixedHeight(self.right_group_hh)
        # right_lay.addWidget(self.active_filters)

        # # --- Группа для кнопок с нулевыми отступами ---
        # self.reset_group = UGroupBox()
        # reset_group_lay = QVBoxLayout(self.reset_group)
        # reset_group_lay.setContentsMargins(*RowArrowWidget.group_margings)
        # reset_group_lay.setSpacing(RowArrowWidget.group_spacing)

        # # Создаем кастомную кнопку редактирования фильтров
        # self.edit_filters_btn = RowArrowWidget(Lng.edit[JsonData.lng_index])
        # self.edit_filters_btn.set_left_icon(self.edit_svg) # Убедитесь, что self.edit_svg определен ранее
        # self.edit_filters_btn.clicked.connect(self.edit_filters.emit) # Метод-обработчик клика

        # # Создаем кастомную кнопку сброса
        # self.reset_btn = RowArrowWidget(Lng.reset[JsonData.lng_index])
        # self.reset_btn.set_left_icon(self.reset_svg)
        # self.reset_btn.clicked.connect(self.reset_cmd)

        # right_lay.addSpacing(10)
        # # Добавляем сначала кнопку редактирования, затем кнопку сброса в слой группы
        # reset_group_lay.addWidget(self.edit_filters_btn)
        # reset_group_lay.addWidget(UHorizontalSep())
        # reset_group_lay.addWidget(self.reset_btn)

        # # Добавляем группу в основной правый контейнер
        # right_lay.addWidget(self.reset_group)
        # right_lay.addSpacing(10)
        # right_lay.addStretch()
        
        # self.splitter.addWidget(self.right_container)

        # # Устанавливаем пропорции ширины
        # self.splitter.setSizes([250, 350])
        # self.splitter.setStretchFactor(0, 1)
        # self.splitter.setStretchFactor(1, 0)

        # self.adjustSize()
        # self.setFixedHeight(self.height())

    # def get_filters_text(self):
    #     active_list = []

    #     if Dynamic.favs_tag_enabled:
    #         active_list.append(Lng.favorites[JsonData.lng_index])

    #     if Dynamic.no_subfolders_tag_enabled:
    #         active_list.append(Lng.without_subfolders[JsonData.lng_index])

    #     if Dynamic.word_tags_list:
    #         active_list.extend(Dynamic.word_tags_list)

    #     if not active_list:
    #         return Lng.no[JsonData.lng_index]
        
    #     return ', '.join(active_list)

    # def item_cmd(self, item: UListWidgetItem):
    #     if isinstance(item, UListSpacerItem):
    #         return
    #     if item.text() == Lng.favorites[JsonData.lng_index]:
    #         if Dynamic.favs_tag_enabled:
    #             Dynamic.favs_tag_enabled = False
    #             item.setCheckState(Qt.CheckState.Unchecked)
    #         else:
    #             Dynamic.favs_tag_enabled = True
    #             item.setCheckState(Qt.CheckState.Checked)
    #     elif item.text() == Lng.without_subfolders[JsonData.lng_index]:
    #         if Dynamic.no_subfolders_tag_enabled:
    #             Dynamic.no_subfolders_tag_enabled = False
    #             item.setCheckState(Qt.CheckState.Unchecked)
    #         else:
    #             Dynamic.no_subfolders_tag_enabled = True
    #             item.setCheckState(Qt.CheckState.Checked)
    #     elif item.text() in Dynamic.word_tags_list:
    #         Dynamic.word_tags_list.remove(item.text())
    #         item.setCheckState(Qt.CheckState.Unchecked)
    #     else:
    #         Dynamic.word_tags_list.append(item.text())
    #         item.setCheckState(Qt.CheckState.Checked)

    #     self.active_filters.setText(self.get_filters_text())
    #     self.reload_thumbnails.emit()

    # def reset_cmd(self):
    #     items = [
    #         self.list_widget.item(i)
    #         for i in range(self.list_widget.count())
    #     ]
    #     items.pop(2)  # удаляем спейсер из списка обработки
    #     for item in items:
    #         item.setCheckState(Qt.CheckState.Unchecked)
    #     Dynamic.favs_tag_enabled = False
    #     Dynamic.no_subfolders_tag_enabled = False
    #     Dynamic.word_tags_list.clear()
    #     self.reload_thumbnails.emit()
    #     self.active_filters.setText(self.get_filters_text())

        self.central_layout.addStretch(1)

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
