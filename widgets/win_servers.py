import json
import os
import re
import subprocess
import traceback
from dataclasses import dataclass

from PyQt5.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (QAction, QHBoxLayout, QLabel, QPushButton,
                             QSpacerItem, QWidget)

from cfg import Cfg, Static
from system.lang import Lng
from system.servers import Servers
from system.shared_utils import SharedUtils

from ._base_widgets import (SingleActionWindow, SmallBtn, ULineEdit,
                            UListWidgetItem, UMenu, VListWidget)


@dataclass(slots=True)
class ServerItem:
    server: str
    login: str
    password: str


class ServerListItem(UListWidgetItem):
    def __init__(self, parent: VListWidget, text: str, server_item: ServerItem):
        super().__init__(parent=parent, text=text)
        self.server_item = server_item


class ServerList(VListWidget):
    edit_server = pyqtSignal(ServerItem)
    remove_server = pyqtSignal(ServerItem)

    def __init__(self, parent = None):
        super().__init__(parent)

    def contextMenuEvent(self, a0):
        list_item: ServerListItem = self.itemAt(a0.pos())
        if not list_item:
            return

        self.menu_ = UMenu(a0)

        edit = QAction("Редактировать", self.menu_)
        edit.triggered.connect(
            lambda: self.edit_server.emit(list_item.server_item)
        )
        self.menu_.addAction(edit)

        rem = QAction("Удалить", self.menu_)
        rem.triggered.connect(
            lambda: self.edit_server.emit(list_item.server_item)
        )
        self.menu_.addAction(rem)

        self.menu_.show_menu()


class LoginWin(SingleActionWindow):
    ok_pressed = pyqtSignal(ServerItem)

    def __init__(self, server_item: ServerItem = None):

        super().__init__()
        self.setFixedWidth(300)

        server_label = QLabel(text=Lng.server[Cfg.lng_index])
        self.central_layout.addWidget(server_label)

        self.server = ULineEdit()
        self.server.setPlaceholderText(Lng.server[Cfg.lng_index])
        self.central_layout.addWidget(self.server)

        login_label = QLabel(text=Lng.login[Cfg.lng_index])
        self.central_layout.addWidget(login_label)

        self.login = ULineEdit()
        self.login.setPlaceholderText(f"{Lng.login[Cfg.lng_index]}")
        self.central_layout.addWidget(self.login)

        self.central_layout.addSpacerItem(QSpacerItem(0, 10))

        pass_label = QLabel(text=Lng.password[Cfg.lng_index])
        self.central_layout.addWidget(pass_label)

        self.pass_ = ULineEdit()
        self.pass_.setPlaceholderText(f"{Lng.password[Cfg.lng_index]}")
        self.central_layout.addWidget(self.pass_)

        self.central_layout.addSpacerItem(QSpacerItem(0, 10))

        self.btn_layout = QHBoxLayout()
        self.btn_layout.setSpacing(10)
        self.central_layout.addLayout(self.btn_layout)

        self.btn_layout.addStretch()

        self.ok_btn = SmallBtn(Lng.ok[Cfg.lng_index])
        self.ok_btn.clicked.connect(self.ok_cmd)
        self.ok_btn.setFixedWidth(90)
        self.btn_layout.addWidget(self.ok_btn)

        self.cancel_btn = SmallBtn(Lng.cancel[Cfg.lng_index])
        self.cancel_btn.setFixedWidth(90)
        self.btn_layout.addWidget(self.cancel_btn)

        self.btn_layout.addStretch()

        if server_item:
            self.server.setText(server_item.server)
            self.login.setText(server_item.login)
            self.pass_.setText(server_item.password)

        self.adjustSize()

    def ok_cmd(self):
        if self.server.text() and self.login.text() and self.pass_.text():
            server_item = ServerItem(
                server=self.server.text(),
                login=self.login.text(),
                password=self.pass_.text()
            )
            self.ok_pressed.emit(server_item)
            self.deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        elif a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.ok_cmd()
        return super().keyPressEvent(a0)


class ServersWin(SingleActionWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Lng.connect_to_server[Cfg.lng_index])
        self.setFixedWidth(400)

        self.central_layout.setContentsMargins(5, 5, 5, 5)
        self.central_layout.setSpacing(10)

        favs = QLabel(Lng.favorites[Cfg.lng_index])
        self.central_layout.addWidget(favs)

        self.v_list = ServerList()
        self.v_list.edit_server.connect(self.login_win)
        self.v_list.setFixedHeight(110)
        self.central_layout.addWidget(self.v_list)

        # Кнопки
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(5)

        # + и - слева
        btn_add = SmallBtn("+")
        btn_add.setFixedWidth(50)
        btn_add.clicked.connect(self.login_win)

        btn_remove = SmallBtn("–")
        btn_remove.setFixedWidth(50)
        # btn_remove.clicked.connect(lambda: self.remove_btn_cmd())

        # Connect справа
        btn_connect = SmallBtn(Lng.connect[Cfg.lng_index])
        # btn_connect.clicked.connect(self.connect_cmd)

        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_remove)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_connect)

        self.central_layout.addWidget(btn_widget)

        self.adjustSize()
        self.setFocus()
        self.init_data()

    # Загрузка данных из JSON
    def init_data(self):
        try:
            with open(Static.external_servers, "r", encoding="utf-8") as f:
                server_list = json.load(f)
            for server, login, pass_ in server_list:
                server_item = ServerItem(
                    server=server,
                    login=login,
                    password=pass_
                )
                list_item = ServerListItem(
                    parent=self.v_list,
                    text=server,
                    server_item=server_item
                )
                self.v_list.addItem(list_item)
        except Exception as e:
            print(traceback.format_exc())

    def login_win(self, server_item: ServerItem = None):

        def ok_pressed(new_server_item: ServerItem):

            data = (
                new_server_item.server,
                new_server_item.login,
                new_server_item.password
            )

            Servers.server_list.append((
                new_server_item.server,
                new_server_item.login,
                new_server_item.password
            ))
            Servers.write_json_data()

            item = ServerListItem(
                parent=self.v_list,
                text=server_item.server,
                server_item=server_item
            )
            self.v_list.addItem(item)

        self.login_win = LoginWin(server_item)
        self.login_win.ok_pressed.connect(ok_pressed)
        self.login_win.center_to_parent(self.window())
        self.login_win.show()


    # def remove_btn_cmd(self):
    #     ind = self.servers_widget.currentIndex()
    #     if ind.isValid():
    #         text = self.servers_widget.get_row_text(ind)
    #         self.servers_widget.model_.removeRow(ind.row())
    #         self.remove_server(text)

    # def remove_server(self, text: str):
    #     self.data.remove(text.split(", "))
    #     self.save_cmd()

    # def save_cmd(self):
        # Servers.server_list = self.data
        # Servers.write_json_data()

    # def is_good_server(self, text: str):
    #     pattern = r"^smb://[\w.-]+/[\w.-]+$"
    #     if re.match(pattern, text):
    #         return True
    #     return False

    # def connect_cmd(self):
    #     text = self.new_server.text()
    #     if text and self.is_good_server(text):
    #         self.show_login_window(text)
    #     else:
    #         item = self.v_list.currentItem()
    #         t = item.text()
    #         print(t, "выделеннаятстрока")

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
    