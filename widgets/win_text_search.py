import re

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout

from cfg import JsonData, Static
from system.lang import Lng

from ._base_widgets import (TransparentLabel, TransparentWidget, UMainWidget,
                            UPushButton, UTextEditLight)


class WinTextSearchTitle(TransparentLabel):
    def __init__(self):
        super().__init__("Редактор текста")


class WinTextSearchTitleRow(TransparentWidget):
    svg_path = Static.COMMON_ICONS / "edit.svg"
    svg_size = (25, 25)

    def __init__(self):
        super().__init__()
        self.h_lay = QHBoxLayout(self)
        self.h_lay.setContentsMargins(0, 0, 0, 0)
        self.h_lay.setSpacing(10)

        self.svg_widget = QSvgWidget()
        self.svg_widget.load(str(self.svg_path))
        self.svg_widget.setFixedSize(*self.svg_size)
        self.h_lay.addWidget(self.svg_widget)

        self.title_label = WinTextSearchTitle()
        self.h_lay.addWidget(self.title_label)



class WinTextSearch(UMainWidget):
    ok_clicked = pyqtSignal(str)
    size_ = (430, 430)  # Немного увеличил высоту, чтобы поместилось описание

    def __init__(self, text: str):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setFixedSize(*self.size_)
        self.central_layout.setSpacing(5)

        self.title_row = WinTextSearchTitleRow()
        self.central_layout.addWidget(self.title_row)

        # 1. Текст описания форматов (RU / EN)
        if JsonData.lng_index == 0:
            description_text = (
                "Для поиска по нескольким словам введите их через запятую или каждое слово с новой строки. "
                "Нажмите \"Форматировать текст\", чтобы подготовить текст для поиска."
            )
        else:
            description_text = (
                "To search for multiple words, enter them separated by commas or each on a new line. "
                "Click \"Format Text\" to prepare the text for searching."
            )
        self.description_label = TransparentLabel(description_text)
        # Разрешаем перенос текста, чтобы описание красиво выглядело
        self.description_label.setWordWrap(True) 
        self.central_layout.addWidget(self.description_label)

        self.text_edit = UTextEditLight()
        self.central_layout.addWidget(self.text_edit)
        self.text_edit.setPlainText(text)

        # 2. Подключаем кнопку форматирования к методу
        self.format_button = UPushButton(
            "Форматировать текст" if JsonData.lng_index == 0 else "Format Text"
        )
        self.format_button.clicked.connect(self.format_input_text)
        self.central_layout.addWidget(self.format_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.btns_container = TransparentWidget()
        self.central_layout.addWidget(self.btns_container)

        btns_layout = QHBoxLayout(self.btns_container)
        btns_layout.setContentsMargins(0, 0, 0, 0)
        btns_layout.setSpacing(5)
        btns_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.ok_btn = UPushButton(Lng.ok[JsonData.lng_index])
        self.ok_btn.clicked.connect(
            lambda: self.ok_clicked.emit(self.text_edit.toPlainText())
        )
        btns_layout.addWidget(self.ok_btn)

        self.cancel_btn = UPushButton(Lng.close[JsonData.lng_index])
        self.cancel_btn.clicked.connect(self.deleteLater)
        btns_layout.addWidget(self.cancel_btn)

    def format_input_text(self):
        """Анализирует текст и приводит его к одной строке через запятую с пробелами."""
        raw_text = self.text_edit.toPlainText().strip()
        if not raw_text:
            return

        # Проверяем, содержит ли текст имена файлов через пробел (например: image.png photo.jpg file.txt)
        # Ищем наличие точек с расширениями (от 2 до 5 символов), после которых идет пробел или конец строки
        if re.search(r'\.\w{2,5}(?:\s|$)', raw_text) and ',' not in raw_text and '\n' not in raw_text:
            # Делим просто по пробелам
            words = [word.strip() for word in raw_text.split() if word.strip()]
        else:
            # Во всех остальных случаях (столбик, запятые, точки с запятой)
            # Регекс делит строку по любым комбинациям запятых, точек с запятой и переносов строк
            words = [word.strip() for word in re.split(r'[,\n;\r]+', raw_text) if word.strip()]

        # Объединяем в красивую строку через запятую с пробелом
        formatted_text = ", ".join(words)
        self.text_edit.setPlainText(formatted_text)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)
