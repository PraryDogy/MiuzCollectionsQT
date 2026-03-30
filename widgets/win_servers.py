import json
import os
import re
import subprocess

from PyQt5.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QListWidgetItem, QPushButton,
                             QSpacerItem, QWidget)

from cfg import Cfg, Static
from system.lang import Lng
from system.servers import Servers
from system.shared_utils import SharedUtils

from ._base_widgets import (SingleActionWindow, SmallBtn, ULineEdit,
                            UListWidgetItem, VListWidget)


class LoginWin(SingleActionWindow):
    def __init__(self, title: str):
        super().__init__()
        self.setFixedWidth(300)
        self.setWindowTitle(title)

        login = QLabel(text=Lng.login[Cfg.lng_index])
        self.central_layout.addWidget(login)

        self.login = ULineEdit()
        self.login.setPlaceholderText(f"{Lng.login[Cfg.lng_index]}")
        self.central_layout.addWidget(self.login)

        self.central_layout.addSpacerItem(QSpacerItem(0, 10))

        pass_ = QLabel(text=Lng.password[Cfg.lng_index])
        self.central_layout.addWidget(pass_)

        self.pass_ = ULineEdit()
        self.pass_.setPlaceholderText(f"{Lng.password[Cfg.lng_index]}")
        self.central_layout.addWidget(self.pass_)

        self.central_layout.addSpacerItem(QSpacerItem(0, 10))

        self.btn_layout = QHBoxLayout()
        self.btn_layout.setSpacing(10)
        self.central_layout.addLayout(self.btn_layout)

        self.btn_layout.addStretch()

        self.ok_btn = SmallBtn(Lng.ok[Cfg.lng_index])
        self.ok_btn.setFixedWidth(90)
        self.btn_layout.addWidget(self.ok_btn)

        self.cancel_btn = SmallBtn(Lng.cancel[Cfg.lng_index])
        self.cancel_btn.setFixedWidth(90)
        self.btn_layout.addWidget(self.cancel_btn)

        self.btn_layout.addStretch()

        self.adjustSize()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        elif a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.deleteLater()
        return super().keyPressEvent(a0)


class ServersWin(SingleActionWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Lng.connect_to_server[Cfg.lng_index])
        self.setFixedWidth(400)

        # Загрузка данных
        self.data: list[list[str]] = []
        self.init_data()

        self.central_layout.setContentsMargins(5, 5, 5, 5)
        self.central_layout.setSpacing(10)

        self.new_server = ULineEdit()
        self.new_server.setPlaceholderText(f"{Lng.server[Cfg.lng_index]}")
        self.central_layout.addWidget(self.new_server)

        favs = QLabel(Lng.favorites[Cfg.lng_index])
        self.central_layout.addWidget(favs)

        self.v_list = VListWidget()
        self.v_list.setFixedHeight(110)
        self.central_layout.addWidget(self.v_list)

        # for i in range(0, 3):
        #     item = UListWidgetItem(self.v_list, text="server" + str(i))
        #     self.v_list.addItem(item)

        # Кнопки
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(5)

        # + и - слева
        btn_add = SmallBtn("+")
        btn_add.setFixedWidth(50)
        btn_add.clicked.connect(self.add_server)

        btn_remove = SmallBtn("–")
        btn_remove.setFixedWidth(50)
        btn_remove.clicked.connect(lambda: self.remove_btn_cmd())

        # Connect справа
        btn_connect = SmallBtn(Lng.connect[Cfg.lng_index])
        # btn_connect.setFixedWidth(90)
        btn_connect.clicked.connect(self.connect_cmd)

        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_remove)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_connect)

        self.central_layout.addWidget(btn_widget)

        self.adjustSize()
        self.setFocus()

        self.new_server.setText(
            "smb://192.168.10.105/Shares"
        )

    # Загрузка данных из JSON
    def init_data(self):
        if os.path.exists(Static.external_servers):
            with open(Static.external_servers, "r", encoding="utf-8") as f:
                self.data = json.load(f)

    def add_server(self):
        text = self.new_server.text().strip()
        if not text:
            return

        parts = [p.strip() for p in text.split(",")]
        if len(parts) != 3:
            return  # неправильный формат

        server, login, password = parts

        # Добавляем в QListWidget
        item_text = f"{server}, {login}, {password}"
        item = QListWidgetItem(item_text)
        item.setSizeHint(QSize(0, 25))
        self.servers_widget.add_row(parts)

        # Добавляем в self.data
        self.data.append(parts)

        # Очищаем QLineEdit
        self.new_server.clear()

        # Сохраняем
        self.save_cmd()

    def remove_btn_cmd(self):
        ind = self.servers_widget.currentIndex()
        if ind.isValid():
            text = self.servers_widget.get_row_text(ind)
            self.servers_widget.model_.removeRow(ind.row())
            self.remove_server(text)

    def remove_server(self, text: str):
        self.data.remove(text.split(", "))
        self.save_cmd()

    def save_cmd(self):
        Servers.server_list = self.data
        Servers.write_json_data()

    def show_login_window(self, text: str):
        self.login_win = LoginWin(text)
        self.login_win.center_to_parent(self.window())
        self.login_win.show()

    def is_good_server(self, text: str):
        pattern = r"^smb://[\w.-]+/[\w.-]+$"
        if re.match(pattern, text):
            return True
        return False

    def connect_cmd(self):
        text = self.new_server.text()
        if text and self.is_good_server(text):
            self.show_login_window(text)
        else:
            item = self.v_list.currentItem()
            t = item.text()
            print(t, "выделеннаятстрока")

        return
        delay = 0
        for server, login, password in self.data:
            if SharedUtils.is_mounted(server):
                continue
            smb = "smb://"
            ip = server.split(smb)[-1]
            cmd = f"{smb}{login}:{password}@{ip}"
            QTimer.singleShot(delay, lambda c=cmd: subprocess.run(["open", c]))
            delay += 200  # задержка 200 мс между подключениями
        QTimer.singleShot(delay + 100, self.deleteLater)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.connect_cmd()
        return super().keyPressEvent(a0)
    