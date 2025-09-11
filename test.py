class WinSettings(QMainWindow):
    left_side_width = 210
    closed = pyqtSignal()
    reset_data = pyqtSignal(MainFolder)

    def __init__(self, settings_item: SettingsItem):
        super().__init__()
        self.filters_copy: list[str] = copy.deepcopy(Filters.filters)
        

class FiltersWid(QWidget):

    def __init__(self, filters_copy: list[str]):
        super().__init__()
        self.filters_copy = filters_copy

        self.v_lay = UVBoxLayout()
        self.v_lay.setSpacing(15)
        self.setLayout(self.v_lay)

        group = QGroupBox()
        g_lay = UVBoxLayout(group)
        g_lay.setContentsMargins(0, 5, 0, 5)
        g_lay.setSpacing(15)

        descr = QLabel(Lng.filters_descr[Cfg.lng])
        descr.setWordWrap(True)
        g_lay.addWidget(descr)

        self.text_wid = UTextEdit()
        self.text_wid.setFixedHeight(220)
        self.text_wid.setPlaceholderText(Lng.filters[Cfg.lng])
        self.text_wid.setPlainText("\n".join(self.filters_copy))
        g_lay.addWidget(self.text_wid)