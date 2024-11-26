from PyQt5.QtWidgets import *

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.button = QPushButton("Change it!", self)
        self.button.clicked.connect(self.change_label)
        layout.addWidget(self.button)

        self.label = QLabel(self)
        self.label.setText("I'm going to change and get bigger!")
        layout.addWidget(self.label)

    def change_label(self):
        self.label.setText("I'm bigger then I was before, unfortunately I'm not fully shown. Can you help me? :)")


app = QApplication([])
main = MainWindow()
main.show()
app.exec()