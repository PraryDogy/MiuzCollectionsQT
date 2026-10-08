import os

from PyQt6.QtCore import QDate, QLocale, QPoint, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QCursor, QIcon
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

    def __init__(self, text: str, svg_path: str, show_reset: bool = True):
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

        if show_reset:
            self.reset_button = UPushButton(Lng.reset[JsonData.lng_index])
            self.reset_button.setIcon(self.reset_icon)
            self.reset_button.clicked.connect(self.reset_clicked.emit)
            layout.addWidget(self.reset_button)


class CalendarTag(UTagWidget):
    def __init__(self):
        super().__init__(
            text=Lng.not_selected[JsonData.lng_index],
            qss_style=self.qss_gray,
        )
        self.adjustSize()
        self.setFixedWidth(self.width())


class DatesWidget(UGroupBox):
    load_st_grid = pyqtSignal()
    calendar_svg = Static.COMMON_ICONS / "calendar.svg"
    svg_calendar_size = (15, 15)
    readable_date = None

    def __init__(self, parent=None):
        super().__init__(parent)

        ind = JsonData.lng_index
        _today = QDate.currentDate()

        self.dates_dict = {
            (_today, _today): Lng.preset_today[ind],
            (_today.addDays(-1), _today.addDays(-1)): Lng.preset_yesterday[ind],
            (_today.addDays(-7), _today): Lng.preset_week[ind],
            (_today.addDays(-14), _today): Lng.preset_two_weeks[ind],
            (_today.addMonths(-1), _today): Lng.preset_month[ind],
            (_today.addYears(-1), _today): Lng.preset_year[ind],
        }

        # Загружаем даты независимо друг от друга
        if Dynamic.py_date_start:
            dt_s = Dynamic.py_date_start
            self.q_date_start = QDate(dt_s.year, dt_s.month, dt_s.day)
        else:
            self.q_date_start = None

        if Dynamic.py_date_end:
            dt_e = Dynamic.py_date_end
            self.q_date_end = QDate(dt_e.year, dt_e.month, dt_e.day)
        else:
            self.q_date_end = None

        self.py_date_start = Dynamic.py_date_start
        self.py_date_end = Dynamic.py_date_end

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(7)

        self.title_widget = WinFiltersTitleWidget(
            text=Lng.dates_management[ind],
            svg_path=str(self.calendar_svg)
        )
        self.title_widget.reset_clicked.connect(lambda: self.reset_all(True))
        self.main_layout.addWidget(self.title_widget)
        self.main_layout.addWidget(USep())

        dynamic_container = TransparentWidget()
        dynamic_container_lay = QHBoxLayout(dynamic_container)
        dynamic_container_lay.setContentsMargins(0, 0, 0, 0)
        dynamic_container_lay.setSpacing(5)

        self.dynamic_label = TransparentLabel(Lng.selected_dates[JsonData.lng_index])
        dynamic_container_lay.addWidget(self.dynamic_label)

        self.main_layout.addWidget(dynamic_container)
        self.main_layout.addSpacing(5)

        self.preset_menu = UMenu(parent=self)

        for qdates, text in self.dates_dict.items():
            action = QAction(text, self.preset_menu)
            action.triggered.connect(
                lambda _, d=qdates: self.action_cmd(d[0], d[1])
            )
            self.preset_menu.addAction(action)

        # КНОПКИ КАЛЕНДАРЕЙ

        self.date_btns_widget = TransparentWidget()
        self.date_btns_layout = QHBoxLayout(self.date_btns_widget)
        self.date_btns_layout.setContentsMargins(0, 0, 0, 0)
        self.date_btns_layout.setSpacing(5)

        dates_btn = UPushButton(Lng.period[JsonData.lng_index])
        dates_btn.setMenu(self.preset_menu)
        self.date_btns_layout.addWidget(dates_btn)

        self.date_btns_layout.addSpacing(10)

        from_label = GrayTextLabel(Lng.start_date[ind])
        self.date_btns_layout.addWidget(from_label)

        self.left_calendar_tag = CalendarTag()
        self.left_calendar_tag.text_clicked.connect(lambda: self.show_calendar_win("start"))
        self.date_btns_layout.addWidget(self.left_calendar_tag)

        self.date_btns_layout.addSpacing(10)

        to_label = GrayTextLabel(Lng.end_date[ind])
        self.date_btns_layout.addWidget(to_label)

        self.right_calendar_tag = CalendarTag()
        self.right_calendar_tag.text_clicked.connect(lambda: self.show_calendar_win("end"))
        self.date_btns_layout.addWidget(self.right_calendar_tag)

        self.date_btns_layout.addStretch(1)
        self.main_layout.addWidget(self.date_btns_widget)

        self.update_readable_date_label()
        self.set_date_buttons_text()

    def is_all_time(self) -> bool:
        # Фильтр считается отключенным, ТОЛЬКО если обе даты None
        return self.q_date_start is None and self.q_date_end is None

    def date_digits(self, q_date: QDate) -> str:
        return q_date.toString("dd.MM.yyyy")

    def show_calendar_win(self, flag: str):
        if flag == "start":
            qdate = self.q_date_start if self.q_date_start is not None else QDate.currentDate()
        else:
            qdate = self.q_date_end if self.q_date_end is not None else QDate.currentDate()

        self.calendar_win = WinCalendar(qdate)
        self.calendar_win.center_to_parent(self.window())

        def on_date_selected(date: QDate):
            if flag == "start":
                self.q_date_start = date
                # Защита от конфликта: если конец ЕСТЬ, и он меньше старта -> сдвигаем конец
                if self.q_date_end is not None and self.q_date_start > self.q_date_end:
                    self.q_date_end = self.q_date_start

            elif flag == "end":
                self.q_date_end = date
                # Защита от конфликта: если старт ЕСТЬ, и он больше конца -> сдвигаем старт
                if self.q_date_start is not None and self.q_date_start > self.q_date_end:
                    self.q_date_start = self.q_date_end

            self.handle_preset_change()
            self.apply_filter(True)

        self.calendar_win.date_selected.connect(on_date_selected)
        self.calendar_win.show()

    def action_cmd(self, q_date_start: QDate, q_date_end: QDate):
        self.q_date_start = q_date_start
        self.q_date_end = q_date_end
        self.handle_preset_change()
        self.apply_filter(True)

    def handle_preset_change(self):
        self.set_date_buttons_text()
        self.update_readable_date_label()

    def set_date_buttons_text(self):
        ind = JsonData.lng_index
        empty_text = Lng.not_selected[ind]

        # Обрабатываем кнопку "Старт" независимо
        if self.q_date_start is None:
            self.left_calendar_tag.text_widget.setText(empty_text)
            self.left_calendar_tag.set_qss_style(self.left_calendar_tag.qss_gray)
        else:
            self.left_calendar_tag.text_widget.setText(self.date_digits(self.q_date_start))
            self.left_calendar_tag.set_qss_style(self.left_calendar_tag.qss_green)

        # Обрабатываем кнопку "Конец" независимо
        if self.q_date_end is None:
            self.right_calendar_tag.text_widget.setText(empty_text)
            self.right_calendar_tag.set_qss_style(self.right_calendar_tag.qss_gray)
        else:
            self.right_calendar_tag.text_widget.setText(self.date_digits(self.q_date_end))
            self.right_calendar_tag.set_qss_style(self.right_calendar_tag.qss_green)

    def update_readable_date_label(self):
        ind = JsonData.lng_index
        locale = QLocale(
            QLocale.Language.Russian if ind == 0 else QLocale.Language.English
        )

        if self.is_all_time():
            text = Lng.all_time[ind]
            
        elif self.q_date_start is not None and self.q_date_end is not None and (self.q_date_start, self.q_date_end) in self.dates_dict:
            text = self.dates_dict[self.q_date_start, self.q_date_end]
            
        elif self.q_date_start is not None and self.q_date_end is None:
            str_from = locale.toString(self.q_date_start, "d MMMM yyyy")
            text = f"{Lng.from_text[ind]} {str_from}"
            
        elif self.q_date_start is None and self.q_date_end is not None:
            str_to = locale.toString(self.q_date_end, "d MMMM yyyy")
            text = f"{Lng.to_text[ind]} {str_to}"
            
        else:
            str_from = locale.toString(self.q_date_start, "d MMMM yyyy")
            str_to = locale.toString(self.q_date_end, "d MMMM yyyy")
            text = f"{Lng.from_text[ind]} {str_from} {Lng.to_text[ind].lower()} {str_to}"

        text = f"{Lng.selected_dates[ind]}: {text.lower()}"
        self.dynamic_label.setText(text)
        DatesWidget.readable_date = text

    def apply_filter(self, load_st_grid: bool):
        # Конвертируем по отдельности (каждый может быть None)
        self.py_date_start = self.q_date_start.toPyDate() if self.q_date_start else None
        self.py_date_end = self.q_date_end.toPyDate() if self.q_date_end else None

        Dynamic.py_date_start = self.py_date_start
        Dynamic.py_date_end = self.py_date_end

        if load_st_grid:
            self.load_st_grid.emit()

    def reset_all(self, load_st_grid: bool):
        self.q_date_start = None
        self.q_date_end = None

        self.apply_filter(load_st_grid)
        self.handle_preset_change()


class WinFiltersUserTag(UTagWidget):
    right_svg_path = Static.COMMON_ICONS / "trash.svg"

    def __init__(self, text: str, left_svg_path: str):
        super().__init__(
            text=text,
            qss_style=UTagWidget.qss_gray,
            left_svg_path=left_svg_path,
            right_svg_path=str(self.right_svg_path)
        )


class WinFiltersStantartTag(UTagWidget):
    def __init__(self, text: str, left_svg_path: str):
        super().__init__(
            text=text,
            qss_style=self.qss_gray,
            left_svg_path=left_svg_path
        )


class WinFiltersFavTag(WinFiltersStantartTag):
    left_svg_path =  Static.COMMON_ICONS / "fav.svg"

    def __init__(self):
        super().__init__(
            text=Lng.favorites[JsonData.lng_index],
            left_svg_path=str(self.left_svg_path),
        )
        if Dynamic.favs_tag_enabled:
            self.set_qss_style(self.qss_green)

    def text_widget_cmd(self, *args):
        if Dynamic.favs_tag_enabled:
            self.set_qss_style(self.qss_gray)
            Dynamic.favs_tag_enabled = False
        else:
            self.set_qss_style(self.qss_green)
            Dynamic.favs_tag_enabled = True
        return super().text_widget_cmd(*args)


class SubfoldersTagWidget(WinFiltersStantartTag):
    left_svg_path =  Static.COMMON_ICONS / "folder_gray.svg"

    def __init__(self):
        super().__init__(
            text=Lng.without_subfolders[JsonData.lng_index], 
            left_svg_path=str(self.left_svg_path)
        )
        if Dynamic.no_subfolders_tag_enabled:
            self.set_qss_style(self.qss_green)

    def text_widget_cmd(self, *args):
        if Dynamic.no_subfolders_tag_enabled:
            self.set_qss_style(self.qss_gray)
            Dynamic.no_subfolders_tag_enabled = False
        else:
            self.set_qss_style(self.qss_green)
            Dynamic.no_subfolders_tag_enabled = True
        return super().text_widget_cmd(*args)


class WordFiltersTagWidget(WinFiltersUserTag):
    left_svg_path = Static.COMMON_ICONS / "tags.svg"

    def __init__(self, text):
        super().__init__(
            text=text,
            left_svg_path=str(self.left_svg_path)
        )
        if text in Dynamic.word_tags_list:
            self.set_qss_style(self.qss_green)

    def text_widget_cmd(self, *args):
        if self.text_widget.text() in Dynamic.word_tags_list:
            self.set_qss_style(self.qss_gray)
            Dynamic.word_tags_list.remove(self.text_widget.text())
        else:
            self.set_qss_style(self.qss_green)
            Dynamic.word_tags_list.append(self.text_widget.text())
        return super().text_widget_cmd(*args)


class AddTagWidget(UTagWidget):
    left_svg_path =  Static.COMMON_ICONS / "plus_simple.svg"
    left_svg_size = (12, 12)

    def __init__(self):
        super().__init__(
            text=Lng.new_tag[JsonData.lng_index],
            qss_style=self.qss_transparent,
            left_svg_path=str(self.left_svg_path)
        )


class StandartTags(TransparentWidget):
    load_st_grid = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.flow_layout = FlowLayout(self, spacing=7)
        self.flow_layout.setContentsMargins(0, 0, 0, 0)
        self._create_tags()

    def _create_tags(self):
        tag = WinFiltersFavTag()
        tag.text_clicked.connect(self.load_st_grid.emit)
        self.flow_layout.addWidget(tag)

        tag = SubfoldersTagWidget()
        tag.text_clicked.connect(self.load_st_grid.emit)
        self.flow_layout.addWidget(tag)


class UserTags(TransparentWidget):
    load_st_grid = pyqtSignal()
    svg_path = Static.COMMON_ICONS / "tags.svg"

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
            tag = WordFiltersTagWidget(word)
            tag.text_clicked.connect(self.load_st_grid.emit)
            tag.right_svg_clicked.connect(
                lambda w=tag: self.show_remove_tag_win(w)
            )
            self.flow_layout.addWidget(tag)

        self.add_tag = AddTagWidget()
        self.add_tag.text_clicked.connect(self.show_text_win)
        self.flow_layout.addWidget(self.add_tag)

    def show_text_win(self):

        def ok_clicked(text: str):
            if text:
                Filters.items.append(text)
                Filters.write_json_data()
                self.flow_layout.clear()
                self._create_tags()

        self.text_win = InputTextWin(
            description=Lng.new_tag_desc[JsonData.lng_index],
            svg_path=str(self.svg_path)
        )
        self.text_win.center_to_parent(self.window())
        self.text_win.ok_clicked.connect(ok_clicked)
        self.text_win.show()

    def show_remove_tag_win(self, widget: WordFiltersTagWidget):

        def ok_clicked():
            text = widget.text_widget.text() 
            Filters.items.remove(text)
            Filters.write_json_data()
            if text in Dynamic.word_tags_list:
                Dynamic.word_tags_list.remove(text)
                self.load_st_grid.emit()
            widget.deleteLater()

        self.remove_tag_win = ConfirmWindow(Lng.remove_tag_question[JsonData.lng_index])
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
        self.v_lay.setContentsMargins(5, 5, 5, 5)
        self.v_lay.setSpacing(7)

        self.title_widget = WinFiltersTitleWidget(
            text=Lng.tag_management[JsonData.lng_index],
            svg_path=str(self.svg_path)
        )
        self.title_widget.reset_clicked.connect(lambda: self.reset_tags(True))
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

    def reset_tags(self, with_sig: bool):
        Dynamic.favs_tag_enabled = False
        Dynamic.no_subfolders_tag_enabled = False
        Dynamic.word_tags_list.clear()
        for i in self.findChildren(UTagWidget)[:-1]:
            i.set_qss_style(UTagWidget.qss_gray)
        if with_sig:
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
        self.central_layout.setContentsMargins(10, 5, 10, 10)

        self.dates_widget = DatesWidget()
        self.dates_widget.load_st_grid.connect(self.load_st_grid.emit)
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

        self.reset_all_button = UPushButton(Lng.reset_all[JsonData.lng_index])
        self.reset_all_button.clicked.connect(self.reset_all_cmd)
        self.buttons_layout.addWidget(self.reset_all_button)

        self.close_button = ActiveButton(Lng.done[JsonData.lng_index])
        self.close_button.clicked.connect(self.deleteLater)
        self.buttons_layout.addWidget(self.close_button)

        self.tags_widget.user_tags.adjustSize()
        self.tags_widget.adjustSize()
        self.adjustSize()

    def reset_all_cmd(self):
        self.dates_widget.reset_all(False)
        self.tags_widget.reset_tags(False)
        self.load_st_grid.emit()

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
