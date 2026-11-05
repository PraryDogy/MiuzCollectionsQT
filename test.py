import re


import re

import re

qss = """
UPushButton:hover,
ULineEdit:hover,
UTextEdit:hover,
USpinBox:hover,
_SvgWithThemeBg:hover[style="base"],
UListWidget::indicator,
UListWidget::indicator:disabled,
UListWidget::item:selected,
UListWidget::item:selected:!active,
UMenu::item:selected {
    background: #1d2833;
}
"""

pattern = r"UListWidget::item:selected\b[^{}]*\{\s*background:\s*(#[0-9a-fA-F]{3,8})\s*;\s*\}"

m = re.search(pattern, qss)
if m:
    print(m.group(1))  # #1d2833