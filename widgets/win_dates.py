import os
import sys
from datetime import datetime, timedelta
from typing import Literal

from PyQt6.QtCore import QDate, QLocale, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (QAction, QBrush, QColor, QIcon, QKeyEvent,
                         QTextCharFormat)
from PyQt6.QtWidgets import (QApplication, QCalendarWidget, QComboBox,
                             QDateEdit, QDialog, QGroupBox, QHBoxLayout,
                             QLabel, QMainWindow, QPushButton, QSpacerItem,
                             QSpinBox, QToolButton, QVBoxLayout, QWidget)

from cfg import Dynamic, JsonData, Static
from system.lang import Lng

from ._base_widgets import (HSep, RowArrowWidget, UMainWidget, UMenu,
                            UPushButton)


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

        period_label = QLabel("Период")
        preset_layout.addWidget(period_label)

        self.preset_button = UPushButton("")
        self.preset_button.setFixedWidth(120)
        preset_layout.addWidget(self.preset_button)

        preset_layout.addStretch(1)

        preset_menu = UMenu(None)
        self.preset_button.setMenu(preset_menu)

        self.preset_actions = [
            QAction("Все время", preset_menu),
            QAction("Сегодня", preset_menu),
            QAction("За неделю", preset_menu),
            QAction("За месяц", preset_menu),
            QAction("За год", preset_menu),
            QAction("Диапазон", preset_menu),
        ]

        self.preset_button.setText(
            self.preset_actions[Dynamic.date_index].text()
        )

        for x, act in enumerate(self.preset_actions, start=0):
            act.triggered.connect(
                lambda e, ind=x, act=act: self.action_cmd(e, ind, act)
            )
            preset_menu.addAction(act)

        # --- Блок ручного выбора дат ---
        date_widget = QWidget()
        group_layout.addWidget(date_widget)
        date_layout = QHBoxLayout(date_widget)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(5)

        from_label = QLabel("С:")
        date_layout.addWidget(from_label)
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        date_layout.addWidget(self.date_from)

        date_layout.addSpacerItem(QSpacerItem(15, 0))

        to_label = QLabel("По:")
        date_layout.addWidget(to_label)
        self.date_to = QDateEdit(QDate.currentDate())
        date_layout.addWidget(self.date_to)

        for widget in [self.date_from, self.date_to]:
            widget.setEnabled(False)
            style_date_edit_calendar(widget)

        self.adjustSize()


        self.apply_btn = UPushButton(Lng.reset[JsonData.lng_index])
        self.apply_btn.clicked.connect(self.clear_btn_cmd) 
        self.central_layout.addWidget(self.apply_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.handle_preset_change(Dynamic.date_index)
        self.adjustSize()


    def action_cmd(self, e, index: int, action: QAction):
        self.preset_button.setText(action.text())
        self.handle_preset_change(index)
        
        if index == 0:
            self.clear_btn_cmd()
        else:
            self.apply_filter(index)
        
    def handle_preset_change(self, index):
        is_custom = (index == len(self.preset_actions) - 1)
        self.date_from.setEnabled(is_custom)
        self.date_to.setEnabled(is_custom)
        
        today = QDate.currentDate()
        if not is_custom:
            self.date_to.setDate(today)
            if index == 0:
                self.date_from.setDate(today)
            elif index == 1: # Сегодня
                self.date_from.setDate(today)
            elif index == 2: # За неделю
                self.date_from.setDate(today.addDays(-7))
            elif index == 3: # За месяц
                self.date_from.setDate(today.addMonths(-1))
            elif index == 4: # За год
                self.date_from.setDate(today.addYears(-1))

    def apply_filter(self, index: int):
        Dynamic.date_start = self.date_from.date().toPyDate()
        Dynamic.date_end = self.date_to.date().toPyDate()
        Dynamic.date_index = index
        self.reload_thumbnails.emit()
        self.dates_btn_solid.emit()

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

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)
