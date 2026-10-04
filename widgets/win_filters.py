import os

from PyQt6.QtCore import QDate, QLocale, QPoint, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout,
                             QWidget)

from cfg import Dynamic, JsonData, Static
from system.filters import Filters
from system.lang import Lng

from ._base_widgets import (ActiveButton, ConfirmWindow, FlowLayout,
                            GrayTextLabel, InputTextWin, TitleTextLabel,
                            TransparentLabel, TransparentWidget, UGroupBox,
                            UMainWidget, UMenu, UPushButton, USep, UTagWidget)
from .win_calendar import WinCalendar

UGroupBox_margins = (5, 5, 5, 5)
UGroupBox_spacing = 10


class WinFiltersTitleWidget(QWidget):
    reset_clicked = pyqtSignal()
    reset_svg_path = Static.COMMON_ICONS / "reset.svg"

    def __init__(self, text: str, svg_path: str):
        super().__init__()

        self.reset_icon = QIcon(str(self.reset_svg_path))
        
        # 1. Создаем главное горизонтальное выравнивание
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Убираем внешние отступы
        layout.setSpacing(8)                  # Отступ между иконкой и текстом
        
        # 2. Создаем SVG-виджет для иконки
        self.icon_widget = QSvgWidget(svg_path)
        self.icon_widget.setFixedSize(QSize(24, 24))  # Задайте нужный размер иконки
        
        # 3. Создаем лейбл для текста
        self.label = TitleTextLabel(text)
        
        # 4. Добавляем виджеты в слой
        layout.addWidget(self.icon_widget)
        layout.addWidget(self.label)
        layout.addStretch(1)
        
        self.reset_button = UPushButton(Lng.reset[JsonData.lng_index])
        self.reset_button.setIcon(self.reset_icon)
        self.reset_button.clicked.connect(self.reset_clicked.emit)
        layout.addWidget(self.reset_button)



class DatesWidget(UGroupBox):
    calendar_svg = Static.COMMON_ICONS / "calendar.svg"
    svg_calendar_size = (15, 15)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.date_start = Dynamic.date_start
        self.date_end = Dynamic.date_end

        if Dynamic.date_start:
            dt = Dynamic.date_start
            self.q_date_start = QDate(dt.year, dt.month, dt.day)
        else:
            self.q_date_start = QDate(WinCalendar.min_year, 1, 1)

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

        self.title_widget = WinFiltersTitleWidget(
            text=Lng.dates_management[JsonData.lng_index],
            svg_path=str(self.calendar_svg)
        )
        self.title_widget.reset_clicked.connect(self.clear_btn_cmd) 
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
        # dynamic_container_lay.addWidget(calendar_icon)

        self.dynamic_label = GrayTextLabel("")
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

        self.calendar_win = WinCalendar(qdate)
        # global_pos = target_btn.mapToGlobal(QPoint(0, target_btn.height()))
        # offset = QPoint(0, 0)  # (по X, по Y)
        # self.calendar_win.move(global_pos + offset)
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
                self.q_date_start = QDate(WinCalendar.min_year, 1, 1)
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
        self.date_start = self.q_date_start.toPyDate()
        self.date_end = self.q_date_end.toPyDate()
        Dynamic.date_index = index

    def clear_btn_cmd(self, *args):
        Dynamic.loaded_thumbs = 0
        Dynamic.date_start = None
        Dynamic.date_end = None
        Dynamic.date_index = 0
        
        all_time_action = self.preset_actions[0]
        self.preset_button.setText(all_time_action.text())
        self.handle_preset_change(0)
        self.reload_thumbnails.emit()


class WinFiltersTagWidget(UTagWidget):
    icon_path = Static.COMMON_ICONS / "trash.svg"
    on_trash_clicked = pyqtSignal()
    load_st_grid = pyqtSignal() 

    def __init__(self, text: str, active: bool, show_trash: bool, left_icon_path: str = None):
        super().__init__()
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.h_lay = QHBoxLayout(self)
        self.h_lay.setContentsMargins(7, 2, 7, 2)
        self.h_lay.setSpacing(6)

        if left_icon_path:
            self.left_icon = QSvgWidget()
            self.left_icon.load(left_icon_path)
            self.left_icon.setFixedSize(*self.icon_size)
            self.h_lay.addWidget(self.left_icon)

        self.title = TransparentLabel(text)
        self.h_lay.addWidget(self.title)

        # Создаем контейнер и иконку только если передан флаг True
        if show_trash:
            self.close_btn_wrapper = TransparentWidget()
            close_lay = QVBoxLayout(self.close_btn_wrapper)
            close_lay.setContentsMargins(0, 1, 0, 0)
            close_lay.setSpacing(0)

            self.trash_btn = QSvgWidget()
            self.trash_btn.mouseReleaseEvent = self.on_trash_clicked_cmd
            self.trash_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.trash_btn.load(str(self.icon_path))
            self.trash_btn.setFixedSize(*self.icon_size)

            close_lay.addWidget(self.trash_btn)
            self.h_lay.addWidget(self.close_btn_wrapper)

    def on_trash_clicked_cmd(self, e):
        self.on_trash_clicked.emit()

    def mouseReleaseEvent(self, a0):
        self.load_st_grid.emit()
        super().mouseReleaseEvent(a0)


class WinFiltersFavTag(WinFiltersTagWidget):
    icon_path =  Static.COMMON_ICONS / "fav.svg"

    def __init__(self):
        if Dynamic.favs_tag_enabled:
            active = True
        else:
            active = False
        text = Lng.favorites[JsonData.lng_index]
        super().__init__(text, active, False, str(self.icon_path))

    def mouseReleaseEvent(self, a0):
        if Dynamic.favs_tag_enabled:
            self.set_active(False)
            Dynamic.favs_tag_enabled = False
        else:
            self.set_active(True)
            Dynamic.favs_tag_enabled = True
        return super().mouseReleaseEvent(a0)


class WinFiltersOnlyFolderTag(WinFiltersTagWidget):
    icon_path =  Static.COMMON_ICONS / "folder_gray.svg"

    def __init__(self):
        if Dynamic.no_subfolders_tag_enabled:
            active = True
        else:
            active = False
        text = Lng.without_subfolders[JsonData.lng_index]
        super().__init__(text, active, False, str(self.icon_path))

    def mouseReleaseEvent(self, a0):
        if Dynamic.no_subfolders_tag_enabled:
            self.set_active(False)
            Dynamic.no_subfolders_tag_enabled = False
        else:
            self.set_active(True)
            Dynamic.no_subfolders_tag_enabled = True
        return super().mouseReleaseEvent(a0)


class WinFiltersWordTag(WinFiltersTagWidget):
    def __init__(self, text):
        if text in Dynamic.word_tags_list:
            active = True
        else:
            active = False
        super().__init__(text, active, True)

    def mouseReleaseEvent(self, a0):
        if self.title.text() in Dynamic.word_tags_list:
            self.set_active(False)
            Dynamic.word_tags_list.remove(self.title.text())
        else:
            self.set_active(True)
            Dynamic.word_tags_list.append(self.title.text())
        return super().mouseReleaseEvent(a0)


class WinFiltersAddTag(WinFiltersTagWidget):
    icon_path =  Static.COMMON_ICONS / "plus_simple.svg"
    clicked_ = pyqtSignal()

    def __init__(self):
        if Dynamic.no_subfolders_tag_enabled:
            active = True
        else:
            active = False
        text = Lng.new_tag[JsonData.lng_index]
        super().__init__(text, active, False, str(self.icon_path))

    def mouseReleaseEvent(self, a0):
        self.clicked_.emit()
        return super().mouseReleaseEvent(a0)


class StandartTags(TransparentWidget):
    load_st_grid = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.flow_layout = FlowLayout(self, spacing=7)
        self.flow_layout.setContentsMargins(0, 0, 0, 0)
        self._create_tags()

    def _create_tags(self):
        tag = WinFiltersFavTag()
        tag.load_st_grid.connect(self.load_st_grid.emit)
        self.flow_layout.addWidget(tag)

        tag = WinFiltersOnlyFolderTag()
        tag.load_st_grid.connect(self.load_st_grid.emit)
        self.flow_layout.addWidget(tag)


class UserTags(TransparentWidget):
    load_st_grid = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        policy.setHeightForWidth(True) # Включаем зависимость высоты от ширины!
        self.setSizePolicy(policy)

        self.flow_layout = FlowLayout(self, spacing=7)
        self.flow_layout.setContentsMargins(0, 0, 0, 0)
        self._create_tags()

    def _create_tags(self):
        for word in Filters.items:
            tag = WinFiltersWordTag(word)
            tag.load_st_grid.connect(self.load_st_grid.emit)
            tag.on_trash_clicked.connect(
                lambda w=tag: self.show_remove_tag_win(w)
            )
            self.flow_layout.addWidget(tag)

        self.add_tag = WinFiltersAddTag()
        self.add_tag.clicked_.connect(self.show_text_win)
        self.flow_layout.addWidget(self.add_tag)

    def show_text_win(self):

        def ok_clicked(text: str):
            if text:
                Filters.items.append(text)
                Filters.write_json_data()
                tag = WinFiltersWordTag(text)
                tag.load_st_grid.connect(self.load_st_grid.emit)
                tag.on_trash_clicked.connect(
                    lambda w=tag: self.show_remove_tag_win(w)
                )

                self.flow_layout.clear()
                self._create_tags()

        self.text_win = InputTextWin(
            title=Lng.new_tag[JsonData.lng_index],
            description=Lng.new_tag_desc[JsonData.lng_index],
            size=(300, 100)
        )
        self.text_win.center_to_parent(self.window())
        self.text_win.ok_clicked.connect(ok_clicked)
        self.text_win.show()

    def show_remove_tag_win(self, widget: WinFiltersWordTag):

        def ok_clicked():
            text = widget.title.text() 
            Filters.items.remove(text)
            Filters.write_json_data()
            if text in Dynamic.word_tags_list:
                Dynamic.word_tags_list.remove(text)
                self.load_st_grid.emit()
            widget.deleteLater()
            self.remove_tag_win.deleteLater()

        self.remove_tag_win = ConfirmWindow(
            text=Lng.remove_tag_question[JsonData.lng_index],
            w=320, h=90
        )
        self.remove_tag_win.ok_clicked.connect(ok_clicked)
        self.remove_tag_win.center_to_parent(self.window())
        self.remove_tag_win.show()

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.flow_layout.heightForWidth(width)

    def sizeHint(self):
        width = self.parentWidget().width() if self.parentWidget() else 500
        return QSize(width, self.heightForWidth(width))


class TagsWidget(UGroupBox):
    load_st_grid = pyqtSignal()
    svg_path = Static.COMMON_ICONS / "tags.svg"

    def __init__(self):
        super().__init__()
        self.v_lay = QVBoxLayout(self)
        self.v_lay.setContentsMargins(*UGroupBox_margins)
        self.v_lay.setSpacing(UGroupBox_spacing)

        self.title_widget = WinFiltersTitleWidget(
            text=Lng.tag_management[JsonData.lng_index],
            svg_path=str(self.svg_path)
        )
        self.title_widget.reset_clicked.connect(self.reset_tags)
        self.v_lay.addWidget(self.title_widget)

        self.v_lay.addWidget(USep())

        st_tags_title = GrayTextLabel(Lng.standart_tags[JsonData.lng_index])
        self.v_lay.addWidget(st_tags_title)

        self.standart_tags = StandartTags()
        self.standart_tags.load_st_grid.connect(self.load_st_grid.emit)
        self.v_lay.addWidget(self.standart_tags)

        user_tags_title = GrayTextLabel(Lng.user_tags[JsonData.lng_index])
        self.v_lay.addWidget(user_tags_title)

        self.user_tags = UserTags()
        self.user_tags.load_st_grid.connect(self.load_st_grid.emit)
        self.v_lay.addWidget(self.user_tags)

    def reset_tags(self):
        Dynamic.favs_tag_enabled = False
        Dynamic.no_subfolders_tag_enabled = False
        Dynamic.word_tags_list.clear()
        tags = self.findChildren(WinFiltersTagWidget)
        for i in tags:
            i.set_active(False)
        self.load_st_grid.emit()


class WinFilters(UMainWidget):
    reset_svg = Static.COMMON_ICONS / "reset.svg"
    edit_svg = Static.COMMON_ICONS / "edit.svg"
    closed_ = pyqtSignal()
    load_st_grid = pyqtSignal()
    edit_filters = pyqtSignal()
    ww = 590

    def __init__(self):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.filters[JsonData.lng_index])
        self.setFixedWidth(self.ww)
        self.central_layout.setSpacing(10)
        self.central_layout.setContentsMargins(10, 10, 10, 10)

        self.dates_widget = DatesWidget()
        self.central_layout.addWidget(self.dates_widget)

        self.tags_widget = TagsWidget()
        self.tags_widget.load_st_grid.connect(self.load_st_grid.emit)
        self.central_layout.addWidget(self.tags_widget)

        buttons_widget = TransparentWidget()
        self.central_layout.addWidget(buttons_widget)
        self.buttons_layout = QHBoxLayout(buttons_widget)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(10)

        self.buttons_layout.addStretch(1)
        self.apply_button = ActiveButton(Lng.apply[JsonData.lng_index])
        self.apply_button.clicked.connect(self.apply_filters)
        self.buttons_layout.addWidget(self.apply_button)

        self.close_button = UPushButton(Lng.close[JsonData.lng_index])
        self.close_button.clicked.connect(self.deleteLater)
        self.buttons_layout.addWidget(self.close_button)

        self.tags_widget.user_tags.adjustSize()
        self.tags_widget.adjustSize()
        self.adjustSize()

    def apply_filters(self):
        date_start = self.dates_widget.date_start
        date_end = self.dates_widget.date_end
        Dynamic.date_start = date_start
        Dynamic.date_end = date_end
        self.load_st_grid.emit()
        self.deleteLater()

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
