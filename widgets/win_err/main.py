from PyQt5.QtWidgets import QMessageBox


class WinErr(QMessageBox):
    def __init__(self, title: str, descr: str):
        super().__init__()
        self.setIcon(QMessageBox.Icon.Warning)
        self.setWindowTitle(title)
        self.setText(descr)
        self.exec()