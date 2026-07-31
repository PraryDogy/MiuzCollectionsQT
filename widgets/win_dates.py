import os

from PyQt6.QtCore import QDate, QLocale, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (QDateEdit, QGroupBox, QHBoxLayout, QLabel,
                             QSpacerItem, QSpinBox, QToolButton, QVBoxLayout,
                             QWidget)

from cfg import Dynamic, JsonData, Static
from system.lang import Lng

from ._base_widgets import HSep, UMainWidget, UMenu, UPushButton


def style_date_edit_calendar(date_edit: QDateEdit):
    date_edit.setCalendarPopup(True)
    calendar = date_edit.calendarWidget()
    if JsonData.lng_index == 0:
        calendar.setLocale(QLocale(QLocale.Language.Russian))
    else:
        calendar.setLocale(QLocale(QLocale.Language.English))

    calendar.setFixedSize(300, 300)
    calendar.setMaximumDate(QDate.currentDate())
    calendar.setMinimumDate(QDate(2018, 1, 1))
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


from PyQt6.QtCore import QLocale # Добавьте импорт QLocale в начало файла

from PyQt6.QtCore import QLocale 

class WinDates(UMainWidget):
    dates_btn_solid = pyqtSignal()
    dates_btn_normal = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    reset_svg = os.path.join(Static.common_icons, "reset.svg")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.search_dates[JsonData.lng_index])
        self.central_layout.setSpacing(10)

        group_box = QGroupBox()
        self.central_layout.addWidget(group_box)
        group_layout = QVBoxLayout(group_box)
        group_layout.setContentsMargins(5, 0, 5, 0)
        group_layout.setSpacing(5)

        # --- Блок пресетов ---
        preset_widget = QWidget()
        group_layout.addWidget(preset_widget)
        preset_layout = QHBoxLayout(preset_widget)
        preset_layout.setContentsMargins(0, 0, 0, 0)
        preset_layout.setSpacing(10)

        period_label = QLabel(Lng.period[JsonData.lng_index])
        preset_layout.addWidget(period_label)

        self.preset_button = UPushButton("")
        self.preset_button.setFixedWidth(120)
        preset_layout.addWidget(self.preset_button)

        preset_layout.addStretch(1)

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

        self.preset_button.setText(
            self.preset_actions[Dynamic.date_index].text()
        )

        for x, act in enumerate(self.preset_actions, start=0):
            act.triggered.connect(
                lambda e, ind=x, act=act: self.action_cmd(e, ind, act)
            )
            preset_menu.addAction(act)

        self.apply_btn = UPushButton(Lng.reset[JsonData.lng_index])
        self.apply_btn.clicked.connect(self.clear_btn_cmd) 
        preset_layout.addWidget(self.apply_btn)

        group_layout.addWidget(HSep())

        # --- Блок ручного выбора дат ---
        date_widget = QWidget()
        group_layout.addWidget(date_widget)
        date_layout = QHBoxLayout(date_widget)
        date_layout.setContentsMargins(0, 5, 0, 5)
        date_layout.setSpacing(2)

        from_label = QLabel(Lng.from_text[JsonData.lng_index])
        date_layout.addWidget(from_label)
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_from.setFixedWidth(110)
        date_layout.addWidget(self.date_from)

        date_layout.addSpacerItem(QSpacerItem(10, 0))

        to_label = QLabel(Lng.to_text[JsonData.lng_index])
        date_layout.addWidget(to_label)
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setFixedWidth(110)
        date_layout.addWidget(self.date_to)

        if Dynamic.date_start and Dynamic.date_end:
            dt = Dynamic.date_start
            dt = QDate(dt.year, dt.month, dt.day)
            self.date_from.setDate(dt)

            dt_end = Dynamic.date_end
            self.date_to.setDate(QDate(dt_end.year, dt_end.month, dt_end.day))

        for widget in [self.date_from, self.date_to]:
            widget.setEnabled(True)  
            style_date_edit_calendar(widget)
            widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            widget.dateChanged.connect(self.on_custom_date_changed)

        date_layout.addStretch(1)

        # --- Читаемый лейбл состояния (ИСПРАВЛЕНО: жесткая фиксация высоты) ---
        self.readable_date_label = QLabel()
        self.readable_date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.readable_date_label.setWordWrap(True)
        self.readable_date_label.setStyleSheet("color: #555555; font-weight: 500;")
        # Фиксируем высоту на 32 пикселя, чтобы вместить 1 или 2 строки без деформации окна
        self.readable_date_label.setFixedHeight(32) 
        self.central_layout.addWidget(self.readable_date_label)

        self.handle_preset_change(Dynamic.date_index)
        self.update_readable_date_label()
        
        # Вызываем один раз для стартового расчета геометрии
        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

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
                self.date_from.setDate(today)
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
        """Форматирует выбранный период в красивую читаемую строку с названиями месяцев"""
        if Dynamic.date_index == 0:
            text = "Выбранный период: все время" if JsonData.lng_index == 0 else "Selected period: all time"
        else:
            if JsonData.lng_index == 0:
                locale = QLocale(QLocale.Language.Russian)
                str_from = locale.toString(self.date_from.date(), "d MMMM yyyy")
                str_to = locale.toString(self.date_to.date(), "d MMMM yyyy")
                text = f"Выбранный период: с {str_from} по {str_to}"
            else:
                locale = QLocale(QLocale.Language.English)
                str_from = locale.toString(self.date_from.date(), "d MMMM yyyy")
                str_to = locale.toString(self.date_to.date(), "d MMMM yyyy")
                text = f"Selected period: from {str_from} to {str_to}"
                
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
        self.dates_btn_normal.emit()

    def set_button_style(self):
        if Dynamic.date_start and Dynamic.date_end:
            self.dates_btn_solid.emit()
        else:
            self.dates_btn_normal.emit()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)

    def deleteLater(self):
        self.set_button_style()
        return super().deleteLater()

    def closeEvent(self, a0):
        self.set_button_style()
        return super().closeEvent(a0)
