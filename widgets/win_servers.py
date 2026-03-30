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

        edit = QAction(Lng.edit[Cfg.lng_index], self.menu_)
        edit.triggered.connect(
            lambda: self.edit_server.emit(list_item.server_item)
        )
        self.menu_.addAction(edit)

        rem = QAction(Lng.delete[Cfg.lng_index], self.menu_)
        rem.triggered.connect(
            lambda: self.remove_server.emit(list_item.server_item)
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
        self.cancel_btn.clicked.connect(self.deleteLater)
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
        self.setFixedSize(350, 250)

        self.central_layout.setContentsMargins(5, 5, 5, 5)
        self.central_layout.setSpacing(10)

        favs = QLabel(Lng.favorites[Cfg.lng_index])
        self.central_layout.addWidget(favs)

        self.v_list = ServerList()
        self.v_list.edit_server.connect(self.show_login_win)
        self.v_list.remove_server.connect(self.remove_cmd)
        self.central_layout.addWidget(self.v_list)

        # Кнопки
        btn_widget = QWidget()
        btn_layout = QHBoxLayout()
        btn_widget.setLayout(btn_layout)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)
        self.central_layout.addWidget(btn_widget)

        btn_layout.addStretch()

        btn_add = SmallBtn(Lng.add[Cfg.lng_index])
        btn_add.setFixedWidth(90)
        btn_add.clicked.connect(self.show_login_win)
        btn_layout.addWidget(btn_add)

        btn_connect = SmallBtn(Lng.connect[Cfg.lng_index])
        btn_connect.setFixedWidth(90)
        btn_connect.clicked.connect(self.connect_cmd)
        btn_layout.addWidget(btn_connect)

        self.adjustSize()
        self.setFocus()
        self.init_data()

    # Загрузка данных из JSON
    def init_data(self):
        for server, login, pass_ in Servers.items:
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
        
        if Servers.items:
            self.v_list.setCurrentRow(0)


    def show_login_win(self, server_item: ServerItem = None):

        def ok_pressed(new_server_item: ServerItem):
            if server_item:
                self.remove_cmd(server_item)
            Servers.items.append([
                new_server_item.server,
                new_server_item.login,
                new_server_item.password
            ])
            Servers.write_json_data()
            list_item = ServerListItem(
                parent=self.v_list,
                text=new_server_item.server,
                server_item=new_server_item
            )
            self.v_list.addItem(list_item)

        self.login_win = LoginWin(server_item)
        self.login_win.ok_pressed.connect(ok_pressed)
        self.login_win.center_to_parent(self.window())
        self.login_win.show()

    def remove_cmd(self, server_item: ServerItem):
        Servers.items.remove([
            server_item.server,
            server_item.login,
            server_item.password
        ])
        Servers.write_json_data()
        for i in range(self.v_list.count()):
            item = self.v_list.item(i)
            if not item:
                continue
            current = (
                item.server_item.server,
                item.server_item.login,
                item.server_item.password
            )
            target = (
                server_item.server,
                server_item.login,
                server_item.password
            )
            if current == target:
                self.v_list.takeItem(i)

    def connect_cmd(self):
        list_item: ServerListItem = self.v_list.currentItem()
        if not list_item:
            return
        server_item = list_item.server_item
        s, l, p = server_item.server, server_item.login, server_item.password
        smb = "smb://"
        ip = s.split(smb)[-1]
        cmd = f"{smb}{l}:{p}@{ip}"
        subprocess.run(["open", cmd])

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)
    