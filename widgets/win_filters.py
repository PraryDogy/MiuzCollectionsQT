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


class DatesButton(UPushButton):
    def __init__(self, text=""):
        super().__init__(text)
        
        # Правильный способ задать фиксированную ширину под дату
        fm = self.fontMetrics()
        # Берем строку с запасом (с пробелами), чтобы текст не прилипал к краям
        max_width = fm.horizontalAdvance(Lng.not_selected[JsonData.lng_index])
        
        # Добавляем 20px на внутренние отступы (padding/borders) кнопки
        self.setFixedWidth(max_width + 20)


class PeriodLabel(GrayTextLabel):
    def __init__(self, text):
        super().__init__(text)


class DatesWidget(UGroupBox):
    load_st_grid = pyqtSignal()
    calendar_svg = Static.COMMON_ICONS / "calendar.svg"
    svg_calendar_size = (15, 15)

    def __init__(self, parent=None):
        super().__init__(parent)

        ind = JsonData.lng_index
        _today = QDate.currentDate()
        self.q_date_min = QDate(WinCalendar.min_year, 1, 1)
        self.all_time = (self.q_date_min, _today)

        self.dates_dict = {
            (_today, _today): Lng.preset_today[ind],
            (_today.addDays(-1), _today.addDays(-1)): Lng.preset_yesterday[ind],
            (_today.addDays(-7), _today): Lng.preset_week[ind],
            (_today.addDays(-14), _today): Lng.preset_two_weeks[ind],
            (_today.addMonths(-1), _today): Lng.preset_month[ind],
            (_today.addYears(-1), _today): Lng.preset_year[ind]
        }

        # Инициализация дат с проверкой Dynamic
        if Dynamic.py_date_start:
            dt = Dynamic.py_date_start
            self.q_date_start = QDate(dt.year, dt.month, dt.day)
        else:
            self.q_date_start = self.q_date_min

        if Dynamic.py_date_end:
            dt = Dynamic.py_date_end
            self.q_date_end = QDate(dt.year, dt.month, dt.day)
        else:
            self.q_date_end = _today

        self.py_date_start = Dynamic.py_date_start
        self.py_date_end = Dynamic.py_date_end
        
        # Главный вертикальный layout для UGroupBox
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(*UGroupBox_margins)
        self.main_layout.setSpacing(UGroupBox_spacing)

        self.title_widget = WinFiltersTitleWidget(
            text=Lng.dates_management[ind],
            svg_path=str(self.calendar_svg)
        )
        self.title_widget.reset_clicked.connect(self.clear_btn_cmd) 
        self.main_layout.addWidget(self.title_widget)

        self.main_layout.addWidget(USep())

        # --- 1. Блок большой даты ---
        dynamic_container = TransparentWidget()
        dynamic_container_lay = QHBoxLayout(dynamic_container)
        dynamic_container_lay.setContentsMargins(0, 0, 0, 0)
        dynamic_container_lay.setSpacing(3)

        choosed_label = TransparentLabel(Lng.period[JsonData.lng_index] + ":")
        dynamic_container_lay.addWidget(choosed_label)

        self.dynamic_label = PeriodLabel("")
        # ИСПРАВЛЕНО: Убрано self.dynamic_label.setFixedWidth(self.width()), 
        # так как в __init__ ширина виджета еще не рассчитана (обычно равна 100 или 0)
        
        dynamic_container_lay.addWidget(self.dynamic_label)
        dynamic_container_lay.addStretch()
        
        self.main_layout.addWidget(dynamic_container)
        self.main_layout.addWidget(USep())
        
        # --- СТРОКА 1: Виджет панели управления ---
        self.top_row_widget = TransparentWidget()
        self.top_row_layout = QHBoxLayout(self.top_row_widget)
        self.top_row_layout.setContentsMargins(0, 0, 0, 0)
        self.top_row_layout.setSpacing(0)

        # Кнопка пресетов
        self.preset_button = UPushButton(Lng.choose_period[ind] + " ")
        self.top_row_layout.addWidget(self.preset_button)

        preset_menu = UMenu(parent=self)
        self.preset_button.setMenu(preset_menu)

        for qdates, text in self.dates_dict.items():
            action = QAction(text, preset_menu)
            # ИСПРАВЛЕНО: Игнорируем boolean параметр от clicked/triggered через _
            action.triggered.connect(
                lambda _, d=qdates: self.action_cmd(d[0], d[1])
            )
            preset_menu.addAction(action)

        self.top_row_layout.addSpacing(15)

        # Выбор дат "От" и "До"
        from_label = TransparentLabel(Lng.from_text[ind] + ":")
        self.top_row_layout.addWidget(from_label)
        self.top_row_layout.addSpacing(5)
        
        self.date_start_btn = DatesButton("")
        self.date_start_btn.clicked.connect(lambda: self.show_calendar_win("start"))
        self.top_row_layout.addWidget(self.date_start_btn)

        self.top_row_layout.addSpacing(10) 

        to_label = TransparentLabel(Lng.to_text[ind] + ":")
        self.top_row_layout.addWidget(to_label)
        self.top_row_layout.addSpacing(5)
        
        self.date_end_btn = DatesButton("")
        self.date_end_btn.clicked.connect(lambda: self.show_calendar_win("end"))
        self.top_row_layout.addWidget(self.date_end_btn)

        self.top_row_layout.addStretch(1)
        self.main_layout.addWidget(self.top_row_widget)

        self.update_readable_date_label()
        self.set_date_buttons_text()

    def date_digits(self, q_date: QDate) -> str:
        return q_date.toString("dd.MM.yyyy")

    def show_calendar_win(self, flag: str):
        # Проверяем, находится ли весь виджет в состоянии "За всё время" (когда на кнопках "Не выбрано")
        is_not_selected = (self.all_time == (self.q_date_start, self.q_date_end))
        
        # Если даты не выбраны, всегда открываем "сегодня" для обеих кнопок
        if is_not_selected:
            qdate = QDate.currentDate()
        else:
            # Иначе открываем ту дату, которая реально выбрана (даже если это q_date_min)
            qdate = self.q_date_start if flag == "start" else self.q_date_end
        
        self.calendar_win = WinCalendar(qdate)
        self.calendar_win.center_to_parent(self.window())

        def on_date_selected(date: QDate):
            if flag == "start":
                self.q_date_start = date
            else:
                self.q_date_end = date
            self.handle_preset_change()
            self.apply_filter()

        self.calendar_win.date_selected.connect(on_date_selected)
        self.calendar_win.show()

    def action_cmd(self, q_date_start: QDate, q_date_end: QDate):
        self.q_date_start = q_date_start
        self.q_date_end = q_date_end
        self.handle_preset_change()
        self.apply_filter() # ИСПРАВЛЕНО: Раскомментировано, иначе фильтр не применялся

    def handle_preset_change(self):
        self.set_date_buttons_text()
        self.update_readable_date_label()

    def set_date_buttons_text(self):
        ind = JsonData.lng_index
        
        if self.all_time == (self.q_date_start, self.q_date_end):
            # Вместо "-" ставим осмысленный текст
            # В Lng добавьте: not_selected = ["Любая", "Any"] или ["Не выбрано", "None"]
            empty_text = Lng.not_selected[ind] 
            
            self.date_start_btn.setText(empty_text)
            self.date_end_btn.setText(empty_text)
        else:
            self.date_start_btn.setText(self.date_digits(self.q_date_start))
            self.date_end_btn.setText(self.date_digits(self.q_date_end))

    def update_readable_date_label(self):
        ind = JsonData.lng_index
        locale = QLocale(QLocale.Language.Russian if ind == 0 else QLocale.Language.English)

        if self.all_time == (self.q_date_start, self.q_date_end):
            text = Lng.all_time[ind]
        elif (self.q_date_start, self.q_date_end) in self.dates_dict:
            text = self.dates_dict[self.q_date_start, self.q_date_end]
        else:
            str_from = locale.toString(self.q_date_start, "d MMMM yyyy")
            str_to = locale.toString(self.q_date_end, "d MMMM yyyy")
            text = f"{Lng.from_text[ind]} {str_from} {Lng.to_text[ind].lower()} {str_to}"

        self.dynamic_label.setText(text.lower())

    def apply_filter(self):
        # ИСПРАВЛЕНО: Корректно передаем None, если выбрано "Все время"
        if self.all_time == (self.q_date_start, self.q_date_end):
            self.py_date_start = None
            self.py_date_end = None
        else:
            self.py_date_start = self.q_date_start.toPyDate()
            self.py_date_end = self.q_date_end.toPyDate()

        Dynamic.py_date_start = self.py_date_start
        Dynamic.py_date_end = self.py_date_end
        self.load_st_grid.emit()

    def clear_btn_cmd(self, *args):
        self.q_date_start = self.q_date_min
        self.q_date_end = QDate.currentDate()
        self.apply_filter()
        self.handle_preset_change() 


class WinFiltersTagWidget(UTagWidget):
    icon_path = Static.COMMON_ICONS / "trash.svg"
    on_trash_clicked = pyqtSignal()
    load_st_grid = pyqtSignal() 

    def __init__(self, text: str, active: bool, show_trash: bool, left_icon_path: str = None):
        super().__init__(active)
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

        self.close_button = UPushButton(Lng.close[JsonData.lng_index])
        self.close_button.clicked.connect(self.deleteLater)
        self.buttons_layout.addWidget(self.close_button)

        self.tags_widget.user_tags.adjustSize()
        self.tags_widget.adjustSize()
        self.adjustSize()

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
